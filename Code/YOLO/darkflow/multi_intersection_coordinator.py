"""
Multi-Intersection Traffic Coordination System
==========================================

Advanced network-wide traffic signal coordination with:
- Dynamic traffic flow optimization
- Green wave coordination
- Network-wide congestion management
- Real-time intersection communication
- Adaptive timing algorithms
- Emergency response coordination

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import numpy as np
import networkx as nx
import threading
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import queue
import json
from collections import defaultdict, deque
import asyncio
from concurrent.futures import ThreadPoolExecutor
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntersectionType(Enum):
    """Types of intersections in the network"""
    FOUR_WAY = "four_way"
    THREE_WAY = "three_way"
    T_INTERSECTION = "t_intersection"
    ROUNDABOUT = "roundabout"
    COMPLEX = "complex"

class CoordinationMode(Enum):
    """Coordination strategies"""
    INDEPENDENT = "independent"
    GREEN_WAVE = "green_wave"
    ADAPTIVE = "adaptive"
    PEAK_HOUR = "peak_hour"
    EMERGENCY = "emergency"
    INCIDENT_RESPONSE = "incident_response"

@dataclass
class IntersectionConfig:
    """Configuration for individual intersection"""
    intersection_id: str
    intersection_type: IntersectionType
    location: Tuple[float, float]  # GPS coordinates or x,y
    connected_intersections: List[str] = field(default_factory=list)
    signal_phases: List[Dict[str, Any]] = field(default_factory=list)
    cycle_length: float = 120.0  # seconds
    min_green_time: float = 10.0
    max_green_time: float = 60.0
    yellow_time: float = 3.0
    all_red_time: float = 2.0
    pedestrian_crossing_time: float = 15.0
    coordination_priority: int = 1  # 1-10, higher = more important
    
@dataclass
class TrafficFlowData:
    """Traffic flow information between intersections"""
    from_intersection: str
    to_intersection: str
    volume: float  # vehicles per hour
    speed: float   # average speed km/h
    density: float  # vehicles per km
    travel_time: float  # seconds
    last_updated: float

@dataclass
class CoordinationSignal:
    """Signal for coordinating between intersections"""
    signal_type: str
    data: Dict[str, Any]
    timestamp: float
    source: str
    destination: str
    priority: int = 1

class IntersectionController:
    """Individual intersection controller with coordination capabilities"""
    
    def __init__(self, config: IntersectionConfig):
        self.config = config
        self.intersection_id = config.intersection_id
        
        # Signal state
        self.current_phase = 0
        self.phase_timer = 0.0
        self.signal_state = "red"
        self.vehicle_counts = defaultdict(int)
        self.queue_lengths = defaultdict(float)
        
        # Coordination state
        self.coordination_mode = CoordinationMode.INDEPENDENT
        self.offset = 0.0  # Phase offset for coordination
        self.cycle_length = config.cycle_length
        self.split_times = [30.0] * len(config.signal_phases)
        
        # Communication
        self.message_queue = queue.Queue()
        self.connected_controllers = {}
        
        # Performance metrics
        self.total_vehicles_passed = 0
        self.total_delay = 0.0
        self.average_queue_length = 0.0
        self.performance_history = deque(maxlen=100)
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Intersection controller initialized: {self.intersection_id}")
    
    def update_traffic_data(self, vehicle_counts: Dict[str, int], queue_lengths: Dict[str, float]):
        """Update traffic data from sensors"""
        with self.lock:
            self.vehicle_counts.update(vehicle_counts)
            self.queue_lengths.update(queue_lengths)
    
    def calculate_optimal_timing(self, network_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate optimal signal timing based on network conditions"""
        base_cycle = self.cycle_length
        
        # Adjust based on coordination mode
        if self.coordination_mode == CoordinationMode.GREEN_WAVE:
            # Optimize for progression
            base_cycle = self._calculate_green_wave_timing(network_data)
        elif self.coordination_mode == CoordinationMode.ADAPTIVE:
            # Optimize based on current traffic
            base_cycle = self._calculate_adaptive_timing()
        elif self.coordination_mode == CoordinationMode.PEAK_HOUR:
            # Optimize for peak hour conditions
            base_cycle = self._calculate_peak_hour_timing(network_data)
        
        return {
            'cycle_length': base_cycle,
            'split_times': self.split_times,
            'offset': self.offset
        }
    
    def _calculate_green_wave_timing(self, network_data: Dict[str, Any]) -> float:
        """Calculate timing for green wave progression"""
        # Get target progression speed from network data
        target_speed = network_data.get('target_speed', 50)  # km/h
        
        # Calculate optimal cycle for progression
        distance_to_next = self._get_distance_to_next_intersection()
        travel_time = (distance_to_next / 1000) / target_speed * 3600  # seconds
        
        # Optimize cycle length for progression
        optimal_cycle = max(60, min(180, travel_time * 2))
        
        return optimal_cycle
    
    def _calculate_adaptive_timing(self) -> float:
        """Calculate adaptive timing based on current traffic"""
        total_queue = sum(self.queue_lengths.values())
        total_vehicles = sum(self.vehicle_counts.values())
        
        if total_vehicles == 0:
            return 60.0  # Minimum cycle for empty intersection
        
        # Calculate cycle based on demand
        base_cycle = 60.0 + (total_queue / 10.0) * 30.0
        return max(60.0, min(180.0, base_cycle))
    
    def _calculate_peak_hour_timing(self, network_data: Dict[str, Any]) -> float:
        """Calculate timing for peak hour conditions"""
        # Use longer cycles during peak hours
        peak_multiplier = network_data.get('peak_multiplier', 1.5)
        return self.cycle_length * peak_multiplier
    
    def _get_distance_to_next_intersection(self) -> float:
        """Get distance to next coordinated intersection"""
        # Simplified - in real system, would use road network data
        return 500.0  # meters
    
    def receive_coordination_signal(self, signal: CoordinationSignal):
        """Receive coordination signal from another intersection"""
        with self.lock:
            self.message_queue.put(signal)
    
    def process_coordination_signals(self) -> List[CoordinationSignal]:
        """Process pending coordination signals"""
        signals = []
        while not self.message_queue.empty():
            try:
                signal = self.message_queue.get_nowait()
                signals.append(signal)
                self._handle_coordination_signal(signal)
            except queue.Empty:
                break
        return signals
    
    def _handle_coordination_signal(self, signal: CoordinationSignal):
        """Handle individual coordination signal"""
        if signal.signal_type == "phase_change":
            # Adjust timing for coordination
            self._adjust_for_phase_change(signal.data)
        elif signal.signal_type == "emergency_approach":
            # Prepare for emergency vehicle
            self.coordination_mode = CoordinationMode.EMERGENCY
        elif signal.signal_type == "incident_detected":
            # Adjust for incident response
            self.coordination_mode = CoordinationMode.INCIDENT_RESPONSE
    
    def _adjust_for_phase_change(self, data: Dict[str, Any]):
        """Adjust timing based on neighboring intersection phase change"""
        target_offset = data.get('offset', 0.0)
        self.offset = target_offset
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for this intersection"""
        with self.lock:
            return {
                'intersection_id': self.intersection_id,
                'total_vehicles_passed': self.total_vehicles_passed,
                'average_delay': self.total_delay / max(1, self.total_vehicles_passed),
                'average_queue_length': np.mean(list(self.queue_lengths.values())) if self.queue_lengths else 0,
                'cycle_length': self.cycle_length,
                'coordination_mode': self.coordination_mode.value,
                'timestamp': time.time()
            }

class NetworkCoordinator:
    """Central coordinator for network-wide optimization"""
    
    def __init__(self):
        self.intersections = {}
        self.network_graph = nx.DiGraph()
        self.traffic_flows = {}
        self.coordination_mode = CoordinationMode.ADAPTIVE
        
        # Communication system
        self.message_bus = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Optimization parameters
        self.optimization_interval = 30.0  # seconds
        self.last_optimization = 0.0
        
        # Network-wide metrics
        self.total_vehicles_in_network = 0
        self.average_network_speed = 0.0
        self.congestion_level = 0.0
        
        # Green wave parameters
        self.green_wave_corridors = []
        self.progression_speeds = {}
        
        # Incident management
        self.active_incidents = {}
        self.incident_impact_zones = {}
        
        logger.info("Network coordinator initialized")
    
    def add_intersection(self, controller: IntersectionController):
        """Add intersection to network"""
        self.intersections[controller.intersection_id] = controller
        
        # Add to network graph
        self.network_graph.add_node(
            controller.intersection_id,
            controller=controller,
            location=controller.config.location,
            priority=controller.config.coordination_priority
        )
        
        # Connect to neighboring intersections
        for neighbor_id in controller.config.connected_intersections:
            if neighbor_id in self.intersections:
                self.network_graph.add_edge(
                    controller.intersection_id,
                    neighbor_id,
                    weight=self._calculate_distance(controller.intersection_id, neighbor_id)
                )
                self.network_graph.add_edge(
                    neighbor_id,
                    controller.intersection_id,
                    weight=self._calculate_distance(neighbor_id, controller.intersection_id)
                )
        
        logger.info(f"Intersection {controller.intersection_id} added to network")
    
    def _calculate_distance(self, intersection1: str, intersection2: str) -> float:
        """Calculate distance between two intersections"""
        if intersection1 not in self.intersections or intersection2 not in self.intersections:
            return 1000.0  # Default distance
        
        loc1 = self.intersections[intersection1].config.location
        loc2 = self.intersections[intersection2].config.location
        
        # Euclidean distance
        return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def update_traffic_flow(self, flow_data: TrafficFlowData):
        """Update traffic flow data between intersections"""
        key = f"{flow_data.from_intersection}->{flow_data.to_intersection}"
        self.traffic_flows[key] = flow_data
        
        # Update network graph edge weight
        if self.network_graph.has_edge(flow_data.from_intersection, flow_data.to_intersection):
            # Use travel time as weight
            self.network_graph[flow_data.from_intersection][flow_data.to_intersection]['weight'] = flow_data.travel_time
    
    def optimize_network(self):
        """Perform network-wide optimization"""
        current_time = time.time()
        
        if current_time - self.last_optimization < self.optimization_interval:
            return
        
        logger.info("Starting network-wide optimization...")
        
        # Analyze current network state
        network_state = self._analyze_network_state()
        
        # Determine optimal coordination strategy
        optimal_mode = self._determine_coordination_mode(network_state)
        
        # Apply coordination strategy
        if optimal_mode == CoordinationMode.GREEN_WAVE:
            self._implement_green_wave(network_state)
        elif optimal_mode == CoordinationMode.ADAPTIVE:
            self._implement_adaptive_coordination(network_state)
        elif optimal_mode == CoordinationMode.PEAK_HOUR:
            self._implement_peak_hour_coordination(network_state)
        
        # Handle incidents
        self._handle_incidents()
        
        # Update coordination mode
        for intersection in self.intersections.values():
            intersection.coordination_mode = optimal_mode
        
        self.last_optimization = current_time
        logger.info(f"Network optimization completed. Mode: {optimal_mode.value}")
    
    def _analyze_network_state(self) -> Dict[str, Any]:
        """Analyze current network state"""
        total_vehicles = 0
        total_delay = 0.0
        total_queue = 0.0
        congested_intersections = []
        
        for intersection in self.intersections.values():
            metrics = intersection.get_performance_metrics()
            total_vehicles += metrics['total_vehicles_passed']
            total_delay += metrics['average_delay']
            total_queue += metrics['average_queue_length']
            
            # Identify congested intersections
            if metrics['average_queue_length'] > 10:
                congested_intersections.append(intersection.intersection_id)
        
        # Calculate network-wide metrics
        network_state = {
            'total_vehicles': total_vehicles,
            'average_delay': total_delay / len(self.intersections),
            'average_queue_length': total_queue / len(self.intersections),
            'congested_intersections': congested_intersections,
            'congestion_level': len(congested_intersections) / len(self.intersections),
            'active_incidents': len(self.active_incidents),
            'time_of_day': time.strftime('%H:%M'),
            'target_speed': self._calculate_target_speed()
        }
        
        return network_state
    
    def _determine_coordination_mode(self, network_state: Dict[str, Any]) -> CoordinationMode:
        """Determine optimal coordination mode based on network state"""
        congestion_level = network_state['congestion_level']
        active_incidents = network_state['active_incidents']
        time_of_day = int(network_state['time_of_day'].split(':')[0])
        
        # Emergency mode takes priority
        if active_incidents > 0:
            return CoordinationMode.EMERGENCY
        
        # Peak hour coordination
        if 7 <= time_of_day <= 9 or 17 <= time_of_day <= 19:
            if congestion_level > 0.6:
                return CoordinationMode.PEAK_HOUR
        
        # Green wave for moderate traffic
        if 0.2 <= congestion_level <= 0.6:
            return CoordinationMode.GREEN_WAVE
        
        # Adaptive for other conditions
        return CoordinationMode.ADAPTIVE
    
    def _implement_green_wave(self, network_state: Dict[str, Any]):
        """Implement green wave coordination"""
        target_speed = network_state['target_speed']
        
        # Identify main corridors
        corridors = self._identify_green_wave_corridors()
        
        for corridor in corridors:
            self._coordinate_corridor(corridor, target_speed)
    
    def _identify_green_wave_corridors(self) -> List[List[str]]:
        """Identify main corridors for green wave coordination"""
        corridors = []
        
        # Find longest paths in network
        try:
            # Get all simple paths up to length 5
            all_paths = []
            for start in self.intersections.keys():
                for end in self.intersections.keys():
                    if start != end:
                        try:
                            paths = list(nx.all_simple_paths(
                                self.network_graph, start, end, cutoff=4
                            ))
                            all_paths.extend(paths)
                        except:
                            continue
            
            # Select best corridors based on traffic flow
            for path in all_paths[:10]:  # Top 10 paths
                if len(path) >= 3:  # At least 3 intersections
                    corridors.append(path)
        
        except Exception as e:
            logger.warning(f"Error identifying corridors: {e}")
            # Fallback to simple corridors
            corridors = [
                list(self.intersections.keys())[:4],  # First 4 intersections
                list(self.intersections.keys())[2:6]  # Next 4
            ]
        
        return corridors
    
    def _coordinate_corridor(self, corridor: List[str], target_speed: float):
        """Coordinate signals along a corridor"""
        if len(corridor) < 2:
            return
        
        # Calculate optimal offsets for green wave
        for i in range(1, len(corridor)):
            prev_intersection = corridor[i-1]
            curr_intersection = corridor[i]
            
            # Calculate travel time between intersections
            distance = self._calculate_distance(prev_intersection, curr_intersection)
            travel_time = (distance / 1000) / target_speed * 3600  # seconds
            
            # Calculate optimal offset
            optimal_offset = travel_time % self.intersections[curr_intersection].cycle_length
            
            # Send coordination signal
            signal = CoordinationSignal(
                signal_type="phase_offset",
                data={'offset': optimal_offset, 'target_speed': target_speed},
                timestamp=time.time(),
                source=prev_intersection,
                destination=curr_intersection,
                priority=2
            )
            
            self._send_coordination_signal(signal)
    
    def _implement_adaptive_coordination(self, network_state: Dict[str, Any]):
        """Implement adaptive coordination based on current conditions"""
        # Calculate optimal cycle lengths for each intersection
        for intersection_id, controller in self.intersections.items():
            # Get local traffic data
            local_data = {
                'network_congestion': network_state['congestion_level'],
                'target_speed': network_state['target_speed'],
                'time_of_day': network_state['time_of_day']
            }
            
            # Calculate optimal timing
            optimal_timing = controller.calculate_optimal_timing(local_data)
            
            # Apply timing
            controller.cycle_length = optimal_timing['cycle_length']
            controller.split_times = optimal_timing['split_times']
            controller.offset = optimal_timing['offset']
    
    def _implement_peak_hour_coordination(self, network_state: Dict[str, Any]):
        """Implement peak hour coordination strategies"""
        # Extend cycle lengths during peak hours
        peak_multiplier = 1.3
        
        for intersection in self.intersections.values():
            intersection.cycle_length = min(180, intersection.config.cycle_length * peak_multiplier)
            
            # Favor main directions
            if intersection.intersection_id in network_state.get('main_corridors', []):
                intersection.split_times = [t * 1.2 for t in intersection.split_times]
    
    def _calculate_target_speed(self) -> float:
        """Calculate target progression speed for network"""
        # Base speed on network conditions
        base_speed = 50.0  # km/h
        
        # Adjust for congestion
        if hasattr(self, 'congestion_level'):
            congestion_factor = max(0.5, 1.0 - self.congestion_level * 0.5)
            base_speed *= congestion_factor
        
        return max(30.0, min(60.0, base_speed))
    
    def _handle_incidents(self):
        """Handle active incidents in the network"""
        for incident_id, incident in self.active_incidents.items():
            # Calculate impact zone
            affected_intersections = self._calculate_incident_impact(incident)
            
            # Adjust signal timing for affected intersections
            for intersection_id in affected_intersections:
                if intersection_id in self.intersections:
                    controller = self.intersections[intersection_id]
                    controller.coordination_mode = CoordinationMode.INCIDENT_RESPONSE
                    
                    # Send incident notification
                    signal = CoordinationSignal(
                        signal_type="incident_detected",
                        data=incident,
                        timestamp=time.time(),
                        source="network_coordinator",
                        destination=intersection_id,
                        priority=3
                    )
                    
                    self._send_coordination_signal(signal)
    
    def _calculate_incident_impact(self, incident: Dict[str, Any]) -> List[str]:
        """Calculate which intersections are affected by an incident"""
        incident_location = incident.get('location', (0, 0))
        impact_radius = incident.get('impact_radius', 1000)  # meters
        
        affected = []
        for intersection_id, controller in self.intersections.items():
            distance = self._calculate_distance_point(
                incident_location, controller.config.location
            )
            
            if distance <= impact_radius:
                affected.append(intersection_id)
        
        return affected
    
    def _calculate_distance_point(self, point1: Tuple[float, float], 
                               point2: Tuple[float, float]) -> float:
        """Calculate distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _send_coordination_signal(self, signal: CoordinationSignal):
        """Send coordination signal to target intersection"""
        if signal.destination in self.intersections:
            self.intersections[signal.destination].receive_coordination_signal(signal)
    
    def report_incident(self, incident_id: str, incident_data: Dict[str, Any]):
        """Report new incident in the network"""
        self.active_incidents[incident_id] = incident_data
        logger.warning(f"Incident reported: {incident_id} - {incident_data.get('type', 'Unknown')}")
        
        # Trigger immediate optimization
        self.optimize_network()
    
    def clear_incident(self, incident_id: str):
        """Clear incident from network"""
        if incident_id in self.active_incidents:
            del self.active_incidents[incident_id]
            logger.info(f"Incident cleared: {incident_id}")
            
            # Return to normal coordination
            for intersection in self.intersections.values():
                if intersection.coordination_mode == CoordinationMode.INCIDENT_RESPONSE:
                    intersection.coordination_mode = CoordinationMode.ADAPTIVE
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get comprehensive network metrics"""
        total_vehicles = 0
        total_delay = 0.0
        total_queue = 0.0
        intersection_metrics = []
        
        for intersection in self.intersections.values():
            metrics = intersection.get_performance_metrics()
            intersection_metrics.append(metrics)
            total_vehicles += metrics['total_vehicles_passed']
            total_delay += metrics['average_delay']
            total_queue += metrics['average_queue_length']
        
        return {
            'network_id': 'main_network',
            'total_intersections': len(self.intersections),
            'total_vehicles_passed': total_vehicles,
            'average_delay_per_intersection': total_delay / len(self.intersections),
            'average_queue_length': total_queue / len(self.intersections),
            'coordination_mode': self.coordination_mode.value,
            'active_incidents': len(self.active_incidents),
            'network_congestion_level': self.congestion_level,
            'target_speed': self._calculate_target_speed(),
            'intersection_metrics': intersection_metrics,
            'timestamp': time.time()
        }
    
    def start_coordination_loop(self):
        """Start the main coordination loop"""
        def coordination_worker():
            while True:
                try:
                    # Process coordination signals
                    for intersection in self.intersections.values():
                        intersection.process_coordination_signals()
                    
                    # Optimize network
                    self.optimize_network()
                    
                    # Sleep until next optimization
                    time.sleep(self.optimization_interval)
                    
                except Exception as e:
                    logger.error(f"Error in coordination loop: {e}")
                    time.sleep(5)  # Wait before retrying
        
        # Start coordination thread
        coordination_thread = threading.Thread(target=coordination_worker, daemon=True)
        coordination_thread.start()
        
        logger.info("Network coordination loop started")

# Factory functions for easy setup
def create_four_way_intersection(intersection_id: str, location: Tuple[float, float],
                             connected_intersections: List[str]) -> IntersectionController:
    """Create a standard four-way intersection controller"""
    config = IntersectionConfig(
        intersection_id=intersection_id,
        intersection_type=IntersectionType.FOUR_WAY,
        location=location,
        connected_intersections=connected_intersections,
        signal_phases=[
            {'name': 'NS_Green', 'directions': ['north', 'south']},
            {'name': 'NS_Yellow', 'directions': ['north', 'south']},
            {'name': 'EW_Green', 'directions': ['east', 'west']},
            {'name': 'EW_Yellow', 'directions': ['east', 'west']}
        ],
        coordination_priority=5
    )
    
    return IntersectionController(config)

def create_network_coordinator() -> NetworkCoordinator:
    """Create and initialize network coordinator"""
    coordinator = NetworkCoordinator()
    
    # Create sample network (4 intersections in a grid)
    intersections = [
        create_four_way_intersection("INT_A", (0, 0), ["INT_B", "INT_D"]),
        create_four_way_intersection("INT_B", (1000, 0), ["INT_A", "INT_C"]),
        create_four_way_intersection("INT_C", (1000, 1000), ["INT_B", "INT_D"]),
        create_four_way_intersection("INT_D", (0, 1000), ["INT_A", "INT_C"])
    ]
    
    # Add intersections to network
    for intersection in intersections:
        coordinator.add_intersection(intersection)
    
    return coordinator

# Export main classes
__all__ = [
    'NetworkCoordinator',
    'IntersectionController',
    'IntersectionConfig',
    'TrafficFlowData',
    'CoordinationSignal',
    'IntersectionType',
    'CoordinationMode',
    'create_four_way_intersection',
    'create_network_coordinator'
]