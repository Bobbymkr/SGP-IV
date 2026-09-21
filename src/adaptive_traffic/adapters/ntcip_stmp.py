"""
NTCIP 1202 STMP Adapter
Actuation via NTCIP 1202 Standard for Signal Control (STMP/STP)
Handles phase timing, cycle length, offset SET/GET operations over UDP.
"""

import logging
import socket
import struct
import time
from typing import List, Optional

from adaptive_traffic.core.monitoring import observe
from adaptive_traffic.core.ports.ntcip_port import (
    NTCIPCycleConfig,
    NTCIPPhaseTiming,
    NTCIPPort,
)

logger = logging.getLogger(__name__)


class NTCIP1202STMPAdapter(NTCIPPort):
    """NTCIP 1202 STMP adapter for signal controller actuation"""

    # NTCIP 1202 OIDs for phase timing objects (per NTCIP 1202 v03)
    OID_PHASE_GREEN = "1.3.6.1.4.1.1206.4.2.2.1.1"  # phaseGreen
    OID_PHASE_YELLOW = "1.3.6.1.4.1.1206.4.2.2.1.2"  # phaseYellow
    OID_PHASE_RED = "1.3.6.1.4.1.1206.4.2.2.1.3"  # phaseRed
    OID_CYCLE_LENGTH = "1.3.6.1.4.1.1206.4.2.3.1.0"  # cycleLength
    OID_OFFSET = "1.3.6.1.4.1.1206.4.2.3.2.0"  # offset
    OID_MAX_GREEN = "1.3.6.1.4.1.1206.4.2.2.1.4"  # maxGreen
    OID_MIN_GREEN = "1.3.6.1.4.1.1206.4.2.2.1.5"  # minGreen

    # STMP protocol constants
    STMP_PORT = 5000
    STMP_VERSION = 1
    STMP_SET_REQUEST = 0x40
    STMP_GET_REQUEST = 0x41
    STMP_RESPONSE = 0x42

    def __init__(self, config: dict):
        self.config = config
        self.controller_ip = config.get("ntcip_controller_ip", "127.0.0.1")
        self.controller_port = config.get("ntcip_stmp_port", self.STMP_PORT)
        self.community = config.get("ntcip_community", "public")
        self.timeout = config.get("ntcip_timeout", 5.0)
        self.max_retries = config.get("ntcip_max_retries", 3)

        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._transaction_id = 0

        # Phase mapping: direction -> phase number
        self.phase_mapping = config.get(
            "ntcip_phase_mapping", {"north": 1, "south": 2, "east": 3, "west": 4}
        )

        logger.info(
            f"NTCIP 1202 STMP adapter initialized for {self.controller_ip}:{self.controller_port}"
        )

    def _create_socket(self) -> socket.socket:
        """Create UDP socket for STMP communication"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        return sock

    def _next_transaction_id(self) -> int:
        """Generate next transaction ID"""
        self._transaction_id = (self._transaction_id + 1) % 65536
        return self._transaction_id

    def _build_stmp_header(self, pdu_type: int, transaction_id: int) -> bytes:
        """Build STMP header: version(1) | pdu_type(1) | transaction_id(2) | community_len(1) | community"""
        community_bytes = self.community.encode("ascii")
        header = struct.pack(
            "!BBBHB", self.STMP_VERSION, pdu_type, 0, transaction_id, len(community_bytes)  # flags
        )
        return header + community_bytes

    def _encode_oid(self, oid: str) -> bytes:
        """Encode OID string to BER format"""
        parts = [int(x) for x in oid.split(".")]
        if len(parts) < 2:
            raise ValueError("Invalid OID")
        # First two components encoded as 40 * first + second
        encoded = [40 * parts[0] + parts[1]]
        for part in parts[2:]:
            encoded.append(part)
        # BER encode each part (base-128, continuation bit on every
        # group except the last-emitted one)
        result = b""
        for part in encoded:
            if part < 128:
                result += struct.pack("!B", part)
            else:
                # Multi-byte encoding
                bytes_needed = (part.bit_length() + 6) // 7
                for i in range(bytes_needed - 1, -1, -1):
                    byte = (part >> (7 * i)) & 0x7F
                    if i != 0:
                        byte |= 0x80
                    result += struct.pack("!B", byte)
        return result

    @staticmethod
    def _encode_length(n: int) -> bytes:
        """BER length octets: short form below 128, long form above.

        A full 4-phase SET is ~300 bytes of varbinds, so the single-byte
        prefix used to crash packing ("ubyte format requires ... <= 255")
        before anything reached the wire.
        """
        if n < 128:
            return struct.pack("!B", n)
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return struct.pack("!B", 0x80 | len(raw)) + raw

    def _build_varbind(self, oid: str, value: int) -> bytes:
        """Build SNMP varbind for STMP payload"""
        oid_bytes = self._encode_oid(oid)
        # Integer value encoding
        if value < 128:
            value_bytes = struct.pack("!B", value)
        else:
            value_bytes = struct.pack("!H", value) if value < 65536 else struct.pack("!I", value)

        # Varbind: SEQUENCE { OID, INTEGER }
        varbind_content = b"\x06" + self._encode_length(len(oid_bytes)) + oid_bytes
        varbind_content += b"\x02" + self._encode_length(len(value_bytes)) + value_bytes
        return b"\x30" + self._encode_length(len(varbind_content)) + varbind_content

    def _send_stmp_request(self, pdu_type: int, varbinds: List[bytes]) -> Optional[bytes]:
        """Send STMP request and return response"""
        if self._socket is None:
            self._socket = self._create_socket()

        transaction_id = self._next_transaction_id()
        header = self._build_stmp_header(pdu_type, transaction_id)

        # Build varbind list
        varbind_list = b"".join(varbinds)
        varbind_list = b"\x30" + self._encode_length(len(varbind_list)) + varbind_list

        # Complete PDU
        pdu = header + varbind_list

        for attempt in range(self.max_retries):
            try:
                self._socket.sendto(pdu, (self.controller_ip, self.controller_port))
                response, _ = self._socket.recvfrom(4096)
                self._connected = True
                return response
            except socket.timeout:
                logger.warning(f"STMP request timeout (attempt {attempt + 1}/{self.max_retries})")
                self._connected = False
            except Exception as e:
                logger.error(f"STMP request failed: {e}")
                self._connected = False

        return None

    def _parse_stmp_response(self, response: bytes) -> dict:
        """Parse STMP response and return dict of OID -> value"""
        # Simplified parsing - in production, use proper ASN.1 parser
        # For now, return mock data for testing
        return {}

    @observe("actuate")
    def set_phase_timing(self, timing: NTCIPCycleConfig) -> bool:
        """Apply phase timing via NTCIP 1202 STMP SET"""
        try:
            varbinds = []

            # Set cycle length
            cycle_oid = self.OID_CYCLE_LENGTH
            varbinds.append(self._build_varbind(cycle_oid, int(timing.cycle_length)))

            # Set offset
            offset_oid = self.OID_OFFSET
            varbinds.append(
                self._build_varbind(offset_oid, int(timing.offset * 10))
            )  # tenths of second

            # Set phase timings
            for phase in timing.phases:
                phase_num = phase.phase_number
                green_oid = f"{self.OID_PHASE_GREEN}.{phase_num}"
                yellow_oid = f"{self.OID_PHASE_YELLOW}.{phase_num}"
                red_oid = f"{self.OID_PHASE_RED}.{phase_num}"

                varbinds.append(self._build_varbind(green_oid, int(phase.green_time)))
                varbinds.append(self._build_varbind(yellow_oid, int(phase.yellow_time)))
                varbinds.append(self._build_varbind(red_oid, int(phase.red_time)))

            response = self._send_stmp_request(self.STMP_SET_REQUEST, varbinds)

            if response:
                logger.info(
                    f"STMP SET successful: cycle={timing.cycle_length}s, offset={timing.offset}s"
                )
                return True
            else:
                logger.error("STMP SET failed - no response")
                return False

        except Exception as e:
            logger.error(f"STMP SET failed: {e}")
            return False

    def get_phase_timing(self) -> Optional[NTCIPCycleConfig]:
        """Get current phase timing via NTCIP 1202 STMP GET"""
        try:
            varbinds = []

            # Request cycle length
            varbinds.append(self._build_varbind(self.OID_CYCLE_LENGTH, 0))

            # Request offset
            varbinds.append(self._build_varbind(self.OID_OFFSET, 0))

            # Request phase timings for all mapped phases
            for direction, phase_num in self.phase_mapping.items():
                varbinds.append(self._build_varbind(f"{self.OID_PHASE_GREEN}.{phase_num}", 0))
                varbinds.append(self._build_varbind(f"{self.OID_PHASE_YELLOW}.{phase_num}", 0))
                varbinds.append(self._build_varbind(f"{self.OID_PHASE_RED}.{phase_num}", 0))

            response = self._send_stmp_request(self.STMP_GET_REQUEST, varbinds)

            if response:
                parsed = self._parse_stmp_response(response)
                return self._build_cycle_config(parsed)
            else:
                logger.warning("STMP GET failed - no response")
                return None

        except Exception as e:
            logger.error(f"STMP GET failed: {e}")
            return None

    def _build_cycle_config(self, parsed: dict) -> NTCIPCycleConfig:
        """Build NTCIPCycleConfig from parsed response"""
        cycle_length = parsed.get(self.OID_CYCLE_LENGTH, 120)
        offset = parsed.get(self.OID_OFFSET, 0) / 10.0

        phases = []
        for direction, phase_num in self.phase_mapping.items():
            green = parsed.get(f"{self.OID_PHASE_GREEN}.{phase_num}", 30)
            yellow = parsed.get(f"{self.OID_PHASE_YELLOW}.{phase_num}", 5)
            red = parsed.get(f"{self.OID_PHASE_RED}.{phase_num}", 85)
            phases.append(
                NTCIPPhaseTiming(
                    phase_number=phase_num, green_time=green, yellow_time=yellow, red_time=red
                )
            )

        return NTCIPCycleConfig(cycle_length=cycle_length, offset=offset, phases=phases)

    # SNMP monitoring methods - delegate to SNMP adapter or return empty
    def get_detector_status(self) -> List:
        return []

    def get_faults(self) -> List:
        return []

    def get_cycle_counters(self) -> List:
        return []

    def is_connected(self) -> bool:
        """Check if controller is reachable via STMP"""
        try:
            # Send a simple GET for cycle length as health check
            varbinds = [self._build_varbind(self.OID_CYCLE_LENGTH, 0)]
            response = self._send_stmp_request(self.STMP_GET_REQUEST, varbinds)
            return response is not None
        except Exception:
            return False

    def close(self):
        """Close the STMP socket"""
        if self._socket:
            self._socket.close()
            self._socket = None
            self._connected = False


class MockNTCIP1202STMPAdapter(NTCIP1202STMPAdapter):
    """Mock STMP adapter for testing without real controller"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._mock_cycle_config = NTCIPCycleConfig(
            cycle_length=120,
            offset=0,
            phases=[
                NTCIPPhaseTiming(1, 30, 5, 85),
                NTCIPPhaseTiming(2, 30, 5, 85),
                NTCIPPhaseTiming(3, 30, 5, 85),
                NTCIPPhaseTiming(4, 30, 5, 85),
            ],
        )
        self._mock_connected = True
        logger.info("Mock NTCIP 1202 STMP adapter initialized")

    def _send_stmp_request(self, pdu_type: int, varbinds: List[bytes]) -> Optional[bytes]:
        """Mock STMP request - always succeeds"""
        return b"mock_response"

    def _parse_stmp_response(self, response: bytes) -> dict:
        """Return mock parsed data"""
        return {
            self.OID_CYCLE_LENGTH: self._mock_cycle_config.cycle_length,
            self.OID_OFFSET: int(self._mock_cycle_config.offset * 10),
            **{
                f"{self.OID_PHASE_GREEN}.{p.phase_number}": int(p.green_time)
                for p in self._mock_cycle_config.phases
            },
            **{
                f"{self.OID_PHASE_YELLOW}.{p.phase_number}": int(p.yellow_time)
                for p in self._mock_cycle_config.phases
            },
            **{
                f"{self.OID_PHASE_RED}.{p.phase_number}": int(p.red_time)
                for p in self._mock_cycle_config.phases
            },
        }

    def set_phase_timing(self, timing: NTCIPCycleConfig) -> bool:
        """Mock SET - update internal state"""
        if not self._mock_connected:
            logger.warning("Mock STMP SET failed: not connected")
            return False
        self._mock_cycle_config = timing
        logger.info(f"Mock STMP SET: cycle={timing.cycle_length}s, offset={timing.offset}s")
        return True

    def get_phase_timing(self) -> Optional[NTCIPCycleConfig]:
        """Mock GET - return current state"""
        return self._mock_cycle_config

    def is_connected(self) -> bool:
        return self._mock_connected

    def set_connected(self, connected: bool):
        """Set mock connection state"""
        self._mock_connected = connected
