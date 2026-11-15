"""Free agents and replacement level: what a waiver-wire pickup is worth, by position.

Per league, season and week the replacement players at a position are the N free
agents with the highest projection for that week (chosen before the games, the way
a manager picks them up). Their mean projection is the *projected level*; their
mean actual points from stored stats is the *realised level*. The season value is
the running mean of realised levels, shrunk toward earlier seasons.

The simulation uses the projected level as a floor for every lineup slot; the
stored files under ``data/replacement/`` are for inspection and later features.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ffapp.config import Config
from ffapp.league import FLEX_ELIGIBLE, resolve_settings
from ffapp.scoring import record_points
from ffapp.stats import actual_points
from ffapp.store import SeasonData, Store, read_json, write_json

log = logging.getLogger(__name__)

POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
PRIOR_WEIGHTS = (0.5, 0.3, 0.2)  # most recent earlier season first


# -- who is a free agent ------------------------------------------------------------


def rostered_now(data: SeasonData) -> set[str]:
    """Every player on a current roster, reserve and taxi included."""
    ids: set[str] = set()
    for roster in data.rosters:
        for key in ("players", "reserve", "taxi"):
            ids.update(str(p) for p in (roster.get(key) or []))
    return ids


def rostered_for_week(data: SeasonData, week: int) -> set[str]:
    """Every player on a roster in a stored week's matchups; current rosters when the week has none."""
    rows = data.matchups.get(week, [])
    ids = {str(p) for team in rows for p in (team.get("players") or [])}
    return ids if ids else rostered_now(data)


def rostered_as_of(data: SeasonData, week: int) -> set[str]:
    """Rostered set to use for ``week``: the stored rosters once the week is scored, current rosters otherwise."""
    completed = int(data.league.get("settings", {}).get("last_scored_leg") or 0)
    return rostered_for_week(data, week) if week <= completed else rostered_now(data)


def free_agents(projections: dict[str, dict], scoring: dict[str, float], rostered: set[str]) -> dict[str, list[tuple[str, float]]]:
    """Unrostered players with a positive projection this week, per position, best first."""
    agents: dict[str, list[tuple[str, float]]] = {pos: [] for pos in POSITIONS}
    for player_id, record in projections.items():
        position = record.get("position")
        if position not in agents or str(player_id) in rostered:
            continue
        projected = record_points(record, scoring)
        if projected > 0:
            agents[position].append((str(player_id), projected))
    for pos in agents:
        agents[pos].sort(key=lambda item: (-item[1], item[0]))
    return agents


# -- weekly levels -----------------------------------------------------------------------


def weekly_level(
    projections: dict[str, dict],
    scoring: dict[str, float],
    rostered: set[str],
    stats: dict[str, dict] | None = None,
    n: int = 3,
) -> dict[str, dict]:
    """Per position: projected level, realised level (None without stats), available count, players."""
    agents = free_agents(projections, scoring, rostered)
    levels = {}
    for pos in POSITIONS:
        top = agents[pos][:n]
        projected = sum(p for _, p in top) / len(top) if top else 0.0
        realised: float | None
        if stats is None:
            realised = None
        elif top:
            realised = sum(actual_points(stats.get(pid), scoring) for pid, _ in top) / len(top)
        else:
            realised = 0.0
        levels[pos] = {
            "projected": round(projected, 2),
            "realised": None if realised is None else round(realised, 2),
            "available": len(agents[pos]),
            "players": [pid for pid, _ in top],
        }
    return levels


def floor_for_slot(slot: str, levels: dict[str, dict] | dict[str, float]) -> float:
    """Replacement level for a lineup slot: FLEX-type slots take the best eligible position."""

    def level(pos: str) -> float:
        value = levels.get(pos, 0.0)
        return float(value["projected"]) if isinstance(value, dict) else float(value or 0.0)

    positions = FLEX_ELIGIBLE.get(slot, (slot,))
    return max((level(p) for p in positions), default=0.0)


# -- season value ----------------------------------------------------------------------------


def season_value(weekly_realised: list[float], prior: float, k: float) -> float:
    """Bayesian shrinkage of the realised weekly mean toward ``prior`` with ``k`` pseudo-weeks."""
    n = len(weekly_realised)
    if n == 0:
        return float(prior)
    mean = sum(weekly_realised) / n
    return (n * mean + k * prior) / (n + k)


def settings_signature(league: dict) -> str:
    """Scoring and roster settings as one comparable string."""
    return json.dumps(
        {"scoring": league.get("scoring_settings") or {}, "roster": list(league.get("roster_positions") or [])},
        sort_keys=True,
    )


def prior_from_seasons(final_values: list[tuple[str, float]], fallback: float) -> tuple[float, list[str]]:
    """50/30/20 over up to three earlier seasons (most recent first), renormalised; fallback with none."""
    use = final_values[: len(PRIOR_WEIGHTS)]
    if not use:
        return float(fallback), []
    weights = PRIOR_WEIGHTS[: len(use)]
    total = sum(weights)
    return sum(w * v for w, (_, v) in zip(weights, use)) / total, [s for s, _ in use]


# -- per-season file -----------------------------------------------------------------------


def replacement_path(store: Store, league_key: str, season: str) -> Path:
    return store.root / "replacement" / league_key / f"{season}.json"


def season_levels(store: Store, config: Config, league_key: str, data: SeasonData, *, n: int) -> dict[int, dict[str, dict]]:
    """Weekly levels for every week of a season that has projections."""
    completed = int(data.league.get("settings", {}).get("last_scored_leg") or 0)
    weeks = {}
    for week in store.projection_weeks(data.season):
        projections = store.read_projections(data.season, week)
        if not projections:
            continue
        scoring = resolve_settings(config, league_key, data.league, week)
        stats = store.read_stats(data.season, week) if week <= completed else {}
        weeks[week] = weekly_level(projections, scoring, rostered_as_of(data, week), stats if stats else None, n)
    return weeks


def build_replacement(
    store: Store, config: Config, league_key: str, data: SeasonData, earlier: list[dict], *, n: int, k: float
) -> dict:
    """The replacement file for one season; ``earlier`` are the already-built files of earlier seasons, oldest first."""
    weeks = season_levels(store, config, league_key, data, n=n)
    signature = settings_signature(data.league)
    comparable = [f for f in reversed(earlier) if f.get("settings_signature") == signature]
    season = {}
    for pos in POSITIONS:
        projected = [w[pos]["projected"] for w in weeks.values()]
        realised = [w[pos]["realised"] for w in weeks.values() if w[pos]["realised"] is not None]
        fallback = sum(projected) / len(projected) if projected else 0.0
        prior, prior_seasons = prior_from_seasons([(f["season"], f["season_values"][pos]["value"]) for f in comparable], fallback)
        season[pos] = {
            "value": round(season_value(realised, prior, k), 2),
            "prior": round(prior, 2),
            "prior_seasons": prior_seasons,
            "weeks_played": len(realised),
            "projected_mean": round(fallback, 2),
        }
    return {
        "league_key": league_key,
        "season": data.season,
        "top_n": n,
        "prior_weeks": k,
        "settings_signature": signature,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "weeks": {str(w): weeks[w] for w in sorted(weeks)},
        "season_values": season,
    }


def write_replacement(store: Store, config: Config, league_key: str) -> list[Path]:
    """Build and write the replacement file for every stored season of a league, oldest first."""
    n = config.simulation.replacement_top_n
    k = config.simulation.prior_weeks
    built: list[dict] = []
    written = []
    for season in store.seasons(league_key):
        data = store.read_season(league_key, season)
        payload = build_replacement(store, config, league_key, data, built, n=n, k=k)
        path = replacement_path(store, league_key, season)
        write_json(path, payload)
        built.append(payload)
        written.append(path)
        log.info("replacement %s %s: %d weeks", league_key, season, len(payload["weeks"]))
    return written


def read_replacement(store: Store, league_key: str, season: str) -> dict | None:
    path = replacement_path(store, league_key, season)
    return read_json(path) if path.exists() else None
