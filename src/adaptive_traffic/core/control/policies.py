"""Pluggable signal-timing policies (screenshot-in -> green-out).

One seam per decision so future upgrades swap a single adapter:

* HeadwayTable   — per-class discharge seconds, city-overridable (trial-and-error
  calibration lands as data rows, never code branches).
* GreenPolicyPort — weighted discharge: ``startup + sum(n_class * h_class)``.
* OrderPolicyPort — clockwise right-hand rule (default) or legacy argmax.
* CapPolicyPort  — dynamic-by-demand cap from a shared cycle budget.
* EmergencyPort / ManualRegistry — ambulance preempt + human override.
  Rule: an ACTIVE manual protocol on a route suppresses EVP on that route's
  signals; elsewhere EVP still fires. (Operator decision, 2026-09-21.)
* CoordinationPort — MARL-ready slot above single-intersection decide.
  ``Independent`` = today's behavior (no-op); learned policies arrive as
  versioned adapters without touching the intersection loop.

Stdlib only; duck-typed city_profile (reads ``discharge_headways`` /
``cycle_budget_s`` when present, else built-in defaults).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Headways: per-class discharge seconds (PCE defaults; cities override via
# CityProfile.discharge_headways after trial-and-error calibration).
# ---------------------------------------------------------------------------

DEFAULT_HEADWAYS: Dict[str, float] = {
    "two_wheeler": 1.0,
    "car": 2.0,
    "autorickshaw": 2.0,
    "cycle": 1.0,
    "tractor": 2.5,
    "bus": 3.2,
    "truck": 3.2,
    "bus_pedigree": 3.2,
}

# Detector/model class names -> headway keys (6-class contract + legacy names).
CLASS_ALIASES: Dict[str, str] = {
    "car": "car",
    "motorcycle": "two_wheeler",
    "moto": "two_wheeler",
    "two_wheeler": "two_wheeler",
    "bus": "bus",
    "truck": "truck",
    "bicycle": "cycle",
    "cycle": "cycle",
    "auto": "autorickshaw",
    "autorickshaw": "autorickshaw",
    "three-wheeler": "autorickshaw",
    "tractor": "tractor",
    "bus_pedigree": "bus_pedigree",
    "van": "car",
    "lcv": "truck",
    "muv": "car",
    "suv": "car",
    "sedan": "car",
    "hatchback": "car",
}


def normalize_class(name: str) -> str:
    """Map any detector/estimator class name to a headway-table key."""
    return CLASS_ALIASES.get((name or "").lower(), "car")


class HeadwayTable:
    """Lookup of per-class discharge seconds with city overrides."""

    def __init__(self, overrides: Optional[Dict[str, float]] = None):
        table = dict(DEFAULT_HEADWAYS)
        for k, v in (overrides or {}).items():
            table[normalize_class(k)] = float(v)
        self.table = table

    @classmethod
    def from_city_profile(cls, profile: Any) -> "HeadwayTable":
        overrides = getattr(profile, "discharge_headways", None) or {}
        return cls(dict(overrides))

    def get(self, class_name: str) -> float:
        return self.table.get(normalize_class(class_name), 2.0)


# ---------------------------------------------------------------------------
# Green policy: how long to serve a queued group.
# ---------------------------------------------------------------------------


class GreenPolicyPort(ABC):
    """Unclamped green seconds for one compatibility group."""

    @abstractmethod
    def compute(
        self,
        class_counts: Dict[str, int],
        headways: HeadwayTable,
        startup_s: float,
    ) -> float:
        pass


class WeightedDischargeGreen(GreenPolicyPort):
    """startup + sum(n_class * h_class): a bus costs more than a bike."""

    def compute(self, class_counts, headways, startup_s):
        total = sum(int(n) * headways.get(c) for c, n in class_counts.items())
        return startup_s + total


class FlatHeadwayGreen(GreenPolicyPort):
    """Legacy: flat seconds per vehicle regardless of class."""

    def __init__(self, headway_s: float = 2.0):
        self.headway_s = headway_s

    def compute(self, class_counts, headways, startup_s):
        return startup_s + sum(int(n) for n in class_counts.values()) * self.headway_s


# ---------------------------------------------------------------------------
# Order policy: which group goes next.
# ---------------------------------------------------------------------------


class OrderPolicyPort(ABC):
    """Return next group index, or -1 to hold position (nothing waiting)."""

    @abstractmethod
    def next(
        self,
        current_group: int,
        demands: List[int],
        waits: List[int],
    ) -> int:
        pass


class ClockwiseOrder(OrderPolicyPort):
    """Right-hand rule: next non-empty group clockwise; hold when all empty."""

    def next(self, current_group, demands, waits):
        n = len(demands)
        for step in range(1, n + 1):
            idx = (current_group + step) % n
            if demands[idx] > 0:
                return idx
        return -1


class ArgmaxOrder(OrderPolicyPort):
    """Legacy: max demand with starvation bound (full rotation forces service)."""

    def next(self, current_group, demands, waits):
        n = len(demands)
        forced = [i for i in range(n) if demands[i] > 0 and waits[i] >= n]
        if forced:
            return max(forced, key=lambda i: waits[i])
        best, best_d = -1, 0
        for i, d in enumerate(demands):
            if d > best_d:
                best, best_d = i, d
        return best


# ---------------------------------------------------------------------------
# Cap policy: dynamic-by-demand upper bound so one approach never starves rest.
# ---------------------------------------------------------------------------


class CapPolicyPort(ABC):
    """Return the allowed ceiling; the engine clamps base green into it."""

    @abstractmethod
    def cap(
        self,
        base_green: float,
        share: float,
        floor_s: float,
        city_max_s: float,
        cycle_budget_s: float,
    ) -> float:
        pass


class DemandShareCap(CapPolicyPort):
    """ceiling = max(floor, min(city_max, cycle_budget * demand_share))."""

    def cap(self, base_green, share, floor_s, city_max_s, cycle_budget_s):
        if share <= 0:
            return city_max_s
        return max(floor_s, min(city_max_s, cycle_budget_s * share))


class FixedMaxCap(CapPolicyPort):
    """Legacy: ceiling is always the city max."""

    def cap(self, base_green, share, floor_s, city_max_s, cycle_budget_s):
        return city_max_s


# ---------------------------------------------------------------------------
# Factories (mirror DetectorPort.create string-key style).
# ---------------------------------------------------------------------------


def create_headways(
    config: Optional[Dict[str, Any]] = None,
    city_profile: Any = None,
) -> HeadwayTable:
    overrides: Dict[str, float] = {}
    if city_profile is not None:
        overrides.update(getattr(city_profile, "discharge_headways", None) or {})
    overrides.update((config or {}).get("discharge_headways", {}) or {})
    return HeadwayTable(overrides)


def create_green_policy(config: Optional[Dict[str, Any]] = None) -> GreenPolicyPort:
    kind = (config or {}).get("green_policy", "weighted")
    if kind == "flat":
        return FlatHeadwayGreen(headway_s=float((config or {}).get("discharge_headway_s", 2.0)))
    return WeightedDischargeGreen()


def create_order_policy(config: Optional[Dict[str, Any]] = None) -> OrderPolicyPort:
    if (config or {}).get("order_policy", "clockwise") == "argmax":
        return ArgmaxOrder()
    return ClockwiseOrder()


def create_cap_policy(config: Optional[Dict[str, Any]] = None) -> CapPolicyPort:
    if (config or {}).get("cap_policy", "demand_share") == "fixed_max":
        return FixedMaxCap()
    return DemandShareCap()


# ---------------------------------------------------------------------------
# Emergency (ambulance) + manual (human/dignitary) priority.
#
# Rule: an ACTIVE manual protocol on a route suppresses EVP preempts on that
# route's signals; EVP still fires everywhere else. Manual > EVP only in the
# sense of route-scoped suppression — otherwise each fires on its own merit.
# ---------------------------------------------------------------------------


@dataclass
class EmergencyEvent:
    """One detected emergency vehicle demanding a green."""

    intersection_id: str
    group_idx: int
    confidence: float = 1.0
    mode: str = "immediate"  # immediate | next_cycle | coordinated
    vehicle_id: str = ""


@dataclass
class ManualProtocol:
    """Pre-approved human override (e.g. dignitary route, IAS/IPS sign-off)."""

    route_id: str
    intersection_ids: List[str]
    group_idxs: List[int]  # groups held green on each listed intersection
    approval_id: str
    signer_role: str = ""
    operator: str = ""
    greens: Dict[int, float] = field(default_factory=dict)  # optional fixed greens


class ManualRegistry:
    """In-memory active-protocol set + append-only audit log.

    Persistence (DB/JWT approval verification) is a future adapter concern;
    the suppression rule lives here so every caller honors it identically.
    """

    def __init__(self):
        self.active: Dict[str, ManualProtocol] = {}  # approval_id -> protocol
        self.audit: List[Dict[str, Any]] = []

    def activate(self, protocol: ManualProtocol) -> str:
        self.active[protocol.approval_id] = protocol
        self.audit.append(
            {
                "event": "activate",
                "approval_id": protocol.approval_id,
                "route_id": protocol.route_id,
            }
        )
        return protocol.approval_id

    def revoke(self, approval_id: str, reason: str = "") -> bool:
        if approval_id in self.active:
            del self.active[approval_id]
            self.audit.append({"event": "revoke", "approval_id": approval_id, "reason": reason})
            return True
        return False

    def covers(self, intersection_id: str, group_idx: Optional[int] = None) -> bool:
        """True when a manual protocol currently owns this intersection.

        Route-scoped (operator rule): an active protocol suppresses EVP on ALL
        of its route's signals, not just the held groups. group_idx is accepted
        for call-site compat and ignored.
        """
        return any(intersection_id in p.intersection_ids for p in self.active.values())


def resolve_priority(
    intersection_id: str,
    group_idx: Optional[int],
    manual: Optional[ManualRegistry],
    emergency: Optional[EmergencyEvent],
) -> str:
    """Return 'manual' | 'evp' | 'adaptive' for one intersection.

    Manual protocol on the route suppresses EVP there (operator rule);
    an emergency for a *different* intersection is unaffected.
    """
    if manual is not None and manual.covers(intersection_id, group_idx):
        return "manual"
    if (
        emergency is not None
        and emergency.intersection_id == intersection_id
        and (manual is None or not manual.covers(intersection_id, emergency.group_idx))
    ):
        return "evp"
    return "adaptive"


# ---------------------------------------------------------------------------
# Coordination slot (MARL-ready; Independent = today's single-junction loop).
# ---------------------------------------------------------------------------


class CoordinationPort(ABC):
    """Propose per-cycle biases; intersection loop may ignore on failure."""

    @abstractmethod
    def bias(self, intersection_id: str, demands: List[int]) -> Dict[str, float]:
        pass


class IndependentCoordination(CoordinationPort):
    """No cross-junction coupling — current behavior, zero regression risk."""

    def bias(self, intersection_id, demands):
        return {}
