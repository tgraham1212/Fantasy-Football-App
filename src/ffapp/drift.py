"""Roster drift: how much of a team's projected edge survives k weeks ahead.

The simulation freezes rosters, but real rosters change. Measured on stored
seasons: a team's replacement-floored projected strength under the roster it held
at week w, evaluated with week-t projections, predicts its true strength at week t
with a slope below one (the edge reverts toward the league mean) plus residual
noise that grows with the horizon. ``estimate`` turns those pairs into a per-league
``DriftModel``; the simulation applies the slope as a shrink and the noise as a
per-run random walk.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field

import numpy as np

from ffapp.config import Config
from ffapp.league import resolve_settings, starter_slots
from ffapp.lineup import lineup_points
from ffapp.store import Store

log = logging.getLogger(__name__)

DIAGNOSTIC_HORIZONS = (2, 3, 5, 8, 12)


@dataclass
class DriftModel:
    league_key: str
    slopes: list[float] = field(default_factory=list)  # index k-1: reversion factor k weeks ahead (1 = none)
    sds: list[float] = field(default_factory=list)  # index k-1: drift noise sd k weeks ahead (points)
    seasons: list[str] = field(default_factory=list)  # seasons the estimate came from
    top_n: int = 3
    floor: bool = True
    note: str = ""

    @property
    def identity(self) -> bool:
        return not self.slopes

    def slope(self, k: int) -> float:
        if not self.slopes:
            return 1.0
        return self.slopes[min(max(k, 1), len(self.slopes)) - 1]

    def sd(self, k: int) -> float:
        if not self.sds or k < 1:
            return 0.0
        return self.sds[min(k, len(self.sds)) - 1]

    def step_sd(self, k: int) -> float:
        """Random-walk step between horizon k-1 and k so the marginal sd at k is sd(k)."""
        return float(np.sqrt(max(0.0, self.sd(k) ** 2 - self.sd(k - 1) ** 2)))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> DriftModel:
        return cls(**{k: raw[k] for k in ("league_key", "slopes", "sds", "seasons", "top_n", "floor", "note") if k in raw})

    @classmethod
    def identity_model(cls, league_key: str, *, top_n: int, floor: bool, note: str) -> DriftModel:
        return cls(league_key=league_key, top_n=top_n, floor=floor, note=note)


# -- measurement -----------------------------------------------------------------------


def strength_pairs(
    store: Store, config: Config, league_key: str, seasons: list[str], *, floor: bool, n: int
) -> dict[int, list[tuple[float, float]]]:
    """k -> [(held-roster strength, true strength)], both relative to the league mean that week.

    For every completed season, as-of week w and later regular-season week t = w + k: the
    best projected lineup for week t under the roster each team held going into week
    w + 1, against the same for the roster it really held at week t. With ``floor`` the
    lineups get the replacement-level floor the simulation uses.
    """
    from ffapp.odds import lineup_from_projections, regular_season_range
    from ffapp.replacement import weekly_level

    pairs: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for season in seasons:
        data = store.read_season(league_key, season)
        if data.status != "complete":
            continue
        regular = list(regular_season_range(data.league))
        slots = starter_slots(data.league)
        players_at = {
            t: {int(r["roster_id"]): [str(p) for p in (r.get("players") or [])] for r in data.matchups.get(t, [])}
            for t in regular
        }
        projections = {t: store.read_projections(season, t) for t in regular}
        scoring = {t: resolve_settings(config, league_key, data.league, t) for t in regular}

        def floor_for(t: int, rosters: dict[int, list[str]]) -> dict[str, float] | None:
            if not floor:
                return None
            rostered = {p for players in rosters.values() for p in players}
            return {pos: lv["projected"] for pos, lv in weekly_level(projections[t], scoring[t], rostered, None, n).items()}

        def strengths(t: int, rosters: dict[int, list[str]]) -> dict[int, float]:
            fl = floor_for(t, rosters)
            return {rid: lineup_points(lineup_from_projections(projections[t], scoring[t], slots, pl, fl)) for rid, pl in rosters.items()}

        true_strength = {t: strengths(t, players_at[t]) for t in regular if players_at[t]}
        for w in range(0, len(regular)):
            held = players_at.get(regular[0] + w)
            if not held:
                continue
            for t in regular:
                k = t - (regular[0] - 1 + w)
                if k < 1 or t not in true_strength:
                    continue
                held_strength = strengths(t, held)
                mean_true = float(np.mean(list(true_strength[t].values())))
                for rid, s in held_strength.items():
                    if rid in true_strength[t]:
                        pairs[k].append((s - mean_true, true_strength[t][rid] - mean_true))
    return dict(pairs)


def fit(pairs: dict[int, list[tuple[float, float]]]) -> tuple[list[float], list[float]]:
    """Raw least-squares slope and residual sd per horizon 1..K (no smoothing)."""
    if not pairs:
        return [], []
    K = max(pairs)
    slopes, sds = [], []
    for k in range(1, K + 1):
        rows = pairs.get(k, [])
        if len(rows) < 3:
            slopes.append(slopes[-1] if slopes else 1.0)
            sds.append(sds[-1] if sds else 0.0)
            continue
        x = np.array([a for a, _ in rows])
        y = np.array([b for _, b in rows])
        if np.allclose(x, x[0]):
            slope, intercept = 1.0, 0.0
        else:
            slope, intercept = np.polyfit(x, y, 1)
        resid = y - (slope * x + intercept)
        slopes.append(float(slope))
        sds.append(float(resid.std()))
    return slopes, sds


def estimate(
    pairs: dict[int, list[tuple[float, float]]], league_key: str, seasons: list[str], *, top_n: int, floor: bool
) -> DriftModel:
    """A DriftModel from strength pairs: k = 1 fixed at (1, 0), slopes non-increasing, sds non-decreasing."""
    if len(seasons) < 2 or not pairs:
        return DriftModel.identity_model(league_key, top_n=top_n, floor=floor, note=f"identity: {len(seasons)} season(s) available, need 2")
    slopes, sds = fit(pairs)
    slopes[0], sds[0] = 1.0, 0.0
    for k in range(1, len(slopes)):
        slopes[k] = min(slopes[k], slopes[k - 1])
        sds[k] = max(sds[k], sds[k - 1])
    return DriftModel(
        league_key=league_key,
        slopes=[round(s, 4) for s in slopes],
        sds=[round(s, 3) for s in sds],
        seasons=list(seasons),
        top_n=top_n,
        floor=floor,
    )


def estimate_for_league(
    store: Store, config: Config, league_key: str, *, exclude_season: str | None = None, floor: bool = True
) -> DriftModel:
    """Estimate from every stored completed season of a league, optionally leaving one out."""
    seasons = [
        s for s in store.seasons(league_key)
        if s != exclude_season and (store.read_league(league_key, s) or {}).get("status") == "complete"
    ]
    n = config.simulation.replacement_top_n
    pairs = strength_pairs(store, config, league_key, seasons, floor=floor, n=n)
    model = estimate(pairs, league_key, seasons, top_n=n, floor=floor)
    log.info("drift %s from %s: %s", league_key, seasons, "identity" if model.identity else f"slopes {model.slopes[:3]}... sds {model.sds[:3]}...")
    return model


def diagnostic(store: Store, config: Config, league_key: str, seasons: list[str], *, horizons=DIAGNOSTIC_HORIZONS) -> dict:
    """Slope and drift sd at chosen horizons under the frozen and the floored roster, for the report."""
    n = config.simulation.replacement_top_n
    out = {"top_n": n, "seasons": list(seasons), "horizons": list(horizons), "frozen": {}, "floored": {}}
    for label, floor in (("frozen", False), ("floored", True)):
        slopes, sds = fit(strength_pairs(store, config, league_key, seasons, floor=floor, n=n))
        for k in horizons:
            if k <= len(slopes):
                out[label][str(k)] = {"slope": round(slopes[k - 1], 3), "sd": round(sds[k - 1], 2)}
    return out


def model_path(store: Store, league_key: str):
    return store.root / "model" / f"{league_key}.json"
