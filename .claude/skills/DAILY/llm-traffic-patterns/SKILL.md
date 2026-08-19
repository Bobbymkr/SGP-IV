# LLM Traffic Patterns

Project-specific patterns for LLM-based traffic control.
Based on Traffic-Alpha/VLMLight (dual-branch RL+LLM), AIMSLaboratory/DeepSignal (fine-tuned LLM), and Traffic-Alpha/iLLM-TSC (RL+LLM integration).
**Adapted for Indian traffic systems - prompt localization and road awareness.**

## Dual-Branch Architecture (VLMLight Pattern)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAST RL BRANCH (System 1)                     │
│  ├─ Observation: 4-lane queues + occupancies + phase timer      │
│  ├─ Action: green duration 10-60s in 5s steps (11 actions)       │
│  ├─ Policy: PPO / MAPPO with centralized critic                  │
│  ├─ Inference: 2-5ms (on GPU)                                    │
│  └─ Frequency: every control cycle (1-2s)                        │
├─────────────────────────────────────────────────────────────────┤
│                    SLOW LLM BRANCH (System 2)                     │
│  ├─ Input: high-level state + summary + historical data          │
│  ├─ Prompt: tool-calling format (function calling)               │
│  ├─ Output: {tool: "emergency_stop", args: {...}} OR              │
│  │           {tool: "adjust_phases", args: {green_durations: [...]}}│
│  ├─ Inference: 200-2000ms (depends on model)                      │
│  └─ Frequency: every N cycles (e.g., every 10s)                  │
└─────────────────────────────────────────────────────────────────┘
```

## LLM Prompt Template (Tool-Calling Format) - Indian Localization

**CRITICAL ADAPTATION**: Indian English phrasing, road sign awareness, local traffic customs.

```python
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class GreenDuration(BaseModel):
    """Green duration per phase (0-3)"""
    phase_durations: Dict[int, int] = Field(
        description={
            "Green duration in seconds per phase. "
            "Phase 0: North-South, Phase 1: East-West, "
            "Phase 2: North-South again, Phase 3: East-West again. "
            "Indian adaptation: respects MIN_GREEN=7s, MAX_GREEN=50s "
            "for Indian vehicle mix including two-wheelers."
        },
        default={0: 30, 1: 30, 2: 30, 3: 30}
    )

class EmergencyAction(BaseModel):
    """Emergency override"""
    action: str = Field(description="Type of emergency action")
    reason: str = Field(description="Human-readable reason")
    duration: Optional[int] = Field(
        default=None, 
        description="Duration in seconds (None = until next cycle). "
                    "Indian context: may be shorter due to dense traffic."
    )

class LLMPromptTemplate:
    """Build prompts for LLM traffic control - Indian adapted"""
    
    @staticmethod
    def build_tool_calling_prompt(state_summary: Dict, 
                                   historical_data: Optional[List] = None,
                                   available_tools: Optional[List[str]] = None) -> str:
        tools = available_tools or ["set_green_durations", "emergency_override", "status_query"]
        
        # Indian English phrasing and road awareness
        prompt = f"""You are an AI traffic signal controller deployed in India.

Current intersection state:
- Phase: {state_summary.get('current_phase', '?')}
- Phase timer: {state_summary.get('phase_timer', '?')}s elapsed
- Queues (meters): North={state_summary.get('north_queue', 0):.1f}, 
  South={state_summary.get('south_queue', 0):.1f}, 
  East={state_summary.get('east_queue', 0):.1f}, 
  West={state_summary.get('west_queue', 0):.1f}
- Occupancies 0-1: North={state_summary.get('north_occ', 0):.2f}, 
  South={state_summary.get('south_occ', 0):.2f}, 
  East={state_summary.get('east_occ', 0):.2f}, 
  West={state_summary.get('west_occ', 0):.2f}
- Time of day: {state_summary.get('time_of_day', '?')}s since midnight

Historical data (last 5 cycles):
{historical_data if historical_data else 'No historical data available'}

Available tools: {', '.join(tools)}

TASK: Based on the current state and historical data, decide the action.

RESPOND IN JSON FORMAT with exactly one of the following structures:

Option A: Adjust green durations
{{
  "tool": "set_green_durations",
  "args": {{
    "phase_durations": {{
      0: <int>, 1: <int>, 2: <int>, 3: <int>
    }}
  }}
}}

Option B: Emergency override
{{
  "tool": "emergency_override",
  "args": {{
    "action": "<one of: pause_all, force_switch, prioritize_direction>",
    "reason": "<string>",
    "duration": <int or null>
  }}
}}

Option C: Status query (no action needed)
{{
  "tool": "status_query",
  "args": {{}}
}}

DO NOT include any reasoning text, apologies, or other content. 
Return ONLY the JSON object above.

--- Indian Traffic Context ---
- This intersection handles Indian traffic conditions: high two-wheeler density 
  (2-3x Western equivalents), frequent encroachment at stop lines, variable lane 
  discipline, and common use of horns as communication between drivers.
- Two-wheelers (motorcycles, scooters, bicycles) may pass from either side 
  and often do not stop completely at red signals.
- Vehicle types present: cars, buses, trucks, two-wheelers, autorickshaws, 
  cycles, and sometimes tractors (on suburban routes).
- Seasonal factors may apply: monsoon waterlogging (June-September), fog 
  (winter months), or extreme heat (April-May).
- Priority should be given to emergency vehicles (ambulances, fire trucks) 
  and Delhi Metro/Bus corridors when applicable.
- Consider peak hour patterns: 8-10 AM (commuter influx) and 5-7 PM (return).
- Output in clear, standard English suitable for Indian traffic engineering context.
- Be aware of Indian road signage: speed limits, no-entry, school zones, 
  pedestrian crossings, and variable message signs (VMS).
- ACCEPTABLE response formats include phase durations that may be equal or 
  different per phase, depending on queue lengths. No phase should receive 
  less than 7 seconds (MIN_GREEN) or more than 50 seconds (MAX_GREEN)."""
        return prompt
```

## LLM Integration Layer - Unchanged (core logic same)

The `LLMController` class from the original skill remains valid - only the prompt 
content changes for Indian adaptation. The safety validator and branch router 
also remain the same.

## Safety Validation (Post-LLM Check) - Unchanged

The `LLMSafetyValidator` class from the original skill applies directly - 
Indian adaptations are in the prompt content (bounds enforcement: MIN_GREEN=7, 
MAX_GREEN=50).

## LLM vs RL Decision Policy - Unchanged

The `BranchRouter` class from the original skill applies directly. 
Indian adaptation: you may set `llm_every_n_cycles=5` (vs 10 default) due to 
Indian traffic's higher unpredictability, causing more frequent LLM calls.

## Fine-Tuning Pattern (DeepSignal) - Add Indian Data Consideration

```python
# If we have our own LLM to fine-tune (like DeepSignal):
# 1. Collect expert demonstrations: (state, expert_action) pairs
#    - Expert = CCDA-Light MARL policy after convergence
#    - States: 10-dim vectors (4 lanes × queue + occupancy + phase + timer)
#    - Actions: green duration indices 0-10
#
# 2. Create dataset (add Indian context):
from datasets import Dataset
import json

expert_data = []
for episode in trained_episodes:
    for step in episode.steps:
        expert_data.append({
            "state": step.observation,  # 10-dim
            "action": step.action,     # 0-10 index
            "reward": step.reward,
            "done": step.done,
            "Indian_context": step.get("Indian_context", False)  # NEW flag
        })

dataset = Dataset.from_list(expert_data)

# 3. Fine-tune LLM (e.g., Llama-3.1-8B)
#    - LoRA adapter (rank=8, alpha=16)
#    - 3-5 epochs on expert data
#    - Loss: cross-entropy on action tokens
#
# 4. After fine-tune, use distilled LLM (faster inference)
#    - 2-3x faster than base model
#    - Similar performance to RL baseline
#
# 5. Add Indian-specific evaluation:
#    - Test with two-wheeler-heavy scenarios
#    - Test with monsoon/flood conditions
#    - Test during peak hours (8-10 AM, 5-7 PM)