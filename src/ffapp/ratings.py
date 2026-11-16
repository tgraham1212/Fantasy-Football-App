"""Manager ratings across the life of a league.

Every scored regular-season week is one free-for-all: all teams ranked by points
scored, rated with Openskill's Plackett-Luce model on a 1000 scale. Ratings follow
the roster owner's Sleeper user ID, so a manager keeps one rating through roster
changes and former members keep their last one. Each preseason every rating mean
moves a fraction of the way back toward the start value (a fixed anchor, so the
scale cannot inflate as members leave and join), and the first rated weeks of a
season apply a tapering multiplier to the mean update so managers settle quickly.

Alongside the rating: each team's weekly z-score (points against that week's league
mean and sample sd) and its career mean, plus background variants kept for later
evaluation (season-to-date mean z, an exponentially weighted z, and a fresh-start
rating that resets to the start value every preseason). Once a season's draft is
done, every member gets a week-0 entry holding the rating they enter the season
with, so the reverted value is what the site shows until week 1 is scored.

Output: ``data/ratings/<league>.json``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from openskill.models import PlackettLuce

from ffapp.config import Config, RatingsConfig
from ffapp.store import Store, read_json, write_json

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rating:
    mu: float
    sigma: float


@dataclass
class LeagueResults:
    """Every rated week of a league plus who the managers are."""

    league_key: str
    seasons: list[str] = field(default_factory=list)
    weeks: list[tuple[str, int, dict[str, float]]] = field(default_factory=list)  # (season, week, manager -> points)
    names: dict[str, str] = field(default_factory=dict)
    seasons_played: dict[str, list[str]] = field(default_factory=dict)
    roster_now: dict[str, int] = field(default_factory=dict)  # manager -> roster_id in the latest season
    vacant: set[str] = field(default_factory=set)
    members: dict[str, list[str]] = field(default_factory=dict)  # season -> managers who owned a roster
    post_draft: set[str] = field(default_factory=set)  # seasons whose draft is done (in season or complete)

    @property
    def current(self) -> set[str]:
        return set(self.roster_now)


POST_DRAFT_STATUSES = ("in_season", "complete")


def vacant_id(season: str, roster_id: int) -> str:
    return f"vacant:{season}:{roster_id}"


# -- inputs -----------------------------------------------------------------------------


def weekly_results(store: Store, league_key: str) -> LeagueResults:
    """Scored regular-season weeks only; playoff weeks, unplayed weeks and all-zero weeks are left out."""
    from ffapp.odds import regular_season_range

    results = LeagueResults(league_key=league_key)
    seasons = store.seasons(league_key)
    for season in seasons:
        data = store.read_season(league_key, season)
        owner: dict[int, str] = {}
        for roster in data.rosters:
            rid = int(roster["roster_id"])
            manager = roster.get("owner_id")
            if manager:
                owner[rid] = str(manager)
            else:
                owner[rid] = vacant_id(season, rid)
                results.vacant.add(owner[rid])
                results.names[owner[rid]] = f"Vacant ({season}, roster {rid})"
        for user in data.users:
            uid = str(user.get("user_id"))
            if uid in owner.values():
                results.names[uid] = user.get("display_name") or uid
        for manager in owner.values():
            results.names.setdefault(manager, manager)
            results.seasons_played.setdefault(manager, []).append(season)
        results.members[season] = sorted(set(owner.values()))
        if data.status in POST_DRAFT_STATUSES:
            results.post_draft.add(season)
        if season == seasons[-1]:
            results.roster_now = {m: rid for rid, m in owner.items()}
        completed = int(data.league.get("settings", {}).get("last_scored_leg") or 0)
        rated_any = False
        for week in regular_season_range(data.league):
            rows = data.matchups.get(week, [])
            if week > completed or not rows:
                continue
            points = {owner[int(t["roster_id"])]: float(t.get("points") or 0.0) for t in rows if int(t["roster_id"]) in owner}
            if len(points) < 2 or all(v == 0 for v in points.values()):
                continue
            results.weeks.append((season, week, points))
            rated_any = True
        if rated_any or season == seasons[-1]:
            results.seasons.append(season)
    return results


# -- the model -----------------------------------------------------------------------------


def make_model(params: RatingsConfig) -> PlackettLuce:
    """Openskill's default model with every parameter scaled from the 25 scale to start_mu."""
    scale = params.start_mu / 25.0
    return PlackettLuce(mu=params.start_mu, sigma=params.start_sigma, beta=(25.0 / 6.0) * scale, tau=(25.0 / 300.0) * scale)


def rate_week(model: PlackettLuce, ratings: dict[str, Rating], points: dict[str, float], k: float = 1.0) -> dict[str, Rating]:
    """One free-for-all: higher points rank higher. ``k`` multiplies each mean change; sigma is the model's."""
    managers = sorted(points)
    teams = [[model.rating(mu=ratings[m].mu, sigma=ratings[m].sigma)] for m in managers]
    rated = model.rate(teams, scores=[points[m] for m in managers])
    out = dict(ratings)
    for m, team in zip(managers, rated):
        new = team[0]
        out[m] = Rating(mu=ratings[m].mu + k * (new.mu - ratings[m].mu), sigma=float(new.sigma))
    return out


def revert(rating: Rating, anchor: float, fraction: float) -> Rating:
    """Preseason: move the mean ``fraction`` of the way toward the anchor; sigma unchanged."""
    return Rating(mu=anchor + (1.0 - fraction) * (rating.mu - anchor), sigma=rating.sigma)


def z_scores(points: dict[str, float]) -> dict[str, float]:
    """Each team's points as standard deviations from the week's mean (sample sd); 0 when there is no spread."""
    values = np.array(list(points.values()), dtype=float)
    if len(values) < 2:
        return {m: 0.0 for m in points}
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    if sd == 0:
        return {m: 0.0 for m in points}
    return {m: (p - mean) / sd for m, p in points.items()}


def multiplier(params: RatingsConfig, rated_week_index: int) -> float:
    """Multiplier for the ``rated_week_index``-th rated week of a season (0-based); 1 past the schedule."""
    if rated_week_index < len(params.early_k):
        return float(params.early_k[rated_week_index])
    return 1.0


# -- the run ---------------------------------------------------------------------------------


def run_ratings(results: LeagueResults, params: RatingsConfig) -> tuple[dict[str, list[dict]], list[tuple[str, int]]]:
    """Per manager, the history of values after every rated week they played (plus week-0 preseason
    entries for post-draft seasons), and the ordered list of (season, week) the entries cover."""
    model = make_model(params)
    start = Rating(mu=params.start_mu, sigma=params.start_sigma)
    main: dict[str, Rating] = {}
    fresh: dict[str, Rating] = {}
    career_sum: dict[str, float] = {}
    career_n: dict[str, int] = {}
    ewma: dict[str, float] = {}
    history: dict[str, list[dict]] = {}
    weeks: list[tuple[str, int]] = []
    by_season: dict[str, list[tuple[int, dict[str, float]]]] = {}
    for season, week, points in results.weeks:
        by_season.setdefault(season, []).append((week, points))
    seasons = list(results.seasons)
    for season in by_season:
        if season not in seasons:
            seasons.append(season)
    seasons.sort()

    for si, season in enumerate(seasons):
        if si > 0:
            main = {m: revert(r, params.start_mu, params.revert) for m, r in main.items()}
            fresh = {m: start for m in fresh}
        season_sum: dict[str, float] = {}
        season_n: dict[str, int] = {}
        if season in results.post_draft:
            weeks.append((season, 0))
            for m in results.members.get(season, []):
                main.setdefault(m, start)
                fresh.setdefault(m, start)
                history.setdefault(m, []).append(
                    {
                        "season": season,
                        "week": 0,
                        "mu": round(main[m].mu, 2),
                        "sigma": round(main[m].sigma, 2),
                        "z": None,
                        "career_z": round(career_sum[m] / career_n[m], 4) if career_n.get(m) else None,
                        "season_z": None,
                        "ewma_z": round(ewma[m], 4) if m in ewma else None,
                        "fresh_mu": round(fresh[m].mu, 2),
                    }
                )
        for index_in_season, (week, points) in enumerate(by_season.get(season, [])):
            weeks.append((season, week))
            for m in points:
                main.setdefault(m, start)
                fresh.setdefault(m, start)
            k = multiplier(params, index_in_season)
            main = rate_week(model, main, points, k)
            fresh = rate_week(model, fresh, points, 1.0)
            zs = z_scores(points)
            for m, z in zs.items():
                career_sum[m] = career_sum.get(m, 0.0) + z
                career_n[m] = career_n.get(m, 0) + 1
                season_sum[m] = season_sum.get(m, 0.0) + z
                season_n[m] = season_n.get(m, 0) + 1
                ewma[m] = z if m not in ewma else (1.0 - params.ewma_weight) * ewma[m] + params.ewma_weight * z
                history.setdefault(m, []).append(
                    {
                        "season": season,
                        "week": week,
                        "mu": round(main[m].mu, 2),
                        "sigma": round(main[m].sigma, 2),
                        "z": round(z, 4),
                        "career_z": round(career_sum[m] / career_n[m], 4),
                        "season_z": round(season_sum[m] / season_n[m], 4),
                        "ewma_z": round(ewma[m], 4),
                        "fresh_mu": round(fresh[m].mu, 2),
                    }
                )
    return history, weeks


def build_ratings(store: Store, config: Config, league_key: str) -> dict:
    results = weekly_results(store, league_key)
    params = config.ratings
    history, weeks = run_ratings(results, params)
    managers = {}
    for m in sorted(results.names):
        managers[m] = {
            "display_name": results.names[m],
            "current": m in results.current,
            "vacant": m in results.vacant,
            "roster_id": results.roster_now.get(m),
            "seasons": results.seasons_played.get(m, []),
            "history": history.get(m, []),
        }
    return {
        "league_key": league_key,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parameters": {
            "model": "openskill.PlackettLuce",
            "revert": params.revert,
            "early_k": list(params.early_k),
            "start_mu": params.start_mu,
            "start_sigma": params.start_sigma,
            "ewma_weight": params.ewma_weight,
        },
        "seasons": results.seasons,
        "weeks": [{"season": s, "week": w} for s, w in weeks],
        "managers": managers,
    }


# -- files ----------------------------------------------------------------------------------


def ratings_path(store: Store, league_key: str) -> Path:
    return store.root / "ratings" / f"{league_key}.json"


def write_ratings(store: Store, config: Config, league_key: str) -> Path:
    payload = build_ratings(store, config, league_key)
    path = ratings_path(store, league_key)
    write_json(path, payload)
    log.info("ratings %s: %d managers, %d weeks", league_key, len(payload["managers"]), len(payload["weeks"]))
    return path


def read_ratings(store: Store, league_key: str) -> dict | None:
    path = ratings_path(store, league_key)
    return read_json(path) if path.exists() else None
