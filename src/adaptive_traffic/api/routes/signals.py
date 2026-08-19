"""
Signal control endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from adaptive_traffic.config.settings import get_settings

router = APIRouter()


class SignalStatus(BaseModel):
    signal_id: str
    intersection_id: str
    current_phase: str
    phase_timer: float
    green_time_remaining: float
    queues: Dict[str, int]
    flows: Dict[str, float]


class SignalTimingUpdate(BaseModel):
    signal_id: str
    green_times: Dict[str, float]
    cycle_length: Optional[float] = None


class TimingPlan(BaseModel):
    plan_id: str
    name: str
    cycle_length: float
    phases: List[Dict]


# In-memory storage (replace with database)
signals_db: Dict[str, SignalStatus] = {}
timing_plans_db: Dict[str, TimingPlan] = {}


@router.get("/", response_model=List[SignalStatus])
async def list_signals(
    intersection_id: Optional[str] = Query(None, description="Filter by intersection")
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
    """Update signal timing plan"""
    if signal_id not in signals_db:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal = signals_db[signal_id]
    signal.queues = timing.green_times  # Update queues with new timing
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
        "timestamp": datetime.utcnow().isoformat()
    }


# Timing plans
@router.get("/plans/", response_model=List[TimingPlan])
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