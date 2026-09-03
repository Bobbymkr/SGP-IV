"""
NTCIP Port Interface
Contract for NTCIP 1202 signal controller integration (actuation + monitoring)
and J2735 V2X communication (BSM receive, SPAT transmit).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

from adaptive_traffic.core.domain import SignalTiming, TrafficState


@dataclass
class NTCIPPhaseTiming:
    """Phase timing parameters for NTCIP 1202 STMP SET operations"""

    phase_number: int
    green_time: float
    yellow_time: float
    red_time: float


@dataclass
class NTCIPCycleConfig:
    """Cycle configuration for NTCIP 1202"""

    cycle_length: float
    offset: float
    phases: List[NTCIPPhaseTiming]


@dataclass
class NTCIPDetectorStatus:
    """Detector status from NTCIP SNMP GET"""

    detector_id: str
    occupied: bool
    fault: bool
    volume: int
    occupancy_pct: float


@dataclass
class NTCIPFault:
    """Fault information from NTCIP SNMP"""

    fault_code: int
    description: str
    severity: str


@dataclass
class NTCIPCycleCounter:
    """Cycle counter from NTCIP SNMP"""

    cycle_number: int
    phase_number: int
    green_time_elapsed: float


@dataclass
class J2735BSM:
    """J2735 Basic Safety Message (received from connected vehicles)"""

    msg_id: int
    temp_id: int
    sec_mark: int
    latitude: int
    longitude: int
    elevation: int
    speed: int
    heading: int
    accel_set: Dict[str, int]
    brakes: Dict[str, bool]
    size: Dict[str, int]
    vehicle_class: int


@dataclass
class J2735SPAT:
    """J2735 Signal Phase and Timing (transmitted to connected vehicles)"""

    msg_id: int
    intersections: List[Dict]


@dataclass
class J2735MAP:
    """J2735 Map Data (static intersection geometry)"""

    msg_id: int
    intersections: List[Dict]


class NTCIPPort(ABC):
    """Port for NTCIP 1202 signal controller integration"""

    @abstractmethod
    def set_phase_timing(self, timing: NTCIPCycleConfig) -> bool:
        """Apply phase timing via NTCIP 1202 STMP (actuation)

        Args:
            timing: Cycle configuration with phase timings

        Returns:
            True if successfully applied, False otherwise
        """
        pass

    @abstractmethod
    def get_phase_timing(self) -> Optional[NTCIPCycleConfig]:
        """Get current phase timing via NTCIP 1202 STMP GET

        Returns:
            Current cycle configuration or None if unavailable
        """
        pass

    @abstractmethod
    def get_detector_status(self) -> List[NTCIPDetectorStatus]:
        """Get detector status via NTCIP SNMP (monitoring)

        Returns:
            List of detector statuses
        """
        pass

    @abstractmethod
    def get_faults(self) -> List[NTCIPFault]:
        """Get active faults via NTCIP SNMP

        Returns:
            List of active faults
        """
        pass

    @abstractmethod
    def get_cycle_counters(self) -> List[NTCIPCycleCounter]:
        """Get cycle counters via NTCIP SNMP

        Returns:
            List of cycle counters
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if controller is reachable

        Returns:
            True if controller responds, False otherwise
        """
        pass


class J2735Port(ABC):
    """Port for J2735 V2X communication"""

    @abstractmethod
    def receive_bsm(self) -> List[J2735BSM]:
        """Receive BSM messages from connected vehicles

        Returns:
            List of received BSM messages
        """
        pass

    @abstractmethod
    def transmit_spat(self, spat: J2735SPAT) -> bool:
        """Transmit SPAT message to connected vehicles

        Args:
            spat: Signal Phase and Timing message to broadcast

        Returns:
            True if transmitted successfully
        """
        pass

    @abstractmethod
    def load_map(self, map_data: J2735MAP) -> bool:
        """Load static MAP data for intersection

        Args:
            map_data: Intersection geometry map

        Returns:
            True if loaded successfully
        """
        pass


def create_ntcip_port(config: dict) -> NTCIPPort:
    """Factory function to create NTCIP port implementation"""
    from adaptive_traffic.adapters.ntcip_snmp import NTCIPSNMPAdapter
    from adaptive_traffic.adapters.ntcip_stmp import NTCIP1202STMPAdapter

    transport = config.get("ntcip_transport", "both")  # "stmp", "snmp", "both"
    if transport == "stmp":
        return NTCIP1202STMPAdapter(config)
    elif transport == "snmp":
        return NTCIPSNMPAdapter(config)
    else:
        # Composite adapter that uses both
        return NTCIPCompositeAdapter(
            stmp=NTCIP1202STMPAdapter(config), snmp=NTCIPSNMPAdapter(config)
        )


def create_j2735_port(config: dict) -> J2735Port:
    """Factory function to create J2735 V2X port implementation"""
    from adaptive_traffic.adapters.j2735 import J2735Adapter

    return J2735Adapter(config)


class NTCIPCompositeAdapter(NTCIPPort):
    """Composite adapter using both STMP (actuation) and SNMP (monitoring)"""

    def __init__(self, stmp: NTCIPPort, snmp: NTCIPPort):
        self._stmp = stmp
        self._snmp = snmp

    def set_phase_timing(self, timing: NTCIPCycleConfig) -> bool:
        return self._stmp.set_phase_timing(timing)

    def get_phase_timing(self) -> Optional[NTCIPCycleConfig]:
        return self._stmp.get_phase_timing()

    def get_detector_status(self) -> List[NTCIPDetectorStatus]:
        return self._snmp.get_detector_status()

    def get_faults(self) -> List[NTCIPFault]:
        return self._snmp.get_faults()

    def get_cycle_counters(self) -> List[NTCIPCycleCounter]:
        return self._snmp.get_cycle_counters()

    def is_connected(self) -> bool:
        return self._stmp.is_connected() and self._snmp.is_connected()
