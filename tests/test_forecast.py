import numpy as np
import pytest

from ffapp.bracket import BracketRules
from ffapp.forecast import expected_seed_order, game_forecasts, histogram, pairing_frequency, win_probability
from ffapp.lineup import Starter
from ffapp.noise import GaussianNoise
from ffapp.simulate import simulate
from ffapp.store import SeasonData
from tests.test_simulate import TEAMS, make_inputs


def season(winners=None, losers=None):
    return SeasonData(league={"season": "2026", "league_id": "x"}, users=[], rosters=[], winners_bracket=winners or [], losers_bracket=losers or [])


def run(completed=9, rules=None, strengths=None, runs=3000):
    inputs = make_inputs(completed=completed, strengths=strengths)
    if rules is not None:
        inputs.rules = rules
    return inputs, simulate(inputs, GaussianNoise(6.0), runs=runs, seed=7)


def test_win_probability_splits_ties():
    assert win_probability(np.array([1.0, 2.0, 3.0, 3.0]), np.array([0.0, 2.0, 4.0, 3.0])) == pytest.approx(0.5)


def test_histogram_shares_sum_to_one_on_shared_bins():
    rng = np.random.default_rng(0)
    a, b = rng.normal(100, 15, 5000), rng.normal(110, 15, 5000)
    h = histogram(a, b)
    assert h["width"] == 2.0 and h["start"] % 2 == 0
    assert len(h["shares"][0]) == len(h["shares"][1])
    assert sum(h["shares"][0]) == pytest.approx(1000, abs=15) and sum(h["shares"][1]) == pytest.approx(1000, abs=15)  # per mille


def test_regular_week_games_cover_the_schedule():
    inputs, result = run(strengths={t: 0.0 for t in TEAMS} | {1: 30.0})
    games = game_forecasts(inputs, result, season())
    assert sorted(games, key=int) == ["10", "11", "12", "13", "14", "15", "16", "17"]
    week10 = games["10"]
    assert week10["kind"] == "regular" and len(week10["games"]) == 6
    for g in week10["games"]:
        a, b = g["teams"]
        assert a["win_prob"] + b["win_prob"] == pytest.approx(1.0, abs=1e-4)
        assert sum(g["hist"]["shares"][0]) == pytest.approx(1000, abs=30)
        assert len(a["lineup"]) == 9 and a["lineup"][0][1] is not None
    strong = next(g for g in week10["games"] if any(t["roster_id"] == 1 for t in g["teams"]))
    assert next(t for t in strong["teams"] if t["roster_id"] == 1)["win_prob"] > 0.8  # +30 against ~25 points of spread: about 88%


def test_replacement_fill_is_marked():
    inputs, result = run()
    inputs.starters[1][10][0] = Starter("TE", "FA:TE", "TE", 6.4)
    games = game_forecasts(inputs, result, season())
    row = next(t for g in games["10"]["games"] for t in g["teams"] if t["roster_id"] == 1)["lineup"][0]
    assert row == ["TE", None, "TE", 6.4]  # player_id None marks the replacement-level fill


def test_projected_bracket_seeds_by_expectation_and_favourite_advances():
    strengths = {t: 40.0 - 3 * t for t in TEAMS}  # team 1 strongest ... team 12 weakest
    inputs, result = run(completed=13, strengths=strengths)
    order = [result.team_ids[i] for i in expected_seed_order(result)]
    assert order[:3] == [1, 2, 3]
    games = game_forecasts(inputs, result, season())
    week15, week16, week17 = games["15"], games["16"], games["17"]
    assert [b["roster_id"] for b in week15["byes"]] == [1, 2]
    r1 = [(g["match"], [t["roster_id"] for t in g["teams"]], g["seeds"]) for g in week15["games"]]
    assert r1 == [(1, [4, 5], [4, 5]), (2, [3, 6], [3, 6])]  # 4 v 5 (the 1 seed's side) first
    assert all(g["projected"] and 0 < g["frequency"] <= 1 for g in week15["games"])
    # reseeded semifinals: seed 1 meets the lowest surviving seed; favourites 4 and 3 win round 1
    semis = {g["match"]: [t["roster_id"] for t in g["teams"]] for g in week16["games"] if g["round"] == 2}
    assert semis[3] == [1, 4] and semis[4] == [2, 3]
    final = next(g for g in week17["games"] if g["place"] == 1)
    assert [t["roster_id"] for t in final["teams"]] == [1, 2]
    assert not any(g["bracket"] == "losers" for w in (week15, week16, week17) for g in w["games"])  # consolation league


def test_toilet_bowl_is_projected_and_advances_the_likelier_lower_scorer():
    rules = BracketRules(playoff_teams=6, playoff_week_start=15, reseed=False, toilet_bowl=True)
    strengths = {t: 40.0 - 3 * t for t in TEAMS}
    inputs, result = run(completed=13, rules=rules, strengths=strengths)
    games = game_forecasts(inputs, result, season())
    losers15 = [g for g in games["15"]["games"] if g["bracket"] == "losers"]
    assert [b["roster_id"] for b in games["15"]["byes"] if b["bracket"] == "losers"] == [12, 11]
    assert [[t["roster_id"] for t in g["teams"]] for g in losers15] == [[9, 8], [10, 7]]
    losers16 = {g["match"]: [t["roster_id"] for t in g["teams"]] for g in games["16"]["games"] if g["bracket"] == "losers" and g["round"] == 2}
    # the weaker team "advances" in a toilet bowl: 9 over 8 and 10 over 7; fixed bracket sends them to 12 and 11
    assert losers16[3] == [12, 9] and losers16[4] == [11, 10]


def test_real_pairings_only_after_the_previous_week_is_final():
    winners = [{"r": 1, "m": 1, "t1": 7, "t2": 8}, {"r": 1, "m": 2, "t1": 9, "t2": 10}]
    inputs, result = run(completed=13)
    early = game_forecasts(inputs, result, season(winners=winners))["15"]["games"]
    assert all(g["projected"] for g in early)  # Sleeper pre-fills from live standings; not real yet
    inputs, result = run(completed=14)
    late = game_forecasts(inputs, result, season(winners=winners))["15"]["games"]
    assert [[t["roster_id"] for t in g["teams"]] for g in late] == [[7, 8], [9, 10]]
    assert all(g["projected"] is False and g["frequency"] is None for g in late)


def test_pairing_frequency():
    from ffapp.bracket import Game

    g = Game(1, 1, np.array([0, 0, 1, 2]), np.array([1, 2, 0, 1]), np.zeros(4), np.zeros(4))
    assert pairing_frequency([g], 1, 1, 0, 1) == 0.5 and pairing_frequency([g], 1, 2, 0, 1) == 0.0
