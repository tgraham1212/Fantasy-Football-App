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
    # 5 league objects + per season (users, rosters, 17 matchups, 2 brackets, 17 weeks of transactions,
    # the draft, its picks and traded picks) + one ADP request per season
    assert first_run_calls == 5 + 5 * (2 + 17 + 2 + 17 + 3) + 5

    client, session = make_client()
    report = sync_all(client, store, config)
    assert report.ok
    assert sorted(s for _, s in report.skipped) == ["2022", "2023", "2024", "2025"]
    assert [s for _, s in report.fetched] == ["2026"]
    assert len(session.calls) == 5 + (2 + 17 + 2 + 17), "only the in-progress season is fetched"

    client, session = make_client()
    report = sync_all(client, store, config, full=True)
    assert report.ok and not report.skipped
    assert len(session.calls) == first_run_calls - 5 * 3 - 5, "complete drafts and stored ADP are kept"


def test_in_progress_season_stores_unplayed_weeks(tmp_path):
    store = Store(tmp_path)
    client, _ = make_client()
    sync_league(client, store, DYNASTY_CFG)
    week9 = store.read_matchups("dynasty", "2026", 9)
    week14 = store.read_matchups("dynasty", "2026", 14)
    assert all(t["points"] > 0 for t in week9)
    assert all(t["points"] == 0 for t in week14) and all(t["matchup_id"] for t in week14)


# -- managers-moves: transactions -----------------------------------------------


def test_transactions_saved_for_every_week(tmp_path):
    store = Store(tmp_path)
    week3 = [{"type": "free_agent", "status": "complete", "adds": {"1": 2}, "drops": None, "leg": 3}]
    client, _ = make_client({f"league/{DYNASTY['2025']}/transactions/3.json": week3})
    assert sync_league(client, store, DYNASTY_CFG).ok
    saved = store.read_transactions("dynasty", "2025")
    assert sorted(saved) == list(season_weeks(store.read_league("dynasty", "2025")))
    assert saved[3] == week3 and saved[4] == []


def test_completed_season_without_transactions_is_backfilled_once(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    client, _ = make_client()
    assert sync_all(client, store, config).ok
    # as stored before transactions were kept
    import shutil
    shutil.rmtree(tmp_path / "leagues" / "dynasty" / "2024" / "transactions")

    client, session = make_client()
    report = sync_all(client, store, config)
    assert ("dynasty", "2024") in report.skipped and ("dynasty", "2024") in report.transactions
    assert sum("/transactions/" in c and DYNASTY["2024"] in c for c in session.calls) == 17
    assert store.has_transactions("dynasty", "2024")

    client, session = make_client()
    report = sync_all(client, store, config)
    assert not any(DYNASTY["2024"] in c and "/transactions/" in c for c in session.calls), "fetched only once"
    assert report.transactions == [("dynasty", "2026")], "the current season is fetched again every sync"


def test_transactions_failure_keeps_files_and_only_warns(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    week5 = [{"type": "waiver", "status": "complete", "adds": {"9": 1}, "drops": None, "leg": 5, "settings": {"waiver_bid": 7}}]
    client, _ = make_client({f"league/{DYNASTY['2026']}/transactions/5.json": week5})
    assert sync_all(client, store, config).ok
    before = tree_digest(tmp_path / "leagues" / "dynasty" / "2026" / "transactions")

    failing, _ = make_client({f"league/{DYNASTY['2026']}/transactions/9.json": 500})
    report = sync_all(failing, store, config)
    assert report.ok, "a transactions failure never fails the sync"
    assert report.warnings and "2026" in report.warnings[0][1]
    assert ("dynasty", "2026") in report.fetched, "matchups still sync"
    assert tree_digest(tmp_path / "leagues" / "dynasty" / "2026" / "transactions") == before


# -- league-draft: drafts and ADP -------------------------------------------------

STARTUP_DRAFT = "780973042817171456"  # the 2022 dynasty startup draft (Yahoo roster transfer)


def test_league_draft_stored(tmp_path):
    store = Store(tmp_path)
    client, session = make_client()
    report = sync_league(client, store, DYNASTY_CFG)
    assert report.ok
    stored = store.read_draft("dynasty", "2022")
    assert stored["draft"]["settings"]["rounds"] == 3 and len(stored["picks"]) == 36
    assert stored["traded_picks"], "traded picks kept"
    assert not any(STARTUP_DRAFT in c for c in session.calls), "the startup draft is never fetched"
    assert ("dynasty", "2026") in report.drafts


def test_complete_draft_fetched_once(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    client, _ = make_client()
    assert sync_all(client, store, config).ok
    (tmp_path / "leagues" / "dynasty" / "2023" / "draft.json").unlink()   # as stored before drafts were kept

    client, session = make_client()
    report = sync_all(client, store, config)
    assert ("dynasty", "2023") in report.skipped and ("dynasty", "2023") in report.drafts
    assert store.has_draft("dynasty", "2023")

    client, session = make_client()
    report = sync_all(client, store, config)
    assert not any("/v1/draft/" in c for c in session.calls), "complete drafts are not fetched again"
    assert report.drafts == []


def test_incomplete_draft_fetched_every_sync(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    draft_id = str(load(f"league/{DYNASTY['2026']}.json")["draft_id"])
    pending = dict(load(f"draft/{draft_id}.json"))
    pending["status"] = "drafting"
    client, _ = make_client({f"draft/{draft_id}.json": pending})
    sync_all(client, store, config)
    client, session = make_client()
    report = sync_all(client, store, config)
    assert any(f"/v1/draft/{draft_id}" in c for c in session.calls) and ("dynasty", "2026") in report.drafts


def test_draft_failure_keeps_files_and_only_warns(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    draft_id = str(load(f"league/{DYNASTY['2026']}.json")["draft_id"])
    pending = dict(load(f"draft/{draft_id}.json"))
    pending["status"] = "drafting"
    client, _ = make_client({f"draft/{draft_id}.json": pending})
    assert sync_all(client, store, config).ok
    before = (tmp_path / "leagues" / "dynasty" / "2026" / "draft.json").read_bytes()

    failing, _ = make_client({f"draft/{draft_id}/picks.json": 500})
    report = sync_all(failing, store, config)
    assert report.ok, "a draft failure never fails the sync"
    assert any("draft for season 2026" in w for _, w in report.warnings)
    assert ("dynasty", "2026") in report.fetched, "matchups still sync"
    assert (tmp_path / "leagues" / "dynasty" / "2026" / "draft.json").read_bytes() == before


def test_adp_stored_once_after_drafts(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    client, _ = make_client()
    report = sync_all(client, store, config)
    assert report.adp == ["2022", "2023", "2024", "2025", "2026"]
    adp = store.read_adp("2025")
    jeanty = next(v for v in adp.values() if v.get("adp_dynasty_half_ppr") == 7.8)
    assert jeanty["position"] == "RB" and all(v.get(k, 0) < 999 for v in adp.values() for k in v if k != "position")

    client, session = make_client()
    report = sync_all(client, store, config)
    assert report.adp == [] and not any("/projections/nfl/2025?" in c for c in session.calls)


def test_adp_waits_for_incomplete_draft(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    draft_id = str(load(f"league/{DYNASTY['2026']}.json")["draft_id"])
    pending = dict(load(f"draft/{draft_id}.json"))
    pending["status"] = "drafting"
    client, _ = make_client({f"draft/{draft_id}.json": pending})
    report = sync_all(client, store, config)
    assert "2026" not in report.adp and not store.has_adp("2026")


def test_adp_failure_only_warns(tmp_path):
    store = Store(tmp_path)
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    client, _ = make_client({"projections/2026/season.json": 500})
    report = sync_all(client, store, config)
    assert report.ok and not store.has_adp("2026")
    assert any("2026" in w for k, w in report.warnings if k == "adp")
    client, session = make_client()
    report = sync_all(client, store, config)
    assert report.adp == ["2026"], "the next sync tries again"
