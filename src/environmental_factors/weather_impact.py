"""
Environmental Factors Module

Implements weather impact modeling, time-of-day patterns, event-based scenarios,
and pedestrian crossing integration for traffic signal optimization.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
import json
import logging
from collections import defaultdict, deque
import math

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """Weather condition types"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN_LIGHT = "rain_light"
    RAIN_MODERATE = "rain_moderate"
    RAIN_HEAVY = "rain_heavy"
    SNOW_LIGHT = "snow_light"
    SNOW_MODERATE = "snow_moderate"
    SNOW_HEAVY = "snow_heavy"
    FOG_LIGHT = "fog_light"
    FOG_HEAVY = "fog_heavy"
    WIND_LIGHT = "wind_light"
    WIND_MODERATE = "wind_moderate"
    WIND_HEAVY = "wind_heavy"


class TimeOfDay(Enum):
    """Time of day categories"""
    EARLY_MORNING = "early_morning"    # 00:00 - 06:00
    MORNING_RUSH = "morning_rush"      # 06:00 - 09:00
    MORNING = "morning"                 # 09:00 - 12:00
    AFTERNOON = "afternoon"             # 12:00 - 17:00
    EVENING_RUSH = "evening_rush"      # 17:00 - 20:00
    EVENING = "evening"                 # 20:00 - 23:00
    NIGHT = "night"                     # 23:00 - 00:00


class EventType(Enum):
    """Event types affecting traffic"""
    SPORTING_EVENT = "sporting_event"
    CONCERT = "concert"
    FESTIVAL = "festival"
    CONFERENCE = "conference"
    SCHOOL_START = "school_start"
    SCHOOL_END = "school_end"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"
    ROAD_WORK = "road_work"
    ACCIDENT = "accident"
    SPECIAL_EVENT = "special_event"


@dataclass
class WeatherData:
    """Weather data structure"""
    condition: WeatherCondition
    temperature: float  # Celsius
    humidity: float     # Percentage
    wind_speed: float  # km/h
    visibility: float   # km
    precipitation: float  # mm/h
    timestamp: datetime
    road_condition: str = "dry"  # dry, wet, icy, snow


@dataclass
class TrafficPattern:
    """Traffic pattern for specific time period"""
    time_of_day: TimeOfDay
    day_type: str  # weekday, weekend, holiday
    base_flow: float  # vehicles per hour
    peak_multiplier: float
    speed_factor: float
    signal_timing_adjustment: float


@dataclass
class EventImpact:
    """Event impact on traffic"""
    event_type: EventType
    start_time: datetime
    end_time: datetime
    location: str
    expected_attendees: int
    traffic_multiplier: float
    affected_approaches: List[str]
    special_signal_timing: Dict[str, float]


@dataclass
class PedestrianData:
    """Pedestrian crossing data"""
    location: str
    count: int
    crossing_time: float  # seconds
    waiting_time: float   # seconds
    timestamp: datetime
    age_distribution: Dict[str, float] = field(default_factory=dict)
    mobility_assistance: bool = False


class WeatherImpactModel:
    """Weather impact modeling on traffic behavior"""
    
    def __init__(self):
        # Weather impact factors (based on research studies)
        self.weather_impacts = {
            WeatherCondition.CLEAR: {
                'speed_factor': 1.0,
                'flow_factor': 1.0,
                'reaction_time_factor': 1.0,
                'visibility_factor': 1.0,
                'braking_distance_factor': 1.0
            },
            WeatherCondition.CLOUDY: {
                'speed_factor': 0.95,
                'flow_factor': 0.98,
                'reaction_time_factor': 1.05,
                'visibility_factor': 0.9,
                'braking_distance_factor': 1.05
            },
            WeatherCondition.RAIN_LIGHT: {
                'speed_factor': 0.85,
                'flow_factor': 0.9,
                'reaction_time_factor': 1.15,
                'visibility_factor': 0.8,
                'braking_distance_factor': 1.3
            },
            WeatherCondition.RAIN_MODERATE: {
                'speed_factor': 0.75,
                'flow_factor': 0.8,
                'reaction_time_factor': 1.25,
                'visibility_factor': 0.7,
                'braking_distance_factor': 1.5
            },
            WeatherCondition.RAIN_HEAVY: {
                'speed_factor': 0.6,
                'flow_factor': 0.65,
                'reaction_time_factor': 1.4,
                'visibility_factor': 0.5,
                'braking_distance_factor': 1.8
            },
            WeatherCondition.SNOW_LIGHT: {
                'speed_factor': 0.7,
                'flow_factor': 0.75,
                'reaction_time_factor': 1.3,
                'visibility_factor': 0.7,
                'braking_distance_factor': 1.6
            },
            WeatherCondition.SNOW_MODERATE: {
                'speed_factor': 0.5,
                'flow_factor': 0.6,
                'reaction_time_factor': 1.5,
                'visibility_factor': 0.5,
                'braking_distance_factor': 2.0
            },
            WeatherCondition.SNOW_HEAVY: {
                'speed_factor': 0.3,
                'flow_factor': 0.4,
                'reaction_time_factor': 1.7,
                'visibility_factor': 0.3,
                'braking_distance_factor': 2.5
            },
            WeatherCondition.FOG_LIGHT: {
                'speed_factor': 0.8,
                'flow_factor': 0.85,
                'reaction_time_factor': 1.2,
                'visibility_factor': 0.6,
                'braking_distance_factor': 1.4
            },
            WeatherCondition.FOG_HEAVY: {
                'speed_factor': 0.5,
                'flow_factor': 0.6,
                'reaction_time_factor': 1.5,
                'visibility_factor': 0.3,
                'braking_distance_factor': 2.0
            }
        }
        
        # Temperature impacts
        self.temperature_impacts = {
            'very_cold': {'threshold': -10, 'speed_factor': 0.9, 'reaction_factor': 1.1},
            'cold': {'threshold': 0, 'speed_factor': 0.95, 'reaction_factor': 1.05},
            'normal': {'threshold': 20, 'speed_factor': 1.0, 'reaction_factor': 1.0},
            'hot': {'threshold': 30, 'speed_factor': 0.98, 'reaction_factor': 1.02},
            'very_hot': {'threshold': 40, 'speed_factor': 0.95, 'reaction_factor': 1.05}
        }
        
        # Wind impacts
        self.wind_impacts = {
            'calm': {'threshold': 10, 'factor': 1.0},
            'light': {'threshold': 30, 'factor': 0.98},
            'moderate': {'threshold': 50, 'factor': 0.95},
            'strong': {'threshold': 70, 'factor': 0.9},
            'severe': {'threshold': 100, 'factor': 0.8}
        }
    
    def calculate_weather_impact(self, weather: WeatherData) -> Dict[str, float]:
        """Calculate comprehensive weather impact on traffic"""
        base_impact = self.weather_impacts.get(weather.condition, self.weather_impacts[WeatherCondition.CLEAR])
        
        # Temperature adjustment
        temp_factor = 1.0
        for temp_category, temp_data in self.temperature_impacts.items():
            if weather.temperature <= temp_data['threshold']:
                temp_factor = temp_data['speed_factor']
                break
        
        # Wind adjustment
        wind_factor = 1.0
        for wind_category, wind_data in self.wind_impacts.items():
            if weather.wind_speed <= wind_data['threshold']:
                wind_factor = wind_data['factor']
                break
        
        # Combined impact
        combined_impact = {
            'speed_factor': base_impact['speed_factor'] * temp_factor * wind_factor,
            'flow_factor': base_impact['flow_factor'] * temp_factor * wind_factor,
            'reaction_time_factor': base_impact['reaction_time_factor'],
            'visibility_factor': base_impact['visibility_factor'],
            'braking_distance_factor': base_impact['braking_distance_factor'],
            'signal_timing_adjustment': self._calculate_signal_timing_adjustment(base_impact, temp_factor, wind_factor)
        }
        
        return combined_impact
    
    def _calculate_signal_timing_adjustment(self, base_impact: Dict, temp_factor: float, wind_factor: float) -> float:
        """Calculate signal timing adjustment based on weather"""
        # Increase green time in poor conditions
        speed_reduction = 1.0 - (base_impact['speed_factor'] * temp_factor * wind_factor)
        reaction_increase = base_impact['reaction_time_factor'] - 1.0
        
        # Timing adjustment (10-30% increase in poor conditions)
        adjustment = 1.0 + (speed_reduction * 0.5) + (reaction_increase * 0.3)
        return min(adjustment, 1.3)  # Cap at 30% increase
    
    def predict_weather_transition_impact(self, current_weather: WeatherData, 
                                        forecast_weather: WeatherData, 
                                        transition_time: int) -> Dict[str, float]:
        """Predict impact of weather transition"""
        current_impact = self.calculate_weather_impact(current_weather)
        forecast_impact = self.calculate_weather_impact(forecast_weather)
        
        # Transition smoothness factor
        time_factor = min(transition_time / 60.0, 1.0)  # Normalize to 0-1 (60 minutes = full transition)
        
        # Interpolate impacts
        transition_impact = {}
        for key in current_impact:
            current_val = current_impact[key]
            forecast_val = forecast_impact[key]
            transition_impact[key] = current_val + (forecast_val - current_val) * time_factor
        
        return transition_impact


class TimeOfDayAnalyzer:
    """Time-of-day traffic pattern analysis"""
    
    def __init__(self):
        # Base traffic patterns (vehicles per hour per lane)
        self.base_patterns = {
            TimeOfDay.EARLY_MORNING: {
                'weekday': {'flow': 200, 'speed': 55, 'peak_factor': 0.3},
                'weekend': {'flow': 150, 'speed': 60, 'peak_factor': 0.2},
                'holiday': {'flow': 100, 'speed': 65, 'peak_factor': 0.15}
            },
            TimeOfDay.MORNING_RUSH: {
                'weekday': {'flow': 1200, 'speed': 35, 'peak_factor': 1.0},
                'weekend': {'flow': 400, 'speed': 50, 'peak_factor': 0.4},
                'holiday': {'flow': 300, 'speed': 55, 'peak_factor': 0.3}
            },
            TimeOfDay.MORNING: {
                'weekday': {'flow': 800, 'speed': 45, 'peak_factor': 0.7},
                'weekend': {'flow': 600, 'speed': 50, 'peak_factor': 0.5},
                'holiday': {'flow': 500, 'speed': 55, 'peak_factor': 0.4}
            },
            TimeOfDay.AFTERNOON: {
                'weekday': {'flow': 900, 'speed': 40, 'peak_factor': 0.8},
                'weekend': {'flow': 700, 'speed': 45, 'peak_factor': 0.6},
                'holiday': {'flow': 600, 'speed': 50, 'peak_factor': 0.5}
            },
            TimeOfDay.EVENING_RUSH: {
                'weekday': {'flow': 1300, 'speed': 30, 'peak_factor': 1.0},
                'weekend': {'flow': 500, 'speed': 45, 'peak_factor': 0.5},
                'holiday': {'flow': 400, 'speed': 50, 'peak_factor': 0.4}
            },
            TimeOfDay.EVENING: {
                'weekday': {'flow': 700, 'speed': 45, 'peak_factor': 0.6},
                'weekend': {'flow': 800, 'speed': 40, 'peak_factor': 0.7},
                'holiday': {'flow': 600, 'speed': 45, 'peak_factor': 0.5}
            },
            TimeOfDay.NIGHT: {
                'weekday': {'flow': 300, 'speed': 60, 'peak_factor': 0.4},
                'weekend': {'flow': 400, 'speed': 55, 'peak_factor': 0.5},
                'holiday': {'flow': 250, 'speed': 65, 'peak_factor': 0.3}
            }
        }
        
        # Signal timing adjustments by time of day
        self.signal_adjustments = {
            TimeOfDay.EARLY_MORNING: {'cycle_length': 0.8, 'green_split': 0.5},
            TimeOfDay.MORNING_RUSH: {'cycle_length': 1.2, 'green_split': 0.6},
            TimeOfDay.MORNING: {'cycle_length': 1.0, 'green_split': 0.55},
            TimeOfDay.AFTERNOON: {'cycle_length': 1.1, 'green_split': 0.55},
            TimeOfDay.EVENING_RUSH: {'cycle_length': 1.3, 'green_split': 0.65},
            TimeOfDay.EVENING: {'cycle_length': 1.0, 'green_split': 0.5},
            TimeOfDay.NIGHT: {'cycle_length': 0.7, 'green_split': 0.45}
        }
    
    def get_time_of_day(self, timestamp: datetime) -> TimeOfDay:
        """Determine time of day category"""
        hour = timestamp.hour
        
        if 0 <= hour < 6:
            return TimeOfDay.EARLY_MORNING
        elif 6 <= hour < 9:
            return TimeOfDay.MORNING_RUSH
        elif 9 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            return TimeOfDay.EVENING_RUSH
        elif 20 <= hour < 23:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def get_day_type(self, timestamp: datetime) -> str:
        """Determine day type"""
        if timestamp.weekday() >= 5:  # Saturday, Sunday
            return 'weekend'
        else:
            return 'weekday'
    
    def get_traffic_pattern(self, timestamp: datetime) -> TrafficPattern:
        """Get traffic pattern for specific time"""
        time_of_day = self.get_time_of_day(timestamp)
        day_type = self.get_day_type(timestamp)
        
        pattern_data = self.base_patterns[time_of_day][day_type]
        signal_data = self.signal_adjustments[time_of_day]
        
        return TrafficPattern(
            time_of_day=time_of_day,
            day_type=day_type,
            base_flow=pattern_data['flow'],
            peak_multiplier=pattern_data['peak_factor'],
            speed_factor=pattern_data['speed'] / 55.0,  # Normalize to free-flow speed
            signal_timing_adjustment=signal_data['cycle_length']
        )
    
    def predict_traffic_evolution(self, start_time: datetime, 
                                duration_hours: int = 24) -> List[TrafficPattern]:
        """Predict traffic pattern evolution over time"""
        patterns = []
        current_time = start_time
        
        for hour in range(duration_hours):
            pattern = self.get_traffic_pattern(current_time)
            patterns.append(pattern)
            current_time += timedelta(hours=1)
        
        return patterns
    
    def calculate_peak_hour_factors(self, patterns: List[TrafficPattern]) -> Dict[str, float]:
        """Calculate peak hour factors from traffic patterns"""
        flows = [p.base_flow * p.peak_multiplier for p in patterns]
        
        if not flows:
            return {}
        
        max_flow = max(flows)
        avg_flow = np.mean(flows)
        
        return {
            'peak_hour_factor': max_flow / avg_flow if avg_flow > 0 else 1.0,
            'peak_flow': max_flow,
            'average_flow': avg_flow,
            'off_peak_factor': min(flows) / max_flow if max_flow > 0 else 1.0
        }


class EventImpactAnalyzer:
    """Event-based traffic impact analysis"""
    
    def __init__(self):
        # Event impact factors
        self.event_impacts = {
            EventType.SPORTING_EVENT: {
                'traffic_multiplier': 2.5,
                'duration_factor': 3.0,  # hours before and after
                'spatial_radius': 5.0,   # km
                'arrival_pattern': 'gradual',
                'departure_pattern': 'sharp'
            },
            EventType.CONCERT: {
                'traffic_multiplier': 2.0,
                'duration_factor': 2.0,
                'spatial_radius': 3.0,
                'arrival_pattern': 'gradual',
                'departure_pattern': 'gradual'
            },
            EventType.FESTIVAL: {
                'traffic_multiplier': 3.0,
                'duration_factor': 4.0,
                'spatial_radius': 8.0,
                'arrival_pattern': 'gradual',
                'departure_pattern': 'gradual'
            },
            EventType.CONFERENCE: {
                'traffic_multiplier': 1.5,
                'duration_factor': 1.5,
                'spatial_radius': 2.0,
                'arrival_pattern': 'sharp',
                'departure_pattern': 'sharp'
            },
            EventType.SCHOOL_START: {
                'traffic_multiplier': 1.8,
                'duration_factor': 0.5,
                'spatial_radius': 1.0,
                'arrival_pattern': 'sharp',
                'departure_pattern': 'minimal'
            },
            EventType.SCHOOL_END: {
                'traffic_multiplier': 1.6,
                'duration_factor': 0.5,
                'spatial_radius': 1.0,
                'arrival_pattern': 'minimal',
                'departure_pattern': 'sharp'
            },
            EventType.HOLIDAY: {
                'traffic_multiplier': 0.7,  # Reduced commuter traffic
                'duration_factor': 24.0,
                'spatial_radius': 50.0,
                'arrival_pattern': 'distributed',
                'departure_pattern': 'distributed'
            },
            EventType.WEEKEND: {
                'traffic_multiplier': 0.8,
                'duration_factor': 48.0,
                'spatial_radius': 50.0,
                'arrival_pattern': 'distributed',
                'departure_pattern': 'distributed'
            },
            EventType.ROAD_WORK: {
                'traffic_multiplier': 0.6,  # Capacity reduction
                'duration_factor': 8.0,
                'spatial_radius': 1.0,
                'arrival_pattern': 'normal',
                'departure_pattern': 'normal'
            },
            EventType.ACCIDENT: {
                'traffic_multiplier': 0.3,  # Severe capacity reduction
                'duration_factor': 2.0,
                'spatial_radius': 2.0,
                'arrival_pattern': 'normal',
                'departure_pattern': 'normal'
            }
        }
    
    def create_event_impact(self, event_type: EventType, start_time: datetime,
                           end_time: datetime, location: str,
                           expected_attendees: int = 0) -> EventImpact:
        """Create event impact object"""
        event_data = self.event_impacts.get(event_type, self.event_impacts[EventType.SPORTING_EVENT])
        
        # Adjust multiplier based on attendees
        if expected_attendees > 0:
            attendee_factor = min(expected_attendees / 10000.0, 2.0)  # Cap at 2x
            traffic_multiplier = event_data['traffic_multiplier'] * (1 + attendee_factor)
        else:
            traffic_multiplier = event_data['traffic_multiplier']
        
        return EventImpact(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            location=location,
            expected_attendees=expected_attendees,
            traffic_multiplier=traffic_multiplier,
            affected_approaches=self._determine_affected_approaches(location),
            special_signal_timing=self._calculate_special_timing(event_type)
        )
    
    def _determine_affected_approaches(self, location: str) -> List[str]:
        """Determine which intersection approaches are affected"""
        # Simplified approach determination
        approaches = ['north', 'south', 'east', 'west']
        
        # In real implementation, this would use GIS data
        if 'stadium' in location.lower():
            return approaches
        elif 'school' in location.lower():
            return ['north', 'south']
        else:
            return approaches[:2]  # Default to two approaches
    
    def _calculate_special_timing(self, event_type: EventType) -> Dict[str, float]:
        """Calculate special signal timing for event"""
        base_timing = {
            'cycle_length_multiplier': 1.0,
            'green_extension': 0.0,
            'pedestrian_phase': 1.0
        }
        
        if event_type in [EventType.SPORTING_EVENT, EventType.CONCERT, EventType.FESTIVAL]:
            base_timing['cycle_length_multiplier'] = 1.2
            base_timing['green_extension'] = 5.0
            base_timing['pedestrian_phase'] = 1.5
        elif event_type in [EventType.SCHOOL_START, EventType.SCHOOL_END]:
            base_timing['cycle_length_multiplier'] = 1.1
            base_timing['pedestrian_phase'] = 2.0
        elif event_type == EventType.ACCIDENT:
            base_timing['cycle_length_multiplier'] = 0.8  # Shorter cycles for quicker response
        
        return base_timing
    
    def calculate_event_temporal_impact(self, event: EventImpact, 
                                      current_time: datetime) -> float:
        """Calculate event impact at specific time"""
        if current_time < event.start_time:
            # Before event - ramp up
            time_to_event = (event.start_time - current_time).total_seconds() / 3600
            if time_to_event < 2.0:  # Within 2 hours
                return 1.0 + (event.traffic_multiplier - 1.0) * (1.0 - time_to_event / 2.0)
        elif current_time <= event.end_time:
            # During event
            return event.traffic_multiplier
        else:
            # After event - ramp down
            time_since_event = (current_time - event.end_time).total_seconds() / 3600
            if time_since_event < 2.0:  # Within 2 hours
                return 1.0 + (event.traffic_multiplier - 1.0) * (time_since_event / 2.0)
        
        return 1.0  # No impact


class PedestrianAnalyzer:
    """Pedestrian crossing analysis and integration"""
    
    def __init__(self):
        # Pedestrian crossing characteristics
        self.crossing_characteristics = {
            'adult': {'speed': 1.2, 'reaction_time': 1.5, 'start_up_time': 3.0},
            'child': {'speed': 0.8, 'reaction_time': 2.0, 'start_up_time': 4.0},
            'elderly': {'speed': 0.9, 'reaction_time': 2.5, 'start_up_time': 5.0},
            'disabled': {'speed': 0.6, 'reaction_time': 3.0, 'start_up_time': 6.0}
        }
        
        # Crossing demand patterns
        self.demand_patterns = {
            TimeOfDay.EARLY_MORNING: {'demand': 0.2, 'group_size': 1.2},
            TimeOfDay.MORNING_RUSH: {'demand': 1.0, 'group_size': 2.0},
            TimeOfDay.MORNING: {'demand': 0.6, 'group_size': 1.5},
            TimeOfDay.AFTERNOON: {'demand': 0.8, 'group_size': 1.8},
            TimeOfDay.EVENING_RUSH: {'demand': 1.2, 'group_size': 2.2},
            TimeOfDay.EVENING: {'demand': 0.9, 'group_size': 1.6},
            TimeOfDay.NIGHT: {'demand': 0.3, 'group_size': 1.1}
        }
    
    def analyze_crossing_demand(self, location: str, 
                              timestamp: datetime) -> Dict[str, float]:
        """Analyze pedestrian crossing demand"""
        time_of_day = self._get_time_of_day(timestamp)
        day_type = self._get_day_type(timestamp)
        
        base_demand = self.demand_patterns[time_of_day]['demand']
        group_size = self.demand_patterns[time_of_day]['group_size']
        
        # Adjust for day type
        if day_type == 'weekend':
            base_demand *= 1.5
            group_size *= 1.3
        elif day_type == 'holiday':
            base_demand *= 1.8
            group_size *= 1.5
        
        # Location-specific adjustments
        location_multiplier = self._get_location_multiplier(location)
        
        return {
            'demand_rate': base_demand * location_multiplier,  # pedestrians per minute
            'average_group_size': group_size,
            'peak_waiting_time': self._estimate_waiting_time(base_demand),
            'crossing_time': self._calculate_crossing_time(group_size)
        }
    
    def _get_time_of_day(self, timestamp: datetime) -> TimeOfDay:
        """Get time of day category"""
        hour = timestamp.hour
        if 0 <= hour < 6:
            return TimeOfDay.EARLY_MORNING
        elif 6 <= hour < 9:
            return TimeOfDay.MORNING_RUSH
        elif 9 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            return TimeOfDay.EVENING_RUSH
        elif 20 <= hour < 23:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def _get_day_type(self, timestamp: datetime) -> str:
        """Get day type"""
        if timestamp.weekday() >= 5:
            return 'weekend'
        else:
            return 'weekday'
    
    def _get_location_multiplier(self, location: str) -> float:
        """Get location-specific demand multiplier"""
        location_lower = location.lower()
        
        if 'school' in location_lower:
            return 2.5
        elif 'hospital' in location_lower:
            return 1.8
        elif 'park' in location_lower:
            return 1.5
        elif 'station' in location_lower:
            return 2.0
        elif 'mall' in location_lower:
            return 1.6
        else:
            return 1.0
    
    def _estimate_waiting_time(self, demand_rate: float) -> float:
        """Estimate average pedestrian waiting time"""
        # Simple queueing model
        if demand_rate < 0.5:
            return 10.0  # seconds
        elif demand_rate < 1.0:
            return 20.0
        elif demand_rate < 2.0:
            return 35.0
        else:
            return 50.0
    
    def _calculate_crossing_time(self, group_size: float) -> float:
        """Calculate crossing time based on group characteristics"""
        # Assume mixed group with average characteristics
        avg_speed = 1.0  # m/s
        crossing_distance = 15.0  # meters (typical intersection)
        
        base_time = crossing_distance / avg_speed
        group_factor = 1.0 + (group_size - 1.0) * 0.2  # Larger groups take longer
        
        return base_time * group_factor
    
    def calculate_pedestrian_phase_timing(self, crossing_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate optimal pedestrian signal phase timing"""
        min_walk_time = crossing_data['crossing_time']
        pedestrian_clearance = min_walk_time + 3.0  # 3 seconds clearance
        
        # Calculate required green time based on demand
        demand_rate = crossing_data['demand_rate']
        if demand_rate > 1.0:  # High demand
            min_green = max(min_walk_time + 5.0, 15.0)
        elif demand_rate > 0.5:  # Medium demand
            min_green = max(min_walk_time + 3.0, 12.0)
        else:  # Low demand
            min_green = max(min_walk_time, 10.0)
        
        return {
            'min_walk_time': min_walk_time,
            'pedestrian_clearance': pedestrian_clearance,
            'min_green_time': min_green,
            'recommended_cycle_extension': max(0, min_green - 10.0)
        }


class EnvironmentalFactorsIntegrator:
    """Main integration of all environmental factors"""
    
    def __init__(self):
        self.weather_model = WeatherImpactModel()
        self.time_analyzer = TimeOfDayAnalyzer()
        self.event_analyzer = EventImpactAnalyzer()
        self.pedestrian_analyzer = PedestrianAnalyzer()
        
        # Active events tracking
        self.active_events = []
        self.weather_history = deque(maxlen=24)  # 24 hours of weather data
        self.pedestrian_history = deque(maxlen=48)  # 48 hours of pedestrian data
    
    def update_weather(self, weather_data: WeatherData):
        """Update current weather conditions"""
        self.weather_history.append(weather_data)
    
    def add_event(self, event: EventImpact):
        """Add new event to tracking"""
        self.active_events.append(event)
        # Remove expired events
        current_time = datetime.now()
        self.active_events = [e for e in self.active_events if e.end_time > current_time]
    
    def add_pedestrian_data(self, pedestrian_data: PedestrianData):
        """Add pedestrian crossing data"""
        self.pedestrian_history.append(pedestrian_data)
    
    def calculate_comprehensive_impact(self, timestamp: datetime, 
                                      location: str) -> Dict[str, Any]:
        """Calculate comprehensive environmental impact"""
        # Get current weather
        current_weather = self.weather_history[-1] if self.weather_history else None
        
        # Calculate individual impacts
        impacts = {}
        
        # Weather impact
        if current_weather:
            impacts['weather'] = self.weather_model.calculate_weather_impact(current_weather)
        
        # Time of day impact
        traffic_pattern = self.time_analyzer.get_traffic_pattern(timestamp)
        impacts['time_of_day'] = {
            'flow_factor': traffic_pattern.peak_multiplier,
            'speed_factor': traffic_pattern.speed_factor,
            'signal_adjustment': traffic_pattern.signal_timing_adjustment
        }
        
        # Event impacts
        event_impact = 1.0
        for event in self.active_events:
            event_impact *= self.event_analyzer.calculate_event_temporal_impact(event, timestamp)
        impacts['events'] = {'traffic_multiplier': event_impact}
        
        # Pedestrian impact
        pedestrian_demand = self.pedestrian_analyzer.analyze_crossing_demand(location, timestamp)
        pedestrian_timing = self.pedestrian_analyzer.calculate_pedestrian_phase_timing(pedestrian_demand)
        impacts['pedestrians'] = {
            'demand_factor': pedestrian_demand['demand_rate'],
            'timing_adjustment': pedestrian_timing['recommended_cycle_extension']
        }
        
        # Combined impact
        combined_impact = self._combine_impacts(impacts)
        impacts['combined'] = combined_impact
        
        return impacts
    
    def _combine_impacts(self, impacts: Dict[str, Dict]) -> Dict[str, float]:
        """Combine all individual impacts"""
        combined = {
            'speed_factor': 1.0,
            'flow_factor': 1.0,
            'signal_timing_adjustment': 1.0,
            'safety_factor': 1.0
        }
        
        # Weather impacts
        if 'weather' in impacts:
            weather = impacts['weather']
            combined['speed_factor'] *= weather['speed_factor']
            combined['flow_factor'] *= weather['flow_factor']
            combined['signal_timing_adjustment'] *= weather['signal_timing_adjustment']
            combined['safety_factor'] *= (2.0 - weather['visibility_factor'])  # Lower visibility = higher safety factor
        
        # Time of day impacts
        if 'time_of_day' in impacts:
            tod = impacts['time_of_day']
            combined['flow_factor'] *= tod['flow_factor']
            combined['speed_factor'] *= tod['speed_factor']
            combined['signal_timing_adjustment'] *= tod['signal_adjustment']
        
        # Event impacts
        if 'events' in impacts:
            events = impacts['events']
            combined['flow_factor'] *= events['traffic_multiplier']
        
        # Pedestrian impacts
        if 'pedestrians' in impacts:
            peds = impacts['pedestrians']
            combined['signal_timing_adjustment'] += peds['timing_adjustment'] / 60.0  # Convert to minutes
            combined['safety_factor'] *= (1.0 + peds['demand_factor'] * 0.1)
        
        return combined
    
    def generate_signal_timing_recommendations(self, impacts: Dict[str, Any]) -> Dict[str, float]:
        """Generate signal timing recommendations based on impacts"""
        combined = impacts.get('combined', {})
        
        base_cycle_length = 120.0  # seconds
        base_green_split = 0.5
        
        # Adjust cycle length
        cycle_adjustment = combined.get('signal_timing_adjustment', 1.0)
        recommended_cycle = base_cycle_length * cycle_adjustment
        
        # Adjust green split based on flow balance
        flow_factor = combined.get('flow_factor', 1.0)
        if flow_factor > 1.2:  # High demand
            green_split = 0.6
        elif flow_factor < 0.8:  # Low demand
            green_split = 0.4
        else:
            green_split = base_green_split
        
        # Safety adjustments
        safety_factor = combined.get('safety_factor', 1.0)
        if safety_factor > 1.3:  # High safety concern
            recommended_cycle *= 1.1
            green_split = 0.55  # More balanced for safety
        
        return {
            'cycle_length': recommended_cycle,
            'green_split': green_split,
            'pedestrian_phase_time': 15.0 * safety_factor,
            'clearance_time': 5.0 * safety_factor
        }
    
    def predict_future_conditions(self, hours_ahead: int = 4) -> List[Dict[str, Any]]:
        """Predict environmental conditions for next few hours"""
        current_time = datetime.now()
        predictions = []
        
        for hour in range(hours_ahead):
            future_time = current_time + timedelta(hours=hour+1)
            
            # Predict traffic pattern
            pattern = self.time_analyzer.get_traffic_pattern(future_time)
            
            # Predict weather (simplified - would use weather API in real implementation)
            weather_prediction = self._predict_weather(future_time)
            
            # Check for scheduled events
            event_impacts = []
            for event in self.active_events:
                if event.start_time <= future_time <= event.end_time:
                    event_impacts.append(event.traffic_multiplier)
            
            # Combine predictions
            prediction = {
                'timestamp': future_time,
                'traffic_pattern': pattern,
                'weather_prediction': weather_prediction,
                'event_impacts': event_impacts,
                'predicted_flow_factor': pattern.peak_multiplier * max(event_impacts + [1.0])
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def _predict_weather(self, timestamp: datetime) -> Dict[str, float]:
        """Simple weather prediction (would use weather API in real implementation)"""
        # Simplified prediction based on current weather
        if self.weather_history:
            current = self.weather_history[-1]
            # Assume gradual weather changes
            return {
                'temperature': current.temperature,
                'visibility': current.visibility,
                'condition': current.condition.value
            }
        else:
            return {
                'temperature': 20.0,
                'visibility': 10.0,
                'condition': 'clear'
            }


# Factory functions
def create_weather_model() -> WeatherImpactModel:
    """Create weather impact model"""
    return WeatherImpactModel()


def create_time_analyzer() -> TimeOfDayAnalyzer:
    """Create time of day analyzer"""
    return TimeOfDayAnalyzer()


def create_event_analyzer() -> EventImpactAnalyzer:
    """Create event impact analyzer"""
    return EventImpactAnalyzer()


def create_pedestrian_analyzer() -> PedestrianAnalyzer:
    """Create pedestrian analyzer"""
    return PedestrianAnalyzer()


def create_environmental_integrator() -> EnvironmentalFactorsIntegrator:
    """Create comprehensive environmental factors integrator"""
    return EnvironmentalFactorsIntegrator()