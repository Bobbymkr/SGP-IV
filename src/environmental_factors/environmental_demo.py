"""
Environmental Factors Demo

Comprehensive demonstration of environmental factors integration:
Weather impact, time-of-day patterns, event scenarios, and pedestrian analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Import our modules
from weather_impact import (
    WeatherImpactModel, TimeOfDayAnalyzer, EventImpactAnalyzer, 
    PedestrianAnalyzer, EnvironmentalFactorsIntegrator,
    WeatherData, EventImpact, PedestrianData, WeatherCondition, EventType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentalFactorsDemo:
    """Main demonstration class for environmental factors"""
    
    def __init__(self, output_dir: str = "environmental_demo_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.integrator = EnvironmentalFactorsIntegrator()
        
        # Demo data
        self.demo_scenarios = self._create_demo_scenarios()
        self.results = {}
        
    def _create_demo_scenarios(self) -> Dict[str, Dict]:
        """Create demonstration scenarios"""
        scenarios = {
            'normal_day': {
                'description': 'Normal weekday with clear weather',
                'weather': WeatherData(
                    condition=WeatherCondition.CLEAR,
                    temperature=22.0,
                    humidity=45.0,
                    wind_speed=10.0,
                    visibility=10.0,
                    precipitation=0.0,
                    timestamp=datetime.now()
                ),
                'events': [],
                'location': 'main_intersection'
            },
            'rainy_rush_hour': {
                'description': 'Heavy rain during evening rush hour',
                'weather': WeatherData(
                    condition=WeatherCondition.RAIN_HEAVY,
                    temperature=18.0,
                    humidity=85.0,
                    wind_speed=25.0,
                    visibility=3.0,
                    precipitation=15.0,
                    timestamp=datetime.now().replace(hour=18, minute=0)
                ),
                'events': [],
                'location': 'main_intersection'
            },
            'stadium_event': {
                'description': 'Sporting event at stadium',
                'weather': WeatherData(
                    condition=WeatherCondition.CLEAR,
                    temperature=25.0,
                    humidity=50.0,
                    wind_speed=15.0,
                    visibility=10.0,
                    precipitation=0.0,
                    timestamp=datetime.now().replace(hour=19, minute=0)
                ),
                'events': [
                    EventImpact(
                        event_type=EventType.SPORTING_EVENT,
                        start_time=datetime.now().replace(hour=18, minute=0),
                        end_time=datetime.now().replace(hour=22, minute=0),
                        location='stadium_intersection',
                        expected_attendees=50000,
                        traffic_multiplier=2.5,
                        affected_approaches=['north', 'south', 'east', 'west'],
                        special_signal_timing={'cycle_length_multiplier': 1.2, 'green_extension': 5.0}
                    )
                ],
                'location': 'stadium_intersection'
            },
            'school_morning': {
                'description': 'School start time with pedestrian activity',
                'weather': WeatherData(
                    condition=WeatherCondition.CLOUDY,
                    temperature=15.0,
                    humidity=60.0,
                    wind_speed=12.0,
                    visibility=8.0,
                    precipitation=0.0,
                    timestamp=datetime.now().replace(hour=8, minute=0)
                ),
                'events': [
                    EventImpact(
                        event_type=EventType.SCHOOL_START,
                        start_time=datetime.now().replace(hour=7, minute=30),
                        end_time=datetime.now().replace(hour=8, minute=30),
                        location='school_intersection',
                        expected_attendees=800,
                        traffic_multiplier=1.8,
                        affected_approaches=['north', 'south'],
                        special_signal_timing={'cycle_length_multiplier': 1.1, 'pedestrian_phase': 2.0}
                    )
                ],
                'location': 'school_intersection'
            },
            'snow_storm': {
                'description': 'Heavy snow storm during morning commute',
                'weather': WeatherData(
                    condition=WeatherCondition.SNOW_HEAVY,
                    temperature=-5.0,
                    humidity=90.0,
                    wind_speed=30.0,
                    visibility=1.0,
                    precipitation=10.0,
                    timestamp=datetime.now().replace(hour=7, minute=30)
                ),
                'events': [],
                'location': 'main_intersection'
            }
        }
        
        return scenarios
    
    def run_weather_impact_demo(self):
        """Demonstrate weather impact modeling"""
        logger.info("Running Weather Impact Demo...")
        
        results = {}
        
        for scenario_name, scenario in self.demo_scenarios.items():
            weather = scenario['weather']
            
            # Calculate weather impact
            impact = self.integrator.weather_model.calculate_weather_impact(weather)
            
            results[scenario_name] = {
                'weather_condition': weather.condition.value,
                'temperature': weather.temperature,
                'impact_factors': impact
            }
            
            logger.info(f"Scenario: {scenario_name}")
            logger.info(f"  Weather: {weather.condition.value}")
            logger.info(f"  Speed Factor: {impact['speed_factor']:.2f}")
            logger.info(f"  Flow Factor: {impact['flow_factor']:.2f}")
            logger.info(f"  Signal Timing Adjustment: {impact['signal_timing_adjustment']:.2f}")
        
        self.results['weather_impact'] = results
        self._plot_weather_impacts(results)
    
    def run_time_of_day_demo(self):
        """Demonstrate time-of-day traffic patterns"""
        logger.info("Running Time-of-Day Demo...")
        
        # Generate 24-hour traffic pattern
        start_time = datetime.now().replace(hour=0, minute=0, second=0)
        patterns = self.integrator.time_analyzer.predict_traffic_evolution(start_time, 24)
        
        # Extract data for plotting
        hours = list(range(24))
        flows = [p.base_flow * p.peak_multiplier for p in patterns]
        speeds = [p.speed_factor * 55 for p in patterns]  # Convert back to km/h
        signal_adjustments = [p.signal_timing_adjustment for p in patterns]
        
        results = {
            'hours': hours,
            'flows': flows,
            'speeds': speeds,
            'signal_adjustments': signal_adjustments,
            'patterns': patterns
        }
        
        self.results['time_of_day'] = results
        self._plot_time_patterns(results)
        
        # Calculate peak hour factors
        peak_factors = self.integrator.time_analyzer.calculate_peak_hour_factors(patterns)
        logger.info(f"Peak Hour Factor: {peak_factors['peak_hour_factor']:.2f}")
        logger.info(f"Peak Flow: {peak_factors['peak_flow']:.0f} vehicles/hour")
        logger.info(f"Average Flow: {peak_factors['average_flow']:.0f} vehicles/hour")
    
    def run_event_impact_demo(self):
        """Demonstrate event impact analysis"""
        logger.info("Running Event Impact Demo...")
        
        results = {}
        
        for scenario_name, scenario in self.demo_scenarios.items():
            if scenario['events']:
                event = scenario['events'][0]
                
                # Calculate temporal impact over 24 hours
                start_time = datetime.now().replace(hour=0, minute=0)
                temporal_impacts = []
                
                for hour in range(24):
                    current_time = start_time + timedelta(hours=hour)
                    impact = self.integrator.event_analyzer.calculate_event_temporal_impact(event, current_time)
                    temporal_impacts.append(impact)
                
                results[scenario_name] = {
                    'event_type': event.event_type.value,
                    'traffic_multiplier': event.traffic_multiplier,
                    'temporal_impacts': temporal_impacts,
                    'special_timing': event.special_signal_timing
                }
                
                logger.info(f"Event: {scenario_name}")
                logger.info(f"  Type: {event.event_type.value}")
                logger.info(f"  Traffic Multiplier: {event.traffic_multiplier:.2f}")
                logger.info(f"  Max Impact: {max(temporal_impacts):.2f}")
        
        self.results['event_impact'] = results
        self._plot_event_impacts(results)
    
    def run_pedestrian_demo(self):
        """Demonstrate pedestrian crossing analysis"""
        logger.info("Running Pedestrian Analysis Demo...")
        
        results = {}
        
        # Test different locations and times
        test_cases = [
            {'location': 'school_intersection', 'time': datetime.now().replace(hour=8, minute=0)},
            {'location': 'stadium_intersection', 'time': datetime.now().replace(hour=19, minute=0)},
            {'location': 'main_intersection', 'time': datetime.now().replace(hour=12, minute=0)},
            {'location': 'hospital_intersection', 'time': datetime.now().replace(hour=14, minute=0)},
        ]
        
        for i, test_case in enumerate(test_cases):
            location = test_case['location']
            timestamp = test_case['time']
            
            # Analyze crossing demand
            demand = self.integrator.pedestrian_analyzer.analyze_crossing_demand(location, timestamp)
            timing = self.integrator.pedestrian_analyzer.calculate_pedestrian_phase_timing(demand)
            
            case_name = f"case_{i+1}"
            results[case_name] = {
                'location': location,
                'time': timestamp.strftime('%H:%M'),
                'demand': demand,
                'timing': timing
            }
            
            logger.info(f"Location: {location} at {timestamp.strftime('%H:%M')}")
            logger.info(f"  Demand Rate: {demand['demand_rate']:.2f} pedestrians/min")
            logger.info(f"  Average Group Size: {demand['average_group_size']:.1f}")
            logger.info(f"  Min Green Time: {timing['min_green_time']:.1f}s")
        
        self.results['pedestrian'] = results
        self._plot_pedestrian_analysis(results)
    
    def run_comprehensive_demo(self):
        """Demonstrate comprehensive environmental factors integration"""
        logger.info("Running Comprehensive Integration Demo...")
        
        results = {}
        
        for scenario_name, scenario in self.demo_scenarios.items():
            # Update integrator with scenario data
            self.integrator.update_weather(scenario['weather'])
            
            # Add events
            for event in scenario['events']:
                self.integrator.add_event(event)
            
            # Calculate comprehensive impact
            timestamp = scenario['weather'].timestamp
            location = scenario['location']
            
            impacts = self.integrator.calculate_comprehensive_impact(timestamp, location)
            recommendations = self.integrator.generate_signal_timing_recommendations(impacts)
            
            results[scenario_name] = {
                'scenario_description': scenario['description'],
                'impacts': impacts,
                'recommendations': recommendations
            }
            
            logger.info(f"Scenario: {scenario_name}")
            logger.info(f"  Combined Speed Factor: {impacts['combined']['speed_factor']:.2f}")
            logger.info(f"  Combined Flow Factor: {impacts['combined']['flow_factor']:.2f}")
            logger.info(f"  Recommended Cycle Length: {recommendations['cycle_length']:.1f}s")
            logger.info(f"  Recommended Green Split: {recommendations['green_split']:.2f}")
        
        self.results['comprehensive'] = results
        self._plot_comprehensive_results(results)
    
    def run_prediction_demo(self):
        """Demonstrate future condition prediction"""
        logger.info("Running Future Prediction Demo...")
        
        # Set up current conditions
        current_weather = WeatherData(
            condition=WeatherCondition.CLEAR,
            temperature=20.0,
            humidity=50.0,
            wind_speed=15.0,
            visibility=10.0,
            precipitation=0.0,
            timestamp=datetime.now()
        )
        
        self.integrator.update_weather(current_weather)
        
        # Add upcoming event
        future_event = EventImpact(
            event_type=EventType.CONCERT,
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=5),
            location='concert_venue',
            expected_attendees=20000,
            traffic_multiplier=2.0,
            affected_approaches=['north', 'south'],
            special_signal_timing={'cycle_length_multiplier': 1.15, 'green_extension': 3.0}
        )
        
        self.integrator.add_event(future_event)
        
        # Predict future conditions
        predictions = self.integrator.predict_future_conditions(hours_ahead=6)
        
        results = {
            'current_conditions': {
                'weather': current_weather.condition.value,
                'temperature': current_weather.temperature
            },
            'upcoming_event': {
                'type': future_event.event_type.value,
                'start_time': future_event.start_time.strftime('%H:%M'),
                'traffic_multiplier': future_event.traffic_multiplier
            },
            'predictions': predictions
        }
        
        self.results['prediction'] = results
        self._plot_predictions(results)
        
        logger.info("Future Conditions Prediction:")
        for pred in predictions:
            logger.info(f"  {pred['timestamp'].strftime('%H:%M')} - Flow Factor: {pred['predicted_flow_factor']:.2f}")
    
    def _plot_weather_impacts(self, results: Dict[str, Any]):
        """Plot weather impact results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Weather Impact Analysis', fontsize=16)
        
        scenarios = list(results.keys())
        speed_factors = [results[s]['impact_factors']['speed_factor'] for s in scenarios]
        flow_factors = [results[s]['impact_factors']['flow_factor'] for s in scenarios]
        signal_adjustments = [results[s]['impact_factors']['signal_timing_adjustment'] for s in scenarios]
        reaction_times = [results[s]['impact_factors']['reaction_time_factor'] for s in scenarios]
        
        # Speed factors
        axes[0, 0].bar(scenarios, speed_factors, color='skyblue')
        axes[0, 0].set_title('Speed Factors by Weather Condition')
        axes[0, 0].set_ylabel('Speed Factor')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Flow factors
        axes[0, 1].bar(scenarios, flow_factors, color='lightgreen')
        axes[0, 1].set_title('Flow Factors by Weather Condition')
        axes[0, 1].set_ylabel('Flow Factor')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Signal timing adjustments
        axes[1, 0].bar(scenarios, signal_adjustments, color='orange')
        axes[1, 0].set_title('Signal Timing Adjustments')
        axes[1, 0].set_ylabel('Timing Adjustment Factor')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Reaction time factors
        axes[1, 1].bar(scenarios, reaction_times, color='salmon')
        axes[1, 1].set_title('Reaction Time Factors')
        axes[1, 1].set_ylabel('Reaction Time Factor')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'weather_impacts.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_time_patterns(self, results: Dict[str, Any]):
        """Plot time-of-day traffic patterns"""
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        fig.suptitle('24-Hour Traffic Patterns', fontsize=16)
        
        hours = results['hours']
        
        # Traffic flow
        axes[0].plot(hours, results['flows'], 'b-', linewidth=2)
        axes[0].set_title('Traffic Flow (vehicles/hour/lane)')
        axes[0].set_ylabel('Flow Rate')
        axes[0].grid(True, alpha=0.3)
        
        # Speed
        axes[1].plot(hours, results['speeds'], 'g-', linewidth=2)
        axes[1].set_title('Average Speed (km/h)')
        axes[1].set_ylabel('Speed')
        axes[1].grid(True, alpha=0.3)
        
        # Signal timing adjustments
        axes[2].plot(hours, results['signal_adjustments'], 'r-', linewidth=2)
        axes[2].set_title('Signal Timing Adjustments')
        axes[2].set_ylabel('Adjustment Factor')
        axes[2].set_xlabel('Hour of Day')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'time_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_event_impacts(self, results: Dict[str, Any]):
        """Plot event impact results"""
        fig, axes = plt.subplots(len(results), 1, figsize=(15, 5*len(results)))
        if len(results) == 1:
            axes = [axes]
        
        fig.suptitle('Event Temporal Impacts', fontsize=16)
        
        for i, (scenario_name, data) in enumerate(results.items()):
            hours = list(range(24))
            impacts = data['temporal_impacts']
            
            axes[i].plot(hours, impacts, 'b-', linewidth=2)
            axes[i].set_title(f"{scenario_name.replace('_', ' ').title()} - {data['event_type']}")
            axes[i].set_ylabel('Traffic Multiplier')
            axes[i].set_xlabel('Hour of Day')
            axes[i].grid(True, alpha=0.3)
            axes[i].axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Baseline')
            axes[i].legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'event_impacts.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_pedestrian_analysis(self, results: Dict[str, Any]):
        """Plot pedestrian analysis results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Pedestrian Crossing Analysis', fontsize=16)
        
        case_names = list(results.keys())
        locations = [results[c]['location'] for c in case_names]
        demand_rates = [results[c]['demand']['demand_rate'] for c in case_names]
        group_sizes = [results[c]['demand']['average_group_size'] for c in case_names]
        min_green_times = [results[c]['timing']['min_green_time'] for c in case_names]
        waiting_times = [results[c]['demand']['peak_waiting_time'] for c in case_names]
        
        # Demand rates
        axes[0, 0].bar(range(len(case_names)), demand_rates, color='skyblue')
        axes[0, 0].set_title('Pedestrian Demand Rate')
        axes[0, 0].set_ylabel('Pedestrians/minute')
        axes[0, 0].set_xticks(range(len(case_names)))
        axes[0, 0].set_xticklabels([loc.replace('_intersection', '') for loc in locations], rotation=45)
        
        # Group sizes
        axes[0, 1].bar(range(len(case_names)), group_sizes, color='lightgreen')
        axes[0, 1].set_title('Average Group Size')
        axes[0, 1].set_ylabel('People per Group')
        axes[0, 1].set_xticks(range(len(case_names)))
        axes[0, 1].set_xticklabels([loc.replace('_intersection', '') for loc in locations], rotation=45)
        
        # Minimum green times
        axes[1, 0].bar(range(len(case_names)), min_green_times, color='orange')
        axes[1, 0].set_title('Minimum Green Time Required')
        axes[1, 0].set_ylabel('Seconds')
        axes[1, 0].set_xticks(range(len(case_names)))
        axes[1, 0].set_xticklabels([loc.replace('_intersection', '') for loc in locations], rotation=45)
        
        # Waiting times
        axes[1, 1].bar(range(len(case_names)), waiting_times, color='salmon')
        axes[1, 1].set_title('Peak Waiting Time')
        axes[1, 1].set_ylabel('Seconds')
        axes[1, 1].set_xticks(range(len(case_names)))
        axes[1, 1].set_xticklabels([loc.replace('_intersection', '') for loc in locations], rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'pedestrian_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_comprehensive_results(self, results: Dict[str, Any]):
        """Plot comprehensive integration results"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Comprehensive Environmental Factors Integration', fontsize=16)
        
        scenarios = list(results.keys())
        speed_factors = [results[s]['impacts']['combined']['speed_factor'] for s in scenarios]
        flow_factors = [results[s]['impacts']['combined']['flow_factor'] for s in scenarios]
        cycle_lengths = [results[s]['recommendations']['cycle_length'] for s in scenarios]
        green_splits = [results[s]['recommendations']['green_split'] for s in scenarios]
        
        # Combined speed factors
        axes[0, 0].bar(scenarios, speed_factors, color='skyblue')
        axes[0, 0].set_title('Combined Speed Factors')
        axes[0, 0].set_ylabel('Speed Factor')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Baseline')
        axes[0, 0].legend()
        
        # Combined flow factors
        axes[0, 1].bar(scenarios, flow_factors, color='lightgreen')
        axes[0, 1].set_title('Combined Flow Factors')
        axes[0, 1].set_ylabel('Flow Factor')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Baseline')
        axes[0, 1].legend()
        
        # Recommended cycle lengths
        axes[1, 0].bar(scenarios, cycle_lengths, color='orange')
        axes[1, 0].set_title('Recommended Cycle Lengths')
        axes[1, 0].set_ylabel('Seconds')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].axhline(y=120.0, color='r', linestyle='--', alpha=0.5, label='Default')
        axes[1, 0].legend()
        
        # Recommended green splits
        axes[1, 1].bar(scenarios, green_splits, color='salmon')
        axes[1, 1].set_title('Recommended Green Splits')
        axes[1, 1].set_ylabel('Green Split Ratio')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Balanced')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comprehensive_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_predictions(self, results: Dict[str, Any]):
        """Plot prediction results"""
        predictions = results['predictions']
        
        fig, axes = plt.subplots(2, 1, figsize=(15, 10))
        fig.suptitle('Future Conditions Prediction', fontsize=16)
        
        hours = [p['timestamp'].hour for p in predictions]
        flow_factors = [p['predicted_flow_factor'] for p in predictions]
        
        # Flow factor prediction
        axes[0].plot(hours, flow_factors, 'b-', linewidth=2, marker='o')
        axes[0].set_title('Predicted Traffic Flow Factors')
        axes[0].set_ylabel('Flow Factor')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Baseline')
        axes[0].legend()
        
        # Add event annotation
        event_start = results['upcoming_event']['start_time']
        event_hour = datetime.strptime(event_start, '%H:%M').hour
        axes[0].axvline(x=event_hour, color='g', linestyle='--', alpha=0.7, label='Event Start')
        axes[0].legend()
        
        # Traffic pattern evolution
        base_flows = []
        for p in predictions:
            pattern = p['traffic_pattern']
            base_flows.append(pattern.base_flow * pattern.peak_multiplier)
        
        axes[1].plot(hours, base_flows, 'g-', linewidth=2, marker='s')
        axes[1].set_title('Base Traffic Pattern Evolution')
        axes[1].set_ylabel('Vehicles/Hour/Lane')
        axes[1].set_xlabel('Hour of Day')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'predictions.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """Save all results to files"""
        # Save JSON results
        json_path = self.output_dir / "environmental_demo_results.json"
        with open(json_path, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            json_results = self._convert_datetime_to_strings(self.results)
            json.dump(json_results, f, indent=2, default=str)
        
        # Generate summary report
        report = self._generate_summary_report()
        report_path = self.output_dir / "demo_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Results saved to {self.output_dir}")
    
    def _convert_datetime_to_strings(self, obj):
        """Convert datetime objects to strings for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_datetime_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_to_strings(item) for item in obj]
        else:
            return obj
    
    def _generate_summary_report(self) -> str:
        """Generate comprehensive summary report"""
        report = []
        report.append("# Environmental Factors Demo Report")
        report.append("=" * 50)
        
        # Demo scenarios
        report.append("\n## Demo Scenarios")
        for scenario_name, scenario in self.demo_scenarios.items():
            report.append(f"### {scenario_name.replace('_', ' ').title()}")
            report.append(f"- Description: {scenario['description']}")
            report.append(f"- Weather: {scenario['weather'].condition.value}")
            report.append(f"- Events: {len(scenario['events'])}")
        
        # Key findings
        report.append("\n## Key Findings")
        
        if 'weather_impact' in self.results:
            report.append("\n### Weather Impact Analysis")
            worst_weather = min(self.results['weather_impact'].items(), 
                              key=lambda x: x[1]['impact_factors']['speed_factor'])
            report.append(f"- Worst weather condition: {worst_weather[0]}")
            report.append(f"- Speed reduction: {(1-worst_weather[1]['impact_factors']['speed_factor'])*100:.1f}%")
        
        if 'time_of_day' in self.results:
            report.append("\n### Time-of-Day Patterns")
            peak_factors = self.integrator.time_analyzer.calculate_peak_hour_factors(self.results['time_of_day']['patterns'])
            report.append(f"- Peak hour factor: {peak_factors['peak_hour_factor']:.2f}")
            report.append(f"- Peak flow: {peak_factors['peak_flow']:.0f} vehicles/hour")
        
        if 'comprehensive' in self.results:
            report.append("\n### Comprehensive Integration")
            max_adjustment = max(self.results['comprehensive'].items(), 
                               key=lambda x: x[1]['recommendations']['cycle_length'])
            report.append(f"- Maximum cycle length adjustment: {max_adjustment[0]}")
            report.append(f"- Recommended cycle length: {max_adjustment[1]['recommendations']['cycle_length']:.1f}s")
        
        # Recommendations
        report.append("\n## Recommendations")
        report.append("1. Implement weather-responsive signal timing")
        report.append("2. Use time-of-day patterns for adaptive control")
        report.append("3. Integrate event-based traffic management")
        report.append("4. Consider pedestrian demand in signal optimization")
        report.append("5. Deploy predictive traffic management system")
        
        return "\n".join(report)
    
    def run_all_demos(self):
        """Run all demonstration modules"""
        logger.info("🚀 Starting Environmental Factors Comprehensive Demo")
        
        # Run individual demos
        self.run_weather_impact_demo()
        self.run_time_of_day_demo()
        self.run_event_impact_demo()
        self.run_pedestrian_demo()
        self.run_comprehensive_demo()
        self.run_prediction_demo()
        
        # Save results
        self.save_results()
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print demo summary"""
        print("\n" + "="*60)
        print("🎯 ENVIRONMENTAL FACTORS DEMO SUMMARY")
        print("="*60)
        
        print(f"📊 Scenarios Analyzed: {len(self.demo_scenarios)}")
        print(f"🌤️ Weather Conditions: {len(set(s['weather'].condition for s in self.demo_scenarios.values()))}")
        print(f"📅 Time Periods: 24-hour analysis")
        print(f"🎪 Events Simulated: {sum(len(s['events']) for s in self.demo_scenarios.values())}")
        print(f"🚶 Pedestrian Locations: {len(set(s['location'] for s in self.demo_scenarios.values()))}")
        
        print("\n📈 Key Insights:")
        if 'weather_impact' in self.results:
            worst_weather = min(self.results['weather_impact'].items(), 
                              key=lambda x: x[1]['impact_factors']['speed_factor'])
            print(f"  • Worst weather impact: {worst_weather[0].replace('_', ' ').title()}")
        
        if 'comprehensive' in self.results:
            max_cycle = max(self.results['comprehensive'].items(), 
                           key=lambda x: x[1]['recommendations']['cycle_length'])
            print(f"  • Maximum signal adjustment: {max_cycle[0].replace('_', ' ').title()}")
        
        print(f"\n💾 Results saved to: {self.output_dir}")
        print("🎉 Environmental Factors Demo completed successfully!")
        print("="*60)


def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description='Environmental Factors Demo')
    parser.add_argument('--output-dir', default='environmental_demo_output', 
                       help='Output directory for results')
    parser.add_argument('--demo', choices=['all', 'weather', 'time', 'events', 'pedestrian', 'comprehensive', 'prediction'],
                       default='all', help='Specific demo to run')
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = EnvironmentalFactorsDemo(args.output_dir)
    
    # Run specified demo
    if args.demo == 'all':
        demo.run_all_demos()
    elif args.demo == 'weather':
        demo.run_weather_impact_demo()
    elif args.demo == 'time':
        demo.run_time_of_day_demo()
    elif args.demo == 'events':
        demo.run_event_impact_demo()
    elif args.demo == 'pedestrian':
        demo.run_pedestrian_demo()
    elif args.demo == 'comprehensive':
        demo.run_comprehensive_demo()
    elif args.demo == 'prediction':
        demo.run_prediction_demo()
    
    # Save results
    demo.save_results()


if __name__ == "__main__":
    main()