"""Records vs rebuilt data in the store (docs/refresh-modes.md, "Where Data Lives")."""
import logging
from datetime import datetime, timedelta, timezone

from ffapp.games import update_games
from ffapp.odds import forecast_projections
from ffapp.slates import capture_slates, final_slates
from ffapp.stamp import site_hash
from ffapp.store import GAME_RECORD_KEYS, Store, read_json, write_json
from tests.test_games import AS_OF, THURSDAY, WEEK, bump, jax_player, prepare


def test_game_file_split_round_trip(tmp_path):
    store = Store(tmp_path / "data")
    payload = {"league_key": "x", "season": "2026", "week": 3, "log": {"1-2": [{"at": "t"}]}, "record": None,
               "forecast": {"games": []}, "views": {"1-2": {}}, "baseline": {"a": 1}}
    store.write_games("x", "2026", 3, payload)
    assert store.read_games("x", "2026", 3) == payload
    assert set(read_json(store.games_path("x", "2026", 3))) == set(GAME_RECORD_KEYS)
    assert set(read_json(store.games_derived_path("x", "2026", 3))) == {"forecast", "views", "baseline"}


def test_unchanged_game_record_is_not_rewritten(tmp_path):
    store = Store(tmp_path / "data")
    payload = {"league_key": "x", "season": "2026", "week": 3, "log": {}, "record": None, "forecast": {"n": 1}}
    store.write_games("x", "2026", 3, payload)
    path = store.games_path("x", "2026", 3)
    stamp = path.stat().st_mtime_ns
    store.write_games("x", "2026", 3, {**payload, "forecast": {"n": 2}})  # only rebuilt data changed
    assert path.stat().st_mtime_ns == stamp
    assert store.read_games("x", "2026", 3)["forecast"] == {"n": 2}


def test_future_projections_are_rebuilt_data_and_move_when_current(tmp_path):
    store = Store(tmp_path / "data")
    store.write_projections("2026", 12, {"p": {"pts": 1}}, future=True)
    assert not store.projections_path("2026", 12).exists()
    assert store.read_projections("2026", 12) == {"p": {"pts": 1}} and store.projection_weeks("2026") == [12]
    store.write_projections("2026", 12, {"p": {"pts": 2}})  # the week became current
    assert store.projections_path("2026", 12).exists() and not store.future_projections_path("2026", 12).exists()


def test_forecast_falls_back_to_the_latest_stored_week(tmp_path, caplog):
    store = Store(tmp_path / "data")
    store.write_projections("2026", 10, {"p": {"pts": 3}})
    with caplog.at_level(logging.WARNING):
        assert forecast_projections(store, "2026", 13) == {"p": {"pts": 3}}
    assert "week 13 missing: using week 10" in caplog.text
    assert forecast_projections(store, "2026", 10) == {"p": {"pts": 3}}


def test_nfl_week_record_has_no_live_clocks(tmp_path):
    store = Store(tmp_path / "data")
    game = {"home": "KC", "away": "BUF", "kickoff_utc": "2026-11-22T18:00:00+00:00", "state": "in_progress",
            "quarter": 2, "clock": 300.0, "home_score": 7, "away_score": 3}
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, "fetched_at": "t1", "games": [game], "byes": []})
    record = store.nfl_week_path("2026", 11)
    assert read_json(record)["games"] == [{k: game[k] for k in ("home", "away", "kickoff_utc", "state")}]
    assert store.read_nfl_week("2026", 11)["games"][0]["clock"] == 300.0  # this run's copy keeps them
    stamp = record.stat().st_mtime_ns
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, "fetched_at": "t2", "games": [{**game, "clock": 120.0}], "byes": []})
    assert record.stat().st_mtime_ns == stamp, "a new clock or fetch time is not a new record"
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, "fetched_at": "t3", "games": [{**game, "state": "final"}], "byes": []})
    assert read_json(record)["games"][0] == {"home": "KC", "away": "BUF", "kickoff_utc": game["kickoff_utc"], "state": "final", "home_score": 7, "away_score": 3}


def test_only_the_current_week_is_logged(seeded_store, dynasty_config):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY)
    later = seeded_store.read_games("dynasty", "2026", WEEK + 1)
    assert later["forecast"] and not any(later["log"].values()), "week 11 is not logged during week 10"
    bump(seeded_store, jax_player(seeded_store), 30)
    update_games(seeded_store, dynasty_config, "dynasty", now=THURSDAY + timedelta(hours=1))
    assert any(seeded_store.read_games("dynasty", "2026", WEEK)["log"].values())
    assert not any(seeded_store.read_games("dynasty", "2026", WEEK + 1)["log"].values())
    assert AS_OF + 1 == WEEK


def nfl(states):
    return {"games": [{"home": f"H{i}", "away": f"A{i}", "kickoff_utc": k, "state": st} for i, (k, st) in enumerate(states)]}


def test_final_slates():
    early, late = "2026-11-22T18:00:00+00:00", "2026-11-22T21:05:00+00:00"
    assert final_slates(nfl([(early, "final"), (early, "final"), (late, "in_progress")])) == [early]
    assert final_slates(nfl([(early, "final"), (early, "in_progress")])) == []


def test_slate_forecasts_are_stored_once(tmp_path):
    store = Store(tmp_path / "data")
    write_json(store.league_dir("x") / "2026" / "league.json", {"season": "2026", "league_id": "1"})
    early, late, night = "2026-11-22T18:00:00+00:00", "2026-11-22T21:05:00+00:00", "2026-11-23T01:20:00+00:00"
    live = {"generated_at": "g1", "live": {"week": 11}, "teams": [{"roster_id": 1, "playoffs": 0.5}], "games": {"11": {"games": []}}}
    store.write_live("x", "2026", live)
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, **nfl([(early, "final"), (late, "in_progress"), (night, "scheduled")])})
    at = datetime(2026, 11, 22, 21, 30, tzinfo=timezone.utc)
    assert capture_slates(store, "x", now=at) == [early]
    store.write_live("x", "2026", {**live, "generated_at": "g2"})
    assert capture_slates(store, "x", now=at) == []  # never overwritten
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, **nfl([(early, "final"), (late, "final"), (night, "final")])})
    assert capture_slates(store, "x", now=datetime(2026, 11, 23, 4, 30, tzinfo=timezone.utc)) == [late, night]
    slates = store.read_slates("x", "2026", 11)
    assert slates[early]["generated_at"] == "g1" and slates[late]["generated_at"] == "g2" and len(slates) == 3


def test_old_slates_are_not_stored(tmp_path):
    store = Store(tmp_path / "data")
    write_json(store.league_dir("x") / "2026" / "league.json", {"season": "2026", "league_id": "1"})
    thursday = "2026-11-20T01:15:00+00:00"
    store.write_live("x", "2026", {"generated_at": "g", "live": {"week": 11}, "teams": [], "games": {}})
    store.write_nfl_week("2026", 11, {"season": "2026", "week": 11, **nfl([(thursday, "final")])})
    assert capture_slates(store, "x", now=datetime(2026, 11, 22, 18, tzinfo=timezone.utc)) == []


def test_site_hash_ignores_refresh_times(tmp_path):
    site = tmp_path / "site"
    write_json(site / "data" / "index.json", {"last_refresh": "a", "leagues": [{"generated_at": "a", "x": 1}]})
    (site / "app.js").write_text("x", encoding="utf-8")
    first = site_hash(site)
    write_json(site / "data" / "index.json", {"last_refresh": "b", "leagues": [{"generated_at": "b", "x": 1}]})
    assert site_hash(site) == first
    write_json(site / "data" / "index.json", {"last_refresh": "b", "leagues": [{"generated_at": "b", "x": 2}]})
    assert site_hash(site) != first
