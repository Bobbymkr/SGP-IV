"""
Signal Control Algorithms
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ControllerType(Enum):
    FIXED = "fixed"
    WEBSTER = "webster"
    FUZZY = "fuzzy"
    DQN = "dqn"


@dataclass
class SignalTiming:
    """Signal timing plan for one intersection"""
    cycle_length: float
    green_times: Dict[str, float]  # direction -> green time
    yellow_time: float
    all_red_time: float
    offset: float = 0.0


@dataclass
class TrafficState:
    """Current traffic state at intersection"""
    queue_lengths: Dict[str, float]  # vehicles per direction
    flow_rates: Dict[str, float]     # vehicles/hour per direction
    occupancy: Dict[str, float]      # detector occupancy per direction
    phase: str                       # current signal phase
    time_in_phase: float             # seconds in current phase


class BaseController(ABC):
    """Base class for signal controllers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_green = config.get('min_green', 10)
        self.max_green = config.get('max_green', 60)
        self.yellow_time = config.get('yellow_time', 5)
        self.all_red_time = config.get('all_red_time', 2)
        self.directions = config.get('directions', ['north', 'south', 'east', 'west'])
    
    @abstractmethod
    def compute_timing(self, state: TrafficState) -> SignalTiming:
        """Compute optimal signal timing given traffic state"""
        pass
    
    def _ensure_bounds(self, value: float) -> float:
        """Ensure value is within min/max green bounds"""
        return max(self.min_green, min(self.max_green, value))


class FixedTimeController(BaseController):
    """Fixed-time signal controller with pre-defined timing plans"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.timing_plans = config.get('timing_plans', {})
        self.current_plan = config.get('default_plan', 'plan_1')
    
    def compute_timing(self, state: TrafficState) -> SignalTiming:
        plan = self.timing_plans.get(self.current_plan, {})
        cycle = plan.get('cycle_length', 120)
        
        green_times = {}
        for direction in self.directions:
            green_times[direction] = plan.get(f'green_{direction}', cycle / len(self.directions))
        
        return SignalTiming(
            cycle_length=cycle,
            green_times=green_times,
            yellow_time=self.yellow_time,
            all_red_time=self.all_red_time
        )
    
    def set_plan(self, plan_name: str):
        """Switch to a different timing plan"""
        if plan_name in self.timing_plans:
            self.current_plan = plan_name


class WebsterController(BaseController):
    """Webster's method for optimal cycle length and green split"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.lost_time = config.get('lost_time', 12)  # seconds per cycle
        self.critical_lane_flow = config.get('critical_lane_flow', {})
    
    def compute_timing(self, state: TrafficState) -> SignalTiming:
        # Calculate critical lane flows
        critical_flows = {}
        for direction in self.directions:
            # Use maximum of queue-based and flow-based estimates
            queue_flow = state.queue_lengths.get(direction, 0) * 3600 / max(state.time_in_phase, 1)
            measured_flow = state.flow_rates.get(direction, 0)
            critical_flows[direction] = max(queue_flow, measured_flow)
        
        # Sum of critical lane flows (Y)
        Y = sum(critical_flows.values())
        
        # Practical capacity (assume 1800 veh/hr/lane)
        C = 1800
        
        # Optimal cycle length (Webster's formula)
        if Y < C:
            optimal_cycle = (1.5 * self.lost_time + 5) / (1 - Y / C)
            optimal_cycle = self._ensure_bounds(optimal_cycle)
        else:
            optimal_cycle = self.max_green * len(self.directions) + self.lost_time
        
        # Green time allocation proportional to critical flows
        effective_green = optimal_cycle - self.lost_time
        green_times = {}
        
        for direction in self.directions:
            if Y > 0:
                green = (critical_flows[direction] / Y) * effective_green
            else:
                green = effective_green / len(self.directions)
            green_times[direction] = self._ensure_bounds(green)
        
        return SignalTiming(
            cycle_length=optimal_cycle,
            green_times=green_times,
            yellow_time=self.yellow_time,
            all_red_time=self.all_red_time
        )


class FuzzyController(BaseController):
    """Fuzzy logic signal controller"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self._setup_fuzzy_rules()
    
    def _setup_fuzzy_rules(self):
        """Define fuzzy membership functions and rules"""
        # Queue length membership: {short, medium, long}
        # Flow rate membership: {low, medium, high}
        # Output: green extension {decrease, maintain, increase}
        pass
    
    def _membership_short(self, x: float) -> float:
        if x <= 5: return 1.0
        elif x <= 15: return (15 - x) / 10
        return 0.0
    
    def _membership_medium(self, x: float) -> float:
        if x <= 5: return 0.0
        elif x <= 15: return (x - 5) / 10
        elif x <= 25: return (25 - x) / 10
        return 0.0
    
    def _membership_long(self, x: float) -> float:
        if x <= 15: return 0.0
        elif x <= 25: return (x - 15) / 10
        return 1.0
    
    def _membership_low_flow(self, x: float) -> float:
        if x <= 200: return 1.0
        elif x <= 600: return (600 - x) / 400
        return 0.0
    
    def _membership_medium_flow(self, x: float) -> float:
        if x <= 200: return 0.0
        elif x <= 600: return (x - 200) / 400
        elif x <= 1000: return (1000 - x) / 400
        return 0.0
    
    def _membership_high_flow(self, x: float) -> float:
        if x <= 600: return 0.0
        elif x <= 1000: return (x - 600) / 400
        return 1.0
    
    def _fuzzy_inference(self, queue_len: float, flow_rate: float) -> float:
        """Fuzzy inference for green time adjustment"""
        # Fuzzify inputs
        q_short = self._membership_short(queue_len)
        q_medium = self._membership_medium(queue_len)
        q_long = self._membership_long(queue_len)
        
        f_low = self._membership_low_flow(flow_rate)
        f_medium = self._membership_medium_flow(flow_rate)
        f_high = self._membership_high_flow(flow_rate)
        
        # Rule base: (queue, flow) -> adjustment factor
        # Rules (simplified):
        # 1. IF queue=short AND flow=low THEN decrease
        # 2. IF queue=short AND flow=high THEN maintain
        # 3. IF queue=medium AND flow=low THEN maintain
        # 4. IF queue=medium AND flow=high THEN increase
        # 5. IF queue=long AND flow=low THEN increase
        # 6. IF queue=long AND flow=high THEN increase strongly
        
        rules = [
            (min(q_short, f_low), 0.8),      # decrease
            (min(q_short, f_medium), 0.9),   # slight decrease
            (min(q_short, f_high), 1.0),     # maintain
            (min(q_medium, f_low), 1.0),     # maintain
            (min(q_medium, f_medium), 1.1),  # slight increase
            (min(q_medium, f_high), 1.2),    # increase
            (min(q_long, f_low), 1.2),       # increase
            (min(q_long, f_medium), 1.3),    # increase more
            (min(q_long, f_high), 1.4),      # increase strongly
        ]
        
        # Weighted average
        numerator = sum(w * v for w, v in rules)
        denominator = sum(w for w, _ in rules)
        
        if denominator > 0:
            return numerator / denominator
        return 1.0
    
    def compute_timing(self, state: TrafficState) -> SignalTiming:
        # Base green time
        base_green = 30
        
        # Compute adjustments for each direction
        green_times = {}
        for direction in self.directions:
            queue = state.queue_lengths.get(direction, 0)
            flow = state.flow_rates.get(direction, 0)
            
            adjustment = self._fuzzy_inference(queue, flow)
            green = self._ensure_bounds(base_green * adjustment)
            green_times[direction] = green
        
        cycle = sum(green_times.values()) + len(self.directions) * (self.yellow_time + self.all_red_time)
        
        return SignalTiming(
            cycle_length=cycle,
            green_times=green_times,
            yellow_time=self.yellow_time,
            all_red_time=self.all_red_time
        )


class DQNController(BaseController):
    """Deep Q-Network based adaptive signal controller"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.state_dim = config.get('state_dim', 8)  # 4 directions * 2 (queue + flow)
        self.action_dim = config.get('action_dim', 12)  # discrete green time choices
        self.model = None
        self._build_model(config)
    
    def _build_model(self, config: Dict):
        """Build or load DQN model"""
        try:
            import torch
            import torch.nn as nn
            
            class DQN(nn.Module):
                def __init__(self, state_dim, action_dim, hidden_dim=128):
                    super().__init__()
                    self.net = nn.Sequential(
                        nn.Linear(state_dim, hidden_dim),
                        nn.ReLU(),
                        nn.Linear(hidden_dim, hidden_dim),
                        nn.ReLU(),
                        nn.Linear(hidden_dim, action_dim)
                    )
                
                def forward(self, x):
                    return self.net(x)
            
            self.model = DQN(self.state_dim, self.action_dim)
            
            # Load pretrained weights if available
            model_path = config.get('model_path')
            if model_path:
                self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
                logger.info(f"Loaded DQN model from {model_path}")
            
            self.model.eval()
            
        except ImportError:
            logger.warning("PyTorch not available, DQN controller will use fallback")
            self.model = None
    
    def _state_to_tensor(self, state: TrafficState):
        """Convert traffic state to model input"""
        features = []
        for direction in self.directions:
            features.append(state.queue_lengths.get(direction, 0))
            features.append(state.flow_rates.get(direction, 0))
        return np.array(features, dtype=np.float32)
    
    def _action_to_green(self, action: int) -> Dict[str, float]:
        """Convert discrete action to green times"""
        # Action space: 12 actions = 3 choices per phase (short, medium, long)
        # Or: 4 directions * 3 levels each
        base_times = [15, 30, 45, 60]  # Possible green times
        
        # Simple mapping: action determines base green for all directions
        green_idx = action // (len(self.directions) + 1)
        base_green = base_times[min(green_idx, len(base_times) - 1)]
        
        # Add small variations per direction
        green_times = {}
        for i, direction in enumerate(self.directions):
            variation = (action + i) % 3 - 1  # -1, 0, or 1
            green = self._ensure_bounds(base_green + variation * 5)
            green_times[direction] = green
        
        return green_times
    
    def compute_timing(self, state: TrafficState) -> SignalTiming:
        if self.model is None:
            # Fallback to Webster
            webster = WebsterController(self.config)
            return webster.compute_timing(state)
        
        import torch
        
        state_tensor = torch.FloatTensor(self._state_to_tensor(state)).unsqueeze(0)
        
        with torch.no_grad():
            q_values = self.model(state_tensor)
            action = q_values.argmax().item()
        
        green_times = self._action_to_green(action)
        cycle = sum(green_times.values()) + len(self.directions) * (self.yellow_time + self.all_red_time)
        
        return SignalTiming(
            cycle_length=cycle,
            green_times=green_times,
            yellow_time=self.yellow_time,
            all_red_time=self.all_red_time
        )


def create_controller(controller_type: str, config: Dict) -> BaseController:
    """Factory function to create signal controller"""
    controllers = {
        ControllerType.FIXED.value: FixedTimeController,
        ControllerType.WEBSTER.value: WebsterController,
        ControllerType.FUZZY.value: FuzzyController,
        ControllerType.DQN.value: DQNController,
    }
    
    controller_class = controllers.get(controller_type.lower())
    if controller_class is None:
        raise ValueError(f"Unknown controller type: {controller_type}")
    
    return controller_class(config)