import copy

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.noise import GaussianNoise
from ffapp.odds import (
    build_inputs,
    completed_weeks,
    fixed_records,
    rosters_as_of,
    run_as_of,
)
from ffapp.projections import upsert_week
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import fetch_season, sync_league
from tests.fixtures import DYNASTY, FixtureSession, load

CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
CONFIG = Config(leagues={"dynasty": CFG})


def client():
    return SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None)


def season(league_id):
    return fetch_season(client(), load(f"league/{league_id}.json"))


# -- 5.1 as-of -----------------------------------------------------------------


def test_as_of_is_last_scored_week_not_calendar_week():
    data = season(DYNASTY["2026"])
    assert completed_weeks(data.league) == 9, "week 10 has Thursday points but is not scored"
    assert completed_weeks(season(DYNASTY["2025"]).league) == 17


def test_as_of_clamps_to_season_bounds():
    league = copy.deepcopy(load(f"league/{DYNASTY['2026']}.json"))
    league["settings"]["last_scored_leg"] = 0
    assert completed_weeks(league) == 0
    league["settings"]["last_scored_leg"] = 25
    assert completed_weeks(league) == 17


def test_fixed_records_only_count_completed_weeks():
    data = season(DYNASTY["2026"])
    records = fixed_records(data, 9)
    assert all(r.games == 9 for r in records.values())
    partial = fixed_records(data, 10)  # if a caller wrongly passed 10, the partly-played week would count
    assert all(r.games == 10 for r in partial.values())
    none = fixed_records(data, 0)
    assert all(r.games == 0 for r in none.values()) and len(none) == 12


# -- 5.2 rosters ----------------------------------------------------------------


def test_current_roster_excludes_reserve_and_taxi():
    data = season(DYNASTY["2026"])
    rosters = rosters_as_of(data, 9, current=True)
    for roster in data.rosters:
        rid = roster["roster_id"]
        assert set(rosters[rid]).isdisjoint(set(roster.get("reserve") or []))
        assert set(rosters[rid]).isdisjoint(set(roster.get("taxi") or []))
        assert len(rosters[rid]) == len(roster["players"]) - len(roster.get("reserve") or []) - len(roster.get("taxi") or [])
    assert any(roster.get("reserve") or roster.get("taxi") for roster in data.rosters), "fixture exercises the exclusion"


def test_backfilled_roster_comes_from_next_week_matchup():
    data = season(DYNASTY["2026"])
    as_of_5 = rosters_as_of(data, 5, current=False)
    week6 = {t["roster_id"]: t["players"] for t in data.matchups[6]}
    assert as_of_5 == {rid: list(map(str, players)) for rid, players in week6.items()}


def test_as_of_zero_uses_week_one_roster():
    data = season(DYNASTY["2026"])
    as_of_0 = rosters_as_of(data, 0, current=False)
    week1 = {t["roster_id"]: list(map(str, t["players"])) for t in data.matchups[1]}
    assert as_of_0 == week1


def test_backfill_falls_back_to_current_roster_when_week_missing():
    data = season(DYNASTY["2026"])
    data.matchups.pop(6)
    assert rosters_as_of(data, 5, current=False) == rosters_as_of(data, 5, current=True)


# -- inputs and the odds store ----------------------------------------------------


def seeded_store(tmp_path):
    store = Store(tmp_path)
    sync_league(client(), store, CFG)
    # give 2026 some projections by reusing the 2025 week-1 fixture for every week
    rows = load("projections/2025/1.json")
    for week in range(1, 18):
        reused = copy.deepcopy(rows)
        for row in reused:
            row["season"] = "2026"
            row["week"] = week
        upsert_week(store, "2026", week, reused)
    return store


def test_build_inputs_covers_remaining_schedule_and_playoffs(tmp_path):
    store = seeded_store(tmp_path)
    data = store.read_season("dynasty", "2026")
    inputs = build_inputs(store, CONFIG, "dynasty", data, 9, current=True)
    assert inputs.regular_weeks == [10, 11, 12, 13, 14]
    assert inputs.playoff_weeks == [15, 16, 17]
    assert all(len(pairs) == 6 for pairs in inputs.schedule.values())
    assert inputs.real_points == {}
    for rid, by_week in inputs.starters.items():
        assert sorted(by_week) == list(range(10, 18))
    assert all(rec.games == 9 for rec in inputs.fixed.values())


def test_run_as_of_writes_history_and_rerun_replaces_only_same_week(tmp_path):
    store = seeded_store(tmp_path)
    data = store.read_season("dynasty", "2026")
    noise = GaussianNoise(5.0)
    for as_of in range(0, 3):
        run_as_of(store, CONFIG, "dynasty", data, as_of, current=False, noise=noise, runs=200)
    assert store.odds_weeks("dynasty", "2026") == [0, 1, 2]
    before = {w: store.read_odds("dynasty", "2026", w) for w in (0, 1)}

    payload = run_as_of(store, CONFIG, "dynasty", data, 2, current=False, noise=noise, runs=300, seed=99)
    assert payload["runs"] == 300 and payload["seed"] == 99 and payload["as_of_week"] == 2
    assert store.read_odds("dynasty", "2026", 2)["runs"] == 300
    assert {w: store.read_odds("dynasty", "2026", w) for w in (0, 1)} == before

    team = payload["teams"][0]
    for key in ("roster_id", "user_id", "display_name", "team_name", "wins", "losses", "ties", "points_for",
                "proj_wins", "proj_losses", "playoffs", "bye", "final", "title", "losers_bracket", "last", "seed_distribution"):
        assert key in team, key
    assert payload["teams"] == sorted(payload["teams"], key=lambda t: -t["playoffs"])
    assert sum(t["playoffs"] for t in payload["teams"]) == pytest.approx(6.0, abs=0.02)
