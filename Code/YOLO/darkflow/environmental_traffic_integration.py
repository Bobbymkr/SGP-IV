#!/usr/bin/env python3
"""
Environmental-Traffic Integration System
Integrates environmental data with traffic management algorithms
"""

import asyncio
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum

# Import existing systems
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'YOLO', 'darkflow'))

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentalTrafficState:
    """Combined environmental and traffic state"""
    traffic_volume: float
    vehicle_count: int
    queue_length: float
    avg_speed: float
    
    # Environmental factors
    temperature: float
    humidity: float
    wind_speed: float
    visibility: float
    precipitation: float
    aqi: float
    road_condition: str
    
    # Impact factors
    speed_reduction_factor: float
    capacity_reduction_factor: float
    safety_risk_factor: float
    
    timestamp: datetime = field(default_factory=datetime.now)

class EnvironmentalTrafficIntegrator:
    """Integrates environmental data with traffic management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.environmental_history = []
        self.traffic_history = []
        self.integration_history = []
        
        # Environmental impact thresholds
        self.impact_thresholds = {
            'visibility_low': 0.5,      # Below 50% visibility
            'precipitation_high': 10,    # Above 10mm/hour
            'wind_high': 20,            # Above 20 km/h
            'aqi_unhealthy': 150,       # Above 150 AQI
            'temperature_extreme_low': -10,  # Below -10°C
            'temperature_extreme_high': 35   # Above 35°C
        }
        
        # Traffic adjustment factors
        self.adjustment_factors = {
            'signal_timing_base': 1.0,
            'speed_limit_base': 1.0,
            'capacity_base': 1.0,
            'safety_margin_base': 0.1
        }
    
    async def process_environmental_traffic_data(
        self, 
        traffic_data: Dict[str, Any], 
        environmental_data: Dict[str, Any]
    ) -> EnvironmentalTrafficState:
        """Process combined environmental and traffic data"""
        
        # Extract traffic metrics
        traffic_volume = traffic_data.get('volume', 0)
        vehicle_count = traffic_data.get('vehicle_count', 0)
        queue_length = traffic_data.get('queue_length', 0)
        avg_speed = traffic_data.get('avg_speed', 50)
        
        # Extract environmental metrics
        temperature = environmental_data.get('temperature', 20)
        humidity = environmental_data.get('humidity', 50)
        wind_speed = environmental_data.get('wind_speed', 5)
        visibility = environmental_data.get('visibility', 1.0)
        precipitation = environmental_data.get('precipitation', 0)
        aqi = environmental_data.get('aqi', 50)
        road_condition = environmental_data.get('road_condition', 'dry')
        
        # Calculate impact factors
        impact_factors = await self.calculate_environmental_impacts(environmental_data)
        
        # Create integrated state
        state = EnvironmentalTrafficState(
            traffic_volume=traffic_volume,
            vehicle_count=vehicle_count,
            queue_length=queue_length,
            avg_speed=avg_speed,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            visibility=visibility,
            precipitation=precipitation,
            aqi=aqi,
            road_condition=road_condition,
            **impact_factors
        )
        
        # Store in history
        self.integration_history.append(state)
        if len(self.integration_history) > 1000:
            self.integration_history.pop(0)
        
        return state
    
    async def calculate_environmental_impacts(self, environmental_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate environmental impact factors"""
        
        temperature = environmental_data.get('temperature', 20)
        humidity = environmental_data.get('humidity', 50)
        wind_speed = environmental_data.get('wind_speed', 5)
        visibility = environmental_data.get('visibility', 1.0)
        precipitation = environmental_data.get('precipitation', 0)
        aqi = environmental_data.get('aqi', 50)
        road_condition = environmental_data.get('road_condition', 'dry')
        
        # Initialize impact factors
        speed_reduction = 0.0
        capacity_reduction = 0.0
        safety_risk = 0.0
        
        # Temperature impacts
        if temperature < self.impact_thresholds['temperature_extreme_low']:
            speed_reduction += 0.2  # Ice potential
            safety_risk += 0.3
        elif temperature > self.impact_thresholds['temperature_extreme_high']:
            speed_reduction += 0.1  # Heat effects
            capacity_reduction += 0.1
        
        # Visibility impacts
        if visibility < self.impact_thresholds['visibility_low']:
            speed_reduction += (1.0 - visibility) * 0.4
            safety_risk += (1.0 - visibility) * 0.5
        
        # Precipitation impacts
        if precipitation > 0:
            if precipitation > self.impact_thresholds['precipitation_high']:
                speed_reduction += 0.4
                capacity_reduction += 0.3
                safety_risk += 0.4
            else:
                speed_reduction += (precipitation / self.impact_thresholds['precipitation_high']) * 0.2
                capacity_reduction += (precipitation / self.impact_thresholds['precipitation_high']) * 0.15
                safety_risk += (precipitation / self.impact_thresholds['precipitation_high']) * 0.2
        
        # Wind impacts
        if wind_speed > self.impact_thresholds['wind_high']:
            speed_reduction += 0.1
            safety_risk += 0.2
        
        # Air quality impacts
        if aqi > self.impact_thresholds['aqi_unhealthy']:
            speed_reduction += 0.1
            safety_risk += 0.15
        
        # Road condition impacts
        road_impacts = self.get_road_condition_impacts(road_condition)
        speed_reduction += road_impacts['speed_reduction']
        capacity_reduction += road_impacts['capacity_reduction']
        safety_risk += road_impacts['safety_risk']
        
        # Cap all factors at 1.0
        speed_reduction = min(1.0, speed_reduction)
        capacity_reduction = min(1.0, capacity_reduction)
        safety_risk = min(1.0, safety_risk)
        
        return {
            'speed_reduction_factor': speed_reduction,
            'capacity_reduction_factor': capacity_reduction,
            'safety_risk_factor': safety_risk
        }
    
    def get_road_condition_impacts(self, road_condition: str) -> Dict[str, float]:
        """Get impact factors for road conditions"""
        
        impacts = {
            'dry': {'speed_reduction': 0.0, 'capacity_reduction': 0.0, 'safety_risk': 0.0},
            'wet': {'speed_reduction': 0.15, 'capacity_reduction': 0.1, 'safety_risk': 0.2},
            'snowy': {'speed_reduction': 0.35, 'capacity_reduction': 0.25, 'safety_risk': 0.4},
            'icy': {'speed_reduction': 0.5, 'capacity_reduction': 0.4, 'safety_risk': 0.6},
            'flooded': {'speed_reduction': 0.7, 'capacity_reduction': 0.6, 'safety_risk': 0.7}
        }
        
        return impacts.get(road_condition, impacts['dry'])
    
    async def calculate_adaptive_signal_timing(
        self, 
        base_timing: Dict[str, int], 
        state: EnvironmentalTrafficState
    ) -> Dict[str, Any]:
        """Calculate adaptive signal timing based on environmental and traffic conditions"""
        
        green_time = base_timing.get('green_time', 30)
        yellow_time = base_timing.get('yellow_time', 3)
        red_time = base_timing.get('red_time', 33)
        
        # Calculate traffic-based adjustment
        traffic_factor = 1.0
        if state.traffic_volume > 0.8:  # High traffic
            traffic_factor += 0.2
        elif state.traffic_volume < 0.3:  # Low traffic
            traffic_factor -= 0.15
        
        # Calculate environmental-based adjustment
        env_factor = 1.0
        if state.safety_risk_factor > 0.5:
            env_factor += 0.3  # Increase timing for safety
        elif state.safety_risk_factor > 0.3:
            env_factor += 0.15
        
        # Queue-based adjustment
        queue_factor = 1.0
        if state.queue_length > 10:  # Long queue
            queue_factor += 0.25
        elif state.queue_length > 5:
            queue_factor += 0.1
        
        # Combined adjustment factor
        total_adjustment = max(0.5, min(2.0, traffic_factor * env_factor * queue_factor))
        
        # Apply adjustments
        adjusted_green = int(green_time * total_adjustment)
        adjusted_yellow = max(3, int(yellow_time * (1 + state.safety_risk_factor * 0.5)))
        adjusted_red = int(red_time * total_adjustment)
        
        # Ensure minimum times
        adjusted_green = max(10, adjusted_green)
        adjusted_yellow = max(3, adjusted_yellow)
        adjusted_red = max(10, adjusted_red)
        
        return {
            'green_time': adjusted_green,
            'yellow_time': adjusted_yellow,
            'red_time': adjusted_red,
            'adjustment_factor': total_adjustment,
            'traffic_factor': traffic_factor,
            'environmental_factor': env_factor,
            'queue_factor': queue_factor,
            'adjustment_reasons': self._get_timing_adjustment_reasons(state, traffic_factor, env_factor, queue_factor)
        }
    
    def _get_timing_adjustment_reasons(
        self, 
        state: EnvironmentalTrafficState, 
        traffic_factor: float, 
        env_factor: float, 
        queue_factor: float
    ) -> List[str]:
        """Get reasons for signal timing adjustments"""
        
        reasons = []
        
        if traffic_factor > 1.1:
            reasons.append("High traffic volume")
        elif traffic_factor < 0.9:
            reasons.append("Low traffic volume")
        
        if env_factor > 1.1:
            reasons.append("Adverse environmental conditions")
            if state.visibility < 0.7:
                reasons.append("Reduced visibility")
            if state.precipitation > 5:
                reasons.append("Heavy precipitation")
            if state.road_condition in ['wet', 'snowy', 'icy']:
                reasons.append(f"Poor road conditions: {state.road_condition}")
        
        if queue_factor > 1.1:
            reasons.append("Long queue detected")
        
        return reasons
    
    async def calculate_dynamic_speed_limit(
        self, 
        base_speed_limit: float, 
        state: EnvironmentalTrafficState
    ) -> Dict[str, Any]:
        """Calculate dynamic speed limit based on conditions"""
        
        # Start with base speed limit
        adjusted_speed = base_speed_limit
        
        # Apply environmental reductions
        if state.speed_reduction_factor > 0:
            adjusted_speed *= (1.0 - state.speed_reduction_factor)
        
        # Apply traffic-based adjustments
        if state.traffic_volume > 0.9:  # Very heavy traffic
            adjusted_speed *= 0.8
        elif state.avg_speed < base_speed_limit * 0.6:  # Traffic already slow
            adjusted_speed = min(adjusted_speed, state.avg_speed * 1.2)
        
        # Apply safety margins
        if state.safety_risk_factor > 0.6:
            adjusted_speed *= 0.7
        elif state.safety_risk_factor > 0.3:
            adjusted_speed *= 0.85
        
        # Ensure reasonable minimum
        adjusted_speed = max(adjusted_speed, 10.0)
        
        # Round to nearest 5 km/h
        adjusted_speed = round(adjusted_speed / 5) * 5
        
        return {
            'adjusted_speed_limit': adjusted_speed,
            'base_speed_limit': base_speed_limit,
            'reduction_percentage': ((base_speed_limit - adjusted_speed) / base_speed_limit) * 100,
            'primary_factors': self._get_speed_limit_factors(state),
            'recommended_duration': self._get_speed_limit_duration(state)
        }
    
    def _get_speed_limit_factors(self, state: EnvironmentalTrafficState) -> List[str]:
        """Get primary factors affecting speed limit"""
        
        factors = []
        
        if state.visibility < 0.7:
            factors.append("Low visibility")
        if state.precipitation > 5:
            factors.append("Heavy precipitation")
        if state.road_condition in ['wet', 'snowy', 'icy']:
            factors.append(f"Road condition: {state.road_condition}")
        if state.wind_speed > 20:
            factors.append("High winds")
        if state.aqi > 150:
            factors.append("Poor air quality")
        if state.temperature < -10 or state.temperature > 35:
            factors.append("Extreme temperature")
        
        return factors
    
    def _get_speed_limit_duration(self, state: EnvironmentalTrafficState) -> str:
        """Get recommended duration for speed limit adjustment"""
        
        if state.safety_risk_factor > 0.7:
            return "Until conditions improve"
        elif state.safety_risk_factor > 0.4:
            return "2-4 hours"
        elif state.precipitation > 10:
            return "1-2 hours after precipitation stops"
        else:
            return "30-60 minutes"
    
    async def generate_traffic_management_recommendations(
        self, 
        state: EnvironmentalTrafficState
    ) -> Dict[str, Any]:
        """Generate comprehensive traffic management recommendations"""
        
        recommendations = {
            'signal_timing': await self.calculate_adaptive_signal_timing({'green_time': 30, 'yellow_time': 3, 'red_time': 33}, state),
            'speed_limits': await self.calculate_dynamic_speed_limit(50, state),
            'traffic_management': [],
            'safety_measures': [],
            'infrastructure_needs': [],
            'public_alerts': []
        }
        
        # Traffic management recommendations
        if state.traffic_volume > 0.8:
            recommendations['traffic_management'].append("Consider ramp metering")
            recommendations['traffic_management'].append("Activate variable speed limits")
        
        if state.queue_length > 10:
            recommendations['traffic_management'].append("Implement queue detection systems")
            recommendations['traffic_management'].append("Consider lane reversal if available")
        
        # Safety measures
        if state.safety_risk_factor > 0.5:
            recommendations['safety_measures'].append("Increase law enforcement presence")
            recommendations['safety_measures'].append("Activate variable message signs")
        
        if state.road_condition in ['snowy', 'icy']:
            recommendations['safety_measures'].append("Dispatch snow/ice removal crews")
            recommendations['safety_measures'].append("Apply de-icing agents")
        
        # Infrastructure needs
        if state.visibility < 0.5:
            recommendations['infrastructure_needs'].append("Ensure road lighting is operational")
            recommendations['infrastructure_needs'].append("Check visibility sensor functionality")
        
        if state.precipitation > 15:
            recommendations['infrastructure_needs'].append("Check drainage systems")
            recommendations['infrastructure_needs'].append("Monitor for flooding")
        
        # Public alerts
        if state.safety_risk_factor > 0.6:
            recommendations['public_alerts'].append("Issue weather-related travel advisory")
            recommendations['public_alerts'].append("Broadcast road condition updates")
        
        return recommendations
    
    async def analyze_environmental_traffic_patterns(
        self, 
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """Analyze patterns in environmental-traffic interactions"""
        
        cutoff_time = datetime.now() - time_window
        recent_data = [state for state in self.integration_history if state.timestamp >= cutoff_time]
        
        if len(recent_data) < 10:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate correlations
        traffic_env_correlation = self._calculate_traffic_environment_correlation(recent_data)
        
        # Identify impact patterns
        impact_patterns = self._identify_impact_patterns(recent_data)
        
        # Generate insights
        insights = self._generate_environmental_insights(recent_data, traffic_env_correlation, impact_patterns)
        
        return {
            'analysis_period': time_window,
            'data_points': len(recent_data),
            'correlations': traffic_env_correlation,
            'impact_patterns': impact_patterns,
            'insights': insights,
            'recommendations': self._get_pattern_based_recommendations(impact_patterns)
        }
    
    def _calculate_traffic_environment_correlation(self, data: List[EnvironmentalTrafficState]) -> Dict[str, float]:
        """Calculate correlations between traffic and environmental factors"""
        
        if len(data) < 2:
            return {}
        
        # Extract data series
        traffic_volume = [state.traffic_volume for state in data]
        avg_speed = [state.avg_speed for state in data]
        visibility = [state.visibility for state in data]
        precipitation = [state.precipitation for state in data]
        temperature = [state.temperature for state in data]
        aqi = [state.aqi for state in data]
        
        # Calculate correlations (simplified Pearson correlation)
        correlations = {}
        
        try:
            correlations['visibility_speed'] = np.corrcoef(visibility, avg_speed)[0, 1] if len(set(visibility)) > 1 else 0
            correlations['precipitation_speed'] = np.corrcoef(precipitation, avg_speed)[0, 1] if len(set(precipitation)) > 1 else 0
            correlations['temperature_traffic'] = np.corrcoef(temperature, traffic_volume)[0, 1] if len(set(temperature)) > 1 else 0
            correlations['aqi_speed'] = np.corrcoef(aqi, avg_speed)[0, 1] if len(set(aqi)) > 1 else 0
        except:
            # Handle any calculation errors
            correlations = {key: 0.0 for key in ['visibility_speed', 'precipitation_speed', 'temperature_traffic', 'aqi_speed']}
        
        return correlations
    
    def _identify_impact_patterns(self, data: List[EnvironmentalTrafficState]) -> Dict[str, Any]:
        """Identify recurring impact patterns"""
        
        patterns = {
            'high_impact_conditions': [],
            'recovery_times': [],
            'peak_impact_hours': [],
            'seasonal_trends': []
        }
        
        # Identify high impact conditions
        high_impact_states = [state for state in data if state.safety_risk_factor > 0.6]
        
        if high_impact_states:
            # Common conditions during high impact
            conditions = {}
            for state in high_impact_states:
                key = f"{state.road_condition}_{state.precipitation > 5}_{state.visibility < 0.5}"
                conditions[key] = conditions.get(key, 0) + 1
            
            patterns['high_impact_conditions'] = sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze peak impact hours
        hourly_impacts = {}
        for state in data:
            hour = state.timestamp.hour
            if hour not in hourly_impacts:
                hourly_impacts[hour] = []
            hourly_impacts[hour].append(state.safety_risk_factor)
        
        for hour, impacts in hourly_impacts.items():
            avg_impact = sum(impacts) / len(impacts)
            if avg_impact > 0.4:
                patterns['peak_impact_hours'].append((hour, avg_impact))
        
        patterns['peak_impact_hours'].sort(key=lambda x: x[1], reverse=True)
        
        return patterns
    
    def _generate_environmental_insights(
        self, 
        data: List[EnvironmentalTrafficState], 
        correlations: Dict[str, float], 
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from environmental-traffic analysis"""
        
        insights = []
        
        # Correlation insights
        if correlations.get('visibility_speed', 0) < -0.5:
            insights.append("Strong negative correlation between visibility and traffic speed")
        
        if correlations.get('precipitation_speed', 0) < -0.4:
            insights.append("Precipitation significantly reduces traffic speeds")
        
        # Pattern insights
        if patterns['peak_impact_hours']:
            peak_hour = patterns['peak_impact_hours'][0][0]
            insights.append(f"Highest environmental impact typically occurs around {peak_hour}:00")
        
        if patterns['high_impact_conditions']:
            top_condition = patterns['high_impact_conditions'][0][0]
            insights.append(f"Most problematic condition: {top_condition}")
        
        # General insights
        avg_safety_risk = sum(state.safety_risk_factor for state in data) / len(data)
        if avg_safety_risk > 0.3:
            insights.append("Environmental conditions frequently create safety risks")
        
        return insights
    
    def _get_pattern_based_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Get recommendations based on identified patterns"""
        
        recommendations = []
        
        if patterns['peak_impact_hours']:
            peak_hour = patterns['peak_impact_hours'][0][0]
            recommendations.append(f"Pre-position resources before {peak_hour}:00 during adverse weather")
        
        if patterns['high_impact_conditions']:
            top_condition = patterns['high_impact_conditions'][0][0]
            if 'wet' in top_condition or 'snowy' in top_condition or 'icy' in top_condition:
                recommendations.append("Prioritize road maintenance equipment for precipitation events")
        
        return recommendations

# Example usage and testing
async def main():
    """Example usage of the environmental-traffic integration system"""
    
    integrator = EnvironmentalTrafficIntegrator()
    
    # Sample data
    traffic_data = {
        'volume': 0.7,
        'vehicle_count': 25,
        'queue_length': 8,
        'avg_speed': 45
    }
    
    environmental_data = {
        'temperature': 15,
        'humidity': 80,
        'wind_speed': 15,
        'visibility': 0.6,
        'precipitation': 8,
        'aqi': 120,
        'road_condition': 'wet'
    }
    
    # Process integrated data
    state = await integrator.process_environmental_traffic_data(traffic_data, environmental_data)
    
    print("Environmental-Traffic Integration Analysis")
    print("=" * 50)
    print(f"Traffic Volume: {state.traffic_volume:.2f}")
    print(f"Average Speed: {state.avg_speed:.1f} km/h")
    print(f"Road Condition: {state.road_condition}")
    print(f"Visibility: {state.visibility:.2f}")
    print(f"Safety Risk Factor: {state.safety_risk_factor:.2f}")
    
    # Get recommendations
    recommendations = await integrator.generate_traffic_management_recommendations(state)
    
    print(f"\nAdaptive Signal Timing:")
    timing = recommendations['signal_timing']
    print(f"  Green Time: {timing['green_time']}s (was 30s)")
    print(f"  Adjustment Factor: {timing['adjustment_factor']:.2f}")
    print(f"  Reasons: {', '.join(timing['adjustment_reasons'])}")
    
    print(f"\nDynamic Speed Limit:")
    speed = recommendations['speed_limits']
    print(f"  Recommended: {speed['adjusted_speed_limit']} km/h (was {speed['base_speed_limit']} km/h)")
    print(f"  Reduction: {speed['reduction_percentage']:.1f}%")
    print(f"  Factors: {', '.join(speed['primary_factors'])}")
    
    print(f"\nSafety Measures:")
    for measure in recommendations['safety_measures']:
        print(f"  - {measure}")

if __name__ == "__main__":
    asyncio.run(main())