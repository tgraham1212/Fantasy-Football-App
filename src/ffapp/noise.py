"""Empirical score noise: how far actual points land from projections.

Residual = actual points - projected points for every rostered player with a
projection, in every completed week of every stored league-season, bucketed by
position and projected-points band. A simulated score is the projection plus a
residual sampled from the matching pool.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from ffapp.config import Config
from ffapp.league import resolve_settings
from ffapp.scoring import record_points
from ffapp.store import Store

log = logging.getLogger(__name__)

POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
BAND_EDGES = (0.0, 2.0, 5.0, 8.0, 11.0, 14.0, 18.0, 22.0)  # last band is 22+
MIN_POOL = 200


def band_of(projected: float) -> int:
    """Index of the projected-points band (0 = 0-2 points, 7 = 22+)."""
    return max(0, int(np.searchsorted(BAND_EDGES, projected, side="right")) - 1)


class NoiseModel(Protocol):
    def sample(self, position: str, projected: float, rng: np.random.Generator, size: int) -> np.ndarray: ...


@dataclass
class ResidualPools:
    by_band: dict[tuple[str, int], np.ndarray] = field(default_factory=dict)
    by_position: dict[str, np.ndarray] = field(default_factory=dict)
    min_pool: int = MIN_POOL

    def pool_for(self, position: str, projected: float) -> np.ndarray:
        pool = self.by_band.get((position, band_of(projected)))
        if pool is not None and len(pool) >= self.min_pool:
            return pool
        fallback = self.by_position.get(position)
        if fallback is not None and len(fallback) > 0:
            return fallback
        return np.zeros(1)  # unknown position: no noise rather than a crash

    def sample(self, position: str, projected: float, rng: np.random.Generator, size: int) -> np.ndarray:
        pool = self.pool_for(position, projected)
        return pool[rng.integers(0, len(pool), size=size)]

    def sizes(self) -> dict[str, int]:
        return {f"{pos}[{band}]": len(arr) for (pos, band), arr in sorted(self.by_band.items())}

    @classmethod
    def from_residuals(cls, residuals: dict[tuple[str, int], list[float]], min_pool: int = MIN_POOL) -> ResidualPools:
        pools = cls(min_pool=min_pool)
        per_position: dict[str, list[float]] = defaultdict(list)
        for (position, band), values in residuals.items():
            pools.by_band[(position, band)] = np.asarray(values, dtype=float)
            per_position[position].extend(values)
        pools.by_position = {pos: np.asarray(vals, dtype=float) for pos, vals in per_position.items()}
        return pools


def collect_residuals(
    store: Store,
    config: Config,
    *,
    exclude_after: tuple[str, int] | None = None,
) -> dict[tuple[str, int], list[float]]:
    """Gather (actual - projected) for every scored player-week in the store.

    ``exclude_after=(season, week)`` leaves out that season's weeks after ``week``,
    so a backfilled as-of run does not learn from games it is pretending not to know.
    """
    residuals: dict[tuple[str, int], list[float]] = defaultdict(list)
    projection_cache: dict[tuple[str, int], dict] = {}
    for league_key in config.leagues:
        for season in store.seasons(league_key):
            league = store.read_league(league_key, season)
            if league is None:
                continue
            completed = int(league.get("settings", {}).get("last_scored_leg") or 0)
            for week in store.matchup_weeks(league_key, season):
                if week > completed:
                    continue
                if exclude_after and season == exclude_after[0] and week > exclude_after[1]:
                    continue
                key = (season, week)
                if key not in projection_cache:
                    projection_cache[key] = store.read_projections(season, week)
                projections = projection_cache[key]
                if not projections:
                    continue
                scoring = resolve_settings(config, league_key, league, week)
                for team in store.read_matchups(league_key, season, week):
                    for player_id, actual in (team.get("players_points") or {}).items():
                        record = projections.get(str(player_id))
                        if record is None or record.get("position") not in POSITIONS:
                            continue
                        projected = record_points(record, scoring)
                        residuals[(record["position"], band_of(projected))].append(float(actual) - projected)
    return residuals


def build_pools(store: Store, config: Config, *, exclude_after: tuple[str, int] | None = None) -> ResidualPools:
    residuals = collect_residuals(store, config, exclude_after=exclude_after)
    pools = ResidualPools.from_residuals(residuals)
    total = sum(len(v) for v in pools.by_position.values())
    log.info("residual pools: %d samples; %s", total, ", ".join(f"{k}={v}" for k, v in pools.sizes().items()))
    return pools


@dataclass
class GaussianNoise:
    """Simple stand-in noise model for tests."""

    sd: float = 5.0

    def sample(self, position: str, projected: float, rng: np.random.Generator, size: int) -> np.ndarray:
        return rng.normal(0.0, self.sd, size=size)
