import json

import pytest
import requests

from ffapp.sleeper import PROJECTIONS_BASE, SleeperClient, SleeperError
from tests.fixtures import DYNASTY, FixtureSession


class FakeResponse:
    def __init__(self, status_code, payload=None, text="not json"):
        self.status_code = status_code
        self._payload = payload
        self._text = text

    def json(self):
        if self._payload is None:
            raise ValueError(self._text)
        return self._payload


class ScriptedSession:
    """Returns the scripted responses in order; raises exceptions placed in the script."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def get(self, url, *, timeout, headers):
        self.calls.append((url, timeout, headers))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClock:
    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def make_client(script, **kwargs):
    session = ScriptedSession(script)
    clock = FakeClock()
    client = SleeperClient(session, sleep=clock.sleep, clock=clock.clock, **kwargs)
    return client, session, clock


def test_success_returns_json_and_sets_user_agent():
    client, session, _ = make_client([FakeResponse(200, {"week": 10})])
    assert client.state() == {"week": 10}
    url, timeout, headers = session.calls[0]
    assert url == "https://api.sleeper.app/v1/state/nfl"
    assert timeout == 30.0
    assert headers["User-Agent"].startswith("ffapp/")


def test_endpoint_urls():
    client, session, _ = make_client([FakeResponse(200, [])] * 6)
    client.league("1")
    client.users("1")
    client.rosters("1")
    client.matchups("1", 7)
    client.winners_bracket("1")
    client.losers_bracket("1")
    assert [c[0].removeprefix("https://api.sleeper.app/v1") for c in session.calls] == [
        "/league/1",
        "/league/1/users",
        "/league/1/rosters",
        "/league/1/matchups/7",
        "/league/1/winners_bracket",
        "/league/1/losers_bracket",
    ]


def test_projections_url_lists_all_positions():
    client, session, _ = make_client([FakeResponse(200, [])])
    client.projections("2026", 11)
    url = session.calls[0][0]
    assert url.startswith(f"{PROJECTIONS_BASE}/2026/11?season_type=regular")
    for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
        assert f"position%5B%5D={pos}" in url


def test_non_retryable_status_raises_immediately():
    client, session, _ = make_client([FakeResponse(404, None)])
    with pytest.raises(SleeperError) as info:
        client.league("missing")
    assert info.value.status == 404
    assert len(session.calls) == 1


def test_retries_transient_failures_with_backoff():
    client, session, clock = make_client(
        [FakeResponse(503, None), requests.ConnectionError("reset"), FakeResponse(200, {"ok": True})]
    )
    assert client.state() == {"ok": True}
    assert len(session.calls) == 3
    # backoff sleeps of 0.5 then 1.0 (throttle sleeps are separate and smaller)
    assert [s for s in clock.slept if s >= 0.5] == [0.5, 1.0]


def test_gives_up_after_retries():
    client, session, _ = make_client([FakeResponse(500, None)] * 4, retries=3)
    with pytest.raises(SleeperError, match="after 4 attempts"):
        client.state()
    assert len(session.calls) == 4


def test_invalid_json_raises():
    client, _, _ = make_client([FakeResponse(200, None, text="<html>")])
    with pytest.raises(SleeperError, match="invalid JSON"):
        client.state()


def test_throttle_spaces_requests():
    client, _, clock = make_client([FakeResponse(200, {})] * 3, min_interval=0.2)
    client.state()
    client.state()
    client.state()
    # the clock does not advance on its own, so each follow-up request waits the full interval
    assert clock.slept == [pytest.approx(0.2), pytest.approx(0.2)]


def test_fixture_session_serves_recorded_responses():
    client = SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None)
    league = client.league(DYNASTY["2025"])
    assert league["season"] == "2025"
    assert len(client.matchups(DYNASTY["2025"], 15)) == 12
    rows = client.projections("2025", 1)
    assert isinstance(rows, list) and rows[0]["season"] == "2025"
    with pytest.raises(SleeperError) as info:
        client.league("0000")
    assert info.value.status == 404
