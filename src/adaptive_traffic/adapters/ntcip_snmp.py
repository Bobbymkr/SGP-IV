"""
NTCIP SNMP Adapter
Monitoring via NTCIP SNMP (detector status, faults, cycle counters)
Uses pysnmp for SNMP GET/GETNEXT operations on standard NTCIP MIBs.
"""

import logging
import time
from typing import List, Optional

from adaptive_traffic.core.ports.ntcip_port import (
    NTCIPCycleConfig,
    NTCIPCycleCounter,
    NTCIPDetectorStatus,
    NTCIPFault,
    NTCIPPort,
)

logger = logging.getLogger(__name__)


class NTCIPSNMPAdapter(NTCIPPort):
    """NTCIP SNMP adapter for signal controller monitoring"""

    # NTCIP 1202 SNMP MIB OIDs (NTCIP 1202 v03)
    # Detector status
    OID_DETECTOR_VEHICLE_COUNT = "1.3.6.1.4.1.1206.4.2.4.1.1"  # detectorVehicleCount
    OID_DETECTOR_OCCUPANCY = "1.3.6.1.4.1.1206.4.2.4.1.2"  # detectorOccupancy
    OID_DETECTOR_STATUS = "1.3.6.1.4.1.1206.4.2.4.1.3"  # detectorStatus
    OID_DETECTOR_FAULT = "1.3.6.1.4.1.1206.4.2.4.1.4"  # detectorFault

    # Fault table
    OID_FAULT_TABLE = "1.3.6.1.4.1.1206.4.2.5.1"  # faultTable
    OID_FAULT_CODE = "1.3.6.1.4.1.1206.4.2.5.1.1"  # faultCode
    OID_FAULT_DESCRIPTION = "1.3.6.1.4.1.1206.4.2.5.1.2"  # faultDescription
    OID_FAULT_SEVERITY = "1.3.6.1.4.1.1206.4.2.5.1.3"  # faultSeverity

    # Cycle counters
    OID_CYCLE_COUNTER_TABLE = "1.3.6.1.4.1.1206.4.2.6.1"  # cycleCounterTable
    OID_CYCLE_NUMBER = "1.3.6.1.4.1.1206.4.2.6.1.1"  # cycleNumber
    OID_CYCLE_PHASE = "1.3.6.1.4.1.1206.4.2.6.1.2"  # cyclePhase
    OID_CYCLE_GREEN_ELAPSED = "1.3.6.1.4.1.1206.4.2.6.1.3"  # cycleGreenElapsed

    # Controller status
    OID_CONTROLLER_STATUS = "1.3.6.1.4.1.1206.4.2.1.1.0"  # controllerStatus

    SNMP_PORT = 161
    SNMP_VERSION = 2  # SNMPv2c

    def __init__(self, config: dict):
        self.config = config
        self.controller_ip = config.get("ntcip_controller_ip", "127.0.0.1")
        self.controller_port = config.get("ntcip_snmp_port", self.SNMP_PORT)
        self.community = config.get("ntcip_snmp_community", "public")
        self.timeout = config.get("ntcip_snmp_timeout", 3.0)
        self.retries = config.get("ntcip_snmp_retries", 2)

        self._snmp_engine = None
        self._connected = False
        self._last_poll = 0
        self._poll_interval = config.get("ntcip_snmp_poll_interval", 10)  # seconds

        # Detector mapping: detector_id -> direction
        self.detector_mapping = config.get(
            "ntcip_detector_mapping",
            {
                "1": "north",
                "2": "south",
                "3": "east",
                "4": "west",
            },
        )

        logger.info(
            f"NTCIP SNMP adapter initialized for {self.controller_ip}:{self.controller_port}"
        )

    def _get_snmp_engine(self):
        """Lazy initialization of SNMP engine"""
        if self._snmp_engine is None:
            try:
                from pysnmp.hlapi import CommunityData, ContextData, SnmpEngine, UdpTransportTarget

                self._snmp_engine = {
                    "engine": SnmpEngine(),
                    "auth": CommunityData(self.community, mpModel=1),  # SNMPv2c
                    "target": UdpTransportTarget(
                        (self.controller_ip, self.controller_port),
                        timeout=self.timeout,
                        retries=self.retries,
                    ),
                    "context": ContextData(),
                }
                logger.info("SNMP engine initialized")
            except ImportError:
                logger.warning("pysnmp not installed - SNMP adapter will use mock mode")
                self._snmp_engine = "mock"
            except Exception as e:
                logger.error(f"Failed to initialize SNMP engine: {e}")
                self._snmp_engine = "mock"
        return self._snmp_engine

    def _snmp_get(self, oid: str) -> Optional[str]:
        """SNMP GET request"""
        engine = self._get_snmp_engine()
        if engine == "mock":
            return self._mock_snmp_get(oid)

        try:
            from pysnmp.hlapi import ObjectIdentity, ObjectType, getCmd

            iterator = getCmd(
                engine["engine"],
                engine["auth"],
                engine["target"],
                engine["context"],
                ObjectType(ObjectIdentity(oid)),
            )
            error_indication, error_status, error_index, var_binds = next(iterator)

            if error_indication:
                logger.warning(f"SNMP GET error for {oid}: {error_indication}")
                self._connected = False
                return None
            elif error_status:
                logger.warning(f"SNMP GET error for {oid}: {error_status}")
                self._connected = False
                return None
            else:
                self._connected = True
                for var_bind in var_binds:
                    return str(var_bind[1])
        except Exception as e:
            logger.error(f"SNMP GET failed for {oid}: {e}")
            self._connected = False
        return None

    def _snmp_getnext(self, oid: str) -> List[tuple]:
        """SNMP GETNEXT request for table walking"""
        engine = self._get_snmp_engine()
        if engine == "mock":
            return self._mock_snmp_getnext(oid)

        try:
            from pysnmp.hlapi import ObjectIdentity, ObjectType, nextCmd

            results = []
            iterator = nextCmd(
                engine["engine"],
                engine["auth"],
                engine["target"],
                engine["context"],
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False,
            )
            for error_indication, error_status, error_index, var_binds in iterator:
                if error_indication:
                    logger.warning(f"SNMP GETNEXT error for {oid}: {error_indication}")
                    self._connected = False
                    break
                elif error_status:
                    logger.warning(f"SNMP GETNEXT error for {oid}: {error_status}")
                    self._connected = False
                    break
                else:
                    self._connected = True
                    for var_bind in var_binds:
                        oid_str = str(var_bind[0])
                        val = str(var_bind[1])
                        if oid_str.startswith(oid):
                            results.append((oid_str, val))
                        else:
                            return results  # End of table
            return results
        except Exception as e:
            logger.error(f"SNMP GETNEXT failed for {oid}: {e}")
            self._connected = False
        return []

    def _mock_snmp_get(self, oid: str) -> Optional[str]:
        """Mock SNMP GET for testing"""
        mock_data = {
            self.OID_CONTROLLER_STATUS: "1",  # operational
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.1": "15",
            f"{self.OID_DETECTOR_OCCUPANCY}.1": "45",
            f"{self.OID_DETECTOR_STATUS}.1": "1",  # occupied
            f"{self.OID_DETECTOR_FAULT}.1": "0",  # no fault
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.2": "12",
            f"{self.OID_DETECTOR_OCCUPANCY}.2": "38",
            f"{self.OID_DETECTOR_STATUS}.2": "1",
            f"{self.OID_DETECTOR_FAULT}.2": "0",
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.3": "20",
            f"{self.OID_DETECTOR_OCCUPANCY}.3": "52",
            f"{self.OID_DETECTOR_STATUS}.3": "1",
            f"{self.OID_DETECTOR_FAULT}.3": "0",
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.4": "18",
            f"{self.OID_DETECTOR_OCCUPANCY}.4": "42",
            f"{self.OID_DETECTOR_STATUS}.4": "1",
            f"{self.OID_DETECTOR_FAULT}.4": "0",
        }
        return mock_data.get(oid)

    def _mock_snmp_getnext(self, oid: str) -> List[tuple]:
        """Mock SNMP GETNEXT for table walking"""
        if oid == self.OID_FAULT_CODE:
            return [
                (f"{self.OID_FAULT_CODE}.1", "0"),
                (f"{self.OID_FAULT_CODE}.2", "0"),
            ]
        elif oid == self.OID_FAULT_DESCRIPTION:
            return [
                (f"{self.OID_FAULT_DESCRIPTION}.1", "No fault"),
                (f"{self.OID_FAULT_DESCRIPTION}.2", "No fault"),
            ]
        elif oid == self.OID_FAULT_SEVERITY:
            return [
                (f"{self.OID_FAULT_SEVERITY}.1", "0"),
                (f"{self.OID_FAULT_SEVERITY}.2", "0"),
            ]
        elif oid == self.OID_CYCLE_NUMBER:
            return [
                (f"{self.OID_CYCLE_NUMBER}.1", "12345"),
                (f"{self.OID_CYCLE_NUMBER}.2", "12346"),
            ]
        elif oid == self.OID_CYCLE_PHASE:
            return [
                (f"{self.OID_CYCLE_PHASE}.1", "1"),
                (f"{self.OID_CYCLE_PHASE}.2", "2"),
            ]
        elif oid == self.OID_CYCLE_GREEN_ELAPSED:
            return [
                (f"{self.OID_CYCLE_GREEN_ELAPSED}.1", "25"),
                (f"{self.OID_CYCLE_GREEN_ELAPSED}.2", "30"),
            ]
        return []

    # --- NTCIPPort interface methods ---

    def set_phase_timing(self, timing: NTCIPCycleConfig) -> bool:
        """STMP operation - not supported in SNMP adapter"""
        logger.warning("SNMP adapter does not support SET operations")
        return False

    def get_phase_timing(self) -> Optional[NTCIPCycleConfig]:
        """STMP operation - not supported in SNMP adapter"""
        logger.warning("SNMP adapter does not support phase timing GET")
        return None

    def get_detector_status(self) -> List[NTCIPDetectorStatus]:
        """Get detector status via SNMP GETNEXT"""
        current_time = time.time()
        if current_time - self._last_poll < self._poll_interval:
            # Return cached data if polled recently
            if hasattr(self, "_cached_detector_status"):
                return self._cached_detector_status

        try:
            results = []
            # Walk detector table
            detector_indices = set()
            for oid in [self.OID_DETECTOR_VEHICLE_COUNT, self.OID_DETECTOR_OCCUPANCY]:
                for oid_str, _ in self._snmp_getnext(oid):
                    # Extract index from OID
                    idx = oid_str.split(".")[-1]
                    detector_indices.add(idx)

            for idx in sorted(detector_indices, key=int):
                volume = int(self._snmp_get(f"{self.OID_DETECTOR_VEHICLE_COUNT}.{idx}") or "0")
                occupancy = float(self._snmp_get(f"{self.OID_DETECTOR_OCCUPANCY}.{idx}") or "0")
                status = int(self._snmp_get(f"{self.OID_DETECTOR_STATUS}.{idx}") or "0")
                fault = int(self._snmp_get(f"{self.OID_DETECTOR_FAULT}.{idx}") or "0")

                results.append(
                    NTCIPDetectorStatus(
                        detector_id=idx,
                        occupied=bool(status),
                        fault=bool(fault),
                        volume=volume,
                        occupancy_pct=occupancy,
                    )
                )

            self._cached_detector_status = results
            self._last_poll = current_time
            return results

        except Exception as e:
            logger.error(f"Failed to get detector status: {e}")
            return []

    def get_faults(self) -> List[NTCIPFault]:
        """Get active faults via SNMP"""
        try:
            results = []
            fault_codes = self._snmp_getnext(self.OID_FAULT_CODE)

            for oid_str, code_str in fault_codes:
                idx = oid_str.split(".")[-1]
                code = int(code_str)

                if code == 0:
                    continue  # No fault

                desc = self._snmp_get(f"{self.OID_FAULT_DESCRIPTION}.{idx}") or "Unknown fault"
                severity_str = self._snmp_get(f"{self.OID_FAULT_SEVERITY}.{idx}") or "0"
                severity_map = {"1": "warning", "2": "minor", "3": "major", "4": "critical"}
                severity = severity_map.get(severity_str, "unknown")

                results.append(NTCIPFault(fault_code=code, description=desc, severity=severity))

            return results

        except Exception as e:
            logger.error(f"Failed to get faults: {e}")
            return []

    def get_cycle_counters(self) -> List[NTCIPCycleCounter]:
        """Get cycle counters via SNMP"""
        try:
            results = []
            cycle_nums = self._snmp_getnext(self.OID_CYCLE_NUMBER)

            for oid_str, num_str in cycle_nums:
                idx = oid_str.split(".")[-1]
                cycle_num = int(num_str)
                phase = int(self._snmp_get(f"{self.OID_CYCLE_PHASE}.{idx}") or "0")
                green_elapsed = float(
                    self._snmp_get(f"{self.OID_CYCLE_GREEN_ELAPSED}.{idx}") or "0"
                )

                results.append(
                    NTCIPCycleCounter(
                        cycle_number=cycle_num, phase_number=phase, green_time_elapsed=green_elapsed
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Failed to get cycle counters: {e}")
            return []

    def is_connected(self) -> bool:
        """Check if controller is reachable via SNMP"""
        if self._snmp_engine == "mock":
            return True
        status = self._snmp_get(self.OID_CONTROLLER_STATUS)
        return status is not None


class MockNTCIPSNMPAdapter(NTCIPSNMPAdapter):
    """Mock SNMP adapter for testing without real controller"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._mock_connected = True
        logger.info("Mock NTCIP SNMP adapter initialized")

    def _get_snmp_engine(self):
        return "mock"

    def _mock_snmp_get(self, oid: str) -> Optional[str]:
        """Override mock SNMP GET with detector data"""
        mock_data = {
            self.OID_CONTROLLER_STATUS: "1",  # operational
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.1": "15",
            f"{self.OID_DETECTOR_OCCUPANCY}.1": "45",
            f"{self.OID_DETECTOR_STATUS}.1": "1",
            f"{self.OID_DETECTOR_FAULT}.1": "0",
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.2": "12",
            f"{self.OID_DETECTOR_OCCUPANCY}.2": "38",
            f"{self.OID_DETECTOR_STATUS}.2": "1",
            f"{self.OID_DETECTOR_FAULT}.2": "0",
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.3": "20",
            f"{self.OID_DETECTOR_OCCUPANCY}.3": "52",
            f"{self.OID_DETECTOR_STATUS}.3": "1",
            f"{self.OID_DETECTOR_FAULT}.3": "0",
            f"{self.OID_DETECTOR_VEHICLE_COUNT}.4": "18",
            f"{self.OID_DETECTOR_OCCUPANCY}.4": "42",
            f"{self.OID_DETECTOR_STATUS}.4": "1",
            f"{self.OID_DETECTOR_FAULT}.4": "0",
        }
        return mock_data.get(oid)

    def _mock_snmp_getnext(self, oid: str) -> List[tuple]:
        """Override mock SNMP GETNEXT with detector table"""
        if oid == self.OID_DETECTOR_VEHICLE_COUNT:
            return [
                (f"{self.OID_DETECTOR_VEHICLE_COUNT}.1", "15"),
                (f"{self.OID_DETECTOR_VEHICLE_COUNT}.2", "12"),
                (f"{self.OID_DETECTOR_VEHICLE_COUNT}.3", "20"),
                (f"{self.OID_DETECTOR_VEHICLE_COUNT}.4", "18"),
            ]
        elif oid == self.OID_DETECTOR_OCCUPANCY:
            return [
                (f"{self.OID_DETECTOR_OCCUPANCY}.1", "45"),
                (f"{self.OID_DETECTOR_OCCUPANCY}.2", "38"),
                (f"{self.OID_DETECTOR_OCCUPANCY}.3", "52"),
                (f"{self.OID_DETECTOR_OCCUPANCY}.4", "42"),
            ]
        elif oid == self.OID_FAULT_CODE:
            return [
                (f"{self.OID_FAULT_CODE}.1", "0"),
                (f"{self.OID_FAULT_CODE}.2", "0"),
            ]
        elif oid == self.OID_FAULT_DESCRIPTION:
            return [
                (f"{self.OID_FAULT_DESCRIPTION}.1", "No fault"),
                (f"{self.OID_FAULT_DESCRIPTION}.2", "No fault"),
            ]
        elif oid == self.OID_FAULT_SEVERITY:
            return [
                (f"{self.OID_FAULT_SEVERITY}.1", "0"),
                (f"{self.OID_FAULT_SEVERITY}.2", "0"),
            ]
        elif oid == self.OID_CYCLE_NUMBER:
            return [
                (f"{self.OID_CYCLE_NUMBER}.1", "12345"),
                (f"{self.OID_CYCLE_NUMBER}.2", "12346"),
            ]
        elif oid == self.OID_CYCLE_PHASE:
            return [
                (f"{self.OID_CYCLE_PHASE}.1", "1"),
                (f"{self.OID_CYCLE_PHASE}.2", "2"),
            ]
        elif oid == self.OID_CYCLE_GREEN_ELAPSED:
            return [
                (f"{self.OID_CYCLE_GREEN_ELAPSED}.1", "25"),
                (f"{self.OID_CYCLE_GREEN_ELAPSED}.2", "30"),
            ]
        return []

    def is_connected(self) -> bool:
        return self._mock_connected

    def set_connected(self, connected: bool):
        self._mock_connected = connected
