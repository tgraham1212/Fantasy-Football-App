import json
import math

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.store import SeasonData, Store
from ffapp.war import (
    Constants,
    WeekRecord,
    baseline_wins,
    build_war,
    consensus_lineup,
    cut_mode,
    owner_attribution,
    player_weeks,
    read_war,
    season_constants,
    stat_totals,
    war_seasons,
    win_probability,
    write_war,
)

# -- lineup and cut -------------------------------------------------------------------------


def test_consensus_lineup_skips_unavailable_and_flex_moves_the_cut():
    ranked = {"QB": ["q1", "q2", "q3", "q4"], "RB": ["r1", "r2", "r3", "r4", "r5"], "WR": ["w1", "w2"]}
    started = {"q1": 90, "q2": 80, "q3": 70, "q4": 60, "r1": 95, "r2": 85, "r3": 50, "r4": 40, "r5": 10, "w1": 45, "w2": 30}
    lineup = consensus_lineup(ranked, {"QB": 2, "RB": 2}, {"FLEX": 2}, lambda pid: pid != "q1", started)
    assert lineup.starters == {"QB": ["q2", "q3"], "RB": ["r1", "r2"]}  # q1 is on bye
    assert lineup.flex == ["r3", "w1"]  # most-started leftovers across RB/WR/TE, by percent not by position rank
    assert lineup.replacement == {"QB": ["q4"], "RB": ["r4", "r5"]}  # r3 went to flex, so the RB cut moved past him


def test_consensus_lineup_without_flex_keeps_three_past_the_cut():
    ranked = {"TE": [f"t{i}" for i in range(1, 8)]}
    lineup = consensus_lineup(ranked, {"TE": 2}, {}, lambda pid: True, {})
    assert lineup.starters["TE"] == ["t1", "t2"] and lineup.flex == [] and lineup.replacement["TE"] == ["t3", "t4", "t5"]


# -- season constants ------------------------------------------------------------------------


def test_season_constants_pool_slots_and_weight_by_slots_per_team():
    records = [
        WeekRecord(1, {"QB": [20.0, 10.0], "RB": [10.0, 10.0, 14.0, 6.0], "FLEX": [8.0, 12.0]}, {"QB": 12.0, "RB": 7.0}),
        WeekRecord(2, {"QB": [16.0, 14.0], "RB": [12.0, 8.0, 10.0, 10.0], "FLEX": [10.0, 10.0]}, {"QB": 14.0, "RB": 9.0}),
    ]
    c = season_constants(records, {"QB": 2, "RB": 4}, {"FLEX": 2}, teams=2)
    assert c.slot_mean == {"QB": 15.0, "RB": 10.0, "FLEX": 10.0}
    assert c.slot_var["QB"] == pytest.approx(52.0 / 3)  # sample variance of 20, 10, 16, 14
    assert c.opponent_mean == 15.0 + 2 * 10.0 + 10.0  # one QB, two RB, one flex per team
    assert c.opponent_sd == pytest.approx(math.sqrt(c.slot_var["QB"] + 2 * c.slot_var["RB"] + c.slot_var["FLEX"]))
    assert c.replacement == {"QB": 13.0, "RB": 8.0}


# -- win probability and WAR -----------------------------------------------------------------


def test_win_probability_matches_spec_example():
    assert win_probability(31.3, 9.2, 20.7) == pytest.approx(0.857, abs=0.002)
    assert win_probability(9.2, 9.2, 20.7) == 0.5
    assert win_probability(10.0, 5.0, 0.0) == 1.0 and win_probability(5.0, 5.0, 0.0) == 0.5


def constants():
    return Constants(slot_mean={"TE": 9.2}, slot_var={"TE": 0.0}, opponent_mean=100.0, opponent_sd=20.7, replacement={"TE": 6.1})


def test_player_weeks_fill_missed_weeks_with_replacement_and_keep_zero_when_played():
    rows, total = player_weeks({1: 31.3, 3: 0.0}, [1, 2, 3], "TE", constants())
    assert [r["played"] for r in rows] == [True, False, True]
    assert rows[1]["score"] == 6.1 and rows[1]["p"] == pytest.approx(win_probability(6.1, 9.2, 20.7), abs=1e-4)
    assert rows[2]["score"] == 0.0 and rows[2]["p"] == pytest.approx(win_probability(0.0, 9.2, 20.7), abs=1e-4)
    assert total == pytest.approx(sum(r["p"] for r in rows), abs=1e-3)


def test_replacement_season_has_zero_war_and_spec_example_gives_154():
    c = constants()
    rows, total = player_weeks({w: 6.1 for w in range(1, 15)}, list(range(1, 15)), "TE", c)
    assert total - baseline_wins("TE", 14, c) == pytest.approx(0.0, abs=1e-9)
    assert 7.70 - 6.16 == pytest.approx(1.54)


# -- cut mode --------------------------------------------------------------------------------


def test_cut_mode(tmp_path):
    store = Store(tmp_path / "data")
    assert cut_mode(store, "2024", [1, 2, 3]) == "yearly"
    for w in (1, 2, 3):
        store.write_espn_week("2024", w, {"players": {}})
    assert cut_mode(store, "2024", [1, 2, 3]) == "weekly"
    assert cut_mode(store, "2024", [1, 2, 3, 4]) == "yearly"  # partly captured
    assert cut_mode(store, "2024", []) == "yearly"


# -- owners and stats --------------------------------------------------------------------------


def test_owner_attribution():
    held = {"p": [(1, "A"), (2, "A"), (3, "B")]}
    assert owner_attribution("p", held, None) == ("B", ["A", "B"])  # completed season: end-of-season holder
    assert owner_attribution("p", held, {"p": "C"}) == ("C", ["A", "B", "C"])  # in progress: current roster
    assert owner_attribution("p", held, {}) == (None, ["A", "B"])  # in progress but dropped
    assert owner_attribution("x", held, None) == (None, [])


def test_stat_totals_sum_and_points_allowed_per_game():
    lines = [{"stats": {"sack": 3, "int": 1, "pts_allow": 20}}, {"stats": {"sack": 2, "pts_allow": 10, "def_td": 1}}]
    assert stat_totals("DEF", lines, 2) == {"sack": 5.0, "int": 1.0, "fum_rec": 0.0, "def_td": 1.0, "pts_allow": 15.0}
    assert stat_totals("QB", [{"stats": {"pass_yd": 300, "pass_td": 2}}], 1) == {"pass_yd": 300.0, "pass_td": 2.0, "pass_int": 0.0, "rush_yd": 0.0, "rush_td": 0.0}


# -- the run --------------------------------------------------------------------------------------


LEAGUE_ID = "900000000000000001"


def synthetic_store(tmp_path, *, status="complete", weekly_snapshots=False, season="2025"):
    """A two-team league with QB, RB, WR, FLEX slots, two scored weeks, stats, a snapshot and a crosswalk."""
    store = Store(tmp_path / "data")
    league = {
        "league_id": LEAGUE_ID, "season": season, "status": status, "name": "Tiny", "previous_league_id": None,
        "roster_positions": ["QB", "RB", "WR", "FLEX", "BN"],
        "scoring_settings": {"pass_yd": 0.04, "pass_td": 4, "rush_yd": 0.1, "rush_td": 6, "rec": 0.5, "rec_yd": 0.1, "rec_td": 6},
        "settings": {"num_teams": 2, "playoff_week_start": 3, "playoff_teams": 6, "last_scored_leg": 2, "start_week": 1, "playoff_type": 1, "type": 0, "leg": 2},
    }
    users = [{"user_id": "A", "display_name": "Alice"}, {"user_id": "B", "display_name": "Bob"}]
    rosters = [
        {"roster_id": 1, "owner_id": "A", "players": ["q1", "r1", "r3", "w2"], "reserve": [], "taxi": []},
        {"roster_id": 2, "owner_id": "B", "players": ["q2", "r2", "w1", "w3"], "reserve": [], "taxi": []},
    ]
    matchups = {
        1: [{"roster_id": 1, "matchup_id": 1, "players": ["q1", "r1", "r3", "w2"], "starters": ["q1", "r1", "w2", "r3"], "points": 0},
            {"roster_id": 2, "matchup_id": 1, "players": ["q2", "r2", "w1", "w3"], "starters": ["q2", "r2", "w1", "w3"], "points": 0}],
        2: [{"roster_id": 1, "matchup_id": 1, "players": ["q1", "r1", "w1", "w2"], "starters": ["q1", "r1", "w2", "w1"], "points": 0},
            {"roster_id": 2, "matchup_id": 1, "players": ["q2", "r2", "r3", "w3"], "starters": ["q2", "r2", "w3", "r3"], "points": 0}],
    }
    store.write_season("tiny", SeasonData(league=league, users=users, rosters=rosters, matchups=matchups))

    def line(first, pos, team, **stats):
        return {"first_name": first, "last_name": "Test", "position": pos, "team": team, "stats": {"pts_half_ppr": 1, **stats}}

    week1 = {
        "q1": line("Q1", "QB", "BUF", pass_yd=300, pass_td=2), "q2": line("Q2", "QB", "KC", pass_yd=200), "q3": line("Q3", "QB", "NE", pass_yd=100),
        "r1": line("R1", "RB", "SF", rush_yd=100, rush_td=1), "r2": line("R2", "RB", "DET", rush_yd=80), "r3": line("R3", "RB", "LV", rush_yd=50),
        "r4": line("R4", "RB", "NYJ", rush_yd=30), "r5": line("R5", "RB", "CHI", rush_yd=10),
        "w1": line("W1", "WR", "DAL", rec=6, rec_yd=90), "w2": line("W2", "WR", "MIA", rec=5, rec_yd=70),
        "w3": line("W3", "WR", "PHI", rec=4, rec_yd=40), "w4": line("W4", "WR", "SEA", rec=2, rec_yd=20),
    }
    week2 = {k: v for k, v in week1.items() if k != "r3"}  # r3 has no game in week 2
    week2["w4"] = line("W4", "WR", "SEA", rec=0, rec_yd=0)  # played and scored nothing
    store.write_stats(season, 1, week1)
    store.write_stats(season, 2, week2)
    espn = {"name": None}
    players = {}
    started = {"q1": 90, "q2": 80, "q3": 20, "r1": 95, "r2": 85, "r3": 50, "r4": 10, "r5": 3, "w1": 88, "w2": 70, "w3": 40, "w4": 8}
    for i, (pid, pct) in enumerate(started.items()):
        players[str(1000 + i)] = {"name": pid.upper() + " Test", "position": week1[pid]["position"], "team": week1[pid]["team"], "started": float(pct), "owned": 99.0}
    store.write_espn_season(season, {"season": season, "week": None, "players": players})
    if weekly_snapshots:
        for w in (1, 2):
            store.write_espn_week(season, w, {"season": season, "week": w, "players": players})
    store.write_crosswalk({pid: {"espn_id": espn_id, "name": rec["name"], "position": rec["position"]} for espn_id, rec in players.items() for pid in [rec["name"].split()[0].lower()]})
    # a retired player listed in the crosswalk with no stat line
    cw = store.read_crosswalk()
    cw["old"] = {"espn_id": None, "name": "Old Timer", "position": "RB"}
    store.write_crosswalk(cw)
    return store


def tiny_config():
    return Config(leagues={"tiny": LeagueConfig(key="tiny", league_id=LEAGUE_ID, name="Tiny")})


def test_build_war_on_a_synthetic_season(tmp_path):
    store = synthetic_store(tmp_path)
    war = build_war(store, tiny_config(), "tiny", "2025")
    assert war["cut"] == "yearly" and war["through_week"] == 2 and war["weeks"] == [1, 2]
    # consensus: QB q1,q2; RB r1,r2; WR w1,w2; flex r3,w3 in week 1 and w3,r4 in week 2 (r3 has no game);
    # replacement: QB q3 both weeks, RB r4,r5 then r5, WR w4 both weeks
    assert set(war["players"]) == {"q1", "q2", "q3", "r1", "r2", "r3", "r4", "r5", "w1", "w2", "w3", "w4"} and "old" not in war["players"]
    assert war["players"]["r3"]["games"] == 1 and war["players"]["r3"]["weekly"][1]["played"] is False
    assert war["players"]["w4"]["games"] == 2 and war["players"]["w4"]["weekly"][1]["score"] == 0.0 and war["players"]["w4"]["weekly"][1]["played"] is True
    assert set(war["replacement"]) == {"QB", "RB", "WR"} and set(war["constants"]["slot_mean"]) == {"QB", "RB", "WR", "FLEX"}
    assert war["replacement"]["QB"]["level"] == pytest.approx(100 * 0.04)
    assert war["replacement"]["RB"]["level"] == pytest.approx(((3.0 + 1.0) / 2 + 1.0) / 2)  # mean of r4,r5 in week 1 and r5 alone in week 2
    assert war["constants"]["slot_mean"]["FLEX"] == pytest.approx((5.0 + 6.0 + 6.0 + 3.0) / 4)  # r3,w3 then w3,r4
    assert war["players"]["q1"]["owner"] == "A" and war["players"]["w1"]["owner"] == "A" and war["players"]["w1"]["holders"] == ["B", "A"]
    assert war["players"]["q3"]["owner"] is None and war["players"]["q3"]["holders"] == []
    assert war["players"]["q1"]["stats"] == {"pass_yd": 600.0, "pass_td": 4.0, "pass_int": 0.0, "rush_yd": 0.0, "rush_td": 0.0}
    assert war["players"]["q1"]["points"] == pytest.approx(2 * (300 * 0.04 + 8))
    top = next(iter(war["players"]))
    assert top == "q1" and war["players"]["q1"]["war"] > 0
    assert war["players"]["q3"]["war"] == pytest.approx(0.0, abs=1e-6)  # q3 is the replacement QB both weeks
    assert war["players"]["r5"]["war"] < 0  # below the RB replacement level in week 1
    for pos, rep in war["replacement"].items():
        rows, total = player_weeks({1: rep["level"], 2: rep["level"]}, [1, 2], pos, Constants(
            slot_mean=war["constants"]["slot_mean"], slot_var={}, opponent_mean=0, opponent_sd=war["constants"]["opponent_sd"], replacement={pos: rep["level"]}))
        assert total == pytest.approx(rep["baseline_wins"], abs=1e-3)


def test_build_war_weekly_cut_and_in_progress_owner(tmp_path):
    store = synthetic_store(tmp_path, status="in_season", weekly_snapshots=True)
    war = build_war(store, tiny_config(), "tiny", "2025")
    assert war["cut"] == "weekly"
    assert war["players"]["w1"]["owner"] == "B"  # current roster wins while the season is in progress
    assert war["players"]["r3"]["owner"] == "A" and war["players"]["r3"]["holders"] == ["A", "B"]


def test_write_war_writes_every_season_and_is_deterministic(tmp_path):
    store = synthetic_store(tmp_path)
    report = write_war(store, tiny_config(), "tiny")
    assert [p.name for p in report.written] == ["2025.json"] and report.skipped == []
    first = read_war(store, "tiny", "2025")
    second_report = write_war(store, tiny_config(), "tiny")
    second = read_war(store, "tiny", "2025")
    first.pop("generated_at"), second.pop("generated_at")
    assert first == second and war_seasons(store, "tiny") == ["2025"]


def test_write_war_skips_and_reports_a_season_without_snapshot(tmp_path):
    store = synthetic_store(tmp_path)
    store.espn_season_path("2025").unlink()
    report = write_war(store, tiny_config(), "tiny")
    assert report.written == [] and "2025" in report.skipped[0] and "snapshot" in report.skipped[0]
    assert read_war(store, "tiny", "2025") is None
