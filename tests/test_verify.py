import copy

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import fetch_season, sync_league
from ffapp.verify import check_season, verify_all
from tests.fixtures import DYNASTY, REDRAFT, FixtureSession, load


def season_data(league_id):
    client = SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None)
    return fetch_season(client, load(f"league/{league_id}.json"))


@pytest.mark.parametrize(
    "league_key, league_id",
    [
        ("dynasty", DYNASTY["2022"]),
        ("dynasty", DYNASTY["2023"]),
        ("dynasty", DYNASTY["2024"]),
        ("dynasty", DYNASTY["2025"]),
        ("redraft", REDRAFT["2025"]),
    ],
)
def test_real_brackets_are_reproduced(league_key, league_id):
    check = check_season(league_key, season_data(league_id))
    assert check.ok, check.mismatches


def test_mismatch_is_reported_with_league_season_and_pairing():
    data = season_data(DYNASTY["2025"])
    # swap the two round-1 pairings' opponents so the real bracket no longer matches ours
    tampered = copy.deepcopy(data.winners_bracket)
    r1 = [g for g in tampered if g["r"] == 1]
    r1[0]["t2"], r1[1]["t2"] = r1[1]["t2"], r1[0]["t2"]
    data.winners_bracket = tampered
    check = check_season("dynasty", data)
    assert not check.ok
    assert check.season == "2025" and check.league_key == "dynasty"
    assert any(m.startswith("winners round 1") for m in check.mismatches)


def test_wrong_reseed_rule_is_caught():
    # 2022: seeds 4 and 6 won round 1, so fixed (1v4, 2v6) and re-seeded (1v6, 2v4) differ
    data = season_data(DYNASTY["2022"])
    data.league = copy.deepcopy(data.league)
    data.league["settings"]["playoff_seed_type"] = 0  # pretend dynasty used a fixed bracket
    check = check_season("dynasty", data)
    assert any("winners round 2" in m for m in check.mismatches)


def test_wrong_losers_style_is_caught():
    data = season_data(REDRAFT["2025"])
    data.league = copy.deepcopy(data.league)
    data.league["settings"]["playoff_type"] = 1  # pretend redraft ran a consolation bracket
    check = check_season("redraft", data)
    assert any("losers round 1" in m for m in check.mismatches)


def test_in_progress_season_is_skipped(tmp_path):
    store = Store(tmp_path)
    cfg = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, cfg)
    checks = verify_all(store, Config(leagues={"dynasty": cfg}))
    assert sorted(c.season for c in checks) == ["2022", "2023", "2024", "2025"]
    assert all(c.ok for c in checks)
