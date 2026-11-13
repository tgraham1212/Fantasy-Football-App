"""Sanity check of league scoring against Sleeper's own half-PPR totals, over stored data.

Runs only when the repository's data/ directory has been populated (``ffapp sync``
and ``ffapp projections --backfill``); it never touches the network. Run with
``pytest -rP tests/test_scoring_live_data.py`` to see the per-league medians.
"""

from pathlib import Path

import pytest

from ffapp.config import load_config
from ffapp.league import resolve_settings
from ffapp.scoring import record_points
from ffapp.store import Store

REPO_ROOT = Path(__file__).resolve().parents[1]
STORE = Store(REPO_ROOT / "data")
SKILL = {"QB", "RB", "WR", "TE"}
WEEKS = (1, 5, 9)  # three completed 2026 weeks


@pytest.mark.skipif(not (REPO_ROOT / "data" / "projections" / "2026").exists(), reason="data/ not populated")
@pytest.mark.parametrize("league_key", ["dynasty", "redraft"])
def test_scored_projections_match_sleeper_half_ppr(league_key):
    config = load_config(REPO_ROOT / "config" / "leagues.yaml")
    league = STORE.read_league(league_key, "2026")
    assert league is not None
    diffs = []
    for week in WEEKS:
        scoring = resolve_settings(config, league_key, league, week)
        for record in STORE.read_projections("2026", week).values():
            if record["position"] in SKILL and "pts_half_ppr" in record["stats"]:
                diffs.append(abs(record_points(record, scoring) - record["stats"]["pts_half_ppr"]))
    assert len(diffs) > 500
    diffs.sort()
    median = diffs[len(diffs) // 2]
    p90 = diffs[int(len(diffs) * 0.9)]
    print(f"{league_key} 2026 weeks {WEEKS}: {len(diffs)} skill-player projections, "
          f"median |ours - pts_half_ppr| = {median:.3f}, p90 = {p90:.3f}, max = {diffs[-1]:.2f}")
    assert median < 0.5
