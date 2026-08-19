"""
Analytics and forecasting endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from adaptive_traffic.core.analytics.forecaster import create_predictive_analytics

router = APIRouter()

# Initialize analytics engine
analytics_engine = create_predictive_analytics({})


class ForecastRequest(BaseModel):
    intersection_id: str
    horizon_hours: int = 24


class ScenarioRequest(BaseModel):
    intersection_id: str
    flow_modifiers: Dict[str, float]  # direction -> multiplier
    duration_hours: int = 2


class Recommendation(BaseModel):
    type: str
    direction: str
    reason: str
    priority: str
    suggested_extension: int


@router.post("/forecast", response_model=Dict)
async def get_forecast(request: ForecastRequest):
    """Get traffic forecast for intersection"""
    try:
        forecast = analytics_engine.get_forecast(request.intersection_id)
        
        return {
            "intersection_id": request.intersection_id,
            "timestamp": forecast.timestamp.isoformat(),
            "horizon_hours": forecast.horizon_hours,
            "flow_predictions": forecast.flow_predictions,
            "speed_predictions": forecast.speed_predictions,
            "congestion_predictions": forecast.congestion_predictions,
            "confidence_intervals": {
                k: {"lower": v[0], "upper": v[1]} 
                for k, v in forecast.confidence_intervals.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenario", response_model=Dict)
async def evaluate_scenario(request: ScenarioRequest):
    """Evaluate what-if scenario"""
    scenario = {
        "flow_modifiers": request.flow_modifiers,
        "duration_hours": request.duration_hours
    }
    
    result = analytics_engine.evaluate_scenario(scenario)
    return result


@router.get("/recommendations/{intersection_id}", response_model=List[Recommendation])
async def get_recommendations(intersection_id: str):
    """Get signal timing recommendations"""
    try:
        recommendations = analytics_engine.get_recommendations(intersection_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_sensor_data(intersection_id: str, data: Dict):
    """Ingest real-time sensor data"""
    # Add timestamp if not present
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now().isoformat()
    
    # Add intersection_id
    data['intersection_id'] = intersection_id
    
    # Ingest into analytics engine
    analytics_engine.ingest_sensor_data(intersection_id, data)
    
    return {"status": "ingested", "intersection_id": intersection_id}


@router.get("/metrics/{intersection_id}")
async def get_metrics(
    intersection_id: str,
    window_hours: int = Query(1, ge=1, le=168)
):
    """Get traffic metrics for time window"""
    # In real implementation, query from database
    # Return mock data
    return {
        "intersection_id": intersection_id,
        "window_hours": window_hours,
        "avg_flow": {
            "north": 450,
            "south": 420,
            "east": 380,
            "west": 350
        },
        "avg_speed": {
            "north": 42.5,
            "south": 44.2,
            "east": 38.7,
            "west": 35.1
        },
        "congestion_level": {
            "north": 0.65,
            "south": 0.58,
            "east": 0.72,
            "west": 0.78
        },
        "total_vehicles": 6542,
        "avg_wait_time": 28.5,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/performance/{intersection_id}")
async def get_performance(
    intersection_id: str,
    days: int = Query(7, ge=1, le=90)
):
    """Get performance analytics"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate daily data points
    daily_data = []
    current = start_date
    while current <= end_date:
        daily_data.append({
            "date": current.date().isoformat(),
            "avg_wait_time": 25 + np.random.normal(0, 5),
            "throughput": 1800 + np.random.normal(0, 100),
            "congestion_index": 0.5 + np.random.normal(0, 0.1),
            "incidents": max(0, int(np.random.normal(1, 1)))
        })
        current += timedelta(days=1)
    
    return {
        "intersection_id": intersection_id,
        "period_days": days,
        "daily_data": daily_data,
        "summary": {
            "avg_wait_time": np.mean([d["avg_wait_time"] for d in daily_data]),
            "total_throughput": sum(d["throughput"] for d in daily_data),
            "avg_congestion": np.mean([d["congestion_index"] for d in daily_data]),
            "total_incidents": sum(d["incidents"] for d in daily_data)
        }
    }


@router.get("/environmental/{intersection_id}")
async def get_environmental_impact(intersection_id: str):
    """Get environmental impact metrics"""
    return {
        "intersection_id": intersection_id,
        "annual_fuel_savings_gal": 12450,
        "annual_co2_reduction_tons": 124,
        "annual_time_savings_hours": 15333,
        "annual_economic_value_usd": 306667,
        "emissions_breakdown": {
            "CO2": 124.0,
            "NOx": 2.8,
            "PM2_5": 0.45,
            "VOCs": 1.2,
            "CO": 12.5
        },
        "equivalent_cars_removed": 27,
        "equivalent_trees_planted": 5636
    }