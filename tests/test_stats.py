import copy
import hashlib

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.league import resolve_settings
from ffapp.sleeper import SleeperClient
from ffapp.stats import StatsError, actual_points, fetch_week, played, refresh_season, refresh_stats, upsert_week
from ffapp.store import Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, REDRAFT, FixtureSession, load

ROWS = load("stats/2025/1.json")
PLAYED = [r for r in ROWS if played(r)]


def make_client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def test_fetch_week_accepts_fixture():
    rows = fetch_week(make_client(), "2025", 1)
    assert len(rows) == len(ROWS)
    assert sum(played(r) for r in rows) == len(PLAYED) and len(PLAYED) < len(ROWS)


def test_bad_shape_is_a_stats_error():
    with pytest.raises(StatsError, match="expected a list"):
        fetch_week(make_client({"stats/2025/1.json": {"rows": []}}), "2025", 1)


def test_source_errors_write_nothing(tmp_path):
    store = Store(tmp_path)
    report = refresh_season(make_client({"stats/2025/1.json": 503}), store, "2025", weeks=[1])
    assert not report.ok and "HTTP 503" in report.errors[0]
    bad = copy.deepcopy(ROWS)
    del bad[0]["stats"]
    report = refresh_season(make_client({"stats/2025/1.json": bad}), store, "2025", weeks=[1])
    assert not report.ok and "missing stats" in report.errors[0]
    assert not (tmp_path / "stats").exists()


def test_a_failing_week_blocks_the_whole_season_write(tmp_path):
    store = Store(tmp_path)
    report = refresh_season(make_client(), store, "2025", weeks=[1, 2])  # week 2 has no fixture -> 404
    assert not report.ok and "week 2" in report.errors[0]
    assert not store.stats_path("2025", 1).exists()


def test_upsert_drops_did_not_play_rows_and_stores_records(tmp_path):
    store = Store(tmp_path)
    result = upsert_week(store, "2025", 1, ROWS)
    assert result.added == len(PLAYED) and result.dropped == len(ROWS) - len(PLAYED) and result.written
    stored = store.read_stats("2025", 1)
    assert len(stored) == len(PLAYED)
    record = stored[str(PLAYED[0]["player_id"])]
    assert record["stats"] == PLAYED[0]["stats"]
    for key in ("position", "team", "last_modified"):
        assert record[key] is not None, key
    assert store.stats_weeks("2025") == [1]


def test_upsert_keeps_newer_version_only(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    before = digest(store.stats_path("2025", 1))
    same = upsert_week(store, "2025", 1, copy.deepcopy(ROWS))
    assert same.unchanged == len(PLAYED) and not same.written and digest(store.stats_path("2025", 1)) == before
    newer = copy.deepcopy(PLAYED[0])
    newer["last_modified"] += 1000
    newer["stats"]["rec"] = 99
    older = copy.deepcopy(PLAYED[1])
    older["last_modified"] -= 1000
    older["stats"]["rec"] = -1
    result = upsert_week(store, "2025", 1, [newer, older])
    assert result.updated == 1 and result.unchanged == 1
    stored = store.read_stats("2025", 1)
    assert stored[str(newer["player_id"])]["stats"]["rec"] == 99
    assert stored[str(older["player_id"])]["stats"] == PLAYED[1]["stats"]
    assert len(stored) == len(PLAYED), "players missing from the response are kept"


def test_empty_or_unplayed_response_leaves_store_alone(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    before = digest(store.stats_path("2025", 1))
    assert not upsert_week(store, "2025", 1, []).written
    assert not upsert_week(store, "2025", 1, [r for r in ROWS if not played(r)]).written
    assert digest(store.stats_path("2025", 1)) == before
    upsert_week(store, "2025", 9, [r for r in ROWS if not played(r)])
    assert not store.stats_path("2025", 9).exists()


def test_refresh_scope(tmp_path):
    report = refresh_stats(make_client(), Store(tmp_path), ["dynasty"])
    assert not report.ok and "run `ffapp sync` first" in report.errors[0]
    store = Store(tmp_path)
    cfg = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
    sync_league(make_client(), store, cfg)
    rows = load("stats/2025/1.json")
    overrides = {f"stats/2026/{w}.json": (copy.deepcopy(rows) if w == 1 else []) for w in range(1, 18)}
    for row in overrides["stats/2026/1.json"]:
        row["season"] = "2026"
    report = refresh_stats(make_client(overrides), store, ["dynasty"])
    assert report.ok and store.stats_weeks("2026") == [1], "current season only; empty weeks store nothing"
    seasons_requested = {url.split("/stats/nfl/")[1].split("/")[0] for url in make_client().request_count and [] or []}
    full = refresh_stats(make_client(overrides), store, ["dynasty"], backfill=True)
    assert not full.ok and any("2022 week 1" in e for e in full.errors), "backfill reaches the earliest stored season"


# -- scoring the stat lines reproduces Sleeper's credited points -----------------------


@pytest.mark.parametrize("league_key, league_id", [("dynasty", DYNASTY["2025"]), ("redraft", REDRAFT["2025"])])
def test_actual_points_match_players_points(tmp_path, league_key, league_id):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    league = load(f"league/{league_id}.json")
    cfg = LeagueConfig(key=league_key, league_id=league_id, name=league_key)
    scoring = resolve_settings(Config(leagues={league_key: cfg}), league_key, league, 1)
    stats = store.read_stats("2025", 1)
    compared, within, misses = 0, 0, []
    for team in load(f"league/{league_id}/matchups/1.json"):
        for pid, credited in (team.get("players_points") or {}).items():
            record = stats.get(str(pid))
            if record is None:
                continue
            compared += 1
            ours = actual_points(record, scoring)
            if abs(ours - float(credited)) <= 0.05:
                within += 1
            else:
                misses.append(f"{pid} {record.get('position')}: ours {ours:.2f} vs sleeper {credited}")
    assert compared >= 25
    assert within / compared >= 0.99, misses
    assert actual_points(None, scoring) == 0.0


def test_upsert_ignores_a_touched_but_unchanged_record(tmp_path):
    """Sleeper bumps last_modified without changing values: not a stat correction, nothing written."""
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    before = digest(store.stats_path("2025", 1))
    touched = copy.deepcopy(ROWS)
    for row in touched:
        row["last_modified"] = int(row.get("last_modified") or 0) + 1000
    result = upsert_week(store, "2025", 1, touched)
    assert result.updated == 0 and not result.written and digest(store.stats_path("2025", 1)) == before
