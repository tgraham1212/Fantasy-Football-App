import numpy as np
import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.noise import MIN_POOL, ResidualPools, band_of, build_pools, collect_residuals
from ffapp.projections import upsert_week
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, FixtureSession, load


@pytest.mark.parametrize(
    "projected, band",
    [(-1.0, 0), (0.0, 0), (1.99, 0), (2.0, 1), (4.9, 1), (5.0, 2), (8.0, 3), (11.0, 4), (14.0, 5), (18.0, 6), (22.0, 7), (40.0, 7)],
)
def test_band_assignment(projected, band):
    assert band_of(projected) == band


def test_small_band_falls_back_to_position_pool():
    residuals = {("WR", 5): list(range(MIN_POOL)), ("WR", 7): [100.0, 101.0]}
    pools = ResidualPools.from_residuals(residuals)
    rng = np.random.default_rng(0)
    assert set(pools.sample("WR", 15.0, rng, 50)) <= set(range(MIN_POOL)), "full band is used as is"
    draws = pools.sample("WR", 30.0, rng, 500)
    assert draws.min() < 100, "band 7 has only 2 samples, so the whole-position pool is used"
    assert set(draws) <= set(range(MIN_POOL)) | {100.0, 101.0}


def test_unknown_position_adds_no_noise():
    pools = ResidualPools.from_residuals({})
    assert list(pools.sample("P", 3.0, np.random.default_rng(0), 3)) == [0.0, 0.0, 0.0]


def test_residuals_from_stored_data(tmp_path):
    store = Store(tmp_path)
    cfg = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
    config = Config(leagues={"dynasty": cfg})
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, cfg)
    upsert_week(store, "2025", 1, load("projections/2025/1.json"))  # the only projections fixture

    residuals = collect_residuals(store, config)
    total = sum(len(v) for v in residuals.values())
    assert total > 0
    assert all(pos in {"QB", "RB", "WR", "TE", "K", "DEF"} for pos, _ in residuals)
    # only 2025 week 1 has projections, so every residual comes from that week
    assert total <= 30 * 1  # at most one residual per projected player

    excluded = collect_residuals(store, config, exclude_after=("2025", 0))
    assert sum(len(v) for v in excluded.values()) == 0

    pools = build_pools(store, config)
    assert pools.by_position
