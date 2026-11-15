import copy
import json

import pytest

from ffapp.config import Config, LeagueConfig, SimulationConfig
from ffapp.projections import upsert_week
from ffapp.replacement import (
    POSITIONS,
    floor_for_slot,
    free_agents,
    prior_from_seasons,
    read_replacement,
    rostered_for_week,
    rostered_now,
    season_value,
    weekly_level,
    write_replacement,
)
from ffapp.sleeper import SleeperClient
from ffapp.stats import upsert_week as upsert_stats
from ffapp.store import SeasonData, Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, FixtureSession, load

CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
CONFIG = Config(leagues={"dynasty": CFG})
SCORING = {"rec": 1.0, "rec_yd": 0.1, "pass_yd": 0.04}


def proj(position, rec=0.0, rec_yd=0.0, pass_yd=0.0):
    return {"position": position, "stats": {"rec": rec, "rec_yd": rec_yd, "pass_yd": pass_yd}}


def wr(points):
    return proj("WR", rec_yd=points * 10)  # 0.1 per yard


@pytest.fixture
def store_2025(tmp_path):
    store = Store(tmp_path / "data")
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, CFG)
    rows = load("projections/2025/1.json")
    for season in ("2025", "2026"):
        for week in range(1, 18):
            reused = copy.deepcopy(rows)
            for row in reused:
                row["season"] = season
                row["week"] = week
            upsert_week(store, season, week, reused)
    upsert_stats(store, "2025", 1, load("stats/2025/1.json"))
    return store


# -- free agents ---------------------------------------------------------------------


def test_free_agents_exclude_rostered_and_zero_projections():
    projections = {"a": wr(9.4), "b": wr(8.9), "c": wr(8.1), "d": wr(12.0), "e": wr(0.0), "q": proj("QB", pass_yd=300)}
    agents = free_agents(projections, SCORING, rostered={"d"})
    assert [pid for pid, _ in agents["WR"]] == ["a", "b", "c"], "d is rostered, e projects 0"
    assert agents["QB"] == [("q", 12.0)]
    assert agents["TE"] == []


def test_rostered_sets_from_season_data():
    data = SeasonData(
        league={"season": "2026", "settings": {"last_scored_leg": 3}},
        users=[],
        rosters=[{"roster_id": 1, "players": ["1", "2"], "reserve": ["3"], "taxi": ["4"]}],
        matchups={2: [{"roster_id": 1, "players": ["1", "9"]}]},
    )
    assert rostered_now(data) == {"1", "2", "3", "4"}, "reserve and taxi count as rostered"
    assert rostered_for_week(data, 2) == {"1", "9"}
    assert rostered_for_week(data, 7) == {"1", "2", "3", "4"}, "no stored matchups for that week -> current rosters"


# -- weekly level -----------------------------------------------------------------------


def test_weekly_level_chooses_by_projection_and_scores_both_ways():
    projections = {"a": wr(9.4), "b": wr(8.9), "c": wr(8.1), "d": wr(7.0)}
    stats = {"a": {"stats": {"rec_yd": 140}}, "b": {"stats": {"rec_yd": 32}}, "c": {"stats": {"rec_yd": 76}}, "d": {"stats": {"rec_yd": 300}}}
    level = weekly_level(projections, SCORING, rostered=set(), stats=stats, n=3)["WR"]
    assert level["projected"] == 8.8
    assert level["realised"] == 8.27, "d scored most but was not chosen, because the choice is by projection"
    assert level["players"] == ["a", "b", "c"] and level["available"] == 4


def test_weekly_level_edge_cases():
    projections = {"t1": proj("TE", rec=5), "t2": proj("TE", rec=3), "k": proj("K")}
    level = weekly_level(projections, SCORING, rostered=set(), stats=None, n=3)
    assert level["TE"]["projected"] == 4.0 and level["TE"]["available"] == 2, "two available tight ends are averaged"
    assert level["TE"]["realised"] is None, "no stats stored -> realised absent"
    assert level["RB"] == {"projected": 0.0, "realised": None, "available": 0, "players": []}
    with_stats = weekly_level(projections, SCORING, rostered=set(), stats={"t1": {"stats": {"rec": 7}}}, n=3)
    assert with_stats["TE"]["realised"] == 3.5, "a chosen player without a stat row counts 0"
    assert with_stats["RB"]["realised"] == 0.0


def test_floor_for_slot_takes_best_eligible_position():
    levels = {"RB": {"projected": 7.5}, "WR": {"projected": 8.2}, "TE": {"projected": 5.0}, "QB": {"projected": 14.0}}
    assert floor_for_slot("RB", levels) == 7.5
    assert floor_for_slot("FLEX", levels) == 8.2
    assert floor_for_slot("SUPER_FLEX", levels) == 14.0
    assert floor_for_slot("K", levels) == 0.0
    assert floor_for_slot("FLEX", {"RB": 7.5, "WR": 6.0}) == 7.5, "plain numbers work too"


# -- season value -------------------------------------------------------------------------


def test_season_value_shrinkage():
    assert season_value([], 6.0, 4) == 6.0
    assert season_value([8.0] * 12, 6.0, 4) == pytest.approx(7.5)
    assert season_value([8.0] * 12, 6.0, 0) == pytest.approx(8.0)


def test_prior_from_seasons():
    prior, used = prior_from_seasons([("2025", 8.0), ("2024", 7.0), ("2023", 6.0), ("2022", 1.0)], fallback=0.0)
    assert prior == pytest.approx(7.3) and used == ["2025", "2024", "2023"]
    prior, used = prior_from_seasons([("2025", 8.0), ("2024", 4.0)], fallback=0.0)
    assert prior == pytest.approx(0.625 * 8.0 + 0.375 * 4.0) and used == ["2025", "2024"]
    assert prior_from_seasons([], fallback=5.5) == (5.5, [])


# -- files ----------------------------------------------------------------------------------


def test_write_replacement_covers_every_season_and_uses_comparable_priors(store_2025):
    config = Config(leagues={"dynasty": CFG}, simulation=SimulationConfig(replacement_top_n=3, prior_weeks=4))
    written = write_replacement(store_2025, config, "dynasty")
    assert [p.name for p in written] == [f"{s}.json" for s in store_2025.seasons("dynasty")]

    current = read_replacement(store_2025, "dynasty", "2026")
    assert sorted(int(w) for w in current["weeks"]) == list(range(1, 18))
    for week in current["weeks"].values():
        assert set(week) == set(POSITIONS)
        assert all(isinstance(week[pos]["projected"], float) for pos in POSITIONS)
        assert all(week[pos]["realised"] is None for pos in POSITIONS), "no 2026 stats stored"
    assert current["top_n"] == 3 and current["prior_weeks"] == 4.0
    assert set(current["season_values"]) == set(POSITIONS)

    past = read_replacement(store_2025, "dynasty", "2025")
    week1 = past["weeks"]["1"]
    assert all(week1[pos]["available"] >= 5 for pos in POSITIONS), "fixture free agents are unrostered in 2025"
    assert all(week1[pos]["projected"] > 0 for pos in POSITIONS)
    assert all(week1[pos]["realised"] is not None for pos in POSITIONS), "2025 week 1 stats are stored"
    assert all(past["weeks"][str(w)][pos]["realised"] is None for w in range(2, 18) for pos in POSITIONS)
    for pos in POSITIONS:
        assert past["season_values"][pos]["weeks_played"] == 1
        assert past["season_values"][pos]["prior_seasons"] == ["2024", "2023", "2022"]
    first = read_replacement(store_2025, "dynasty", "2022")
    for pos in POSITIONS:
        assert first["season_values"][pos]["prior_seasons"] == [] and first["season_values"][pos]["prior"] == first["season_values"][pos]["projected_mean"]
        assert first["season_values"][pos]["weeks_played"] == 0 and first["season_values"][pos]["value"] == first["season_values"][pos]["prior"]

    # a season with different settings is not used as a prior
    (store_2025.root / "leagues" / "dynasty" / "2024" / "league.json").write_text(
        json.dumps({**json.loads((store_2025.root / "leagues" / "dynasty" / "2024" / "league.json").read_text()), "scoring_settings": {"rec": 9.0}}),
        encoding="utf-8",
    )
    write_replacement(store_2025, config, "dynasty")
    assert read_replacement(store_2025, "dynasty", "2025")["season_values"]["QB"]["prior_seasons"] == ["2023", "2022"]
