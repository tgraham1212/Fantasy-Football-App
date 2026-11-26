from datetime import datetime, timezone

import pytest

from ffapp.games import update_games
from ffapp.views import lineup_choices, model_lineup
from tests.test_games import AS_OF, WEEK, prepare

SCORING = {"rec_yd": 0.1, "rush_yd": 0.1, "pass_yd": 0.04}


def proj(position, **stats):
    return {"position": position, "fantasy_positions": [position], "team": "KC", "stats": stats}


def test_model_lineup_uses_frozen_projections_and_fills_short_slots():
    projections = {"qb": proj("QB", pass_yd=400), "wr66": proj("WR", rec_yd=66), "wr64": proj("WR", rec_yd=64), "rb": proj("RB", rush_yd=90)}
    row = {"roster_id": 1, "players": ["qb", "wr66", "wr64", "rb"]}
    # the log froze wr64 at 7.0 before kickoff: the frozen value beats his stored 6.4
    entries = [{"time": "t1", "teams": [1, 2], "players": {"1": {"wr64": [7.0, False], "wr66": [6.6, False]}}}]
    rows = model_lineup(row, ["QB", "RB", "WR", "TE"], entries, projections, SCORING, {"TE": 5.5}, {})
    assert rows == [["QB", "qb", "QB", 16.0], ["RB", "rb", "RB", 9.0], ["WR", "wr64", "WR", 7.0], ["TE", None, "TE", 5.5]]
    rows = model_lineup(row, ["QB", "RB", "WR", "TE"], [], projections, SCORING, {"TE": 5.5}, {})
    assert rows[2] == ["WR", "wr66", "WR", 6.6]  # without the log: stored projections, the 6.6 receiver


def test_lineup_choices_examples_and_live_rule():
    actual = [["QB", "a", "QB", 20.0], ["WR", "m", "WR", 6.4]]
    model = [["QB", "a", "QB", 20.0], ["WR", "w", "WR", 6.6]]
    points = {"a": 30.0, "m": 7.4, "w": 0.0}
    assert lineup_choices(actual, model, points, {}, lambda pid: True) == 7.4
    assert lineup_choices(model, actual, points, {}, lambda pid: True) == -7.4
    with_fill = [["QB", "a", "QB", 20.0], ["WR", None, "WR", 8.0]]
    assert lineup_choices(actual, with_fill, points, {"WR": 4.2}, lambda pid: True) == 3.2  # fill counts the realised level
    assert lineup_choices(actual, with_fill, points, {}, lambda pid: pid == "a") == 0.0  # live: m not kicked off, fill not yet counted
    big = [["RB", "x", "RB", 10.0]], [["RB", "y", "RB", 9.0]]
    assert lineup_choices(*big, {"x": 3.0, "y": 15.0}, {}, lambda pid: True) == -12.0


def test_views_for_pre_log_and_logged_weeks(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    pre = seeded_store.read_games("dynasty", "2026", AS_OF)
    assert len(pre["views"]) == 6
    view = next(iter(pre["views"].values()))
    assert view["model"]["source"] == "pre-week" and view["actual"]["source"] == "rebuilt"
    data = seeded_store.read_season("dynasty", "2026")
    rid = view["actual"]["teams"][0]["roster_id"]
    starters = next(r for r in data.matchups[AS_OF] if int(r["roster_id"]) == rid)["starters"]
    assert [row[1] for row in view["actual"]["teams"][0]["lineup"]] == [None if s == "0" else str(s) for s in starters]
    real_starters = {str(s) for s in starters if str(s) not in ("0", "")}
    assert set(view["actual"]["teams"][0]["wpa"]) == real_starters  # WPA belongs to the actual view's starters
    for side in (0, 1):
        assert view["actual"]["teams"][side]["lineup_choices"] == view["model"]["teams"][side]["lineup_choices"]
    assert view["actual"]["teams"][0]["win_prob"] + view["actual"]["teams"][1]["win_prob"] == pytest.approx(1.0, abs=1e-3)

    # computed once: a re-run leaves the views alone
    assert AS_OF not in update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 13, tzinfo=timezone.utc))

    # a logged week once final: actual = record (real starters), model simulated from frozen projections
    data.matchups[WEEK] = data.matchups[AS_OF]
    data.league["settings"]["last_scored_leg"] = WEEK
    seeded_store.write_season("dynasty", data)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 24, tzinfo=timezone.utc))
    logged = seeded_store.read_games("dynasty", "2026", WEEK)
    v = next(iter(logged["views"].values()))
    assert v["actual"]["source"] == "log" and v["model"]["source"] == "model"
    record_game = next(g for g in logged["record"]["games"] if g["key"] == next(iter(logged["views"])))
    assert v["actual"]["teams"][0]["win_prob"] == record_game["teams"][0]["win_prob"]
    first = v["model"]
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 24, 1, tzinfo=timezone.utc), force_records=True)
    assert next(iter(seeded_store.read_games("dynasty", "2026", WEEK)["views"].values()))["model"] == first  # deterministic


def test_past_season_lineup_choices(seeded_store, dynasty_config):
    """game-predictions 2.8.2: every team in every finished regular-season week gets lineup choices, rebuilt
    from that week's stored projections; a team that started exactly the model lineup scores 0; a week
    with stored game views keeps the stored value."""
    from ffapp.league import resolve_settings, starter_slots
    from ffapp.odds import completed_weeks
    from ffapp.store import write_json
    from ffapp.views import season_lineup_choices, week_floor

    store, config = seeded_store, dynasty_config
    data = store.read_season("dynasty", "2026")
    done = min(completed_weeks(data.league), 13)
    week = 1
    rows = [r for r in data.matchups[week] if r.get("matchup_id") is not None]
    row = rows[0]
    rid = int(row["roster_id"])
    slots = starter_slots(data.league)
    projections = store.read_projections("2026", week)
    scoring = resolve_settings(config, "dynasty", data.league, week)
    model = model_lineup(row, slots, [], projections, scoring, week_floor(store, config, data, week, projections, scoring), store.read_crosswalk() or {})
    row["starters"] = [r[1] or "0" for r in model]  # this team started the model lineup
    path = store.matchup_path("dynasty", "2026", week)
    write_json(path, data.matchups[week])

    choices = season_lineup_choices(store, config, "dynasty", store.read_season("dynasty", "2026"))
    assert {(w, int(r["roster_id"])) for w in range(1, done + 1) for r in data.matchups.get(w, []) if r.get("matchup_id") is not None} <= set(choices)
    assert choices[(week, rid)] == 0.0, "starting the model lineup gives no lineup choices"

    write_json(store.games_derived_path("dynasty", "2026", 2), {"views": {"k": {"actual": {"teams": [{"roster_id": rid, "lineup_choices": 7.4}]}}}})
    assert season_lineup_choices(store, config, "dynasty", store.read_season("dynasty", "2026"))[(2, rid)] == 7.4, "stored game views win"
