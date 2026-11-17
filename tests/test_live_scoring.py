import math

import numpy as np
import pytest

from ffapp.lineup import Starter
from ffapp.noise import GaussianNoise, ResidualPools, band_of
from ffapp.simulate import simulate, starter_score
from tests.test_simulate import make_inputs


def test_defaults_reproduce_the_pre_live_formula_exactly():
    noise = GaussianNoise(6.0)
    starter = Starter("WR", "a", "WR", 12.5)
    got = starter_score(starter, noise, np.random.default_rng(3), 1000)
    expected = 12.5 + noise.sample("WR", 12.5, np.random.default_rng(3), 1000)
    assert np.array_equal(got, expected)


def test_simulation_unchanged_with_default_starters():
    a = simulate(make_inputs(completed=9), GaussianNoise(6.0), runs=500, seed=11)
    b = simulate(make_inputs(completed=9), GaussianNoise(6.0), runs=500, seed=11)
    assert all(np.array_equal(a.weekly_scores[w], b.weekly_scores[w]) for w in a.weekly_scores)
    assert np.array_equal(a.seeds, b.seeds)


def test_final_starter_scores_his_points_with_no_noise():
    scores = starter_score(Starter("RB", "a", "RB", 10.0, fixed=18.4, share=0.0), GaussianNoise(6.0), np.random.default_rng(0), 500)
    assert (scores == 18.4).all()


def test_half_time_matches_the_spec_example():
    # projected 10, 11 at half: mean 11 + 0.5 * 10 = 16, spread sqrt(0.5) of a full game's
    scores = starter_score(Starter("WR", "a", "WR", 10.0, fixed=11.0, share=0.5), GaussianNoise(6.0), np.random.default_rng(1), 200_000)
    assert scores.mean() == pytest.approx(16.0, abs=0.05)
    assert scores.std() == pytest.approx(6.0 * math.sqrt(0.5), rel=0.02)


def test_bias_scales_with_time_left_and_scatter_with_its_square_root():
    pools = ResidualPools.from_residuals({("WR", band_of(10.0)): [2.0, 4.0, 6.0] * 100}, min_pool=10)  # mean miss +4, sd 1.63
    assert pools.bias("WR", 10.0) == pytest.approx(4.0) and pools.spread("WR", 10.0) == pytest.approx(math.sqrt(8 / 3))
    scores = starter_score(Starter("WR", "a", "WR", 10.0, fixed=5.0, share=0.25), pools, np.random.default_rng(2), 100_000)
    assert scores.mean() == pytest.approx(5.0 + 0.25 * (10.0 + 4.0), abs=0.02)
    assert scores.std() == pytest.approx(0.5 * math.sqrt(8 / 3), rel=0.03)
