import numpy as np
import pytest

from ffapp.bracket import BracketRules, run_six_team_bracket


def scripted(results):
    """decide() that looks the higher scorer up from {(round, frozenset(pair)): higher}."""

    def decide(round, a, b):
        out = []
        for x, y in zip(a, b):
            out.append(results[(round, frozenset((int(x), int(y))))])
        return np.array(out)

    return decide


SEEDS = [1, 2, 3, 4, 5, 6]
# round 1: 4 beats 5, 6 beats 3
ROUND_ONE = {(1, frozenset((4, 5))): 4, (1, frozenset((3, 6))): 6}


def test_fixed_bracket_pairs_seed_one_with_the_4v5_winner():
    results = dict(ROUND_ONE)
    results.update({(2, frozenset((1, 4))): 1, (2, frozenset((2, 6))): 6, (2, frozenset((5, 3))): 3})
    results.update({(3, frozenset((1, 6))): 6, (3, frozenset((4, 2))): 2})
    out = run_six_team_bracket(SEEDS, scripted(results), reseed=False)
    assert out.game(2, 3).pair() == {1, 4} and out.game(2, 4).pair() == {2, 6}
    assert out.game(2, 5).pair() == {5, 3} and out.game(2, 5).place == 5
    assert out.game(3, 6).pair() == {1, 6} and out.game(3, 7).pair() == {4, 2}
    places = {p: int(t[0]) for p, t in out.places.items()}
    assert places == {1: 6, 2: 1, 3: 2, 4: 4, 5: 3, 6: 5}


def test_reseed_bracket_pairs_seed_one_with_lowest_survivor():
    results = dict(ROUND_ONE)
    results.update({(2, frozenset((1, 6))): 1, (2, frozenset((2, 4))): 4, (2, frozenset((5, 3))): 5})
    results.update({(3, frozenset((1, 4))): 4, (3, frozenset((6, 2))): 2})
    out = run_six_team_bracket(SEEDS, scripted(results), reseed=True)
    assert out.game(2, 3).pair() == {1, 6} and out.game(2, 4).pair() == {2, 4}
    assert int(out.champion[0]) == 4 and int(out.runner_up[0]) == 1
    assert int(out.places[3][0]) == 2 and int(out.places[5][0]) == 5


def test_reseed_when_seed_three_survives():
    results = {(1, frozenset((4, 5))): 5, (1, frozenset((3, 6))): 3}
    results.update({(2, frozenset((1, 5))): 1, (2, frozenset((2, 3))): 2, (2, frozenset((4, 6))): 6})
    results.update({(3, frozenset((1, 2))): 2, (3, frozenset((5, 3))): 3})
    out = run_six_team_bracket(SEEDS, scripted(results), reseed=True)
    assert out.game(2, 3).pair() == {1, 5} and out.game(2, 4).pair() == {2, 3}
    assert int(out.champion[0]) == 2


def test_toilet_bowl_advances_the_lower_scorer():
    # reverse-seeded losers bracket: "top seed" is roster 12
    seeds = [12, 11, 10, 9, 8, 7]
    results = {(1, frozenset((9, 8))): 9, (1, frozenset((10, 7))): 7}  # 8 and 10 lose and advance
    results.update({(2, frozenset((12, 8))): 12, (2, frozenset((11, 10))): 10, (2, frozenset((9, 7))): 9})
    results.update({(3, frozenset((8, 11))): 11, (3, frozenset((12, 10))): 10})
    out = run_six_team_bracket(seeds, scripted(results), reseed=False, advance_loser=True)
    assert out.game(1, 1).pair() == {9, 8} and out.game(1, 2).pair() == {10, 7}
    assert out.game(2, 3).pair() == {12, 8} and out.game(2, 4).pair() == {11, 10}
    assert out.game(3, 6).pair() == {8, 11}
    assert int(out.places[1][0]) == 8, "the team that keeps losing 'wins' the toilet bowl"


def test_vectorized_over_runs():
    runs = 4
    seeds = [np.full(runs, s) for s in SEEDS]
    rng = np.random.default_rng(1)

    def decide(round, a, b):
        return np.where(rng.random(len(a)) < 0.5, a, b)

    out = run_six_team_bracket(seeds, decide, reseed=True)
    assert out.champion.shape == (runs,)
    for run in range(runs):
        placed = sorted(int(out.places[p][run]) for p in range(1, 7))
        assert placed == SEEDS, "every seed gets exactly one place in each run"
        assert int(out.champion[run]) in {int(out.game(3, 6).t1[run]), int(out.game(3, 6).t2[run])}


def test_bracket_rules_from_league_settings():
    dynasty = BracketRules.from_league({"settings": {"playoff_teams": 6, "playoff_week_start": 15, "playoff_seed_type": 1, "playoff_type": 1}})
    redraft = BracketRules.from_league({"settings": {"playoff_teams": 6, "playoff_week_start": 15, "playoff_seed_type": 0, "playoff_type": 0}})
    assert dynasty.reseed and not dynasty.toilet_bowl
    assert not redraft.reseed and redraft.toilet_bowl
    order = list(range(101, 113))
    assert dynasty.losers_seeds(order) == [107, 108, 109, 110, 111, 112]
    assert redraft.losers_seeds(order) == [112, 111, 110, 109, 108, 107]
    assert dynasty.week_for_round(3) == 17
    assert not BracketRules.from_league({"settings": {"playoff_teams": 4}}).supported()


def test_wrong_seed_count_rejected():
    with pytest.raises(ValueError):
        run_six_team_bracket([1, 2, 3], lambda r, a, b: a, reseed=False)
