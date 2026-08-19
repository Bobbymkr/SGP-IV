# MARL Coordination Patterns

Project-specific patterns for multi-agent reinforcement learning coordination.
Based on Traffic-Alpha/CCDA-Light, MAPPO with centralized critic, and Tianshou/RLlib frameworks.
**Adapted for Indian traffic systems - denser neighbor networks and faster intervention.**

## Multi-Agent Framework Choices

| Framework | Best For | Key Features | Trade-offs |
|-----------|----------|--------------|------------|
| **Tianshou** | Research, rapid prototyping | Simple API, on-policy/off-policy, reparameterization | Less mature ecosystem |
| **RLlib** (Ray) | Production, scaling | Distributed training, fault-tolerance, multi-agent out-of-box | Higher overhead, Ray cluster needed |
| **MAPPOTorch** (SB3) | Simple multi-intersection | PyTorch-native, easy GPU, good docs | Limited MARL algorithms |
| **Custom** (vanilla PyTorch) | Full control | Complete freedom, no dependencies | Need to implement everything |

I'll use **Tianshou** for this project - it's the sweet spot for research + production hybrid workloads.

## Architecture: CCDA-Light (Centralized Critic Decentralized Actors) - Indian Adapted

```
Each intersection agent has:
- Own observation: 4 lanes × (queue + occupancy) + phase + timer = 10 dims (or 12/16 if 3-4 lanes)
- Own action: green duration 10-60s in 5s steps = 11 actions
- Shared neighbor info: phases + queues of neighboring intersections
- Communication: periodic gossip (every intervention_freq seconds = 7s Indian)

Global orchestrator maintains:
- Replay buffer per agent
- Target network updates
- Intervention scheduler
```

### Agent Class (Tianshou) - Indian Adaptation

```python
import torch
import torch.nn as nn
import numpy as np
from torch.distributions import Categorical

class Actor(nn.Module):
    """Decentralized actor - one per intersection"""
    def __init__(self, state_dim=8, action_dim=11, hidden=128, num_lanes=4):
        super().__init__()
        self.num_lanes = num_lanes  # Indian: 4 vs 3-lane variants
        # Indian: state_dim may be 8 (4 lanes × 2 features) or 12 (6 lanes) or 16 (8 lanes)
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim)
        )
    
    def forward(self, x):
        return self.net(x)
    
    def get_action(self, x, temp=1.0):
        logits = self.forward(x) / temp
        probs = Categorical(logits=logits)
        action = probs.sample()
        return action, probs.log_prob(action)

class Critic(nn.Module):
    """Centralized critic - shared across all intersections"""
    def __init__(self, state_dim=32, action_dim=44, hidden=256, num_neighbors=3):
        """
        state_dim: 8 states × (1 + num_neighbors) or 12/16 for Indian 3-4 lane roads
        action_dim: 11 actions × (1 + num_neighbors)
        """
        super().__init__()
        # State-action value function
        self.net = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1)
        )
    
    def forward(self, state, action):
        x = torch.cat([state, action], dim=-1)
        return self.net(x).squeeze(-1)

class MARLAgent:
    """One agent per intersection - Indian adapted"""
    def __init__(self, agent_id, state_dim=8, action_dim=11, num_neighbors=3, 
                 num_lanes=4, intervention_freq=7):
        """
        Indian adaptation:
        - num_lanes: 3 or 4 (vs 2 in Western)
        - intervention_freq: 7s (vs 10s Western) - more frequent due to higher volatility
        - num_neighbors: often 3-4 in dense Indian grid (vs 1-2 sparser West)
        """
        self.agent_id = agent_id
        self.num_neighbors = num_neighbors
        self.num_lanes = num_lanes
        self.intervention_freq = intervention_freq  # 7s Indian default
        self.last_intervention = -self.intervention_freq
        
        # Actor (local, decentralized) - state_dim accounts for num_lanes
        # If num_lanes=4: state_dim = 8 (4×2); if 3: state_dim = 6; if 8: state_dim = 16
        actual_state_dim = num_lanes * 2  # 6 for 3-lane, 8 for 4-lane
        self.actor = Actor(actual_state_dim, action_dim)
        self.actor_optim = torch.optim.Adam(self.actor.parameters(), lr=3e-4)
        
        # Target actor
        self.target_actor = Actor(actual_state_dim, action_dim)
        self.target_actor.load_state_dict(self.actor.state_dict())
        
        # Critic (centralized) - takes all intersections' states
        total_state_dim = actual_state_dim * (1 + num_neighbors)
        total_action_dim = action_dim * (1 + num_neighbors)
        self.critic = Critic(total_state_dim, total_action_dim)
        self.critic_optim = torch.optim.Adam(self.critic.parameters(), lr=3e-4)
        
        # Experience buffer
        self.buffer = []
        self.gamma = 0.99
        self.tau = 0.005  # soft update coefficient
        
        # Intervention frequency (Indian: 7s)
        self.last_intervention_time = -self.intervention_freq
    
    def _build_input(self, state: dict, neighbors_states: list):
        """Build full state+action vector for critic - accounts for num_lanes"""
        # Own state: num_lanes × 2 features (queue + occupancy)
        actual_state_dim = self.num_lanes * 2
        s = torch.FloatTensor(list(state.values())).unsqueeze(0)
        
        # Neighbors' states - each has same num_lanes structure
        for ns in neighbors_states:
            # Ensure neighbor state has same number of features
            ns_list = list(ns.values())
            if len(ns_list) != actual_state_dim:
                # Pad or trim to match
                if len(ns_list) < actual_state_dim:
                    ns_list = ns_list + [0.0] * (actual_state_dim - len(ns_list))
                else:
                    ns_list = ns_list[:actual_state_dim]
            s = torch.cat([s, torch.FloatTensor(ns_list).unsqueeze(0)], dim=-1)
        
        return s
    
    def select_action(self, state, neighbors_states=None, eval_mode=False):
        """Select action using actor network"""
        with torch.no_grad():
            # Build actor input (own state only for decentralized)
            actual_state_dim = self.num_lanes * 2
            s = torch.FloatTensor(
                [state.get(f'lane_{i}_queue', 0) if i < self.num_lanes else 0 
                 for i in range(self.num_lanes)] + 
                [state.get(f'lane_{i}_occ', 0) if i < self.num_lanes else 0 
                 for i in range(self.num_lanes)]
            ).unsqueeze(0)
            # Also add phase and timer
            s = torch.cat([s, 
                          torch.FloatTensor([state.get('current_phase', 0), 
                                            state.get('phase_timer', 0)]).unsqueeze(0)], dim=-1)
            
            logits = self.actor(s)
            
            if eval_mode:
                action = logits.argmax(-1)
            else:
                # Epsilon-greedy exploration
                if np.random.random() < 0.1:  # explore
                    action = torch.randint(0, 11, (1,)).item()
                else:
                    action = logits.argmax(-1).item()
        
        # Map to green duration
        actions = list(range(10, 61, 5))  # [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        green_duration = actions[action]
        
        return green_duration, action
    
    def learn(self, batch, buffer_size):
        """Learn from batch of experiences - Indian adaptation note"""
        states, actions, rewards, next_states, dones = batch
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)  # action indices
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)
        
        # --- Actor Update (policy gradient) ---
        # Select action using current actor
        logits = self.actor(states)
        action_probs = torch.softmax(logits, dim=-1)
        selected_log_probs = torch.log(action_probs.gather(1, actions.unsqueeze(1)) + 1e-8)
        
        # Select next action using target actor
        with torch.no_grad():
            next_logits = self.target_actor(next_states)
            next_actions = next_logits.argmax(-1)
            next_selected_log_probs = torch.log(
                torch.softmax(next_logits, dim=-1).gather(1, next_actions.unsqueeze(1)) + 1e-8
            )
            
            # Compute TD target
            q_next = self.critic(next_states, next_selected_log_probs.unsqueeze(1))
            td_target = rewards + self.gamma * q_next * (1 - dones)
        
        # Compute advantage (GAE)
        # ... (simplified for this excerpt)
        
        # --- Critic Update ---
        # Get actions from actors for critic input
        with torch.no_grad():
            actor_logits = self.actor(states)
            actor_actions = torch.zeros_like(actions).long()
        
        # Critic targets
        td_target = rewards + self.gamma * self.critic(
            next_states, 
            torch.zeros_like(actor_actions).unsqueeze(1)  # placeholder
        ) * (1 - dones)
        
        critic_loss = nn.MSELoss()(
            self.critic(states, torch.zeros_like(actions).unsqueeze(1)),
            td_target.detach()
        )
        
        self.critic_optim.zero_grad()
        critic_loss.backward()
        self.critic_optim.step()
        
        # --- Soft Update Target Networks ---
        for target_param, param in zip(self.target_actor.parameters(), self.actor.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)
```

### Intervention Scheduler (CCDA-Light, Indian Frequency)

```python
class InterventionScheduler:
    """CCDA-Light: periodically intervene to escape local optima - Indian adapted"""
    def __init__(self, freq=7, intervention_types=None):
        """
        Indian adaptation: freq=7s vs 10s Western
        Indian intersections have higher traffic volatility, need more frequent escapes
        """
        self.freq = freq  # seconds between interventions
        self.last_intervention = -freq
        self.intervention_types = intervention_types or ['phase_switch', 'duration_adjust', 'all_red']
    
    def check_intervention(self, current_phase, phase_timer, agent_id):
        if phase_timer - self.last_intervention >= self.freq:
            self.last_intervention = phase_timer
            return self._pick_intervention()
        return None
    
    def _pick_intervention(self):
        intervention = np.random.choice(self.intervention_types)
        if intervention == 'phase_switch':
            return {'type': 'switch_phase', 'target': np.random.randint(4)}
        elif intervention == 'duration_adjust':
            return {'type': 'adjust_duration', 'delta': np.random.randint(-5, 6)}
        elif intervention == 'all_red':
            return {'type': 'all_red', 'duration': 3}  # Indian: 3s vs 2s
        return None
```

## Rules

- **State dim**: 8 (= 4 lanes × 2 features: queue_normalized, occupancy) or 12 (= 6 lanes) or 16 (= 8 lanes) for Indian 3-4 lane roads
- **Action dim**: 11 (= green duration 10-60s in 5s steps)
- **Decentralized**: each agent only sees its own intersection + neighbor comms (Indian: neighbors often 3-4 in dense grid)
- **Centralized**: critic sees all intersections (for credit assignment)
- **Experience replay**: store (s, a, r, s', done) tuples
- **PPO clipped objective**: L^CLIP(θ) = min(r(θ)Â(Q̂(φ) - ε), r(θ)Â(Q̂(φ) + ε)ε)
  where r(θ) = π_θ(a|s)/π_old(a|s), Â = advantage estimate
- **γ (discount) = 0.99**, **τ (GAE) = 0.95**, **λ (GAE lambda) = 0.95**
- **Intervention frequency: 7s** (CCDA-Light Indian default vs 10s Western)
- **Neighbors**: share phase + queue info via UDP broadcast (Indian: denser grid, more neighbors)
- **All agents use same network architecture** (homogeneous) - but state_dim varies by num_lanes
- **Evaluation**: ε-greedy with ε anneal from 1.0 → 0.05 over 100k steps
- **Model save**: every 10k steps + best-val
- **Convergence check**: stop if avg reward doesn't improve 50 epochs
- **Num lanes per approach**: 3 (default Indian) or 4 (major Mumbai/Delhi intersections)
- **Neighbor count**: 3 (typical Indian grid) or 4 (dense metro like Kolkata)
- **Intervention delta**: duration_adjust delta range can be wider: np.random.randint(-8, 8) 
  for Indian (larger adjustments needed due to higher volatility)