from datetime import datetime, timezone

import pytest

from ffapp.schedule import Schedule, ScheduleError, parse_scoreboard, refresh_schedule, team
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from tests.fixtures import FixtureSession, load


def client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_parse_scoreboard_maps_states_teams_and_byes():
    week10 = parse_scoreboard(load("espn/scoreboard/10.json"))
    week11 = parse_scoreboard(load("espn/scoreboard/11.json"))
    assert len(week10["games"]) == 14 and len(week11["games"]) == 13
    assert {g["state"] for g in week10["games"]} == {"final"} and {g["state"] for g in week11["games"]} == {"scheduled"}
    teams10 = {t for g in week10["games"] for t in (g["home"], g["away"])}
    assert "WAS" in teams10 and "WSH" not in teams10  # ESPN's WSH stored under Sleeper's WAS
    assert week10["byes"] == ["CHI", "DEN", "PHI", "TB"]
    assert week11["games"][0] == {"home": "HOU", "away": "IND", "kickoff_utc": "2026-11-20T01:15:00+00:00", "state": "scheduled"}
    assert [g["kickoff_utc"] for g in week11["games"]] == sorted(g["kickoff_utc"] for g in week11["games"])


@pytest.mark.parametrize("payload", [[], {"events": [{"id": "1"}]}, {"events": [{"date": "x", "status": {"type": {"state": "pre"}}, "competitions": [{"competitors": []}]}]}])
def test_parse_scoreboard_rejects_unexpected_shapes(payload):
    with pytest.raises(ScheduleError):
        parse_scoreboard(payload)


def test_team_aliases():
    assert team("WSH") == "WAS" and team("jac") == "JAX" and team("KC") == "KC"


def test_refresh_stores_current_and_next_week(tmp_path):
    store = Store(tmp_path / "data")
    report = refresh_schedule(client(), store)  # the state fixture says 2026 week 10
    assert report.ok and report.written == [("2026", 10), ("2026", 11)]
    assert store.read_nfl_week("2026", 11)["games"][0]["home"] == "HOU"


def test_refresh_failure_leaves_stored_weeks_unchanged(tmp_path):
    store = Store(tmp_path / "data")
    refresh_schedule(client(), store)
    before = store.read_nfl_week("2026", 10)
    report = refresh_schedule(client({"espn/scoreboard/11.json": 503}), store)
    assert not report.ok and "week 11" in report.errors[0]
    assert store.read_nfl_week("2026", 10) == before  # week 10 was fetched fine but nothing is written on failure


def test_refresh_offseason_stores_nothing(tmp_path):
    store = Store(tmp_path / "data")
    report = refresh_schedule(client({"state/nfl.json": {"season": "2027", "week": 0, "season_type": "off"}}), store)
    assert report.ok and report.written == []


def test_kickoff_lookup(tmp_path):
    store = Store(tmp_path / "data")
    refresh_schedule(client(), store)
    sched = Schedule(store, "2026")
    assert sched.kickoff(11, "IND") == utc(2026, 11, 20, 1, 15)
    assert sched.kicked_off(11, "IND", utc(2026, 11, 22, 12)) is True  # Saturday after Thursday night
    assert sched.kicked_off(11, "IND", utc(2026, 11, 19, 12)) is False
    assert sched.kicked_off(10, "WAS", utc(2026, 11, 1)) is True  # a final game counts as kicked off whatever the clock says
    assert sched.on_bye(11, "ATL") is True and sched.on_bye(11, "IND") is False
    assert sched.on_bye(12, "IND") is None  # week not stored
    assert "WAS" in sched.teams_playing(10) and "CHI" not in sched.teams_playing(10)
