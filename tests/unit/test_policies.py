"""Policy ports: weighted greens, clockwise order, dynamic cap, priority rule.

Fast by design: no model, no camera — pure policy math + canned estimates.
"""

import pytest

from adaptive_traffic.config.city_profile import get_city_profile
from adaptive_traffic.core.analytics.queue_estimator import QueueEstimator
from adaptive_traffic.core.closed_loop import create_loop, decide, inject_estimate
from adaptive_traffic.core.analytics.queue_estimator import LaneQueue, QueueEstimate
from adaptive_traffic.core.control.policies import (
    ArgmaxOrder,
    ClockwiseOrder,
    DemandShareCap,
    EmergencyEvent,
    HeadwayTable,
    ManualProtocol,
    ManualRegistry,
    WeightedDischargeGreen,
    create_cap_policy,
    create_green_policy,
    create_order_policy,
    normalize_class,
    resolve_priority,
)
from adaptive_traffic.core.domain import VehicleDetection


def _det(class_id, class_name, x1):
    return VehicleDetection(
        class_id=class_id,
        class_name=class_name,
        confidence=0.9,
        bbox=(x1, 300, x1 + 50, 460),
        center=(x1 + 25, 380),
    )


def test_weighted_discharge_math():
    green = WeightedDischargeGreen().compute(
        {"bus": 2, "two_wheeler": 3}, HeadwayTable(), startup_s=2.0
    )
    assert green == pytest.approx(2 * 3.2 + 3 * 1.0 + 2.0)


def test_class_aliases_and_city_override():
    assert normalize_class("motorcycle") == "two_wheeler"
    assert normalize_class("auto") == "autorickshaw"
    assert normalize_class("bicycle") == "cycle"
    profile = get_city_profile("bangalore")
    table = HeadwayTable.from_city_profile(profile)
    assert table.get("car") == 2.0
    custom = HeadwayTable.from_city_profile(type("P", (), {"discharge_headways": {"car": 2.5}})())
    assert custom.get("car") == 2.5 and custom.get("bus") == 3.2


def test_factory_defaults_are_new_behavior_with_legacy_escape():
    assert isinstance(create_green_policy({}), WeightedDischargeGreen)
    assert isinstance(create_order_policy({}), ClockwiseOrder)
    assert isinstance(create_cap_policy({}), DemandShareCap)
    assert isinstance(create_order_policy({"order_policy": "argmax"}), ArgmaxOrder)


def test_clockwise_skips_empty_and_holds():
    order = ClockwiseOrder()
    assert order.next(0, [5, 0, 3], [0, 0, 0]) == 2
    assert order.next(2, [5, 0, 3], [0, 0, 0]) == 0
    assert order.next(0, [0, 0], [0, 0]) == -1


def test_argmax_parity_with_legacy_selection():
    order = ArgmaxOrder()
    assert order.next(0, [2, 9], [0, 0]) == 1
    assert order.next(1, [4, 4], [2, 0]) == 0  # starvation bound fires
    assert order.next(0, [0, 0], [0, 0]) == -1


def test_demand_share_cap():
    cap = DemandShareCap()
    assert cap.cap(80.0, 0.1, 15.0, 70.0, 120.0) == pytest.approx(15.0)
    assert cap.cap(34.0, 1.0, 15.0, 70.0, 120.0) == pytest.approx(70.0)
    assert cap.cap(20.0, 0.0, 15.0, 70.0, 120.0) == pytest.approx(70.0)


def test_manual_protocol_suppresses_evp_on_its_route():
    reg = ManualRegistry()
    reg.activate(
        ManualProtocol(
            route_id="vip-1",
            intersection_ids=["loop-1"],
            group_idxs=[0],
            approval_id="IAS-42",
            signer_role="IAS",
            operator="ctrl-1",
        )
    )
    evp = EmergencyEvent(intersection_id="loop-1", group_idx=1)
    assert resolve_priority("loop-1", 0, reg, evp) == "manual"
    assert resolve_priority("loop-1", 1, reg, evp) == "manual"
    assert (
        resolve_priority(
            "other-ix", None, reg, EmergencyEvent(intersection_id="other-ix", group_idx=0)
        )
        == "evp"
    )
    assert resolve_priority("loop-1", 1, None, evp) == "evp"
    assert resolve_priority("loop-1", 1, reg, None) == "manual"
    assert resolve_priority("loop-1", 1, None, None) == "adaptive"


def test_estimator_reports_by_class():
    est = QueueEstimator(get_city_profile("bangalore"))
    dets = [_det(0, "car", 50), _det(0, "car", 300), _det(1, "bus", 500)]
    out = est.estimate_from_detections(dets)
    assert out.total_vehicles == 3
    assert out.by_class["south"] == {"car": 2, "bus": 1}


def test_mixed_class_green_beats_flat_count():
    sim, ix_id = create_loop(city_profile=get_city_profile("bangalore"))
    est = QueueEstimate(
        intersection_id=ix_id,
        timestamp=0.0,
        lanes=[],
        by_direction={"south": LaneQueue("south_0", "south", 10, 100.0, 10.0, 0.9)},
        total_vehicles=10,
        total_length_m=100.0,
        by_class={"south": {"bus": 10}},
    )
    inject_estimate(sim, ix_id, est)
    plan = decide(sim, ix_id)
    # 10 buses weighted: 2 + 10*3.2 = 34 (flat count would give 22)
    assert plan["greens"][0] == pytest.approx(34.0)
    assert plan["mode"] == "adaptive"


def test_manual_mode_holds_and_reports():
    profile = get_city_profile("bangalore")
    sim, ix_id = create_loop(city_profile=profile)
    reg = ManualRegistry()
    reg.activate(
        ManualProtocol(
            route_id="vip-1", intersection_ids=[ix_id], group_idxs=[], approval_id="IPS-7"
        )
    )
    plan = decide(
        sim, ix_id, manual=reg, emergency=EmergencyEvent(intersection_id=ix_id, group_idx=1)
    )
    assert plan["mode"] == "manual"
