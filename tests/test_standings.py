import pytest

from ffapp.standings import pairings, regular_season_records, seed_order, seeds
from tests.fixtures import DYNASTY, REDRAFT, load


def team(roster_id, matchup_id, points):
    return {"roster_id": roster_id, "matchup_id": matchup_id, "points": points}


def test_hand_checked_four_team_season_with_a_tie():
    weeks = {
        1: [team(1, 1, 100.0), team(2, 1, 90.0), team(3, 2, 80.0), team(4, 2, 80.0)],
        2: [team(1, 1, 70.0), team(3, 1, 95.0), team(2, 2, 110.0), team(4, 2, 60.0)],
        3: [team(1, 1, 120.0), team(4, 1, 50.0), team(2, 2, 85.0), team(3, 2, 85.5)],
    }
    records = regular_season_records(weeks, range(1, 4))
    assert (records[1].wins, records[1].losses, records[1].ties) == (2, 1, 0)
    assert (records[2].wins, records[2].losses, records[2].ties) == (1, 2, 0)
    assert (records[3].wins, records[3].losses, records[3].ties) == (2, 0, 1)
    assert (records[4].wins, records[4].losses, records[4].ties) == (0, 2, 1)
    assert records[1].points_for == 290.0 and records[1].points_against == 235.0
    assert records[3].results == ["T", "W", "W"]
    # team 3 has 2.5 win value, team 1 has 2.0, team 2 has 1.0, team 4 has 0.5
    assert seed_order(records) == [3, 1, 2, 4]
    assert seeds(records) == {3: 1, 1: 2, 2: 3, 4: 4}


def test_points_break_equal_records():
    weeks = {
        1: [team(1, 1, 100.0), team(2, 1, 90.0), team(3, 2, 130.0), team(4, 2, 80.0)],
        2: [team(1, 1, 70.0), team(3, 1, 95.0), team(2, 2, 110.0), team(4, 2, 60.0)],
    }
    records = regular_season_records(weeks, range(1, 3))
    # 3 is 2-0; 1 and 2 are both 1-1 and 2 has 200 points to 1's 170
    assert seed_order(records) == [3, 2, 1, 4]


def test_unplayed_weeks_are_simply_not_counted():
    weeks = {1: [team(1, 1, 100.0), team(2, 1, 90.0)], 2: [team(1, 1, 0.0), team(2, 1, 0.0)]}
    records = regular_season_records(weeks, range(1, 2))
    assert records[1].games == 1 and records[2].games == 1


def test_bye_rows_are_skipped():
    assert pairings([team(1, 1, 10.0), team(2, 1, 5.0), team(3, None, 7.0)]) == [
        ({"roster_id": 1, "matchup_id": 1, "points": 10.0}, {"roster_id": 2, "matchup_id": 1, "points": 5.0})
    ]


@pytest.mark.parametrize("league_id", [DYNASTY["2025"], REDRAFT["2025"], DYNASTY["2022"]])
def test_recomputed_records_match_sleeper_roster_settings(league_id):
    matchups = {w: load(f"league/{league_id}/matchups/{w}.json") for w in range(1, 15)}
    records = regular_season_records(matchups, range(1, 15))
    for roster in load(f"league/{league_id}/rosters.json"):
        rec = records[roster["roster_id"]]
        s = roster["settings"]
        assert (rec.wins, rec.losses, rec.ties) == (s["wins"], s["losses"], s.get("ties", 0))
        assert rec.points_for == pytest.approx(s["fpts"] + s.get("fpts_decimal", 0) / 100, abs=0.011)
        assert rec.points_against == pytest.approx(
            s.get("fpts_against", 0) + s.get("fpts_against_decimal", 0) / 100, abs=0.011
        )


@pytest.mark.parametrize("league_id", [DYNASTY["2025"], REDRAFT["2025"]])
def test_seeds_match_round_one_of_real_bracket(league_id):
    matchups = {w: load(f"league/{league_id}/matchups/{w}.json") for w in range(1, 15)}
    seed_of = seeds(regular_season_records(matchups, range(1, 15)))
    round_one = [g for g in load(f"league/{league_id}/winners_bracket.json") if g["r"] == 1]
    played = {frozenset((seed_of[g["t1"]], seed_of[g["t2"]])) for g in round_one}
    assert played == {frozenset((3, 6)), frozenset((4, 5))}
