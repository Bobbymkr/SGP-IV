"""Simulation throughput benchmark — fixed seed, standard config."""

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_traffic.core.simulation.engine import create_intersection, create_simulation


def bench(steps: int = 5000, seed: int = 42) -> dict:
    random.seed(seed)
    sim = create_simulation(
        {
            "time_step": 0.1,
            "max_time": steps * 0.1 + 10,
        }
    )
    sim.add_intersection(
        create_intersection(
            {
                "id": "bench-1",
                "signal_timing": {"NS_green": 30, "NS_yellow": 3, "EW_green": 30, "EW_yellow": 3},
            }
        )
    )
    start = time.perf_counter()
    for _ in range(steps):
        sim.step()
    elapsed = time.perf_counter() - start
    return {
        "steps": steps,
        "elapsed_s": round(elapsed, 3),
        "steps_per_s": int(steps / elapsed),
        "vehicles_completed": sim.stats["total_completed"],
        "avg_waiting_time": round(sim.stats["total_waiting_time"] / max(sim.stats["total_completed"], 1), 2),
        "seed": seed,
    }


if __name__ == "__main__":
    result = bench()
    print(result)
