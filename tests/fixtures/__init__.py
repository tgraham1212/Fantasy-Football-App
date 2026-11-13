"""Recorded Sleeper API responses, laid out by endpoint path.

sleeper/league/<id>.json                 GET /v1/league/<id>
sleeper/league/<id>/users.json           GET /v1/league/<id>/users
sleeper/league/<id>/rosters.json         GET /v1/league/<id>/rosters
sleeper/league/<id>/matchups/<week>.json GET /v1/league/<id>/matchups/<week>
sleeper/league/<id>/winners_bracket.json GET /v1/league/<id>/winners_bracket
sleeper/league/<id>/losers_bracket.json  GET /v1/league/<id>/losers_bracket
sleeper/state/nfl.json                   GET /v1/state/nfl
sleeper/projections/<season>/<week>.json GET projections/nfl/<season>/<week> (trimmed)

Recorded 2026-11-13. Dynasty ("Taco Tuesdays") league IDs by season:
2022 780973042250809344, 2023 939158991781838848, 2024 1069001128785944576,
2025 1204820704843792384, 2026 1339662153812025344.
Redraft ("Chris Carter's Fall Guys"): 2025 1257462631510315008, 2026 1389347876550770688.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

FIXTURES_ROOT = Path(__file__).resolve().parent
SLEEPER_ROOT = FIXTURES_ROOT / "sleeper"

DYNASTY = {
    "2022": "780973042250809344",
    "2023": "939158991781838848",
    "2024": "1069001128785944576",
    "2025": "1204820704843792384",
    "2026": "1339662153812025344",
}
REDRAFT = {
    "2025": "1257462631510315008",
    "2026": "1389347876550770688",
}


def load(relative: str):
    """Load a fixture by its path under tests/fixtures/sleeper, e.g. ``league/123.json``."""
    return json.loads((SLEEPER_ROOT / relative).read_text(encoding="utf-8"))


class _FixtureResponse:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no body")
        return self._payload


class FixtureSession:
    """A stand-in for ``requests.Session`` that serves recorded responses by URL.

    Unknown URLs get a 404. Every call is recorded in ``calls`` so tests can
    count requests. ``overrides`` maps a fixture-relative path to a payload (or
    an int status code) to inject failures or edited data for one test.
    """

    def __init__(self, overrides: dict | None = None):
        self.calls: list[str] = []
        self.overrides = overrides or {}

    @staticmethod
    def fixture_path(url: str) -> str | None:
        path = urlparse(url).path
        if path.startswith("/v1/league/"):
            parts = path.removeprefix("/v1/league/").split("/")
            if len(parts) == 1:
                return f"league/{parts[0]}.json"
            if len(parts) == 2 and parts[1] in {"users", "rosters", "winners_bracket", "losers_bracket"}:
                return f"league/{parts[0]}/{parts[1]}.json"
            if len(parts) == 3 and parts[1] == "matchups":
                return f"league/{parts[0]}/matchups/{parts[2]}.json"
            return None
        if path.startswith("/v1/state/"):
            return f"state/{path.removeprefix('/v1/state/')}.json"
        if path.startswith("/projections/nfl/"):
            season, week = path.removeprefix("/projections/nfl/").split("/")
            return f"projections/{season}/{week}.json"
        return None

    def get(self, url: str, *, timeout: float, headers: dict[str, str]):
        self.calls.append(url)
        relative = self.fixture_path(url)
        if relative is None:
            return _FixtureResponse(404)
        if relative in self.overrides:
            payload = self.overrides[relative]
            if isinstance(payload, int):
                return _FixtureResponse(payload)
            return _FixtureResponse(200, payload)
        file = SLEEPER_ROOT / relative
        if not file.exists():
            return _FixtureResponse(404)
        return _FixtureResponse(200, json.loads(file.read_text(encoding="utf-8")))
