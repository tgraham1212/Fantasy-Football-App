from datetime import datetime, timezone

import pytest

from ffapp.games import update_games
from ffapp.views import default_lineup, lineup_choices, model_lineup
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
    """game-predictions 2.8 and 2.8.1: starters' points minus the default lineup's, empty slots 0 on either
    side, and during the live week only Players whose games have kicked off."""
    default = [["QB", "a", "QB", 20.0], ["WR", "w", "WR", 6.6]]
    actual = [["QB", "b", "QB", 18.0], ["WR", "w", "WR", 6.6]]  # started QB B over the default's QB A
    assert lineup_choices(actual, default, {"a": 10.0, "b": 15.0, "w": 9.0}, lambda pid: True) == 5.0
    assert lineup_choices(actual, default, {"a": 15.0, "b": 10.0, "w": 9.0}, lambda pid: True) == -5.0
    assert lineup_choices(default, default, {"a": 15.0, "w": 9.0}, lambda pid: True) == 0.0, "following the default scores 0"
    empty = [["QB", "a", "QB", 20.0], ["WR", None, "WR", 0.0]]
    assert lineup_choices(empty, default, {"a": 15.0, "w": 8.2}, lambda pid: True) == -8.2, "an empty slot counts 0"
    assert lineup_choices(empty, empty, {"a": 15.0}, lambda pid: True) == 0.0
    live = [["QB", "a", "QB", 20.0], ["WR", "m", "WR", 6.4]]
    assert lineup_choices(live, default, {"a": 30.0, "m": 7.4, "w": 0.0}, lambda pid: pid in ("a", "m")) == 7.4  # w not kicked off
    assert lineup_choices(live, default, {"a": 30.0, "m": 7.4, "w": 0.0}, lambda pid: pid == "a") == 0.0
    big = [["RB", "x", "RB", 10.0]], [["RB", "y", "RB", 9.0]]
    assert lineup_choices(*big, {"x": 3.0, "y": 15.0}, lambda pid: True) == -12.0


def test_default_lineup_is_roster_only():
    """game-predictions 2.8: the default lineup is the best legal lineup from the rostered Players alone, never
    a free agent, and a slot no rostered Player can fill is left empty (0 on both sides)."""
    projections = {"qb": proj("QB", pass_yd=200), "k": proj("K"), "fa_k": proj("K", rec_yd=90), "rb": proj("RB", rush_yd=90)}
    row = {"roster_id": 1, "players": ["qb", "k", "rb"]}  # fa_k is unrostered and projects higher
    rows = default_lineup(row, ["QB", "RB", "TE", "K"], [], projections, SCORING, {})
    assert [r[1] for r in rows] == ["qb", "rb", "k"], "no free agent, and no fill for the TE nobody can play"
    actual = [["QB", "qb", "QB", 8.0], ["RB", "rb", "RB", 9.0], ["TE", None, "TE", 0.0], ["K", "k", "K", 0.0]]
    assert lineup_choices(actual, rows, {"qb": 12.0, "rb": 4.0, "k": 7.0, "fa_k": 15.0}, lambda pid: True) == 0.0

    # a starter with no stored projection counts the same on both sides, even over a projected backup
    row = {"roster_id": 1, "players": ["brady", "qb", "rb", "k"], "starters": ["brady", "rb", "0", "k"]}
    rows = default_lineup(row, ["QB", "RB", "TE", "K"], [], projections, SCORING, {"brady": {"position": "QB"}})
    assert [r[1] for r in rows] == ["brady", "rb", "k"]
    actual = [["QB", "brady", "QB", 0.0], ["RB", "rb", "RB", 9.0], ["TE", None, "TE", 0.0], ["K", "k", "K", 0.0]]
    assert lineup_choices(actual, rows, {"brady": 27.2, "qb": 9.0, "rb": 4.0, "k": 7.0}, lambda pid: True) == 0.0


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
    assert pre["lineup_basis"] == "roster-default"
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
    """game-predictions 2.8.2: every team in every finished regular-season week gets lineup choices, computed
    from that week's stored projections and rostered Players only; a team that started exactly the default
    lineup scores 0; stored values are kept only when they follow the current rule."""
    from ffapp.league import resolve_settings, starter_slots
    from ffapp.odds import completed_weeks
    from ffapp.store import write_json
    from ffapp.views import season_lineup_choices

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
    default = default_lineup(row, slots, [], projections, scoring, store.read_crosswalk() or {})
    by_slot = {}
    for r in default:
        by_slot.setdefault(r[0], []).append(r[1])
    row["starters"] = [by_slot[s].pop(0) if by_slot.get(s) else "0" for s in slots]  # this team started the default lineup
    write_json(store.matchup_path("dynasty", "2026", week), data.matchups[week])

    choices = season_lineup_choices(store, config, "dynasty", store.read_season("dynasty", "2026"))
    assert {(w, int(r["roster_id"])) for w in range(1, done + 1) for r in data.matchups.get(w, []) if r.get("matchup_id") is not None} <= set(choices)
    assert choices[(week, rid)] == 0.0, "starting the default lineup gives no lineup choices"

    current = {"lineup_basis": "roster-default", "views": {"k": {"actual": {"teams": [{"roster_id": rid, "lineup_choices": 7.4}]}}}}
    write_json(store.games_derived_path("dynasty", "2026", 2), current)
    assert season_lineup_choices(store, config, "dynasty", store.read_season("dynasty", "2026"))[(2, rid)] == 7.4, "current-rule stored views win"
    write_json(store.games_derived_path("dynasty", "2026", 2), {"views": current["views"]})
    assert season_lineup_choices(store, config, "dynasty", store.read_season("dynasty", "2026"))[(2, rid)] != 7.4, "an earlier rule's value is recomputed"


def test_old_rule_lineup_choices_recomputed_once(seeded_store, dynasty_config):
    """A week stored under an earlier lineup-choices rule has only its lineup choices recomputed, once,
    and its committed record is left as it was."""
    from ffapp.store import read_json, write_json

    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    derived_path = seeded_store.games_derived_path("dynasty", "2026", AS_OF)
    record_path = seeded_store.games_path("dynasty", "2026", AS_OF)
    derived = read_json(derived_path)
    right = {k: [t["lineup_choices"] for t in v["actual"]["teams"]] for k, v in derived["views"].items()}
    for v in derived["views"].values():  # an old build: other figures and no basis marker
        for side in ("actual", "model"):
            for t in v[side]["teams"]:
                t["lineup_choices"] = 99.9
    del derived["lineup_basis"]
    write_json(derived_path, derived)
    record_before = record_path.read_bytes() if record_path.exists() else None

    assert AS_OF in update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 13, tzinfo=timezone.utc))
    after = read_json(derived_path)
    assert after["lineup_basis"] == "roster-default"
    assert {k: [t["lineup_choices"] for t in v["actual"]["teams"]] for k, v in after["views"].items()} == right
    assert all(t["lineup_choices"] != 99.9 for v in after["views"].values() for t in v["model"]["teams"])
    assert (record_path.read_bytes() if record_path.exists() else None) == record_before, "the committed record is untouched"
    assert AS_OF not in update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 14, tzinfo=timezone.utc)), "only once"
