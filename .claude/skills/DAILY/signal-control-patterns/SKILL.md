---
name: signal-control-patterns
description: "Project-specific patterns for adaptive traffic signal control."
---

# Signal Control Patterns

Project-specific patterns for adaptive traffic signal control.
Based on `Code/YOLO/darkflow/` controllers: Webster, DQN, Fuzzy, GA, PSO, and CCDA-Light MARL.
**Adapted for Indian traffic systems - adjusted safety bounds and controller parameters.**

## Controller Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

@dataclass
class SignalState:
    current_phase: int          # 0-3
    phase_timer: int            # seconds elapsed in phase
    queues: Dict[str, float]    # per-lane queue lengths (meters)
    occupancies: Dict[str, float] # per-lane occupancy 0-1
    time_of_day: int            # seconds since midnight
    phase_history: List[int]    # last N phases

@dataclass
class SignalAction:
    next_phase: int             # 0-3
    green_duration: int         # seconds (7-50, Indian adaptation)
    force_switch: bool = False  # override minimum green

class BaseController(ABC):
    @abstractmethod
    def act(self, state: SignalState) -> SignalAction:
        pass

    @abstractmethod
    def update(self, state: SignalState, reward: float):
        pass

    def get_min_green(self) -> int:
        return 7  # Indian: 7s vs 10s Western - two-wheelers need less

    def get_max_green(self) -> int:
        return 50  # Indian: 50s vs 60s - cap for high-volume intersections

    def get_yellow_time(self) -> float:
        return 3.5  # Indian: 3.5s vs 5s - shorter reaction times

    def get_all_red_time(self) -> int:
        return 3  # Indian: 3s vs 2s - extra clearance for encroachment
```

## Controllers

### 1. Webster's Method (Classic - Indian Bounds)
```python
class WebsterController(BaseController):
    """Webster's optimal cycle length formula - Indian adapted"""
    def __init__(self, lost_time_per_phase=5):
        self.lost_time = lost_time_per_phase

    def act(self, state: SignalState) -> SignalAction:
        # Critical flow ratio per phase
        y = []
        for phase in range(2):  # NS=0, EW=1
            lanes = ['north_0', 'south_0'] if phase == 0 else ['east_0', 'west_0']
            # Indian: use actual queue lengths, no /5.0 simplification needed
            max_y = max(state.queues.get(l, 0) / 4.5 for l in lanes)  # 4.5m avg Indian car
            y.append(max_y)

        Y = sum(y)
        # Indian intersections often have Y > 1 due to high density
        if Y >= 1: Y = 0.95

        # Optimal cycle length
        C = (1.5 * self.lost_time + 3.5) / (1 - Y)  # 3.5 vs 5 (Indian lost time)
        C = int(np.clip(C, 40, 100))  # Indian: max 100s vs 120s

        # Green splits
        green_times = [int(c * y[i] / Y) for i, c in enumerate([C]*2)]
        # Indian: clamp to 7-50 (vs 10-60 Western)
        green_times = [np.clip(g, 7, 50) for g in green_times]

        next_phase = (state.current_phase + 1) % 2
        return SignalAction(
            next_phase=next_phase,
            green_duration=green_times[next_phase]
        )

    def update(self, state, reward):
        pass  # No learning
```

### 2. DQN Controller (Indian Bounds)
```python
import torch
import torch.nn as nn

class DQNController(BaseController):
    def __init__(self, state_dim=8, action_dim=11, hidden=128):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.q_net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim)
        ).to(self.device)

        self.target_net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim)
        ).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())

        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=1e-4)
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995

        # Indian adaptation: actions still 11 (10-60s in 5s steps)
        # But SafetyWrapper will clamp to 7-50
        self.actions = list(range(10, 61, 5))  # [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

    def _state_to_tensor(self, state: SignalState):
        vec = []
        for lane in ['north_0', 'south_0', 'east_0', 'west_0']:
            vec.append(state.queues.get(lane, 0) / 100.0)  # normalize
            vec.append(state.occupancies.get(lane, 0))
        vec.append(state.current_phase / 3.0)
        vec.append(state.phase_timer / 50.0)  # Indian: max 50s not 60s
        return torch.FloatTensor(vec).unsqueeze(0).to(self.device)

    def act(self, state: SignalState) -> SignalAction:
        s = self._state_to_tensor(state)

        if np.random.random() < self.epsilon:
            action_idx = np.random.randint(len(self.actions))
        else:
            with torch.no_grad():
                q_vals = self.q_net(s)
                action_idx = q_vals.argmax().item()

        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

        green_duration = self.actions[action_idx]
        # SafetyWrapper will clamp this to 7-50, but also ensure min green

        next_phase = (state.current_phase + 1) % 4

        return SignalAction(next_phase=next_phase, green_duration=green_duration)

    def update(self, state, reward):
        # Experience replay would go here
        pass
```

### 3. MaxPressure (Indian Bounds)
```python
class MaxPressureController(BaseController):
    """MaxPressure: max sum of queue pressures across phases - Indian adapted"""
    def act(self, state: SignalState) -> SignalAction:
        pressures = []
        for phase in range(4):  # 4 phases
            # Pressure = sum of queues on green - sum on red
            if phase in [0, 2]:  # NS green
                green_queues = ['north_0', 'south_0']
                red_queues = ['east_0', 'west_0']
            else:  # EW green
                green_queues = ['east_0', 'west_0']
                red_queues = ['north_0', 'south_0']

            pressure = sum(state.queues.get(l, 0) for l in green_queues) - \
                       sum(state.queues.get(l, 0) for l in red_queues)
            pressures.append(pressure)

        best_phase = int(np.argmax(pressures))

        # Indian: green time proportional to pressure, clamped to 7-50
        green = int(np.clip(7 + pressures[best_phase] * 1.5, 7, 50))  # 7 vs 10 min

        return SignalAction(
            next_phase=best_phase,
            green_duration=green
        )

    def update(self, state, reward):
        pass
```

### 4. CCDA-Light MARL Controller (Indian Intervention Freq)
```python
class CCDAController(BaseController):
    """Centralized Critic Decentralized Actors - Traffic-Alpha/CCDA-Light - Indian adapted"""

    def __init__(self, intersection_id, neighbors, state_dim=8, action_dim=11):
        self.intersection_id = intersection_id
        self.neighbors = neighbors  # list of neighbor intersection IDs

        # Decentralized Actor (per intersection)
        self.actor = nn.Sequential(
            nn.Linear(state_dim + len(neighbors)*4, 128),  # + neighbor phases
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 11)  # 11 green duration actions (10-60s in 5s steps)
        )

        # Centralized Critic (shared)
        total_state_dim = (state_dim + 4) * (1 + len(neighbors))
        self.critic = nn.Sequential(
            nn.Linear(total_state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

        # Indian adaptation: more frequent interventions (7s vs 10s)
        # due to higher traffic volatility at Indian intersections
        self.intervention_freq = 7  # seconds between interventions (was 10)
        self.last_intervention = -self.intervention_freq

    def act(self, state: SignalState) -> SignalAction:
        # Check intervention frequency (CCDA-Light pattern, Indian freq)
        if state.phase_timer - self.last_intervention < self.intervention_freq:
            # Continue current phase
            return SignalAction(
                next_phase=state.current_phase,
                green_duration=state.phase_timer + 1
            )

        # Build input with neighbor info
        actor_input = self._build_actor_input(state)

        with torch.no_grad():
            action_logits = self.actor(actor_input)
            action_idx = action_logits.argmax().item()

        self.last_intervention = state.phase_timer
        green_duration = list(range(10, 61, 5))[action_idx]
        # Note: SafetyWrapper will clamp green_duration to 7-50
        next_phase = (state.current_phase + 1) % 4

        return SignalAction(
            next_phase=next_phase,
            green_duration=green_duration
        )

    def _build_actor_input(self, state):
        # Own state + neighbor phases (simplified)
        vec = []
        for lane in ['north_0', 'south_0', 'east_0', 'west_0']:
            vec.append(state.queues.get(lane, 0))
            vec.append(state.occupancies.get(lane, 0))
        vec.append(state.current_phase)
        vec.append(state.phase_timer)
        return torch.FloatTensor(vec).unsqueeze(0)
```

## Safety Constraints (ALL controllers must respect) - Indian Bounds

```python
class SafetyWrapper:
    def __init__(self, controller: BaseController):
        self.controller = controller
        # Indian adaptation: bounds changed from 10-60 to 7-50
        self.min_green = 7
        self.max_green = 50
        self.yellow = 3.5
        self.all_red = 3
        self.last_switch_time = 0

    def act(self, state: SignalState) -> SignalAction:
        action = self.controller.act(state)

        # Enforce minimum green (Indian: 7s vs 10s)
        if state.phase_timer < self.min_green:
            action.next_phase = state.current_phase
            action.green_duration = self.min_green
            action.force_switch = False

        # Enforce maximum green (Indian: 50s vs 60s)
        if state.phase_timer >= self.max_green:
            action.next_phase = (state.current_phase + 1) % 4
            action.force_switch = True

        # Clamp green duration to Indian bounds [7, 50]
        action.green_duration = int(np.clip(action.green_duration,
                                             self.min_green,
                                             self.max_green))

        return action
```

## Reward Functions (for RL) - Indian Adaptations

```python
def compute_reward(state: SignalState, action: SignalAction,
                   next_state: SignalState, reward_type='queue'):

    if reward_type == 'queue':
        # Negative total queue length
        return -sum(next_state.queues.values())

    elif reward_type == 'delay':
        # Negative total delay (queue * wait_time)
        # Indian: 2.0s/veh vs 2.5s/veh Western (faster decision)
        return -sum(q * 2.0 for q in next_state.queues.values())

    elif reward_type == 'throughput':
        # Vehicles passed through
        return sum(next_state.queues.get(l, 0) - state.queues.get(l, 0)
                   for l in state.queues)

    elif reward_type == 'pressure':
        # MaxPressure reward
        pressures = []
        for phase in range(4):
            if phase in [0, 2]:
                g = ['north_0', 'south_0']
                r = ['east_0', 'west_0']
            else:
                g = ['east_0', 'west_0']
                r = ['north_0', 'south_0']
            p = sum(next_state.queues.get(l, 0) for l in g) - \
                sum(next_state.queues.get(l, 0) for l in r)
            pressures.append(p)
        return max(pressures)

    elif reward_type == 'ccda':
        # CCDA-Light: weighted combination
        queue_reward = -sum(next_state.queues.values())
        delay_reward = -sum(q * 2.0 for q in next_state.queues.values())
        throughput_reward = sum(max(0, next_state.queues.get(l, 0) - state.queues.get(l, 0))
                               for l in state.queues)
        # Indian: slightly different weights for higher variance
        return 0.5 * queue_reward + 0.3 * delay_reward + 0.2 * throughput_reward
```

## Rules

- All controllers inherit `BaseController` and respect `SafetyWrapper`
- **Minimum green: 7s** (Indian: two-wheelers need less), **Maximum: 50s** (cap for high-volume)
- **Yellow: 3.5s** (Indian: shorter reaction times), **All-red: 3s** (extra clearance for encroachment)
- Phase order: 0(NS)→1(EW)→2(NS)→3(EW) or configurable
- Action space: green duration 10-60s in 5s steps (11 actions), but SafetyWrapper clamps to 7-50
- State: 4 lanes × (queue + occupancy) + phase + timer = 10 dims
- CCDA: intervention frequency configurable (Indian: default 7s vs 10s Western)
- All three Indian bounds (MIN_GREEN=7, MAX_GREEN=50, YELLOW=3.5, ALL_RED=3) must be
  enforced by SafetyWrapper on every control cycle
- Two-wheeler consideration: 7s minimum green allows quick passage of bike/autorickshaw groups
- Higher variance in Indian traffic → consider adding variance_penalty to reward functions
