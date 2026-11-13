import copy

import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.projections import upsert_week
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, FixtureSession, load

DYNASTY_CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")


@pytest.fixture
def dynasty_config():
    return Config(leagues={"dynasty": DYNASTY_CFG})


@pytest.fixture
def seeded_store(tmp_path):
    """A store with the dynasty league synced from fixtures and 2026 projections for every week.

    The 2025 week-1 projections fixture is reused for each 2026 week (season/week
    rewritten), which is enough for lineups and simulations to have real-looking inputs.
    """
    store = Store(tmp_path / "data")
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, DYNASTY_CFG)
    rows = load("projections/2025/1.json")
    for week in range(1, 18):
        reused = copy.deepcopy(rows)
        for row in reused:
            row["season"] = "2026"
            row["week"] = week
        upsert_week(store, "2026", week, reused)
    return store
