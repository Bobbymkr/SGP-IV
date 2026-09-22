"""
J2735 V2X Adapter
Encoder/decoder for J2735 2020 messages:
- BSM (Basic Safety Message) - receive from connected vehicles
- SPAT (Signal Phase and Timing) - transmit to connected vehicles
- MAP (Map Data) - static intersection geometry (loaded from city profile)
"""

import logging
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from adaptive_traffic.core.ports.ntcip_port import J2735BSM, J2735MAP, J2735SPAT, J2735Port, NTCIPCycleConfig

logger = logging.getLogger(__name__)


# J2735 Message IDs (per J2735 2020)
MSG_ID_BSM = 0x12  # Basic Safety Message
MSG_ID_SPAT = 0x13  # Signal Phase and Timing
MSG_ID_MAP = 0x14  # Map Data


@dataclass
class BSMVehicleData:
    """Parsed vehicle data from BSM for queue refinement"""

    temp_id: int
    latitude: float  # decimal degrees
    longitude: float
    speed: float  # m/s
    heading: float  # degrees
    lane_id: Optional[int] = None
    distance_to_stop_line: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


class J2735Adapter(J2735Port):
    """J2735 V2X adapter for BSM receive + SPAT transmit"""

    def __init__(self, config: dict):
        self.config = config
        self.bsm_port = config.get("j2735_bsm_port", 1735)  # UDP port for BSM receive
        self.spat_port = config.get("j2735_spat_port", 1736)  # UDP port for SPAT transmit
        self.broadcast_ip = config.get("j2735_broadcast_ip", "255.255.255.255")
        self.tx_power_dbm = config.get("j2735_tx_power_dbm", 20)
        self.transmit_interval = config.get("j2735_transmit_interval", 0.1)  # 100ms = 10Hz

        self._bsm_socket: Optional[socket.socket] = None
        self._spat_socket: Optional[socket.socket] = None
        self._map_data: Optional[J2735MAP] = None
        self._last_transmit = 0
        self._intersection_id = config.get("intersection_id", "main")

        # BSM parsing config
        self.max_bsm_age = config.get("j2735_max_bsm_age", 1.0)  # seconds
        self.bsm_buffer: List[BSMVehicleData] = []

        logger.info(
            f"J2735 adapter initialized: BSM rx on {self.bsm_port}, SPAT tx on {self.spat_port}"
        )

    def _create_bsm_socket(self) -> socket.socket:
        """Create UDP socket for BSM reception"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.bsm_port))
        sock.setblocking(False)
        return sock

    def _create_spat_socket(self) -> socket.socket:
        """Create UDP socket for SPAT transmission"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def load_map(self, map_data: J2735MAP) -> bool:
        """Load static MAP data for intersection"""
        self._map_data = map_data
        logger.info(f"Loaded MAP data for {len(map_data.intersections)} intersections")
        return True

    def load_map_from_city_profile(self, city_profile: dict) -> bool:
        """Load MAP from city profile geometry"""
        try:
            # City profile contains intersection geometry
            geometry = city_profile.get("intersection_geometry", {})
            approaches = geometry.get("approaches", ["north", "south", "east", "west"])
            lanes_per_approach = geometry.get("lanes_per_approach", 2)
            lane_width = geometry.get("lane_width", 3.5)
            stop_line_positions = geometry.get("stop_line_positions", {})

            # Build MAP structure
            intersections = []
            for i, approach in enumerate(approaches):
                intersection = {
                    "id": i + 1,
                    "name": approach,
                    "ref_point": {
                        "lat": stop_line_positions.get(approach, {}).get("lat", 0),
                        "lon": stop_line_positions.get(approach, {}).get("lon", 0),
                        "elevation": stop_line_positions.get(approach, {}).get("elevation", 0),
                    },
                    "lanes": [],
                }
                for lane_idx in range(lanes_per_approach):
                    lane = {
                        "lane_id": lane_idx,
                        "ingress_approach": i,
                        "egress_approach": i,
                        "lane_width": lane_width,
                        "lane_attributes": {
                            "directional_use": "ingress",
                            "shared_with": [],
                            "lane_type": "vehicle",
                        },
                    }
                    intersection["lanes"].append(lane)
                intersections.append(intersection)

            self._map_data = J2735MAP(msg_id=MSG_ID_MAP, intersections=intersections)
            logger.info(
                f"Built MAP from city profile: {len(approaches)} approaches, {lanes_per_approach} lanes each"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to build MAP from city profile: {e}")
            return False

    def receive_bsm(self) -> List[J2735BSM]:
        """Receive BSM messages from connected vehicles"""
        if self._bsm_socket is None:
            self._bsm_socket = self._create_bsm_socket()

        bsms = []
        current_time = time.time()

        try:
            while True:
                data, addr = self._bsm_socket.recvfrom(4096)
                bsm = self._decode_bsm(data)
                if bsm:
                    bsms.append(bsm)
                    # Also parse for queue refinement
                    vehicle_data = self._parse_bsm_for_queue(bsm)
                    if vehicle_data:
                        self.bsm_buffer.append(vehicle_data)
        except BlockingIOError:
            pass  # No more data
        except Exception as e:
            logger.error(f"BSM receive error: {e}")

        # Clean old BSMs
        self.bsm_buffer = [
            v for v in self.bsm_buffer if current_time - v.timestamp < self.max_bsm_age
        ]

        return bsms

    def _decode_bsm(self, data: bytes) -> Optional[J2735BSM]:
        """Decode raw BSM payload (UPER encoded per J2735)"""
        # Simplified decoder - real implementation needs ASN.1 UPER codec
        # For now, return mock parsed data
        try:
            # In production, use asn1tools or similar for UPER decoding
            # This is a placeholder that returns mock data
            if len(data) < 20:
                return None

            # Mock parsing - extract basic fields assuming known structure
            # Real BSM has: msgId, tempId, secMark, lat, long, elev, speed, heading, accelSet, brakes, size, vehicleClass
            temp_id = struct.unpack("!I", data[1:5])[0] if len(data) >= 5 else 0
            lat = struct.unpack("!i", data[5:9])[0] if len(data) >= 9 else 0
            lon = struct.unpack("!i", data[9:13])[0] if len(data) >= 13 else 0
            speed = struct.unpack("!H", data[13:15])[0] if len(data) >= 15 else 0
            heading = struct.unpack("!H", data[15:17])[0] if len(data) >= 17 else 0

            return J2735BSM(
                msg_id=MSG_ID_BSM,
                temp_id=temp_id,
                sec_mark=int(time.time() * 1000) % 60000,
                latitude=lat,
                longitude=lon,
                elevation=0,
                speed=speed,
                heading=heading,
                accel_set={"long": 0, "lat": 0, "vert": 0, "yaw": 0},
                brakes={
                    "wheel": False,
                    "traction": False,
                    "abs": False,
                    "scs": False,
                    "brake_boost": False,
                    "aux": False,
                },
                size={"width": 180, "length": 450},
                vehicle_class=0,
            )
        except Exception as e:
            logger.debug(f"BSM decode failed: {e}")
            return None

    def _parse_bsm_for_queue(self, bsm: J2735BSM) -> Optional[BSMVehicleData]:
        """Parse BSM into vehicle data for queue length refinement"""
        if not self._map_data:
            return None

        try:
            # Convert lat/lon to local coordinates (simplified)
            # Real implementation uses map projection
            lat_deg = bsm.latitude / 1e7
            lon_deg = bsm.longitude / 1e7
            speed_ms = bsm.speed / 100.0  # cm/s to m/s
            heading_deg = bsm.heading / 125.0  # 1/125 degree units

            # Determine which approach/lane the vehicle is on
            # This is simplified - real implementation uses MAP geometry
            lane_id = self._estimate_lane(lat_deg, lon_deg, heading_deg)
            distance = self._estimate_distance_to_stop_line(lat_deg, lon_deg, lane_id)

            return BSMVehicleData(
                temp_id=bsm.temp_id,
                latitude=lat_deg,
                longitude=lon_deg,
                speed=speed_ms,
                heading=heading_deg,
                lane_id=lane_id,
                distance_to_stop_line=distance,
            )
        except Exception as e:
            logger.debug(f"BSM queue parse failed: {e}")
            return None

    def _estimate_lane(self, lat: float, lon: float, heading: float) -> Optional[int]:
        """Estimate lane ID from position and heading"""
        # Simplified - in reality uses MAP lane geometry
        if not self._map_data:
            return None
        # Mock: return lane based on heading quadrant
        if 315 <= heading or heading < 45:
            return 0  # Northbound
        elif 45 <= heading < 135:
            return 1  # Eastbound
        elif 135 <= heading < 225:
            return 2  # Southbound
        else:
            return 3  # Westbound

    def _estimate_distance_to_stop_line(
        self, lat: float, lon: float, lane_id: Optional[int]
    ) -> Optional[float]:
        """Estimate distance to stop line"""
        # Mock implementation - real uses MAP geometry
        if lane_id is None:
            return None
        return 30.0  # Mock distance within queue zone (< 50m)

    def get_bsm_vehicle_data(self) -> List[BSMVehicleData]:
        """Get parsed BSM vehicle data for queue refinement"""
        return list(self.bsm_buffer)

    def get_queue_refinement(self) -> Dict[str, int]:
        """Get queue length refinement from BSM data

        Returns:
            Dict mapping direction -> additional vehicles detected via BSM
        """
        if not self._map_data:
            return {}

        counts = {approach: 0 for approach in ["north", "south", "east", "west"]}

        for vehicle in self.bsm_buffer:
            if vehicle.distance_to_stop_line is not None and vehicle.distance_to_stop_line < 50:
                # Vehicle is in queue zone
                if vehicle.lane_id is not None:
                    # Map lane to direction (simplified)
                    directions = ["north", "east", "south", "west"]
                    if vehicle.lane_id < len(directions):
                        counts[directions[vehicle.lane_id]] += 1

        return counts

    def transmit_spat(self, spat: J2735SPAT) -> bool:
        """Transmit SPAT message to connected vehicles"""
        if self._spat_socket is None:
            self._spat_socket = self._create_spat_socket()

        current_time = time.time()
        if current_time - self._last_transmit < self.transmit_interval:
            return True  # Rate limited

        try:
            payload = self._encode_spat(spat)
            self._spat_socket.sendto(payload, (self.broadcast_ip, self.spat_port))
            self._last_transmit = current_time
            logger.debug(f"SPAT transmitted: {len(payload)} bytes")
            return True
        except Exception as e:
            logger.error(f"SPAT transmit failed: {e}")
            return False

    def _encode_spat(self, spat: J2735SPAT) -> bytes:
        """Encode SPAT message (UPER per J2735)"""
        # Simplified encoder - real implementation needs ASN.1 UPER codec
        # Build mock payload
        payload = bytearray()
        payload.append(spat.msg_id)

        # Encode intersections
        for intersection in spat.intersections:
            intersection_id = intersection.get("id", 1)
            payload.extend(struct.pack("!H", intersection_id))

            # Encode phase states
            states = intersection.get("states", [])
            for state in states:
                phase = state.get("phase", 1)
                state_val = state.get("state", 3)  # 3 = permissive-movement-allowed (green)
                min_end_time = state.get("min_end_time", 0)
                max_end_time = state.get("max_end_time", 0)

                payload.extend(struct.pack("!B", phase))
                payload.extend(struct.pack("!B", state_val))
                payload.extend(struct.pack("!H", min_end_time))
                payload.extend(struct.pack("!H", max_end_time))

        return bytes(payload)

    def create_spat_from_timing(
        self, timing: "NTCIPCycleConfig", current_phase: int, phase_timer: float
    ) -> J2735SPAT:
        """Create SPAT message from NTCIP cycle config"""
        if not self._map_data:
            return J2735SPAT(msg_id=MSG_ID_SPAT, intersections=[])

        intersections = []
        for i, approach in enumerate(["north", "south", "east", "west"]):
            if i < len(timing.phases):
                phase = timing.phases[i]
                # Determine current state based on phase timer
                if i == current_phase:
                    green_end = phase.green_time
                    yellow_end = phase.green_time + phase.yellow_time
                    if phase_timer < green_end:
                        state = 3  # permissive-movement-allowed (green)
                    elif phase_timer < yellow_end:
                        state = 4  # permissive-clearance (yellow)
                    else:
                        state = 1  # stop-and-remain (red)
                else:
                    state = 1  # stop-and-remain (red)

                intersection = {
                    "id": i + 1,
                    "states": [
                        {
                            "phase": phase.phase_number,
                            "state": state,
                            "min_end_time": int(phase_timer * 10),  # tenths of second
                            "max_end_time": int(
                                (
                                    phase_timer
                                    + (
                                        green_end - phase_timer
                                        if state == 3
                                        else yellow_end - phase_timer
                                    )
                                )
                                * 10
                            ),
                        }
                    ],
                }
                intersections.append(intersection)

        return J2735SPAT(msg_id=MSG_ID_SPAT, intersections=intersections)

    def close(self):
        """Close sockets"""
        if self._bsm_socket:
            self._bsm_socket.close()
            self._bsm_socket = None
        if self._spat_socket:
            self._spat_socket.close()
            self._spat_socket = None


class MockJ2735Adapter(J2735Adapter):
    """Mock J2735 adapter for testing"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._mock_bsms = []
        logger.info("Mock J2735 adapter initialized")

    def _create_bsm_socket(self):
        return None

    def _create_spat_socket(self):
        return None

    def receive_bsm(self) -> List[J2735BSM]:
        return list(self._mock_bsms)

    def transmit_spat(self, spat: J2735SPAT) -> bool:
        logger.debug(f"Mock SPAT transmit: {len(spat.intersections)} intersections")
        return True

    def inject_bsm(self, bsm: J2735BSM):
        """Inject mock BSM for testing"""
        self._mock_bsms.append(bsm)
        vehicle_data = self._parse_bsm_for_queue(bsm)
        if vehicle_data:
            self.bsm_buffer.append(vehicle_data)
