import hashlib
from pathlib import Path

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import fetch_season, season_weeks, sync_all, sync_league, walk_history
from tests.fixtures import DYNASTY, FixtureSession, load

DYNASTY_CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")


def make_client(overrides=None):
    session = FixtureSession(overrides)
    return SleeperClient(session, min_interval=0, sleep=lambda s: None), session


def tree_digest(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# -- 2.2 history walk ---------------------------------------------------------


def test_walk_full_dynasty_chain_newest_last():
    client, _ = make_client()
    chain = walk_history(client, DYNASTY["2026"])
    assert [l["season"] for l in chain] == ["2022", "2023", "2024", "2025", "2026"]
    assert chain[-1]["league_id"] == DYNASTY["2026"]


@pytest.mark.parametrize("terminator", [None, "", "0", 0])
def test_walk_three_season_chain_stops_on_terminator(terminator):
    patched = dict(load(f"league/{DYNASTY['2024']}.json"))
    patched["previous_league_id"] = terminator
    client, session = make_client({f"league/{DYNASTY['2024']}.json": patched})
    chain = walk_history(client, DYNASTY["2026"])
    assert [l["season"] for l in chain] == ["2024", "2025", "2026"]
    assert len(session.calls) == 3


def test_walk_guards_against_cycles():
    patched = dict(load(f"league/{DYNASTY['2024']}.json"))
    patched["previous_league_id"] = DYNASTY["2026"]
    client, _ = make_client({f"league/{DYNASTY['2024']}.json": patched})
    chain = walk_history(client, DYNASTY["2026"])
    assert [l["season"] for l in chain] == ["2024", "2025", "2026"]


# -- 2.3 per-season store, atomic ----------------------------------------------


def test_season_weeks_cover_regular_season_and_three_playoff_rounds():
    league = load(f"league/{DYNASTY['2025']}.json")
    assert list(season_weeks(league)) == list(range(1, 18))


def test_fetch_and_store_completed_season(tmp_path):
    client, _ = make_client()
    store = Store(tmp_path)
    league = load(f"league/{DYNASTY['2025']}.json")
    data = fetch_season(client, league)
    store.write_season("dynasty", data)

    base = tmp_path / "leagues" / "dynasty" / "2025"
    assert (base / "league.json").exists()
    assert (base / "users.json").exists()
    assert (base / "rosters.json").exists()
    assert (base / "brackets.json").exists()
    assert sorted(p.name for p in (base / "matchups").iterdir()) == [f"week_{w:02d}.json" for w in range(1, 18)]
    assert not list(base.glob(".*.tmp")), "no temp files left behind"

    again = store.read_season("dynasty", "2025")
    assert again.league == league
    assert len(again.winners_bracket) == 7 and len(again.losers_bracket) == 7
    assert sorted(again.matchups) == list(range(1, 18))
    assert store.seasons("dynasty") == ["2025"]


def test_failed_fetch_leaves_stored_files_byte_identical(tmp_path):
    store = Store(tmp_path)
    client, _ = make_client()
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    assert sync_all(client, store, config).ok
    before = tree_digest(tmp_path)

    # Second sync: week 15 of 2025 now fails on the server. Full mode forces a refetch.
    failing, _ = make_client({f"league/{DYNASTY['2025']}/matchups/15.json": 500})
    report = sync_league(failing, store, DYNASTY_CFG, full=True)
    assert not report.ok
    assert any("2025" in msg for _, msg in report.errors)
    assert ("dynasty", "2026") in report.fetched, "other seasons still sync"
    after = tree_digest(tmp_path)
    season_2025 = {k: v for k, v in before.items() if k.startswith(str(Path("leagues/dynasty/2025")))}
    assert season_2025, "sanity: 2025 files were stored by the first sync"
    for path, digest in season_2025.items():
        assert after[path] == digest, f"{path} changed after a failed fetch"


def test_history_walk_failure_is_reported(tmp_path):
    client, _ = make_client({f"league/{DYNASTY['2026']}.json": 503})
    report = sync_league(client, Store(tmp_path), DYNASTY_CFG)
    assert not report.ok and "history walk failed" in report.errors[0][1]


# -- 2.4 completed seasons are not re-fetched ----------------------------------


def test_routine_sync_skips_complete_seasons_and_full_refetches(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})

    client, session = make_client()
    report = sync_all(client, store, config)
    assert report.ok
    assert sorted(s for _, s in report.fetched) == ["2022", "2023", "2024", "2025", "2026"]
    first_run_calls = len(session.calls)
    # 5 league objects + per season (users, rosters, 17 matchups, 2 brackets)
    assert first_run_calls == 5 + 5 * (2 + 17 + 2)

    client, session = make_client()
    report = sync_all(client, store, config)
    assert report.ok
    assert sorted(s for _, s in report.skipped) == ["2022", "2023", "2024", "2025"]
    assert [s for _, s in report.fetched] == ["2026"]
    assert len(session.calls) == 5 + (2 + 17 + 2), "only the in-progress season is fetched"

    client, session = make_client()
    report = sync_all(client, store, config, full=True)
    assert report.ok and not report.skipped
    assert len(session.calls) == first_run_calls


def test_in_progress_season_stores_unplayed_weeks(tmp_path):
    store = Store(tmp_path)
    client, _ = make_client()
    sync_league(client, store, DYNASTY_CFG)
    week9 = store.read_matchups("dynasty", "2026", 9)
    week14 = store.read_matchups("dynasty", "2026", 14)
    assert all(t["points"] > 0 for t in week9)
    assert all(t["points"] == 0 for t in week14) and all(t["matchup_id"] for t in week14)
