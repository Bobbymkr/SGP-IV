"""The UI API table must match the routes the FastAPI app really serves."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from adaptive_traffic.ui.views.advanced import API_ROUTES  # noqa: E402


def _app_paths():
    from adaptive_traffic.api.main import app

    return set(app.openapi()["paths"])


def test_listed_routes_are_served_by_the_api():
    served = _app_paths()
    missing = [f"{m} {p}" for m, p, _ in API_ROUTES if p not in served]
    assert not missing, f"UI lists routes the API does not serve: {missing}"


def test_listed_methods_are_known_verbs():
    assert {m for m, _, _ in API_ROUTES} <= {"GET", "POST", "PUT", "DELETE"}


def test_every_served_route_is_listed():
    listed = {p for _, p, _ in API_ROUTES}
    unlisted = sorted(_app_paths() - listed)
    assert not unlisted, f"API serves routes the UI does not list: {unlisted}"
