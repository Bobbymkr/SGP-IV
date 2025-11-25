#!/usr/bin/env python3
"""
Enhanced Traffic Signal Algorithms with Environmental Integration
Updates existing traffic algorithms to incorporate weather impact factors
"""

import asyncio
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum
import random

# Import existing systems
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'YOLO', 'darkflow'))

logger = logging.getLogger(__name__)

@dataclass
class EnhancedTrafficMetrics:
    """Enhanced traffic metrics with environmental factors"""
    vehicle_count: int
    queue_length: float
    average_speed: float
    traffic_density: float
    flow_rate: float
    
    # Environmental factors
    weather_condition: str
    visibility_factor: float
    road_condition_factor: float
    safety_risk_factor: float
    capacity_reduction_factor: float
    
    # Calculated metrics
    effective_capacity: float
    adjusted_flow_rate: float
    congestion_level: float
    
    timestamp: datetime = field(default_factory=datetime.now)

class WeatherAwareSignalController:
    """Weather-aware traffic signal controller"""
    
    def __init__(self, intersection_id: str):
        self.intersection_id = intersection_id
        self.logger = logging.getLogger(f"{__name__}.{intersection_id}")
        
        # Base signal timing parameters
        self.base_green_time = 30  # seconds
        self.base_yellow_time = 3   # seconds
        self.base_red_time = 33     # seconds
        self.min_green_time = 10    # seconds
        self.max_green_time = 90    # seconds
        
        # Environmental adjustment parameters
        self.weather_adjustments = {
            'clear': {'timing_multiplier': 1.0, 'speed_multiplier': 1.0},
            'light_rain': {'timing_multiplier': 1.1, 'speed_multiplier': 0.95},
            'moderate_rain': {'timing_multiplier': 1.2, 'speed_multiplier': 0.85},
            'heavy_rain': {'timing_multiplier': 1.3, 'speed_multiplier': 0.75},
            'light_snow': {'timing_multiplier': 1.25, 'speed_multiplier': 0.8},
            'moderate_snow': {'timing_multiplier': 1.4, 'speed_multiplier': 0.7},
            'heavy_snow': {'timing_multiplier': 1.5, 'speed_multiplier': 0.6},
            'fog': {'timing_multiplier': 1.35, 'speed_multiplier': 0.65},
            'strong_wind': {'timing_multiplier': 1.1, 'speed_multiplier': 0.9}
        }
        
        # Traffic state tracking
        self.current_metrics = None
        self.historical_metrics = []
        self.environmental_history = []
        
        # Adaptive learning parameters
        self.learning_rate = 0.01
        self.performance_history = []
        
    async def calculate_weather_adjusted_timing(
        self, 
        traffic_metrics: Dict[str, Any],
        environmental_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate weather-adjusted signal timing"""
        
        # Extract environmental conditions
        weather_condition = environmental_factors.get('weather', 'clear')
        visibility = environmental_factors.get('visibility', 1.0)
        road_condition = environmental_factors.get('road_condition', 'dry')
        precipitation = environmental_factors.get('precipitation', 0)
        wind_speed = environmental_factors.get('wind_speed', 0)
        
        # Get base weather adjustments
        weather_adj = self.weather_adjustments.get(weather_condition, self.weather_adjustments['clear'])
        
        # Calculate additional adjustments
        visibility_adj = 1.0
        if visibility < 0.7:
            visibility_adj = 1.0 + (0.7 - visibility) * 0.5
        
        road_adj = 1.0
        if road_condition == 'wet':
            road_adj = 1.15
        elif road_condition == 'snowy':
            road_adj = 1.3
        elif road_condition == 'icy':
            road_adj = 1.5
        
        # Calculate traffic-based adjustments
        traffic_volume = traffic_metrics.get('volume', 0.5)
        queue_length = traffic_metrics.get('queue_length', 0)
        avg_speed = traffic_metrics.get('avg_speed', 50)
        
        traffic_adj = 1.0
        if traffic_volume > 0.8:
            traffic_adj = 1.2
        elif traffic_volume > 0.6:
            traffic_adj = 1.1
        elif traffic_volume < 0.3:
            traffic_adj = 0.8
        
        # Queue-based adjustments
        queue_adj = 1.0
        if queue_length > 10:
            queue_adj = 1.3
        elif queue_length > 5:
            queue_adj = 1.15
        
        # Speed-based adjustments
        speed_adj = 1.0
        if avg_speed < 30:  # Very slow traffic
            speed_adj = 1.2
        elif avg_speed < 40:  # Slow traffic
            speed_adj = 1.1
        
        # Combine all adjustments
        total_multiplier = (
            weather_adj['timing_multiplier'] * 
            visibility_adj * 
            road_adj * 
            traffic_adj * 
            queue_adj * 
            speed_adj
        )
        
        # Apply to base timing
        adjusted_green = int(self.base_green_time * total_multiplier)
        adjusted_yellow = int(self.base_yellow_time * max(1.0, visibility_adj * road_adj))
        adjusted_red = int(self.base_red_time * total_multiplier)
        
        # Apply constraints
        adjusted_green = max(self.min_green_time, min(self.max_green_time, adjusted_green))
        adjusted_yellow = max(3, min(6, adjusted_yellow))
        adjusted_red = max(10, min(120, adjusted_red))
        
        # Calculate performance metrics
        cycle_time = adjusted_green + adjusted_yellow + adjusted_red
        green_ratio = adjusted_green / cycle_time
        
        return {
            'green_time': adjusted_green,
            'yellow_time': adjusted_yellow,
            'red_time': adjusted_red,
            'cycle_time': cycle_time,
            'green_ratio': green_ratio,
            'total_multiplier': total_multiplier,
            'adjustments': {
                'weather': weather_adj['timing_multiplier'],
                'visibility': visibility_adj,
                'road_condition': road_adj,
                'traffic': traffic_adj,
                'queue': queue_adj,
                'speed': speed_adj
            },
            'environmental_factors': {
                'weather_condition': weather_condition,
                'visibility': visibility,
                'road_condition': road_condition,
                'precipitation': precipitation,
                'wind_speed': wind_speed
            },
            'traffic_factors': {
                'volume': traffic_volume,
                'queue_length': queue_length,
                'avg_speed': avg_speed
            }
        }
    
    async def optimize_multi_phase_timing(
        self, 
        phases: List[Dict[str, Any]],
        environmental_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize multi-phase signal timing with environmental considerations"""
        
        # Calculate base timing for each phase
        phase_timings = []
        total_cycle_time = 0
        
        for i, phase in enumerate(phases):
            traffic_metrics = phase.get('traffic_metrics', {})
            
            # Calculate phase-specific timing
            timing = await self.calculate_weather_adjusted_timing(traffic_metrics, environmental_factors)
            
            # Apply phase-specific adjustments
            phase_priority = phase.get('priority', 1.0)
            timing['green_time'] = int(timing['green_time'] * phase_priority)
            
            # Ensure minimum inter-green time
            if i > 0:
                min_inter_green = 5  # seconds
                prev_phase = phase_timings[i-1]
                if timing['green_time'] < min_inter_green:
                    timing['green_time'] = min_inter_green
            
            phase_timings.append(timing)
            total_cycle_time += timing['cycle_time']
        
        # Balance cycle times across phases
        avg_cycle_time = total_cycle_time / len(phases)
        balanced_timings = []
        
        for timing in phase_timings:
            # Scale to average cycle time
            scale_factor = avg_cycle_time / timing['cycle_time']
            balanced_timing = timing.copy()
            balanced_timing['green_time'] = int(timing['green_time'] * scale_factor)
            balanced_timing['yellow_time'] = max(3, int(timing['yellow_time'] * scale_factor))
            balanced_timing['red_time'] = int(timing['red_time'] * scale_factor)
            balanced_timing['cycle_time'] = balanced_timing['green_time'] + balanced_timing['yellow_time'] + balanced_timing['red_time']
            
            # Apply constraints
            balanced_timing['green_time'] = max(self.min_green_time, min(self.max_green_time, balanced_timing['green_time']))
            
            balanced_timings.append(balanced_timing)
        
        # Calculate coordination offsets for green wave
        coordination_offsets = self._calculate_coordination_offsets(balanced_timings, environmental_factors)
        
        return {
            'phase_timings': balanced_timings,
            'coordination_offsets': coordination_offsets,
            'total_cycle_time': sum(t['cycle_time'] for t in balanced_timings),
            'optimization_objectives': {
                'minimize_delay': True,
                'maximize_throughput': True,
                'ensure_safety': True,
                'environmental_responsiveness': True
            }
        }
    
    def _calculate_coordination_offsets(
        self, 
        phase_timings: List[Dict[str, Any]], 
        environmental_factors: Dict[str, Any]
    ) -> List[int]:
        """Calculate coordination offsets for green wave timing"""
        
        # Base coordination distance (assuming 500m between signals)
        base_distance = 500  # meters
        
        # Adjust speed for environmental conditions
        weather_condition = environmental_factors.get('weather', 'clear')
        base_speed = 50  # km/h
        
        if weather_condition in self.weather_adjustments:
            speed_multiplier = self.weather_adjustments[weather_condition]['speed_multiplier']
        else:
            speed_multiplier = 1.0
        
        # Adjust for visibility and road conditions
        visibility = environmental_factors.get('visibility', 1.0)
        road_condition = environmental_factors.get('road_condition', 'dry')
        
        if visibility < 0.7:
            speed_multiplier *= 0.8
        if road_condition == 'wet':
            speed_multiplier *= 0.9
        elif road_condition == 'snowy':
            speed_multiplier *= 0.7
        elif road_condition == 'icy':
            speed_multiplier *= 0.5
        
        # Calculate effective speed
        effective_speed = base_speed * speed_multiplier  # km/h
        effective_speed_ms = effective_speed / 3.6  # m/s
        
        # Calculate travel time between signals
        travel_time = base_distance / effective_speed_ms  # seconds
        
        # Calculate offsets for each phase
        offsets = []
        for i, timing in enumerate(phase_timings):
            offset = int(i * travel_time) % timing['cycle_time']
            offsets.append(offset)
        
        return offsets
    
    async def implement_emergency_preemption(
        self, 
        emergency_vehicle_data: Dict[str, Any],
        current_timing: Dict[str, Any],
        environmental_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implement emergency vehicle preemption with environmental considerations"""
        
        # Extract emergency vehicle information
        ev_type = emergency_vehicle_data.get('type', 'ambulance')
        ev_distance = emergency_vehicle_data.get('distance', 1000)  # meters
        ev_speed = emergency_vehicle_data.get('speed', 80)  # km/h
        ev_approach_time = emergency_vehicle_data.get('approach_time', ev_distance / (ev_speed / 3.6))  # seconds
        
        # Adjust approach time for environmental conditions
        weather_condition = environmental_factors.get('weather', 'clear')
        visibility = environmental_factors.get('visibility', 1.0)
        road_condition = environmental_factors.get('road_condition', 'dry')
        
        # Environmental speed reduction for emergency vehicles
        env_speed_factor = 1.0
        if weather_condition in ['heavy_rain', 'heavy_snow', 'fog']:
            env_speed_factor = 0.8
        elif visibility < 0.5:
            env_speed_factor = 0.7
        elif road_condition == 'icy':
            env_speed_factor = 0.6
        
        # Adjusted approach time
        adjusted_approach_time = ev_approach_time / env_speed_factor
        
        # Calculate preemption timing
        preemption_start = max(0, adjusted_approach_time - 10)  # Start 10s before arrival
        preemption_duration = 20  # Hold green for 20s
        
        # Determine if immediate preemption is needed
        immediate_preemption = adjusted_approach_time < 15  # Less than 15s away
        
        # Calculate signal adjustments
        if immediate_preemption:
            # Immediate switch to green for emergency approach
            new_timing = {
                'green_time': max(preemption_duration, current_timing.get('green_time', 30)),
                'yellow_time': 3,
                'red_time': 5,
                'preemption_active': True,
                'preemption_type': 'immediate'
            }
        else:
            # Gradual adjustment for coordinated preemption
            adjustment_factor = max(1.0, preemption_duration / current_timing.get('green_time', 30))
            new_timing = {
                'green_time': int(current_timing.get('green_time', 30) * adjustment_factor),
                'yellow_time': current_timing.get('yellow_time', 3),
                'red_time': current_timing.get('red_time', 33),
                'preemption_active': True,
                'preemption_type': 'coordinated'
            }
        
        return {
            'timing_adjustments': new_timing,
            'preemption_schedule': {
                'start_time': preemption_start,
                'duration': preemption_duration,
                'approach_time': adjusted_approach_time,
                'environmental_factor': env_speed_factor
            },
            'emergency_vehicle': {
                'type': ev_type,
                'distance': ev_distance,
                'speed': ev_speed,
                'adjusted_speed': ev_speed * env_speed_factor
            },
            'safety_considerations': {
                'visibility_adequate': visibility > 0.3,
                'road_conditions_safe': road_condition not in ['icy', 'flooded'],
                'weather_permissible': weather_condition not in ['blizzard', 'thunderstorm']
            }
        }
    
    async def adaptive_learning_update(
        self, 
        performance_metrics: Dict[str, Any],
        environmental_factors: Dict[str, Any],
        applied_timing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update adaptive learning parameters based on performance"""
        
        # Extract performance metrics
        average_delay = performance_metrics.get('average_delay', 30)
        throughput = performance_metrics.get('throughput', 100)
        queue_length = performance_metrics.get('queue_length', 5)
        safety_incidents = performance_metrics.get('safety_incidents', 0)
        
        # Calculate performance score
        delay_score = max(0, 1.0 - (average_delay / 60))  # Normalize to 0-1
        throughput_score = min(1.0, throughput / 200)  # Normalize to 0-1
        queue_score = max(0, 1.0 - (queue_length / 20))  # Normalize to 0-1
        safety_score = max(0, 1.0 - (safety_incidents / 5))  # Normalize to 0-1
        
        overall_score = (delay_score + throughput_score + queue_score + safety_score) / 4
        
        # Store performance data
        self.performance_history.append({
            'timestamp': datetime.now(),
            'score': overall_score,
            'environmental_factors': environmental_factors,
            'applied_timing': applied_timing,
            'metrics': performance_metrics
        })
        
        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)
        
        # Analyze performance patterns
        learning_insights = self._analyze_performance_patterns(environmental_factors)
        
        # Update weather adjustment parameters if needed
        weather_condition = environmental_factors.get('weather', 'clear')
        if overall_score < 0.6 and weather_condition in self.weather_adjustments:
            # Poor performance - adjust parameters
            current_adj = self.weather_adjustments[weather_condition]['timing_multiplier']
            
            if delay_score < 0.5:  # High delay
                # Increase green time
                new_adj = min(2.0, current_adj * 1.05)
                self.weather_adjustments[weather_condition]['timing_multiplier'] = new_adj
                learning_insights['adjustment_made'] = f"Increased timing multiplier for {weather_condition} to {new_adj:.2f}"
            
            elif throughput_score < 0.5 and queue_score > 0.7:  # Low throughput but short queues
                # Decrease green time to improve flow
                new_adj = max(0.8, current_adj * 0.95)
                self.weather_adjustments[weather_condition]['timing_multiplier'] = new_adj
                learning_insights['adjustment_made'] = f"Decreased timing multiplier for {weather_condition} to {new_adj:.2f}"
        
        return {
            'performance_score': overall_score,
            'component_scores': {
                'delay': delay_score,
                'throughput': throughput_score,
                'queue': queue_score,
                'safety': safety_score
            },
            'learning_insights': learning_insights,
            'updated_parameters': self.weather_adjustments.get(weather_condition, {})
        }
    
    def _analyze_performance_patterns(self, current_environmental: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance patterns for learning insights"""
        
        if len(self.performance_history) < 10:
            return {"insufficient_data": True}
        
        # Get recent performance data
        recent_data = self.performance_history[-50:]
        
        # Group by weather conditions
        weather_performance = {}
        for record in recent_data:
            weather = record['environmental_factors'].get('weather', 'clear')
            if weather not in weather_performance:
                weather_performance[weather] = []
            weather_performance[weather].append(record['score'])
        
        # Calculate average performance by weather
        weather_averages = {}
        for weather, scores in weather_performance.items():
            weather_averages[weather] = sum(scores) / len(scores)
        
        # Identify patterns
        insights = {}
        
        # Best performing weather conditions
        if weather_averages:
            best_weather = max(weather_averages.items(), key=lambda x: x[1])
            worst_weather = min(weather_averages.items(), key=lambda x: x[1])
            
            insights['best_performing_weather'] = best_weather
            insights['worst_performing_weather'] = worst_weather
            
            # Performance gap analysis
            performance_gap = best_weather[1] - worst_weather[1]
            if performance_gap > 0.3:
                insights['significant_performance_gap'] = True
                insights['gap_analysis'] = f"Performance gap of {performance_gap:.2f} between {best_weather[0]} and {worst_weather[0]}"
        
        # Trend analysis
        if len(recent_data) >= 20:
            recent_scores = [record['score'] for record in recent_data[-20:]]
            older_scores = [record['score'] for record in recent_data[-40:-20]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            
            if recent_avg > older_avg + 0.05:
                insights['performance_trend'] = 'improving'
            elif recent_avg < older_avg - 0.05:
                insights['performance_trend'] = 'declining'
            else:
                insights['performance_trend'] = 'stable'
        
        return insights

# Example usage and testing
async def main():
    """Example usage of weather-aware signal controller"""
    
    controller = WeatherAwareSignalController("intersection_001")
    
    # Sample traffic data
    traffic_metrics = {
        'volume': 0.7,
        'queue_length': 8,
        'avg_speed': 35
    }
    
    # Sample environmental data
    environmental_factors = {
        'weather': 'moderate_rain',
        'visibility': 0.6,
        'road_condition': 'wet',
        'precipitation': 8,
        'wind_speed': 15
    }
    
    # Calculate weather-adjusted timing
    timing = await controller.calculate_weather_adjusted_timing(traffic_metrics, environmental_factors)
    
    print("Weather-Aware Signal Timing")
    print("=" * 40)
    print(f"Green Time: {timing['green_time']}s (base: 30s)")
    print(f"Yellow Time: {timing['yellow_time']}s (base: 3s)")
    print(f"Red Time: {timing['red_time']}s (base: 33s)")
    print(f"Total Multiplier: {timing['total_multiplier']:.2f}")
    
    print(f"\nAdjustments:")
    for factor, value in timing['adjustments'].items():
        print(f"  {factor}: {value:.2f}")
    
    # Test multi-phase optimization
    phases = [
        {'traffic_metrics': {'volume': 0.8, 'queue_length': 10, 'avg_speed': 30}, 'priority': 1.2},
        {'traffic_metrics': {'volume': 0.6, 'queue_length': 5, 'avg_speed': 40}, 'priority': 1.0},
        {'traffic_metrics': {'volume': 0.4, 'queue_length': 3, 'avg_speed': 45}, 'priority': 0.8}
    ]
    
    multi_phase = await controller.optimize_multi_phase_timing(phases, environmental_factors)
    
    print(f"\nMulti-Phase Optimization:")
    print(f"Total Cycle Time: {multi_phase['total_cycle_time']}s")
    for i, phase_timing in enumerate(multi_phase['phase_timings']):
        print(f"  Phase {i+1}: Green={phase_timing['green_time']}s, Total={phase_timing['cycle_time']}s")
    
    # Test emergency preemption
    emergency_data = {
        'type': 'ambulance',
        'distance': 500,
        'speed': 80
    }
    
    preemption = await controller.implement_emergency_preemption(
        emergency_data, timing, environmental_factors
    )
    
    print(f"\nEmergency Preemption:")
    print(f"Type: {preemption['timing_adjustments']['preemption_type']}")
    print(f"Approach Time: {preemption['preemption_schedule']['approach_time']:.1f}s")
    print(f"Environmental Factor: {preemption['preemption_schedule']['environmental_factor']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())