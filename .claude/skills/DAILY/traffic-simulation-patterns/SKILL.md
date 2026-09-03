---
name: traffic-simulation-patterns
description: "Project-specific patterns for the Adaptive-Traffic-Signal-Timer Pygame simulation."
---

# Traffic Simulation Patterns

Project-specific patterns for the Adaptive-Traffic-Signal-Timer Pygame simulation.
Encodes the actual simulation architecture from `Code/YOLO/darkflow/simulation.py` and `simulation_enhanced.py`.
**Adapted for Indian traffic systems specifications.**

## Core Architecture

### Render Loop (60 FPS target)
```python
# simulation.py:main()
pygame.init()
simulation = pygame.sprite.Group()
clock = pygame.time.Clock()

while running:
    dt = clock.tick(60) / 1000.0  # seconds
    handle_events()
    update_vehicles(dt)
    update_signals(dt)
    render()
    pygame.display.flip()
```

### Vehicle Dynamics
- **Spawning**: Random per-lane, weighted by vehicle type (car/bus/truck/rickshaw/bike/**two_wheeler/cycle/autorickshaw**)
- **Movement**: Car-following model with `gap=12` (stopping), `gap2=12` (moving) - smaller gap tolerated in dense Indian traffic
- **Turning**: 3 rotation angles, midpoint interpolation
- **Speeds** (px/frame): `{'car':2.0, 'bus':1.7, 'truck':1.7, 'autorickshaw':2.3, 'two_wheeler':3.0, 'cycle':3.2, 'tractor':1.5}`

**Vehicle type weights for spawning** (replace default weights):
```python
vehicle_type_weights = {'car': 1.0, 'bus': 1.2, 'truck': 1.3,
                         'two_wheeler': 0.6, 'autorickshaw': 0.8,
                         'cycle': 0.5, 'tractor': 0.3}
```

### Signal Timing Algorithm (Indian Parameters)
```python
# Queue-based adaptive (simulation.py)
# Indian adaptation: MIN_GREEN=7, YELLOW=3.5, ALL_RED=3, MAX_GREEN=50
def set_signal_timing():
    for i in range(4):
        queue = count_vehicles_at_stop_line(direction[i])
        # Indian: weighted queue - two-wheelers count less
        weighted_queue = sum(queue.get(t, 0) * vehicle_weights.get(t, 1.0)
                            for t in vehicle_types)
        green = min(max(weighted_queue * service_time, MIN_GREEN), MAX_GREEN)
        signals[i].green = green
```

### Signal Phases (4-way)
| Phase | Green Directions | Red Directions |
|-------|------------------|----------------|
| 1 | North-South (0,2) | East-West (1,3) |
| 2 | East-West (1,3) | North-South (0,2) |

### Key Indian Adaptations
- **MIN_GREEN=7** (vs 10) - two-wheelers need less green time
- **YELLOW=3.5** (vs 5) - shorter Indian reaction times
- **ALL_RED=3** (vs 2) - extra clearance for common encroachment
- **MAX_GREEN=50** (vs 60) - cap for high-volume Indian intersections
- **Vehicle speeds**: two_wheeler=3.0, cycle=3.2 (fastest in Indian traffic)
- **Gap=12** (vs 15) - smaller gap tolerated in dense traffic
- **Vehicle weights**: two_wheeler=0.6, cycle=0.5 (shorter vehicle, less road space)

### Key Files
- `Code/YOLO/darkflow/simulation.py` - Base simulation (working)
- `Code/YOLO/darkflow/simulation_enhanced.py` - Enhanced with AI controllers
- `Code/YOLO/darkflow/simulation_multi_intersection.py` - Network coordination
- `src/utils/config.py` - Dataclasses: SimulationConfig, AIConfig, VisualConfig

## Integration Patterns

### Gymnasium Wrapper
```python
class TrafficEnv(gym.Env):
    def __init__(self, config):
        self.sim = Simulation(config)
        self.observation_space = spaces.Box(...)  # 4-lane queues + phase
        # Indian: action_space remains Discrete(11) but green duration bounds
        # are enforced by SafetyWrapper (MIN_GREEN=7, MAX_GREEN=50)
        self.action_space = spaces.Discrete(11)   # green time 10-60s in 5s steps

    def step(self, action):
        self.sim.set_green_time(action)
        self.sim.step()
        return obs, reward, done, info
```

### Detection → Queue Pipeline
```python
# detector outputs: [{class, bbox, conf}]
# → project to lanes using config.stop_lines
# → count per lane → EWMA smoothing → queue length
# Indian: use expanded class map from yolov8-tensorrt-patterns (8 classes)
```

## Rules
- Never modify `simulation.py` directly - extend via `simulation_enhanced.py`
- Vehicle spawning uses `random.choices()` with type weights (Indian weights)
- Signal timing MUST respect `MIN_GREEN=7`, `MAX_GREEN=50`, `YELLOW=3.5`, `ALL_RED=3`
- All coordinates in `VisualConfig` - single source of truth
- Use `config.py` dataclasses for all parameters - no magic numbers
- Vehicle type weights: car=1.0, bus=1.2, truck=1.3, two_wheeler=0.6, autorickshaw=0.8, cycle=0.5, tractor=0.3
- Speeds: car=2.0, bus=1.7, truck=1.7, autorickshaw=2.3, two_wheeler=3.0, cycle=3.2, tractor=1.5
- Gap distance: 12 px (smaller than default 15, tolerated in dense Indian traffic)
