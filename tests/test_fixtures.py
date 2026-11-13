"""Every recorded fixture loads and carries the fields the design relies on."""

import pytest

from tests.fixtures import DYNASTY, REDRAFT, SLEEPER_ROOT, load

ALL_LEAGUE_IDS = sorted(set(DYNASTY.values()) | set(REDRAFT.values()))
FULL_SEASONS = [DYNASTY["2025"], REDRAFT["2025"]]


@pytest.mark.parametrize("league_id", ALL_LEAGUE_IDS)
def test_league_fixture_fields(league_id):
    league = load(f"league/{league_id}.json")
    assert league["league_id"] == league_id
    assert league["season"].isdigit()
    assert league["status"] in {"complete", "in_season", "pre_draft", "drafting", "post_season"}
    assert league["total_rosters"] == 12
    assert "previous_league_id" in league
    assert isinstance(league["scoring_settings"], dict) and league["scoring_settings"]
    assert "FLEX" in league["roster_positions"]
    settings = league["settings"]
    for key in ("playoff_teams", "playoff_week_start", "playoff_seed_type", "last_scored_leg"):
        assert key in settings, key
    assert settings["playoff_teams"] == 6
    assert settings["playoff_week_start"] == 15


def test_chain_ends_with_zero_string():
    assert load(f"league/{DYNASTY['2022']}.json")["previous_league_id"] == "0"


def test_chain_links_dynasty_seasons():
    seasons = sorted(DYNASTY)
    for newer, older in zip(seasons[1:], seasons[:-1]):
        assert load(f"league/{DYNASTY[newer]}.json")["previous_league_id"] == DYNASTY[older]


@pytest.mark.parametrize("league_id", [DYNASTY["2022"], DYNASTY["2025"], DYNASTY["2026"], REDRAFT["2025"], REDRAFT["2026"]])
def test_users_and_rosters(league_id):
    users = load(f"league/{league_id}/users.json")
    rosters = load(f"league/{league_id}/rosters.json")
    assert len(rosters) == 12
    user_ids = {u["user_id"] for u in users}
    for user in users:
        assert user["display_name"]
    for roster in rosters:
        assert roster["roster_id"] in range(1, 13)
        assert roster["owner_id"] in user_ids
        assert isinstance(roster["players"], list)
        assert "reserve" in roster and "taxi" in roster
        assert set(roster["settings"]) >= {"wins", "losses", "ties", "fpts"}


@pytest.mark.parametrize("league_id", FULL_SEASONS)
def test_full_season_matchups(league_id):
    for week in range(1, 18):
        matchups = load(f"league/{league_id}/matchups/{week}.json")
        assert len(matchups) == 12, week
        for team in matchups:
            assert "roster_id" in team and "points" in team
            assert isinstance(team["players"], list) and isinstance(team["starters"], list)
            assert isinstance(team["players_points"], dict)
        if week <= 14:
            assert all(t["matchup_id"] for t in matchups), f"week {week} missing pairings"
            ids = [t["matchup_id"] for t in matchups]
            assert all(ids.count(m) == 2 for m in ids)


@pytest.mark.parametrize("league_id", FULL_SEASONS)
def test_brackets(league_id):
    winners = load(f"league/{league_id}/winners_bracket.json")
    losers = load(f"league/{league_id}/losers_bracket.json")
    assert len(winners) == 7 and len(losers) == 7
    for game in winners + losers:
        assert {"r", "m", "t1", "t2", "w", "l"} <= set(game)
        assert game["w"] is not None, "completed season has every bracket game decided"
    assert sorted({g["r"] for g in winners}) == [1, 2, 3]


def test_in_progress_season_week_10_is_not_scored():
    # Recorded on a Friday: week 10's Thursday game had been played, so some teams already
    # show partial points, but Sleeper's last_scored_leg still says 9. That is the
    # "week partly played" case the simulation must treat as unplayed.
    league = load(f"league/{DYNASTY['2026']}.json")
    assert league["status"] == "in_season"
    assert league["settings"]["last_scored_leg"] == 9
    week9 = load(f"league/{DYNASTY['2026']}/matchups/9.json")
    week10 = load(f"league/{DYNASTY['2026']}/matchups/10.json")
    assert all(t["points"] > 0 for t in week9)
    assert sum(t["points"] for t in week10) < sum(t["points"] for t in week9) / 2
    assert all(t["matchup_id"] for t in week10), "schedule is known before the week is played"
    for week in range(11, 18):
        assert len(load(f"league/{DYNASTY['2026']}/matchups/{week}.json")) == 12


def test_state():
    state = load("state/nfl.json")
    assert state["season"] == "2026"
    assert state["week"] == 10
    assert state["season_type"] == "regular"


def test_projections_fixture_shape():
    rows = load("projections/2025/1.json")
    assert isinstance(rows, list) and len(rows) >= 30
    # Sleeper returns a stats dict for every player; only rows with pts_* keys are projections.
    # The rest carry nothing but ADP fields and are dropped by the upsert.
    with_stats = [r for r in rows if any(k.startswith("pts_") for k in r["stats"])]
    without_stats = [r for r in rows if not any(k.startswith("pts_") for k in r["stats"])]
    assert len(without_stats) >= 3, "fixture keeps a few ADP-only rows for the drop test"
    assert all("adp_dd_ppr" in r["stats"] for r in without_stats)
    positions = {r["player"]["position"] for r in with_stats}
    assert positions == {"QB", "RB", "WR", "TE", "K", "DEF"}
    for row in with_stats:
        for key in ("player_id", "season", "week", "stats", "last_modified", "team", "opponent", "company"):
            assert key in row, key
        assert row["season"] == "2025" and row["week"] == 1
    kicker = next(r for r in with_stats if r["player"]["position"] == "K")
    assert "fgm_yds" in kicker["stats"] and "xpm" in kicker["stats"]


def test_fixture_tree_is_small():
    total = sum(p.stat().st_size for p in SLEEPER_ROOT.rglob("*.json"))
    assert total < 6 * 1024 * 1024, "fixtures should stay a few MB at most"
