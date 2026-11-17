from datetime import datetime, timezone

import pytest

from ffapp.games import last_unlocked, record_lineup, simulate_fixed, update_games, week_games
from ffapp.noise import GaussianNoise
from ffapp.odds import run_as_of

AS_OF = 9  # the fixture league has weeks 1-9 scored
WEEK = AS_OF + 1


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


THURSDAY, SATURDAY, SUNDAY = utc(2026, 11, 19, 12), utc(2026, 11, 21, 12), utc(2026, 11, 22, 16)


def prepare(store, config, *, schedule=True):
    data = store.read_season("dynasty", "2026")
    for as_of in (AS_OF - 1, AS_OF):
        run_as_of(store, config, "dynasty", data, as_of, current=as_of == AS_OF, noise=GaussianNoise(5.0), runs=300)
    if schedule:
        # every NFL team kicks off Sunday 18:00 UTC except Jacksonville (Thursday night)
        teams = sorted({rec["team"] for rec in store.read_projections("2026", WEEK).values() if rec.get("team")})
        games = [{"home": t, "away": "XXX", "kickoff_utc": "2026-11-22T18:00:00+00:00", "state": "scheduled"} for t in teams if t != "JAX"]
        games.append({"home": "JAX", "away": "YYY", "kickoff_utc": "2026-11-20T01:15:00+00:00", "state": "scheduled"})
        store.write_nfl_week("2026", WEEK, {"games": games, "byes": []})
    return data


def jax_player(store):
    return next(pid for pid, rec in store.read_projections("2026", WEEK).items() if rec.get("team") == "JAX" and rec.get("position") != "DEF")


def bump(store, pid, delta):
    """Change one stored projection so the next log entry differs."""
    records = store.read_projections("2026", WEEK)
    records[pid]["stats"]["rec_yd"] = float(records[pid]["stats"].get("rec_yd") or 0) + delta
    store.write_projections("2026", WEEK, records)


def roster_with(store, pid):
    data = store.read_season("dynasty", "2026")
    return next(int(r["roster_id"]) for r in data.rosters if pid in [str(p) for p in r.get("players") or []])


def test_weekend_log_freezes_a_player_at_kickoff(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    pid = jax_player(seeded_store)
    other = next(p for p, rec in seeded_store.read_projections("2026", WEEK).items() if rec.get("team") not in ("JAX", None) and rec.get("position") == "WR")
    assert WEEK in update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY)
    bump(seeded_store, pid, 100)  # after his Thursday kickoff: must not show up
    bump(seeded_store, other, 50)  # Sunday player: must show up
    update_games(seeded_store, dynasty_config, "dynasty", now=SATURDAY)
    bump(seeded_store, other, 50)
    update_games(seeded_store, dynasty_config, "dynasty", now=SUNDAY)
    stored = seeded_store.read_games("dynasty", "2026", WEEK)
    assert stored["forecast"]["as_of_week"] == AS_OF and len(stored["forecast"]["games"]) == 6
    rid = roster_with(seeded_store, pid) if any(pid in e["players"].get(str(t), {}) for es in stored["log"].values() for e in es for t in e["teams"]) else None
    if rid is not None:
        entries = next(es for es in stored["log"].values() if rid in es[0]["teams"])
        values = [e["players"][str(rid)][pid] for e in entries]
        assert values[0][1] is False and all(v[1] for v in values[1:])  # locked from Saturday on
        assert len({v[0] for v in values}) == 1  # projection frozen at Thursday's value
    rid_o = roster_with(seeded_store, other) if any(other in e["players"].get(str(t), {}) for es in stored["log"].values() for e in es for t in e["teams"]) else None
    if rid_o is not None:
        entries = next(es for es in stored["log"].values() if rid_o in es[0]["teams"])
        assert len(entries) == 3 and len({e["players"][str(rid_o)][other][0] for e in entries}) == 3
    assert rid is not None and rid_o is not None, "both fixture players must be rostered for this test to mean anything"


def test_unchanged_run_adds_no_entry(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY)
    before = seeded_store.read_games("dynasty", "2026", WEEK)
    assert WEEK not in update_games(seeded_store, dynasty_config, "dynasty", now=utc(2026, 11, 19, 13))
    assert seeded_store.read_games("dynasty", "2026", WEEK) == before


def test_last_unlocked_and_record_lineup():
    entries = [
        {"teams": [1, 2], "players": {"1": {"thu": [11.0, False], "sun": [14.0, False]}}},
        {"teams": [1, 2], "players": {"1": {"thu": [11.0, True], "sun": [2.0, False]}}},  # Saturday: ruled out
        {"teams": [1, 2], "players": {"1": {"thu": [11.0, True], "sun": [2.0, True]}}},
    ]
    assert last_unlocked(entries, 1, "sun") == 2.0 and last_unlocked(entries, 1, "thu") == 11.0
    assert last_unlocked(entries, 1, "never") is False
    row = {"roster_id": 1, "starters": ["thu", "sun", "surprise", "0"]}
    projections = {"surprise": {"position": "WR", "stats": {"rec": 5.0}}}
    lineup = record_lineup(row, ["QB", "RB", "WR", "TE"], entries, projections, {"rec": 1.0}, {"thu": {"position": "QB"}, "sun": {"position": "RB"}})
    assert lineup == [["QB", "thu", "QB", 11.0], ["RB", "sun", "RB", 2.0], ["WR", "surprise", "WR", 5.0], ["TE", None, "TE", 0.0]]


def test_simulate_fixed_is_deterministic_and_skips_empty_slots():
    lineups = {1: [["QB", "a", "QB", 20.0], ["TE", None, "TE", 0.0]], 2: [["QB", "b", "QB", 10.0]]}
    one = simulate_fixed(lineups, GaussianNoise(3.0), None, seed=5, runs=2000)
    two = simulate_fixed(lineups, GaussianNoise(3.0), None, seed=5, runs=2000)
    assert all((one[r] == two[r]).all() for r in one)
    assert one[1].mean() == pytest.approx(20.0, abs=0.5) and one[1].std() == pytest.approx(3.0, abs=0.3)


def test_pre_week_record_for_weeks_before_the_log(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY)
    stored = seeded_store.read_games("dynasty", "2026", AS_OF)
    record = stored["record"]
    assert record["source"] == "pre-week" and record["as_of_week"] == AS_OF - 1
    data = seeded_store.read_season("dynasty", "2026")
    assert len(record["games"]) == len(week_games(data, AS_OF)) == 6
    g = record["games"][0]
    assert g["winner"] in (g["teams"][0]["roster_id"], g["teams"][1]["roster_id"], None)
    assert g["actual"][0] > 0 and len(g["hist"]["shares"]) == 2
    assert g["teams"][0]["win_prob"] + g["teams"][1]["win_prob"] == pytest.approx(1.0, abs=1e-3)
    # weeks without a pre-week forecast stored (as-of 7 was never run) get no record
    assert (seeded_store.read_games("dynasty", "2026", AS_OF - 1) or {}).get("record") is None


def test_record_from_log_once_the_week_is_final(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY)
    # pretend week 10 was logged and has now been played: copy week 9's matchups into week 10 and mark it scored
    data = seeded_store.read_season("dynasty", "2026")
    data.matchups[WEEK] = data.matchups[AS_OF]
    data.league["settings"]["last_scored_leg"] = WEEK
    seeded_store.write_season("dynasty", data)
    update_games(seeded_store, dynasty_config, "dynasty", now=SUNDAY)
    record = seeded_store.read_games("dynasty", "2026", WEEK)["record"]
    assert record["source"] == "log" and len(record["games"]) == 6
    first = record["games"][0]
    starters = next(r for r in data.matchups[WEEK] if int(r["roster_id"]) == first["teams"][0]["roster_id"])["starters"]
    assert [row[1] for row in first["teams"][0]["lineup"]] == [None if s == "0" else str(s) for s in starters]
    # computed once: a later projection change and re-run leave it alone
    bump(seeded_store, jax_player(seeded_store), 30)
    assert WEEK not in update_games(seeded_store, dynasty_config, "dynasty", now=utc(2026, 11, 24))
    assert seeded_store.read_games("dynasty", "2026", WEEK)["record"] == record
