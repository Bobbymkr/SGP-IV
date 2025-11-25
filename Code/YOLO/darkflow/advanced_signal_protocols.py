"""
Advanced Traffic Signal Protocols
================================

Complex intersection management with:
- Protected/permitted turn movements
- Leading pedestrian intervals (LPI)
- Transit signal priority (TSP)
- Variable lane control
- Intersection conflict monitoring
- Advanced phase sequencing

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
from collections import deque, defaultdict
import math
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovementType(Enum):
    """Types of traffic movements"""
    THROUGH = "through"
    LEFT_TURN = "left_turn"
    RIGHT_TURN = "right_turn"
    U_TURN = "u_turn"
    PEDESTRIAN_CROSSING = "pedestrian_crossing"

class SignalPhase(Enum):
    """Advanced signal phase types"""
    PROTECTED_THROUGH = "protected_through"
    PROTECTED_LEFT = "protected_left"
    PROTECTED_RIGHT = "protected_right"
    PERMITTED_LEFT = "permitted_left"
    PERMITTED_RIGHT = "permitted_right"
    PEDESTRIAN_WALK = "pedestrian_walk"
    PEDESTRIAN_DONT_WALK = "pedestrian_dont_walk"
    ALL_RED = "all_red"
    FLASHING_RED = "flashing_red"
    YELLOW_ARROW = "yellow_arrow"

class LaneType(Enum):
    """Advanced lane types"""
    THROUGH_LANE = "through_lane"
    LEFT_TURN_LANE = "left_turn_lane"
    RIGHT_TURN_LANE = "right_turn_lane"
    BUS_LANE = "bus_lane"
    BIKE_LANE = "bike_lane"
    REVERSIBLE_LANE = "reversible_lane"
    EMERGENCY_LANE = "emergency_lane"

class PriorityType(Enum):
    """Signal priority types"""
    TRANSIT_PRIORITY = "transit_priority"
    EMERGENCY_PREEMPTION = "emergency_preemption"
    PEDESTRIAN_PRIORITY = "pedestrian_priority"
    BICYCLE_PRIORITY = "bicycle_priority"
    TRUCK_PRIORITY = "truck_priority"

@dataclass
class Movement:
    """Traffic movement definition"""
    movement_id: str
    from_lane: str
    to_lane: str
    movement_type: MovementType
    conflicting_movements: List[str] = field(default_factory=list)
    priority: int = 1  # 1-10, higher = more important
    vehicle_types: List[str] = field(default_factory=list)
    pedestrian_crossing: bool = False
    transit_priority: bool = False

@dataclass
class Phase:
    """Advanced signal phase definition"""
    phase_id: str
    phase_name: str
    movements: List[str]  # Movement IDs
    phase_type: SignalPhase
    min_duration: float = 5.0
    max_duration: float = 60.0
    pedestrian_phase: bool = False
    transit_phase: bool = False
    yellow_duration: float = 3.0
    all_red_duration: float = 2.0
    phase_order: int = 0

@dataclass
class TimingPlan:
    """Advanced timing plan"""
    plan_id: str
    plan_name: str
    time_period: str  # "morning_peak", "off_peak", etc.
    cycle_length: float
    phases: List[Phase]
    phase_transitions: List[Tuple[str, str, float]]  # (from_phase, to_phase, transition_time)
    pedestrian_times: Dict[str, float] = field(default_factory=dict)
    priority_intervals: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)
    coordination_offsets: Dict[str, float] = field(default_factory=dict)

class ConflictMonitor:
    """Monitor intersection conflicts and near-misses"""
    
    def __init__(self):
        self.conflict_zones = {}
        self.conflict_history = deque(maxlen=100)
        self.near_misses = deque(maxlen=50)
        self.conflict_threshold = 2.0  # seconds
        self.near_miss_threshold = 1.0  # seconds
        
        # Conflict types
        self.conflict_types = {
            'right_angle': 'Right-angle collision',
            'head_on': 'Head-on collision',
            'sideswipe': 'Sideswipe collision',
            'rear_end': 'Rear-end collision',
            'pedestrian_conflict': 'Pedestrian-vehicle conflict',
            'bike_conflict': 'Bicycle-vehicle conflict'
        }
        
        logger.info("Conflict monitor initialized")
    
    def add_conflict_zone(self, zone_id: str, movements: List[str], 
                        detection_area: Tuple[float, float, float, float]):
        """Add conflict monitoring zone"""
        self.conflict_zones[zone_id] = {
            'movements': movements,
            'detection_area': detection_area,
            'last_conflict': 0,
            'conflict_count': 0
        }
    
    def check_conflicts(self, vehicle_positions: Dict[str, Tuple[float, float]], 
                      vehicle_velocities: Dict[str, Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Check for potential conflicts"""
        conflicts = []
        current_time = time.time()
        
        for zone_id, zone in self.conflict_zones.items():
            # Check vehicles in conflict zone
            vehicles_in_zone = []
            
            for vehicle_id, pos in vehicle_positions.items():
                if self._is_in_area(pos, zone['detection_area']):
                    vehicles_in_zone.append({
                        'vehicle_id': vehicle_id,
                        'position': pos,
                        'velocity': vehicle_velocities.get(vehicle_id, (0, 0))
                    })
            
            # Check for conflicts between vehicles in zone
            if len(vehicles_in_zone) >= 2:
                conflict = self._analyze_vehicle_conflict(vehicles_in_zone, zone)
                if conflict:
                    conflict['timestamp'] = current_time
                    conflict['zone_id'] = zone_id
                    conflicts.append(conflict)
                    
                    # Update zone statistics
                    zone['last_conflict'] = current_time
                    zone['conflict_count'] += 1
        
        # Add to history
        for conflict in conflicts:
            self.conflict_history.append(conflict)
        
        return conflicts
    
    def _is_in_area(self, position: Tuple[float, float], 
                   area: Tuple[float, float, float, float]) -> bool:
        """Check if position is within area"""
        x, y = position
        x1, y1, x2, y2 = area
        
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _analyze_vehicle_conflict(self, vehicles: List[Dict[str, Any]], 
                               zone: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze potential conflict between vehicles"""
        if len(vehicles) < 2:
            return None
        
        # Calculate Time to Collision (TTC) for all vehicle pairs
        min_ttc = float('inf')
        conflict_type = None
        
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                v1, v2 = vehicles[i], vehicles[j]
                
                # Calculate relative positions and velocities
                rel_pos = (v2['position'][0] - v1['position'][0],
                           v2['position'][1] - v1['position'][1])
                rel_vel = (v2['velocity'][0] - v1['velocity'][0],
                           v2['velocity'][1] - v1['velocity'][1])
                
                # Calculate TTC
                ttc = self._calculate_ttc(rel_pos, rel_vel)
                
                if 0 < ttc < min_ttc:
                    min_ttc = ttc
                    
                    # Determine conflict type based on approach angles
                    conflict_type = self._determine_conflict_type(rel_pos, rel_vel)
        
        if min_ttc < self.conflict_threshold:
            return {
                'conflict_type': conflict_type,
                'ttc': min_ttc,
                'vehicles_involved': [v['vehicle_id'] for v in vehicles],
                'severity': 'high' if min_ttc < 1.0 else 'medium',
                'zone_movements': zone['movements']
            }
        
        return None
    
    def _calculate_ttc(self, relative_position: Tuple[float, float], 
                      relative_velocity: Tuple[float, float]) -> float:
        """Calculate Time to Collision"""
        # Simplified TTC calculation
        # In real implementation, would use more sophisticated methods
        
        if abs(relative_velocity[0]) < 0.1 and abs(relative_velocity[1]) < 0.1:
            return float('inf')  # Vehicles nearly stationary relative to each other
        
        # Calculate TTC for each axis
        ttc_x = relative_position[0] / relative_velocity[0] if abs(relative_velocity[0]) > 0.1 else float('inf')
        ttc_y = relative_position[1] / relative_velocity[1] if abs(relative_velocity[1]) > 0.1 else float('inf')
        
        # Return minimum positive TTC
        ttc_values = [ttc for ttc in [ttc_x, ttc_y] if ttc > 0]
        return min(ttc_values) if ttc_values else float('inf')
    
    def _determine_conflict_type(self, relative_position: Tuple[float, float], 
                              relative_velocity: Tuple[float, float]) -> str:
        """Determine type of conflict based on approach vectors"""
        # Simplified conflict type determination
        angle = math.atan2(relative_position[1], relative_position[0]) * 180 / math.pi
        
        # Normalize angle to 0-360
        angle = (angle + 360) % 360
        
        # Determine conflict type based on angle
        if 45 <= angle < 135 or 225 <= angle < 315:
            return 'head_on'
        elif 135 <= angle < 225 or 315 <= angle < 360 or 0 <= angle < 45:
            return 'rear_end'
        else:
            return 'sideswipe'
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get conflict monitoring statistics"""
        if not self.conflict_history:
            return {
                'total_conflicts': 0,
                'conflict_rate': 0,
                'conflict_types': {},
                'high_risk_periods': []
            }
        
        # Calculate statistics
        total_conflicts = len(self.conflict_history)
        time_window = 3600  # 1 hour
        recent_conflicts = [
            c for c in self.conflict_history
            if time.time() - c['timestamp'] < time_window
        ]
        
        conflict_rate = len(recent_conflicts) / (time_window / 60)  # conflicts per minute
        
        # Count by type
        type_counts = defaultdict(int)
        for conflict in self.conflict_history:
            type_counts[conflict['conflict_type']] += 1
        
        # Identify high-risk periods
        high_risk_periods = self._identify_high_risk_periods()
        
        return {
            'total_conflicts': total_conflicts,
            'conflict_rate': conflict_rate,
            'conflict_types': dict(type_counts),
            'high_risk_periods': high_risk_periods,
            'last_conflict': self.conflict_history[-1]['timestamp'] if self.conflict_history else None
        }
    
    def _identify_high_risk_periods(self) -> List[Dict[str, Any]]:
        """Identify periods with high conflict rates"""
        # Group conflicts by time periods
        time_periods = defaultdict(list)
        
        for conflict in self.conflict_history:
            hour = time.localtime(conflict['timestamp']).tm_hour
            time_periods[hour].append(conflict)
        
        # Calculate conflict rates by hour
        hourly_rates = {}
        for hour, conflicts in time_periods.items():
            hourly_rates[hour] = len(conflicts)
        
        # Find high-risk periods (above average)
        if hourly_rates:
            avg_rate = np.mean(list(hourly_rates.values()))
            high_risk_hours = [
                hour for hour, rate in hourly_rates.items()
                if rate > avg_rate * 1.5
            ]
            
            return [
                {
                    'hour': hour,
                    'conflict_count': hourly_rates[hour],
                    'risk_level': 'high'
                }
                for hour in high_risk_hours
            ]
        
        return []

class AdvancedSignalController:
    """Advanced traffic signal controller with complex protocols"""
    
    def __init__(self, intersection_id: str):
        self.intersection_id = intersection_id
        
        # Movement and phase definitions
        self.movements = {}
        self.phases = {}
        self.current_phase = None
        self.phase_timer = 0.0
        
        # Timing plans
        self.timing_plans = {}
        self.current_plan = None
        self.plan_transition_time = 0.0
        
        # Priority systems
        self.priority_requests = queue.PriorityQueue()
        self.active_priorities = {}
        
        # Lane control
        self.lane_configurations = {}
        self.lane_usage = defaultdict(int)
        
        # Pedestrian systems
        self.pedestrian_phases = {}
        self.leading_pedestrian_intervals = {}
        
        # Transit systems
        self.transit_priority = {}
        self.bus_detection = {}
        
        # Conflict monitoring
        self.conflict_monitor = ConflictMonitor()
        
        # Performance metrics
        self.performance_metrics = {
            'total_vehicles_served': 0,
            'average_delay': 0.0,
            'phase_changes': 0,
            'priority_activations': 0,
            'conflicts_detected': 0
        }
        
        # State management
        self.controller_state = 'normal'
        self.emergency_mode = False
        self.flash_mode = False
        
        logger.info(f"Advanced signal controller initialized: {intersection_id}")
    
    def add_movement(self, movement: Movement):
        """Add movement definition to controller"""
        self.movements[movement.movement_id] = movement
        
        # Add to conflict monitor
        if movement.movement_id not in self.conflict_monitor.conflict_zones:
            # Create conflict zone for this movement
            zone_area = self._create_movement_conflict_zone(movement)
            self.conflict_monitor.add_conflict_zone(
                movement.movement_id, [movement.movement_id], zone_area
            )
        
        logger.info(f"Movement added: {movement.movement_id}")
    
    def add_phase(self, phase: Phase):
        """Add phase definition to controller"""
        self.phases[phase.phase_id] = phase
        
        # Create conflict zones for phase movements
        for movement_id in phase.movements:
            if movement_id in self.movements:
                movement = self.movements[movement_id]
                zone_area = self._create_movement_conflict_zone(movement)
                self.conflict_monitor.add_conflict_zone(
                    f"{phase.phase_id}_{movement_id}", [movement_id], zone_area
                )
        
        logger.info(f"Phase added: {phase.phase_id}")
    
    def _create_movement_conflict_zone(self, movement: Movement) -> Tuple[float, float, float, float]:
        """Create conflict detection zone for movement"""
        # Simplified zone creation
        # In real implementation, would use actual intersection geometry
        
        zone_size = 10.0  # 10 meter zone
        return (-zone_size, -zone_size, zone_size, zone_size)
    
    def add_timing_plan(self, plan: TimingPlan):
        """Add timing plan to controller"""
        self.timing_plans[plan.plan_id] = plan
        
        # Set as current plan if no plan is active
        if self.current_plan is None:
            self.current_plan = plan
            self._activate_plan(plan)
        
        logger.info(f"Timing plan added: {plan.plan_id}")
    
    def _activate_plan(self, plan: TimingPlan):
        """Activate a timing plan"""
        self.current_plan = plan
        self.plan_transition_time = time.time()
        
        # Initialize phase sequence
        if plan.phases:
            self.current_phase = plan.phases[0]
            self.phase_timer = 0.0
        
        logger.info(f"Timing plan activated: {plan.plan_id}")
    
    def request_priority(self, priority_type: PriorityType, vehicle_id: str, 
                      movement_id: str, duration: float, priority_level: int = 5):
        """Request signal priority"""
        request = {
            'request_id': f"PRIO_{int(time.time())}",
            'priority_type': priority_type,
            'vehicle_id': vehicle_id,
            'movement_id': movement_id,
            'duration': duration,
            'priority_level': priority_level,
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        # Add to priority queue (negative for max-heap behavior)
        self.priority_requests.put((-priority_level, request))
        
        logger.info(f"Priority request: {priority_type.value} for {vehicle_id}")
    
    def process_priority_requests(self):
        """Process pending priority requests"""
        while not self.priority_requests.empty():
            try:
                priority, request = self.priority_requests.get_nowait()
                priority_level = -priority
                
                # Check if request is still valid
                if time.time() - request['timestamp'] > 60:  # 1 minute timeout
                    continue
                
                # Process based on priority type
                if request['priority_type'] == PriorityType.TRANSIT_PRIORITY:
                    self._handle_transit_priority(request)
                elif request['priority_type'] == PriorityType.EMERGENCY_PREEMPTION:
                    self._handle_emergency_preemption(request)
                elif request['priority_type'] == PriorityType.PEDESTRIAN_PRIORITY:
                    self._handle_pedestrian_priority(request)
                
                request['status'] = 'processed'
                self.active_priorities[request['request_id']] = request
                
            except queue.Empty:
                break
    
    def _handle_transit_priority(self, request: Dict[str, Any]):
        """Handle transit signal priority request"""
        movement_id = request['movement_id']
        
        # Find phase that serves this movement
        target_phase = None
        for phase_id, phase in self.phases.items():
            if movement_id in phase.movements:
                target_phase = phase
                break
        
        if target_phase and target_phase.transit_phase:
            # Extend green time for transit phase
            if self.current_phase == target_phase:
                self.phase_timer = min(
                    target_phase.max_duration,
                    self.phase_timer + request['duration']
                )
            
            # Insert transit phase into sequence
            self._insert_priority_phase(target_phase, request['duration'])
            
            self.performance_metrics['priority_activations'] += 1
            logger.info(f"Transit priority activated: {request['vehicle_id']}")
    
    def _handle_emergency_preemption(self, request: Dict[str, Any]):
        """Handle emergency preemption request"""
        self.emergency_mode = True
        
        # Immediately set all signals to red
        self._set_all_signals_red()
        
        # After 2 seconds, set green for emergency vehicle movement
        threading.Timer(2.0, self._activate_emergency_phase, args=[request]).start()
        
        self.performance_metrics['priority_activations'] += 1
        logger.critical(f"Emergency preemption activated: {request['vehicle_id']}")
    
    def _activate_emergency_phase(self, request: Dict[str, Any]):
        """Activate emergency phase"""
        movement_id = request['movement_id']
        
        # Find and activate phase for emergency movement
        for phase_id, phase in self.phases.items():
            if movement_id in phase.movements:
                self.current_phase = phase
                self.phase_timer = request['duration']
                break
        
        # Schedule return to normal operation
        threading.Timer(request['duration'], self._return_to_normal_operation).start()
    
    def _return_to_normal_operation(self):
        """Return to normal operation after emergency"""
        self.emergency_mode = False
        self.controller_state = 'normal'
        
        # Resume normal timing plan
        if self.current_plan:
            self._activate_plan(self.current_plan)
        
        logger.info("Returned to normal operation")
    
    def _handle_pedestrian_priority(self, request: Dict[str, Any]):
        """Handle pedestrian priority request"""
        # Activate leading pedestrian interval
        self._activate_leading_pedestrian_interval(request)
        
        self.performance_metrics['priority_activations'] += 1
        logger.info(f"Pedestrian priority activated: {request['vehicle_id']}")
    
    def _activate_leading_pedestrian_interval(self, request: Dict[str, Any]):
        """Activate leading pedestrian interval"""
        # LPI gives pedestrians head start before vehicles get green
        self._set_all_signals_red()
        
        # Activate pedestrian walk signal
        for phase_id, phase in self.pedestrian_phases.items():
            if phase.pedestrian_phase:
                phase.current_state = SignalPhase.PEDESTRIAN_WALK
                phase.phase_timer = 7.0  # 7 seconds walk
        
        # After 7 seconds, start vehicle phases
        threading.Timer(7.0, self._start_vehicle_phases_after_lpi).start()
    
    def _start_vehicle_phases_after_lpi(self):
        """Start vehicle phases after LPI"""
        # Resume normal phase sequence
        if self.current_plan and self.current_plan.phases:
            self.current_phase = self.current_plan.phases[0]
            self.phase_timer = 0.0
    
    def _insert_priority_phase(self, priority_phase: Phase, duration: float):
        """Insert priority phase into sequence"""
        # Simplified - in real implementation would be more complex
        self.current_phase = priority_phase
        self.phase_timer = duration
    
    def _set_all_signals_red(self):
        """Set all signals to red"""
        for phase in self.phases.values():
            phase.current_state = SignalPhase.ALL_RED
            phase.phase_timer = 0.0
    
    def update_phase_timing(self, dt: float):
        """Update current phase timing"""
        if not self.current_phase:
            return
        
        self.phase_timer += dt
        
        # Check for phase transition
        if self.phase_timer >= self.current_phase.max_duration:
            self._advance_to_next_phase()
        elif self.emergency_mode:
            # In emergency mode, check if emergency phase should end
            if self.phase_timer >= self.current_phase.max_duration:
                self._return_to_normal_operation()
    
    def _advance_to_next_phase(self):
        """Advance to next phase in timing plan"""
        if not self.current_plan or not self.current_plan.phases:
            return
        
        current_index = self.current_plan.phases.index(self.current_phase)
        next_index = (current_index + 1) % len(self.current_plan.phases)
        
        self.current_phase = self.current_plan.phases[next_index]
        self.phase_timer = 0.0
        self.performance_metrics['phase_changes'] += 1
        
        logger.info(f"Phase advanced to: {self.current_phase.phase_id}")
    
    def get_signal_status(self) -> Dict[str, Any]:
        """Get current signal status"""
        status = {
            'intersection_id': self.intersection_id,
            'current_phase': self.current_phase.phase_id if self.current_phase else None,
            'phase_timer': self.phase_timer,
            'controller_state': self.controller_state,
            'emergency_mode': self.emergency_mode,
            'active_priorities': len(self.active_priorities),
            'timing_plan': self.current_plan.plan_id if self.current_plan else None,
            'movements': {},
            'performance_metrics': self.performance_metrics.copy()
        }
        
        # Add movement statuses
        for movement_id, movement in self.movements.items():
            status['movements'][movement_id] = {
                'movement_type': movement.movement_type.value,
                'priority': movement.priority,
                'vehicle_types': movement.vehicle_types,
                'signal_state': self._get_movement_signal_state(movement_id)
            }
        
        return status
    
    def _get_movement_signal_state(self, movement_id: str) -> str:
        """Get current signal state for movement"""
        if not self.current_phase:
            return SignalPhase.ALL_RED.value
        
        if movement_id in self.current_phase.movements:
            return self.current_phase.phase_type.value
        else:
            return SignalPhase.ALL_RED.value
    
    def update_performance_metrics(self, vehicle_data: Dict[str, Any]):
        """Update performance metrics"""
        # Update vehicle counts
        self.performance_metrics['total_vehicles_served'] += vehicle_data.get('vehicles_served', 0)
        
        # Update delay calculations
        current_delay = vehicle_data.get('average_delay', 0)
        total_vehicles = self.performance_metrics['total_vehicles_served']
        
        if total_vehicles > 0:
            # Calculate running average delay
            self.performance_metrics['average_delay'] = (
                (self.performance_metrics['average_delay'] * (total_vehicles - 1) + current_delay) / total_vehicles
            )
        
        # Update conflict count
        conflicts = self.conflict_monitor.get_conflict_statistics()
        self.performance_metrics['conflicts_detected'] = conflicts['total_conflicts']
    
    def get_advanced_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        conflict_stats = self.conflict_monitor.get_conflict_statistics()
        
        return {
            'intersection_id': self.intersection_id,
            'controller_state': self.controller_state,
            'timing_plan': self.current_plan.plan_id if self.current_plan else None,
            'current_phase': self.current_phase.phase_id if self.current_phase else None,
            'phase_efficiency': self._calculate_phase_efficiency(),
            'priority_utilization': self._calculate_priority_utilization(),
            'conflict_statistics': conflict_stats,
            'level_of_service': self._calculate_level_of_service(),
            'performance_metrics': self.performance_metrics,
            'timestamp': time.time()
        }
    
    def _calculate_phase_efficiency(self) -> float:
        """Calculate phase efficiency metrics"""
        if not self.current_phase:
            return 0.0
        
        # Efficiency based on phase utilization vs. allocated time
        allocated_time = self.current_phase.max_duration
        used_time = self.phase_timer
        
        # Consider minimum green time requirements
        min_efficiency = min(1.0, used_time / max(1.0, allocated_time))
        
        return min_efficiency
    
    def _calculate_priority_utilization(self) -> float:
        """Calculate priority system utilization"""
        if not self.active_priorities:
            return 0.0
        
        # Calculate utilization based on active priority requests
        total_requests = len(self.active_priorities)
        max_concurrent = 10  # Maximum concurrent priorities
        
        return min(1.0, total_requests / max_concurrent)
    
    def _calculate_level_of_service(self) -> str:
        """Calculate overall Level of Service (LOS)"""
        avg_delay = self.performance_metrics['average_delay']
        
        # Simplified LOS calculation based on average delay
        if avg_delay < 10:
            return 'A'  # Excellent
        elif avg_delay < 20:
            return 'B'  # Good
        elif avg_delay < 35:
            return 'C'  # Fair
        elif avg_delay < 55:
            return 'D'  # Poor
        else:
            return 'F'  # Failed

# Factory functions
def create_standard_intersection() -> AdvancedSignalController:
    """Create standard 4-way intersection controller"""
    controller = AdvancedSignalController("STANDARD_4_WAY")
    
    # Add standard movements
    movements = [
        Movement("EB_THROUGH", "east_bound", "east_bound", MovementType.THROUGH, 
                ["NB_THROUGH", "WB_LEFT"], 5, ["car", "truck"]),
        Movement("WB_THROUGH", "west_bound", "west_bound", MovementType.THROUGH,
                ["EB_THROUGH", "NB_LEFT"], 5, ["car", "truck"]),
        Movement("NB_THROUGH", "north_bound", "north_bound", MovementType.THROUGH,
                ["SB_THROUGH", "EB_LEFT"], 5, ["car", "truck"]),
        Movement("SB_THROUGH", "south_bound", "south_bound", MovementType.THROUGH,
                ["NB_THROUGH", "WB_LEFT"], 5, ["car", "truck"]),
        Movement("EB_LEFT", "east_bound", "north_bound", MovementType.LEFT_TURN,
                ["WB_THROUGH", "NB_THROUGH"], 3, ["car", "truck"]),
        Movement("WB_LEFT", "west_bound", "south_bound", MovementType.LEFT_TURN,
                ["EB_THROUGH", "SB_THROUGH"], 3, ["car", "truck"]),
        Movement("NB_LEFT", "north_bound", "west_bound", MovementType.LEFT_TURN,
                ["SB_THROUGH", "EB_THROUGH"], 3, ["car", "truck"]),
        Movement("SB_LEFT", "south_bound", "east_bound", MovementType.LEFT_TURN,
                ["NB_THROUGH", "WB_THROUGH"], 3, ["car", "truck"])
    ]
    
    for movement in movements:
        controller.add_movement(movement)
    
    # Add standard phases
    phases = [
        Phase("P1", "Main Street Green", ["EB_THROUGH", "WB_THROUGH"], 
              SignalPhase.PROTECTED_THROUGH, 10.0, 40.0),
        Phase("P2", "Main Street Left", ["EB_LEFT", "WB_LEFT"], 
              SignalPhase.PROTECTED_LEFT, 10.0, 20.0),
        Phase("P3", "Cross Street Green", ["NB_THROUGH", "SB_THROUGH"], 
              SignalPhase.PROTECTED_THROUGH, 10.0, 40.0),
        Phase("P4", "Cross Street Left", ["NB_LEFT", "SB_LEFT"], 
              SignalPhase.PROTECTED_LEFT, 10.0, 20.0)
    ]
    
    for phase in phases:
        controller.add_phase(phase)
    
    # Add standard timing plan
    timing_plan = TimingPlan(
        "STANDARD", "Standard Timing Plan", "all_day",
        120.0, phases,
        [("P1", "P2", 3.0), ("P2", "P3", 3.0), 
         ("P3", "P4", 3.0), ("P4", "P1", 3.0)]
    )
    
    controller.add_timing_plan(timing_plan)
    
    return controller

# Export main classes
__all__ = [
    'AdvancedSignalController',
    'ConflictMonitor',
    'Movement',
    'Phase',
    'TimingPlan',
    'MovementType',
    'SignalPhase',
    'LaneType',
    'PriorityType',
    'create_standard_intersection'
]