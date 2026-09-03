"""
NTCIP/J2735 Adapters Package
Factory functions for creating NTCIP and J2735 adapters.
"""

from adaptive_traffic.adapters.j2735 import J2735Adapter, MockJ2735Adapter
from adaptive_traffic.adapters.ntcip_snmp import MockNTCIPSNMPAdapter, NTCIPSNMPAdapter
from adaptive_traffic.adapters.ntcip_stmp import MockNTCIP1202STMPAdapter, NTCIP1202STMPAdapter
from adaptive_traffic.core.ports.ntcip_port import J2735Port, NTCIPPort


def create_ntcip_stmp_adapter(config: dict, mock: bool = False) -> NTCIPPort:
    """Factory function to create NTCIP 1202 STMP adapter

    Args:
        config: Configuration dict with:
            - ntcip_controller_ip: Controller IP address
            - ntcip_stmp_port: STMP UDP port (default 5000)
            - ntcip_community: SNMP community string
            - ntcip_timeout: Request timeout in seconds
            - ntcip_max_retries: Max retry attempts
            - ntcip_phase_mapping: Dict mapping direction -> phase number
        mock: If True, return mock adapter for testing

    Returns:
        NTCIPPort implementation for STMP actuation
    """
    if mock:
        return MockNTCIP1202STMPAdapter(config)
    return NTCIP1202STMPAdapter(config)


def create_ntcip_snmp_adapter(config: dict, mock: bool = False) -> NTCIPPort:
    """Factory function to create NTCIP SNMP adapter

    Args:
        config: Configuration dict with:
            - ntcip_controller_ip: Controller IP address
            - ntcip_snmp_port: SNMP UDP port (default 161)
            - ntcip_snmp_community: SNMP community string
            - ntcip_snmp_timeout: Request timeout in seconds
            - ntcip_snmp_retries: Max retry attempts
            - ntcip_snmp_poll_interval: Minimum poll interval in seconds
            - ntcip_detector_mapping: Dict mapping detector_id -> direction
        mock: If True, return mock adapter for testing

    Returns:
        NTCIPPort implementation for SNMP monitoring
    """
    if mock:
        return MockNTCIPSNMPAdapter(config)
    return NTCIPSNMPAdapter(config)


def create_ntcip_adapter(config: dict, mock: bool = False) -> NTCIPPort:
    """Factory function to create composite NTCIP adapter (STMP + SNMP)

    Args:
        config: Configuration dict (merged for both STMP and SNMP)
        mock: If True, return mock adapters for testing

    Returns:
        NTCIPPort composite implementation
    """
    from adaptive_traffic.core.ports.ntcip_port import NTCIPCompositeAdapter

    stmp = create_ntcip_stmp_adapter(config, mock=mock)
    snmp = create_ntcip_snmp_adapter(config, mock=mock)
    return NTCIPCompositeAdapter(stmp=stmp, snmp=snmp)


def create_j2735_adapter(config: dict, mock: bool = False) -> J2735Port:
    """Factory function to create J2735 V2X adapter

    Args:
        config: Configuration dict with:
            - j2735_bsm_port: BSM receive UDP port (default 1735)
            - j2735_spat_port: SPAT transmit UDP port (default 1736)
            - j2735_broadcast_ip: Broadcast IP for SPAT (default 255.255.255.255)
            - j2735_tx_power_dbm: Transmit power in dBm
            - j2735_transmit_interval: Minimum transmit interval in seconds
            - j2735_max_bsm_age: Max age of BSM for queue refinement
            - intersection_id: Intersection identifier
        mock: If True, return mock adapter for testing

    Returns:
        J2735Port implementation
    """
    if mock:
        return MockJ2735Adapter(config)
    return J2735Adapter(config)


__all__ = [
    "NTCIP1202STMPAdapter",
    "MockNTCIP1202STMPAdapter",
    "NTCIPSNMPAdapter",
    "MockNTCIPSNMPAdapter",
    "J2735Adapter",
    "MockJ2735Adapter",
    "create_ntcip_stmp_adapter",
    "create_ntcip_snmp_adapter",
    "create_ntcip_adapter",
    "create_j2735_adapter",
]
