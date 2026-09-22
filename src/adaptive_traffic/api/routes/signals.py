"""
Signal control endpoints with NTCIP/J2735 V2X integration
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from adaptive_traffic.adapters import (
    create_j2735_adapter,
    create_ntcip_adapter,
)
from adaptive_traffic.config.settings import get_settings
from adaptive_traffic.core.ports.ntcip_port import (
    NTCIPCycleConfig,
    NTCIPPhaseTiming,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global adapter instances (initialized on first use)
_ntcip_adapter = None
_j2735_adapter = None


def get_ntcip_adapter():
    """Get or create NTCIP adapter"""
    global _ntcip_adapter
    if _ntcip_adapter is None:
        settings = get_settings()
        config = {
            "ntcip_controller_ip": settings.ntcip_controller_ip,
            "ntcip_stmp_port": settings.ntcip_stmp_port,
            "ntcip_snmp_port": settings.ntcip_snmp_port,
            "ntcip_community": settings.ntcip_community,
            "ntcip_snmp_community": settings.ntcip_snmp_community,
            "ntcip_timeout": settings.ntcip_timeout,
            "ntcip_max_retries": settings.ntcip_max_retries,
            "ntcip_phase_mapping": settings.ntcip_phase_mapping,
            "ntcip_detector_mapping": settings.ntcip_detector_mapping,
            "ntcip_transport": settings.ntcip_transport,
        }
        _ntcip_adapter = create_ntcip_adapter(config, mock=settings.environment != "production")
        logger.info(f"NTCIP adapter initialized (mock={settings.environment != 'production'})")
    return _ntcip_adapter


def get_j2735_adapter():
    """Get or create J2735 V2X adapter"""
    global _j2735_adapter
    if _j2735_adapter is None:
        settings = get_settings()
        config = {
            "j2735_bsm_port": settings.j2735_bsm_port,
            "j2735_spat_port": settings.j2735_spat_port,
            "j2735_broadcast_ip": settings.j2735_broadcast_ip,
            "j2735_tx_power_dbm": settings.j2735_tx_power_dbm,
            "j2735_transmit_interval": settings.j2735_transmit_interval,
            "j2735_max_bsm_age": settings.j2735_max_bsm_age,
            "intersection_id": "main",
        }
        _j2735_adapter = create_j2735_adapter(config, mock=settings.environment != "production")
        logger.info(f"J2735 adapter initialized (mock={settings.environment != 'production'})")
    return _j2735_adapter


class SignalStatus(BaseModel):
    signal_id: str
    intersection_id: str
    current_phase: str
    phase_timer: float
    green_time_remaining: float
    queues: dict[str, int]
    flows: dict[str, float]


class SignalTimingUpdate(BaseModel):
    signal_id: str
    green_times: dict[str, float]
    cycle_length: float | None = None
    yellow_time: float = Field(default=5.0, description="Yellow time in seconds")
    all_red_time: float = Field(default=2.0, description="All-red time in seconds")
    offset: float = Field(default=0.0, description="Cycle offset in seconds")


class TimingPlan(BaseModel):
    plan_id: str
    name: str
    cycle_length: float
    phases: list[dict]


class NTCIPHealthResponse(BaseModel):
    """NTCIP controller health response"""

    signal_id: str
    connected: bool
    detector_status: list[dict]
    faults: list[dict]
    cycle_counters: list[dict]
    timestamp: str


class BSMQueueRefinement(BaseModel):
    """BSM-based queue refinement"""

    signal_id: str
    additional_vehicles: dict[str, int]
    bsm_count: int
    timestamp: str


class SPATTransmitRequest(BaseModel):
    """SPAT transmit request"""

    signal_id: str
    current_phase: int
    phase_timer: float


# In-memory storage (replace with database)
signals_db: dict[str, SignalStatus] = {}
timing_plans_db: dict[str, TimingPlan] = {}


@router.get("/", response_model=list[SignalStatus])
async def list_signals(
    intersection_id: str | None = Query(None, description="Filter by intersection")
):
    """List all signal controllers"""
    signals = list(signals_db.values())
    if intersection_id:
        signals = [s for s in signals if s.intersection_id == intersection_id]
    return signals


@router.get("/{signal_id}", response_model=SignalStatus)
async def get_signal(signal_id: str):
    """Get signal status"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signals_db[signal_id]


@router.post("/{signal_id}/timing", response_model=SignalStatus)
async def update_signal_timing(signal_id: str, timing: SignalTimingUpdate):
    """Update signal timing plan and push to NTCIP controller via STMP"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal = signals_db[signal_id]

    # Build NTCIP cycle config from timing update
    cycle_length = timing.cycle_length or sum(timing.green_times.values()) + len(
        timing.green_times
    ) * (timing.yellow_time + timing.all_red_time)

    phases = []
    for i, (direction, green_time) in enumerate(timing.green_times.items()):
        phase_num = i + 1
        phases.append(
            NTCIPPhaseTiming(
                phase_number=phase_num,
                green_time=green_time,
                yellow_time=timing.yellow_time,
                red_time=cycle_length - green_time - timing.yellow_time - timing.all_red_time,
            )
        )

    ntcp_config = NTCIPCycleConfig(cycle_length=cycle_length, offset=timing.offset, phases=phases)

    # Push to controller via NTCIP STMP
    adapter = get_ntcip_adapter()
    success = adapter.set_phase_timing(ntcp_config)

    if not success:
        logger.warning(f"NTCIP STMP SET failed for signal {signal_id} - falling back to local")
        # Graceful degradation: log but don't fail the request

    # Update local state
    signal.queues = timing.green_times
    signal.updated_at = datetime.utcnow()

    return signal


@router.get("/{signal_id}/status")
async def get_signal_status(signal_id: str):
    """Get detailed signal status"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal = signals_db[signal_id]
    return {
        "signal_id": signal_id,
        "intersection_id": signal.intersection_id,
        "current_phase": signal.current_phase,
        "phase_timer": signal.phase_timer,
        "green_time_remaining": signal.green_time_remaining,
        "queues": signal.queues,
        "flows": signal.flows,
        "timestamp": datetime.utcnow().isoformat(),
    }


# NTCIP Monitoring Endpoints
@router.get("/{signal_id}/health", response_model=NTCIPHealthResponse)
async def get_signal_health(signal_id: str):
    """Get NTCIP controller health via SNMP monitoring"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    adapter = get_ntcip_adapter()

    # Get detector status
    detector_status = []
    for det in adapter.get_detector_status():
        detector_status.append(
            {
                "detector_id": det.detector_id,
                "occupied": det.occupied,
                "fault": det.fault,
                "volume": det.volume,
                "occupancy_pct": det.occupancy_pct,
            }
        )

    # Get faults
    faults = []
    for fault in adapter.get_faults():
        faults.append(
            {
                "fault_code": fault.fault_code,
                "description": fault.description,
                "severity": fault.severity,
            }
        )

    # Get cycle counters
    cycle_counters = []
    for counter in adapter.get_cycle_counters():
        cycle_counters.append(
            {
                "cycle_number": counter.cycle_number,
                "phase_number": counter.phase_number,
                "green_time_elapsed": counter.green_time_elapsed,
            }
        )

    return NTCIPHealthResponse(
        signal_id=signal_id,
        connected=adapter.is_connected(),
        detector_status=detector_status,
        faults=faults,
        cycle_counters=cycle_counters,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/{signal_id}/ntcip/timing")
async def get_ntcip_timing(signal_id: str):
    """Get current phase timing from NTCIP controller via STMP GET"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    adapter = get_ntcip_adapter()
    timing = adapter.get_phase_timing()

    if timing is None:
        raise HTTPException(status_code=503, detail="NTCIP controller unavailable")

    return {
        "signal_id": signal_id,
        "cycle_length": timing.cycle_length,
        "offset": timing.offset,
        "phases": [
            {
                "phase_number": p.phase_number,
                "green_time": p.green_time,
                "yellow_time": p.yellow_time,
                "red_time": p.red_time,
            }
            for p in timing.phases
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


# J2735 V2X Endpoints
@router.get("/{signal_id}/v2x/queue-refinement", response_model=BSMQueueRefinement)
async def get_v2x_queue_refinement(signal_id: str):
    """Get queue length refinement from BSM messages"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    adapter = get_j2735_adapter()

    # Receive latest BSMs
    adapter.receive_bsm()

    # Get queue refinement
    refinement = adapter.get_queue_refinement()
    bsm_data = adapter.get_bsm_vehicle_data()

    return BSMQueueRefinement(
        signal_id=signal_id,
        additional_vehicles=refinement,
        bsm_count=len(bsm_data),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/{signal_id}/v2x/spat")
async def transmit_spat(signal_id: str, request: SPATTransmitRequest):
    """Transmit SPAT message to connected vehicles"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")

    adapter = get_j2735_adapter()

    # Get current timing from NTCIP
    ntcp_adapter = get_ntcip_adapter()
    timing = ntcp_adapter.get_phase_timing()

    if timing is None:
        # Fallback to local signal state (existence already checked above)
        from adaptive_traffic.core.ports.ntcip_port import NTCIPCycleConfig, NTCIPPhaseTiming

        timing = NTCIPCycleConfig(
            cycle_length=120,
            offset=0,
            phases=[
                NTCIPPhaseTiming(1, 30, 5, 85),
                NTCIPPhaseTiming(2, 30, 5, 85),
                NTCIPPhaseTiming(3, 30, 5, 85),
                NTCIPPhaseTiming(4, 30, 5, 85),
            ],
        )

    # Create and transmit SPAT
    spat = adapter.create_spat_from_timing(timing, request.current_phase, request.phase_timer)
    success = adapter.transmit_spat(spat)

    return {
        "signal_id": signal_id,
        "transmitted": success,
        "intersections": len(spat.intersections),
        "timestamp": datetime.utcnow().isoformat(),
    }


# Timing plans
@router.get("/plans/", response_model=list[TimingPlan])
async def list_timing_plans():
    """List all timing plans"""
    return list(timing_plans_db.values())


@router.post("/plans/", response_model=TimingPlan)
async def create_timing_plan(plan: TimingPlan):
    """Create new timing plan"""
    timing_plans_db[plan.plan_id] = plan
    return plan


@router.get("/plans/{plan_id}", response_model=TimingPlan)
async def get_timing_plan(plan_id: str):
    """Get timing plan"""
    if plan_id not in timing_plans_db:
        raise HTTPException(status_code=404, detail="Timing plan not found")
    return timing_plans_db[plan_id]


@router.put("/plans/{plan_id}", response_model=TimingPlan)
async def update_timing_plan(plan_id: str, plan: TimingPlan):
    """Update timing plan"""
    if plan_id not in timing_plans_db:
        raise HTTPException(status_code=404, detail="Timing plan not found")
    timing_plans_db[plan_id] = plan
    return plan


@router.delete("/plans/{plan_id}")
async def delete_timing_plan(plan_id: str):
    """Delete timing plan"""
    if plan_id not in timing_plans_db:
        raise HTTPException(status_code=404, detail="Timing plan not found")
    del timing_plans_db[plan_id]
    return {"message": "Timing plan deleted"}
