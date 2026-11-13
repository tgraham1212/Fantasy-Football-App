import copy
import hashlib

import pytest

from ffapp.projections import (
    ProjectionsError,
    fetch_week,
    is_projection,
    refresh_projections,
    refresh_season,
    upsert_week,
    validate_rows,
)
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store
from tests.fixtures import FixtureSession, load

ROWS = load("projections/2025/1.json")
PROJECTED = [r for r in ROWS if is_projection(r)]


def make_client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


# -- 3.1 source function and shape checks -------------------------------------


def test_fetch_week_accepts_fixture():
    rows = fetch_week(make_client(), "2025", 1)
    assert len(rows) == len(ROWS)
    assert sum(is_projection(r) for r in rows) == 30


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"rows": []}, "expected a list"),
        ([{"player_id": "1", "season": "2025", "week": 1}], "missing stats"),
        ([{"player_id": "1", "season": "2025", "week": 1, "stats": None}], "stats is not an object"),
        (["nope"], "not an object"),
        ([{"player_id": "1", "season": "2024", "week": 1, "stats": {}}], "is for 2024"),
    ],
)
def test_validate_rejects_bad_shapes(payload, message):
    with pytest.raises(ProjectionsError, match=message):
        validate_rows(payload, "2025", 1)


def test_source_errors_write_nothing(tmp_path):
    store = Store(tmp_path)
    # non-list body
    report = refresh_season(make_client({"projections/2025/1.json": {"rows": []}}), store, "2025", weeks=[1])
    assert not report.ok and "expected a list" in report.errors[0]
    # missing stats on a row
    bad = copy.deepcopy(ROWS)
    del bad[0]["stats"]
    report = refresh_season(make_client({"projections/2025/1.json": bad}), store, "2025", weeks=[1])
    assert not report.ok and "missing stats" in report.errors[0]
    # HTTP error
    report = refresh_season(make_client({"projections/2025/1.json": 500}), store, "2025", weeks=[1])
    assert not report.ok and "HTTP 500" in report.errors[0]
    assert not (tmp_path / "projections").exists(), "nothing was written"


def test_a_failing_week_blocks_the_whole_season_write(tmp_path):
    store = Store(tmp_path)
    # week 1 is fine, week 2 404s (no fixture): nothing is written for the season
    report = refresh_season(make_client(), store, "2025", weeks=[1, 2])
    assert not report.ok and "week 2" in report.errors[0]
    assert not store.projections_path("2025", 1).exists()


# -- 3.2 upsert ----------------------------------------------------------------


def test_upsert_drops_adp_only_rows_and_stores_records(tmp_path):
    store = Store(tmp_path)
    result = upsert_week(store, "2025", 1, ROWS)
    assert result.added == 30 and result.dropped == len(ROWS) - 30 and result.written
    stored = store.read_projections("2025", 1)
    assert len(stored) == 30
    record = stored[str(PROJECTED[0]["player_id"])]
    assert record["stats"] == PROJECTED[0]["stats"]
    for key in ("position", "team", "opponent", "company", "last_modified"):
        assert record[key] is not None, key


def test_upsert_unchanged_when_same_version(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    before = digest(store.projections_path("2025", 1))
    result = upsert_week(store, "2025", 1, copy.deepcopy(ROWS))
    assert result.unchanged == 30 and result.added == 0 and result.updated == 0
    assert not result.written and digest(store.projections_path("2025", 1)) == before


def test_upsert_replaces_only_newer_versions(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    newer = copy.deepcopy(PROJECTED[0])
    newer["last_modified"] += 1000
    newer["stats"]["pts_half_ppr"] = 99.9
    older = copy.deepcopy(PROJECTED[1])
    older["last_modified"] -= 1000
    older["stats"]["pts_half_ppr"] = -1.0
    result = upsert_week(store, "2025", 1, [newer, older])
    assert result.updated == 1 and result.unchanged == 1
    stored = store.read_projections("2025", 1)
    assert stored[str(newer["player_id"])]["stats"]["pts_half_ppr"] == 99.9
    assert stored[str(older["player_id"])]["stats"] == PROJECTED[1]["stats"]
    assert len(stored) == 30, "players missing from the response are kept"


def test_upsert_empty_response_leaves_file_untouched(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 1, ROWS)
    before = digest(store.projections_path("2025", 1))
    assert not upsert_week(store, "2025", 1, []).written
    adp_only = [r for r in ROWS if not is_projection(r)]
    assert not upsert_week(store, "2025", 1, adp_only).written
    assert digest(store.projections_path("2025", 1)) == before


def test_upsert_empty_response_for_new_week_creates_nothing(tmp_path):
    store = Store(tmp_path)
    upsert_week(store, "2025", 7, [])
    assert not store.projections_path("2025", 7).exists()


# -- refresh scope ---------------------------------------------------------------


def test_refresh_requires_synced_seasons(tmp_path):
    report = refresh_projections(make_client(), Store(tmp_path), ["dynasty"])
    assert not report.ok and "run `ffapp sync` first" in report.errors[0]
