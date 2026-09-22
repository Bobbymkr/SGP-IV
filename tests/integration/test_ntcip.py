"""
NTCIP Integration Tests
Tests for NTCIP 1202 STMP actuation, SNMP monitoring, and J2735 V2X communication.
"""

import pytest

from adaptive_traffic.adapters.j2735 import MockJ2735Adapter
from adaptive_traffic.adapters.ntcip_snmp import MockNTCIPSNMPAdapter
from adaptive_traffic.adapters.ntcip_stmp import MockNTCIP1202STMPAdapter
from adaptive_traffic.core.ports.ntcip_port import (
    J2735BSM,
    J2735MAP,
    J2735SPAT,
    NTCIPCycleConfig,
    NTCIPCycleCounter,
    NTCIPDetectorStatus,
    NTCIPFault,
    NTCIPPhaseTiming,
)


class TestNTCIPSTMPAdapter:
    """Test NTCIP 1202 STMP adapter (actuation)"""

    @pytest.fixture
    def stmp_config(self):
        return {
            "ntcip_controller_ip": "127.0.0.1",
            "ntcip_stmp_port": 5000,
            "ntcip_community": "public",
            "ntcip_timeout": 5.0,
            "ntcip_max_retries": 3,
            "ntcip_phase_mapping": {"north": 1, "south": 2, "east": 3, "west": 4},
        }

    @pytest.fixture
    def mock_stmp_adapter(self, stmp_config):
        return MockNTCIP1202STMPAdapter(stmp_config)

    @pytest.fixture
    def sample_cycle_config(self):
        return NTCIPCycleConfig(
            cycle_length=120.0,
            offset=0.0,
            phases=[
                NTCIPPhaseTiming(1, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(2, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(3, 25.0, 5.0, 90.0),
                NTCIPPhaseTiming(4, 25.0, 5.0, 90.0),
            ],
        )

    def test_stmp_set_phase_timing(self, mock_stmp_adapter, sample_cycle_config):
        """Test STMP SET operation for phase timing"""
        result = mock_stmp_adapter.set_phase_timing(sample_cycle_config)
        assert result is True

        # Verify internal state was updated
        retrieved = mock_stmp_adapter.get_phase_timing()
        assert retrieved is not None
        assert retrieved.cycle_length == 120.0
        assert retrieved.offset == 0.0
        assert len(retrieved.phases) == 4
        assert retrieved.phases[0].green_time == 30.0
        assert retrieved.phases[0].yellow_time == 5.0

    def test_stmp_get_phase_timing(self, mock_stmp_adapter, sample_cycle_config):
        """Test STMP GET operation for phase timing"""
        # First set a configuration
        mock_stmp_adapter.set_phase_timing(sample_cycle_config)

        # Then retrieve it
        retrieved = mock_stmp_adapter.get_phase_timing()
        assert retrieved is not None
        assert retrieved.cycle_length == sample_cycle_config.cycle_length
        assert retrieved.offset == sample_cycle_config.offset
        assert len(retrieved.phases) == len(sample_cycle_config.phases)

    def test_stmp_is_connected(self, mock_stmp_adapter):
        """Test connection check"""
        assert mock_stmp_adapter.is_connected() is True

        mock_stmp_adapter.set_connected(False)
        assert mock_stmp_adapter.is_connected() is False

    def test_stmp_mock_round_trip(self, mock_stmp_adapter, sample_cycle_config):
        """Test full STMP round-trip: SET then GET"""
        # SET
        set_result = mock_stmp_adapter.set_phase_timing(sample_cycle_config)
        assert set_result is True

        # GET
        get_result = mock_stmp_adapter.get_phase_timing()
        assert get_result is not None

        # Verify all fields match
        assert get_result.cycle_length == sample_cycle_config.cycle_length
        assert get_result.offset == sample_cycle_config.offset
        for i, (orig, retrieved) in enumerate(zip(sample_cycle_config.phases, get_result.phases)):
            assert orig.phase_number == retrieved.phase_number
            assert orig.green_time == retrieved.green_time
            assert orig.yellow_time == retrieved.yellow_time
            assert orig.red_time == retrieved.red_time


class TestNTCIPSNMPAdapter:
    """Test NTCIP SNMP adapter (monitoring)"""

    @pytest.fixture
    def snmp_config(self):
        return {
            "ntcip_controller_ip": "127.0.0.1",
            "ntcip_snmp_port": 161,
            "ntcip_snmp_community": "public",
            "ntcip_snmp_timeout": 3.0,
            "ntcip_snmp_retries": 2,
            "ntcip_detector_mapping": {"1": "north", "2": "south", "3": "east", "4": "west"},
        }

    @pytest.fixture
    def mock_snmp_adapter(self, snmp_config):
        return MockNTCIPSNMPAdapter(snmp_config)

    def test_snmp_get_detector_status(self, mock_snmp_adapter):
        """Test SNMP detector status retrieval"""
        detectors = mock_snmp_adapter.get_detector_status()

        assert len(detectors) == 4
        for det in detectors:
            assert isinstance(det, NTCIPDetectorStatus)
            assert det.detector_id in ["1", "2", "3", "4"]
            assert isinstance(det.occupied, bool)
            assert isinstance(det.fault, bool)
            assert isinstance(det.volume, int)
            assert isinstance(det.occupancy_pct, float)
            assert det.volume >= 0
            assert 0 <= det.occupancy_pct <= 100

    def test_snmp_get_faults(self, mock_snmp_adapter):
        """Test SNMP fault retrieval"""
        faults = mock_snmp_adapter.get_faults()

        # Mock returns no faults (code 0)
        assert isinstance(faults, list)
        for fault in faults:
            assert isinstance(fault, NTCIPFault)
            assert isinstance(fault.fault_code, int)
            assert isinstance(fault.description, str)
            assert isinstance(fault.severity, str)

    def test_snmp_get_cycle_counters(self, mock_snmp_adapter):
        """Test SNMP cycle counter retrieval"""
        counters = mock_snmp_adapter.get_cycle_counters()

        assert isinstance(counters, list)
        for counter in counters:
            assert isinstance(counter, NTCIPCycleCounter)
            assert isinstance(counter.cycle_number, int)
            assert isinstance(counter.phase_number, int)
            assert isinstance(counter.green_time_elapsed, float)

    def test_snmp_is_connected(self, mock_snmp_adapter):
        """Test SNMP connection check"""
        assert mock_snmp_adapter.is_connected() is True

        mock_snmp_adapter.set_connected(False)
        assert mock_snmp_adapter.is_connected() is False


class TestJ2735Adapter:
    """Test J2735 V2X adapter (BSM receive, SPAT transmit)"""

    @pytest.fixture
    def j2735_config(self):
        return {
            "j2735_bsm_port": 1735,
            "j2735_spat_port": 1736,
            "j2735_broadcast_ip": "255.255.255.255",
            "j2735_tx_power_dbm": 20,
            "j2735_transmit_interval": 0.1,
            "j2735_max_bsm_age": 1.0,
            "intersection_id": "main",
        }

    @pytest.fixture
    def mock_j2735_adapter(self, j2735_config):
        adapter = MockJ2735Adapter(j2735_config)
        # Load a simple MAP for testing
        map_data = J2735MAP(
            msg_id=0x14,
            intersections=[
                {
                    "id": 1,
                    "name": "north",
                    "ref_point": {"lat": 0, "lon": 0, "elevation": 0},
                    "lanes": [
                        {
                            "lane_id": 0,
                            "ingress_approach": 0,
                            "egress_approach": 0,
                            "lane_width": 3.5,
                        }
                    ],
                }
            ],
        )
        adapter.load_map(map_data)
        return adapter

    def test_j2735_load_map(self, mock_j2735_adapter):
        """Test MAP loading"""
        assert mock_j2735_adapter._map_data is not None
        assert len(mock_j2735_adapter._map_data.intersections) == 1

    def test_j2735_receive_bsm(self, mock_j2735_adapter):
        """Test BSM reception"""
        # Create a mock BSM
        bsm = J2735BSM(
            msg_id=0x12,
            temp_id=12345,
            sec_mark=30000,
            latitude=123456789,
            longitude=987654321,
            elevation=100,
            speed=1500,  # 15 m/s = 54 km/h
            heading=0,  # Northbound
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

        mock_j2735_adapter.inject_bsm(bsm)

        received = mock_j2735_adapter.receive_bsm()
        assert len(received) == 1
        assert received[0].temp_id == 12345

    def test_j2735_bsm_queue_refinement(self, mock_j2735_adapter):
        """Test BSM-based queue refinement"""
        # Inject BSMs for vehicles in queue zone
        for i in range(3):
            bsm = J2735BSM(
                msg_id=0x12,
                temp_id=1000 + i,
                sec_mark=30000,
                latitude=123456789,
                longitude=987654321,
                elevation=100,
                speed=0,  # Stopped
                heading=0,
                accel_set={"long": 0, "lat": 0, "vert": 0, "yaw": 0},
                brakes={
                    "wheel": True,
                    "traction": False,
                    "abs": False,
                    "scs": False,
                    "brake_boost": False,
                    "aux": False,
                },
                size={"width": 180, "length": 450},
                vehicle_class=0,
            )
            mock_j2735_adapter.inject_bsm(bsm)

        refinement = mock_j2735_adapter.get_queue_refinement()

        assert isinstance(refinement, dict)
        assert "north" in refinement
        # Should detect 3 vehicles in northbound queue
        assert refinement["north"] == 3

    def test_j2735_transmit_spat(self, mock_j2735_adapter):
        """Test SPAT transmission"""
        # Create a sample cycle config
        cycle_config = NTCIPCycleConfig(
            cycle_length=120.0,
            offset=0.0,
            phases=[
                NTCIPPhaseTiming(1, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(2, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(3, 25.0, 5.0, 90.0),
                NTCIPPhaseTiming(4, 25.0, 5.0, 90.0),
            ],
        )

        spat = mock_j2735_adapter.create_spat_from_timing(cycle_config, 0, 10.0)
        assert isinstance(spat, J2735SPAT)
        assert spat.msg_id == 0x13
        assert len(spat.intersections) == 4

        # Transmit
        result = mock_j2735_adapter.transmit_spat(spat)
        assert result is True

    def test_j2735_spat_phase_states(self, mock_j2735_adapter):
        """Test SPAT phase state encoding"""
        cycle_config = NTCIPCycleConfig(
            cycle_length=120.0,
            offset=0.0,
            phases=[
                NTCIPPhaseTiming(1, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(2, 30.0, 5.0, 85.0),
            ],
        )

        # Test green phase (current_phase=0, timer < green)
        spat_green = mock_j2735_adapter.create_spat_from_timing(cycle_config, 0, 10.0)
        assert spat_green.intersections[0]["states"][0]["state"] == 3  # Green

        # Test yellow phase (current_phase=0, timer >= green but < green+yellow)
        # Actually at timer=30, it should be yellow
        spat_yellow = mock_j2735_adapter.create_spat_from_timing(cycle_config, 0, 30.0)
        assert spat_yellow.intersections[0]["states"][0]["state"] == 4  # Yellow

        # Test red phase for other approaches
        assert spat_green.intersections[1]["states"][0]["state"] == 1  # Red


class TestNTCIPIntegration:
    """End-to-end NTCIP integration tests"""

    @pytest.fixture
    def full_config(self):
        return {
            "ntcip_controller_ip": "127.0.0.1",
            "ntcip_stmp_port": 5000,
            "ntcip_snmp_port": 161,
            "ntcip_community": "public",
            "ntcip_snmp_community": "public",
            "ntcip_timeout": 5.0,
            "ntcip_max_retries": 3,
            "ntcip_phase_mapping": {"north": 1, "south": 2, "east": 3, "west": 4},
            "ntcip_detector_mapping": {"1": "north", "2": "south", "3": "east", "4": "west"},
            "ntcip_transport": "both",
            "j2735_bsm_port": 1735,
            "j2735_spat_port": 1736,
            "j2735_broadcast_ip": "255.255.255.255",
            "j2735_tx_power_dbm": 20,
            "j2735_transmit_interval": 0.1,
            "j2735_max_bsm_age": 1.0,
            "intersection_id": "main",
        }

    def test_full_ntcip_stack_roundtrip(self, full_config):
        """Test full NTCIP stack: STMP SET -> SNMP GET -> J2735 SPAT"""
        from adaptive_traffic.adapters import create_j2735_adapter, create_ntcip_adapter

        # Create adapters in mock mode
        ntcip = create_ntcip_adapter(full_config, mock=True)
        j2735 = create_j2735_adapter(full_config, mock=True)

        # Load MAP for J2735
        map_data = J2735MAP(
            msg_id=0x14,
            intersections=[
                {
                    "id": i + 1,
                    "name": approach,
                    "ref_point": {"lat": 0, "lon": 0, "elevation": 0},
                    "lanes": [
                        {
                            "lane_id": 0,
                            "ingress_approach": i,
                            "egress_approach": i,
                            "lane_width": 3.5,
                        }
                    ],
                }
                for i, approach in enumerate(["north", "south", "east", "west"])
            ],
        )
        j2735.load_map(map_data)

        # 1. Set phase timing via STMP
        cycle_config = NTCIPCycleConfig(
            cycle_length=120.0,
            offset=10.0,
            phases=[
                NTCIPPhaseTiming(1, 35.0, 5.0, 80.0),
                NTCIPPhaseTiming(2, 35.0, 5.0, 80.0),
                NTCIPPhaseTiming(3, 25.0, 5.0, 90.0),
                NTCIPPhaseTiming(4, 25.0, 5.0, 90.0),
            ],
        )

        set_result = ntcip.set_phase_timing(cycle_config)
        assert set_result is True

        # 2. Verify via STMP GET
        retrieved = ntcip.get_phase_timing()
        assert retrieved is not None
        assert retrieved.cycle_length == 120.0
        assert retrieved.offset == 10.0

        # 3. Check monitoring via SNMP
        detectors = ntcip.get_detector_status()
        assert len(detectors) == 4

        faults = ntcip.get_faults()
        assert isinstance(faults, list)

        counters = ntcip.get_cycle_counters()
        assert isinstance(counters, list)

        # 4. Transmit SPAT via J2735
        spat = j2735.create_spat_from_timing(retrieved, 0, 15.0)
        transmit_result = j2735.transmit_spat(spat)
        assert transmit_result is True

        # 5. Simulate BSM reception and queue refinement
        for i in range(2):
            bsm = J2735BSM(
                msg_id=0x12,
                temp_id=2000 + i,
                sec_mark=30000,
                latitude=123456789,
                longitude=987654321,
                elevation=100,
                speed=0,
                heading=0,
                accel_set={"long": 0, "lat": 0, "vert": 0, "yaw": 0},
                brakes={
                    "wheel": True,
                    "traction": False,
                    "abs": False,
                    "scs": False,
                    "brake_boost": False,
                    "aux": False,
                },
                size={"width": 180, "length": 450},
                vehicle_class=0,
            )
            j2735.inject_bsm(bsm)

        refinement = j2735.get_queue_refinement()
        assert refinement["north"] == 2

    def test_fallback_graceful_degradation(self, full_config):
        """Test graceful degradation when STMP fails"""
        from adaptive_traffic.adapters import create_ntcip_adapter

        ntcip = create_ntcip_adapter(full_config, mock=True)

        # Simulate controller disconnection
        ntcip._stmp.set_connected(False)

        cycle_config = NTCIPCycleConfig(
            cycle_length=120.0, offset=0.0, phases=[NTCIPPhaseTiming(1, 30.0, 5.0, 85.0)]
        )

        # SET should fail gracefully
        result = ntcip.set_phase_timing(cycle_config)
        assert result is False  # Mock returns False when disconnected

        # GET should also fail gracefully
        retrieved = ntcip.get_phase_timing()
        assert retrieved is None or retrieved.cycle_length == 120.0  # Returns cached/mock

        # But SNMP monitoring should still work (separate transport)
        assert ntcip._snmp.is_connected() is True
        detectors = ntcip.get_detector_status()
        assert len(detectors) == 4


class TestNTCIPEncoding:
    """Test NTCIP/J2735 encoding/decoding utilities"""

    def test_ntcip_phase_timing_dataclass(self):
        """Test NTCIPPhaseTiming dataclass"""
        phase = NTCIPPhaseTiming(phase_number=1, green_time=30.0, yellow_time=5.0, red_time=85.0)
        assert phase.phase_number == 1
        assert phase.green_time == 30.0
        assert phase.yellow_time == 5.0
        assert phase.red_time == 85.0

    def test_ntcip_cycle_config_dataclass(self):
        """Test NTCIPCycleConfig dataclass"""
        config = NTCIPCycleConfig(
            cycle_length=120.0,
            offset=5.0,
            phases=[
                NTCIPPhaseTiming(1, 30.0, 5.0, 85.0),
                NTCIPPhaseTiming(2, 30.0, 5.0, 85.0),
            ],
        )
        assert config.cycle_length == 120.0
        assert config.offset == 5.0
        assert len(config.phases) == 2

    def test_j2735_bsm_dataclass(self):
        """Test J2735BSM dataclass"""
        bsm = J2735BSM(
            msg_id=0x12,
            temp_id=12345,
            sec_mark=30000,
            latitude=123456789,
            longitude=987654321,
            elevation=100,
            speed=1500,
            heading=0,
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
        assert bsm.msg_id == 0x12
        assert bsm.temp_id == 12345
        assert bsm.speed == 1500

    def test_j2735_spat_dataclass(self):
        """Test J2735SPAT dataclass"""
        spat = J2735SPAT(
            msg_id=0x13,
            intersections=[
                {
                    "id": 1,
                    "states": [{"phase": 1, "state": 3, "min_end_time": 100, "max_end_time": 400}],
                }
            ],
        )
        assert spat.msg_id == 0x13
        assert len(spat.intersections) == 1

    def test_j2735_map_dataclass(self):
        """Test J2735MAP dataclass"""
        map_data = J2735MAP(
            msg_id=0x14, intersections=[{"id": 1, "name": "main", "ref_point": {}, "lanes": []}]
        )
        assert map_data.msg_id == 0x14
        assert len(map_data.intersections) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
