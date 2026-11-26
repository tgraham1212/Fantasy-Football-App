from datetime import datetime, timezone

import pytest

from ffapp.lineup import Starter
from ffapp.live import LiveContext, clock_label, live_lineup, live_week
from ffapp.noise import GaussianNoise
from ffapp.odds import lineup_from_projections, run_as_of, simulate_league
from ffapp.schedule import Schedule
from ffapp.store import Store

SLOTS = ["QB", "RB", "WR", "FLEX"]
SCORING = {"pass_yd": 0.04, "rush_yd": 0.1, "rec_yd": 0.1}


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


SATURDAY = utc(2026, 11, 21, 12)


def proj(position, team, **stats):
    return {"position": position, "fantasy_positions": [position], "team": team, "stats": stats}


PROJECTIONS = {
    "qb": proj("QB", "BUF", pass_yd=250),  # 10
    "rbthu": proj("RB", "IND", rush_yd=120),  # 12, Thursday (final)
    "wrthu": proj("WR", "IND", rec_yd=150),  # 15, Thursday, started at FLEX
    "wrben": proj("WR", "HOU", rec_yd=60),  # 6, Thursday, on the bench
    "wrsun": proj("WR", "KC", rec_yd=90),  # 9, Sunday
    "wrsun2": proj("WR", "KC", rec_yd=50),  # 5, Sunday
    "rbsun": proj("RB", "KC", rush_yd=80),  # 8, Sunday
}


def week_store(tmp_path, *, in_progress=False):
    store = Store(tmp_path / "data")
    games = [
        {"home": "HOU", "away": "IND", "kickoff_utc": "2026-11-20T01:15:00+00:00", "state": "final", "quarter": 4, "clock": 0.0},
        {"home": "KC", "away": "BUF", "kickoff_utc": "2026-11-22T18:00:00+00:00", "state": "scheduled"},
    ]
    if in_progress:
        games[1] = {**games[1], "state": "in_progress", "quarter": 2, "clock": 0.0}
    store.write_nfl_week("2026", 11, {"games": games, "byes": []})
    return store


def open_lineup(open_slots, available):
    return lineup_from_projections(PROJECTIONS, SCORING, open_slots, available, None)


def build(store, row, roster, now=SATURDAY):
    return live_lineup(row, SLOTS, roster, PROJECTIONS, SCORING, Schedule(store, "2026"), 11, now, {}, open_lineup)


ROSTER = ["qb", "rbthu", "wrthu", "wrben", "wrsun", "wrsun2", "rbsun"]
ROW = {"roster_id": 1, "starters": ["qb", "rbthu", "wrsun", "wrthu"], "players_points": {"rbthu": 21.5, "wrthu": 3.0, "wrben": 30.0}}


def test_locked_starters_hold_their_slots_and_score_their_points(tmp_path):
    lineup = build(week_store(tmp_path), ROW, ROSTER)
    by_slot = {s.slot: s for s in lineup}
    assert [s.slot for s in lineup] == SLOTS
    assert by_slot["RB"] == Starter("RB", "rbthu", "RB", 12.0, fixed=21.5, share=0.0, status="final", clock=None)
    assert by_slot["FLEX"].player_id == "wrthu" and by_slot["FLEX"].fixed == 3.0 and by_slot["FLEX"].share == 0.0  # model would bench him
    assert all(s.player_id != "wrben" for s in lineup)  # 30 points on the bench do not count
    assert by_slot["QB"].player_id == "qb" and by_slot["QB"].share == 1.0 and by_slot["QB"].status is None
    assert by_slot["WR"].player_id == "wrsun"  # open slot: model's pick from players not yet locked


def test_open_slot_repicked_after_a_ruling_out(tmp_path):
    projections_out = dict(PROJECTIONS)
    del projections_out["wrsun"]  # ruled out on Saturday: no projection
    lineup = live_lineup(ROW, SLOTS, ROSTER, projections_out, SCORING, Schedule(week_store(tmp_path), "2026"), 11, SATURDAY, {},
                         lambda o, a: lineup_from_projections(projections_out, SCORING, o, a, None))
    assert {s.slot: s.player_id for s in lineup}["WR"] == "wrsun2"


def test_in_progress_starter_keeps_the_share_left(tmp_path):
    row = {**ROW, "starters": ["qb", "rbthu", "wrsun", "wrthu"], "players_points": {"qb": 7.2}}
    lineup = build(week_store(tmp_path, in_progress=True), row, ROSTER, now=utc(2026, 11, 22, 19, 30))
    qb = next(s for s in lineup if s.slot == "QB")
    assert qb.status == "in_progress" and qb.fixed == 7.2 and qb.share == pytest.approx(0.5) and qb.clock == "Q2 0:00"


def test_live_week_only_after_the_first_kickoff(tmp_path):
    store = week_store(tmp_path)
    data = type("D", (), {"season": "2026"})()
    assert live_week(store, data, 10, utc(2026, 11, 19, 12)) == 11  # the Thursday game is stored as final
    store.write_nfl_week("2026", 11, {"games": [{"home": "HOU", "away": "IND", "kickoff_utc": "2026-11-20T01:15:00+00:00", "state": "scheduled"}], "byes": []})
    assert live_week(Store(store.root), data, 10, utc(2026, 11, 19, 12)) is None  # Wednesday
    assert live_week(Store(store.root), data, 10, utc(2026, 11, 20, 2)) == 11  # after kickoff by the clock


def test_clock_label():
    assert clock_label({"state": "in_progress", "quarter": 3, "clock": 252.0}) == "Q3 4:12"
    assert clock_label({"state": "in_progress", "quarter": 5, "clock": 120.0}) == "OT 2:00"
    assert clock_label({"state": "final"}) is None


# -- frozen as-of results and the live file ---------------------------------------------------------


def live_schedule(store, week, kicked=True):
    state = "final" if kicked else "scheduled"
    teams = sorted({rec["team"] for rec in store.read_projections("2026", week).values() if rec.get("team")})
    games = [{"home": t, "away": "XXX", "kickoff_utc": "2026-11-20T01:15:00+00:00", "state": state, "quarter": 4, "clock": 0.0} for t in teams[:1]]
    games += [{"home": t, "away": "YYY", "kickoff_utc": "2026-11-22T18:00:00+00:00", "state": "scheduled"} for t in teams[1:]]
    store.write_nfl_week("2026", week, {"games": games, "byes": []})


def test_live_run_writes_live_file_and_leaves_the_as_of_result_frozen(seeded_store, dynasty_config):
    data = seeded_store.read_season("dynasty", "2026")
    run_as_of(seeded_store, dynasty_config, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=200)
    frozen = seeded_store.odds_path("dynasty", "2026", 9).read_bytes()
    live_schedule(seeded_store, 10)
    payload = run_as_of(seeded_store, dynasty_config, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=200, seed=3,
                        live=LiveContext(week=10, at=SATURDAY))
    assert seeded_store.odds_path("dynasty", "2026", 9).read_bytes() == frozen
    live = seeded_store.read_live("dynasty", "2026")
    total = len(seeded_store.read_nfl_week("2026", 10)["games"])
    assert live["as_of_week"] == 9 and live["live"] == {"week": 10, "games_final": 1, "games_total": total, "at": SATURDAY.isoformat()}
    assert payload["live"]["week"] == 10


def test_non_live_run_removes_a_stale_live_file(seeded_store, dynasty_config):
    data = seeded_store.read_season("dynasty", "2026")
    seeded_store.write_live("dynasty", "2026", {"as_of_week": 9})
    run_as_of(seeded_store, dynasty_config, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=200)
    assert seeded_store.read_live("dynasty", "2026") is None and seeded_store.odds_path("dynasty", "2026", 9).exists()


def test_backfill_never_writes_a_live_file(seeded_store, dynasty_config):
    live_schedule(seeded_store, 10)
    simulate_league(seeded_store, dynasty_config, "dynasty", backfill_season=True, runs=100, now=SATURDAY)
    assert seeded_store.odds_weeks("dynasty", "2026") == list(range(0, 9))  # backfilled 0-8; 9 frozen out by the live week
    assert seeded_store.read_live("dynasty", "2026")["live"]["week"] == 10


def test_live_forecast_rows_and_log_keep_pre_kickoff_projections(seeded_store, dynasty_config):
    from ffapp.games import update_games

    data = seeded_store.read_season("dynasty", "2026")
    run_as_of(seeded_store, dynasty_config, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=200)
    thursday = utc(2026, 11, 19, 12)
    update_games(seeded_store, dynasty_config, "dynasty", now=thursday)  # before any kickoff: plain forecast
    before = seeded_store.read_games("dynasty", "2026", 10)
    live_schedule(seeded_store, 10)
    run_as_of(seeded_store, dynasty_config, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=200, live=LiveContext(week=10, at=SATURDAY))
    update_games(seeded_store, dynasty_config, "dynasty", now=SATURDAY)
    stored = seeded_store.read_games("dynasty", "2026", 10)
    assert stored["forecast"]["live"] is True
    teams = [t for g in stored["forecast"]["games"] for t in g["teams"]]
    locked_rows = [row for t in teams for row in t["lineup"] if len(row) == 8]
    assert locked_rows, "the first NFL team kicked off, so some starters are locked"
    assert all(row[4] in ("final", "in_progress") for row in locked_rows)
    live_teams = [t for t in teams if "points_so_far" in t]
    assert live_teams and all(t["to_play"] < len(t["lineup"]) for t in live_teams if any(len(r) == 8 for r in t["lineup"]))
    # once either side has started, both teams show points so far (0.0 and all to play when theirs haven't)
    for g in stored["forecast"]["games"]:
        if any(len(r) == 8 for t in g["teams"] for r in t["lineup"]):
            assert all("points_so_far" in t for t in g["teams"])
    # the log: a player locked on Saturday keeps the projection he had on Thursday
    for key, entries in stored["log"].items():
        if len(entries) < 2:
            continue
        thursday_entry, saturday_entry = entries[0], entries[-1]
        for rid, players in saturday_entry["players"].items():
            for pid, (proj, locked) in players.items():
                if locked and pid in thursday_entry["players"][rid]:
                    assert proj == thursday_entry["players"][rid][pid][0]
    assert any(len(es) >= 2 for es in stored["log"].values()) and before["forecast"].get("live") is False
    # lineup views during the live week: actual = the starters each Manager set (2.7.3), model = frozen
    # pre-kickoff projections
    assert stored["views"] and all(v["actual"]["source"] == "live" and v["model"]["source"] == "model" for v in stored["views"].values())
    starters_of = {int(r["roster_id"]): [None if str(p) in ("0", "") else str(p) for p in r.get("starters") or []]
                   for r in seeded_store.read_season("dynasty", "2026").matchups[10]}
    for v in stored["views"].values():
        for t in v["actual"]["teams"]:
            assert [row[1] for row in t["lineup"]] == starters_of[t["roster_id"]], "the set starters, no model picks or fills"
    # win probability added: a pre-kickoff baseline per real game, and a value for every locked starter
    assert set(stored["baseline"]) == {g["key"] for g in stored["forecast"]["games"]}
    assert all(b["margin_sd"] > 0 for b in stored["baseline"].values())
    for t in live_teams:
        locked_ids = {row[1] for row in t["lineup"] if len(row) == 8 and row[1]}
        assert set(t["wpa"]) == locked_ids
