"""Build simulation inputs from stored data, run the sim, and keep the odds history."""

from __future__ import annotations

import logging
import zlib
from datetime import datetime, timezone

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.league import owners, resolve_settings, starter_slots
from ffapp.lineup import Candidate, Starter, best_lineup
from ffapp.noise import NoiseModel, build_pools
from ffapp.scoring import record_points
from ffapp.simulate import SimInputs, simulate, summarize
from ffapp.standings import pairings, regular_season_records
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)


# -- 5.1 as-of ------------------------------------------------------------------


def completed_weeks(league: dict) -> int:
    """Weeks Sleeper has fully scored for this league-season (0 before week 1 ends)."""
    settings = league.get("settings", {})
    rules = BracketRules.from_league(league)
    last_week = rules.week_for_round(rules.rounds)
    return max(0, min(int(settings.get("last_scored_leg") or 0), last_week))


def regular_season_range(league: dict) -> range:
    settings = league.get("settings", {})
    start = int(settings.get("start_week") or 1)
    return range(start, BracketRules.from_league(league).playoff_week_start)


def fixed_records(data: SeasonData, as_of: int):
    """Regular-season records after ``as_of`` completed weeks."""
    weeks = [w for w in regular_season_range(data.league) if w <= as_of]
    roster_ids = [int(r["roster_id"]) for r in data.rosters]
    return regular_season_records(data.matchups, weeks, roster_ids=roster_ids)


# -- 5.2 rosters ----------------------------------------------------------------


def rosters_as_of(data: SeasonData, as_of: int, *, current: bool) -> dict[int, list[str]]:
    """Players available to each team.

    Current run: today's roster minus injured reserve and taxi squad.
    Backfilled run as of week N: the roster each team carried into week N+1,
    taken from that week's matchup rows (falls back to the current roster when
    that week is not stored).
    """
    current_rosters = {
        int(r["roster_id"]): [
            str(p)
            for p in (r.get("players") or [])
            if p not in set(r.get("reserve") or []) and p not in set(r.get("taxi") or [])
        ]
        for r in data.rosters
    }
    if current:
        return current_rosters
    rows = data.matchups.get(as_of + 1, [])
    by_roster = {int(t["roster_id"]): [str(p) for p in (t.get("players") or [])] for t in rows}
    return {rid: by_roster.get(rid) or current_rosters[rid] for rid in current_rosters}


# -- inputs -----------------------------------------------------------------------


def projected_lineup(
    store: Store, config: Config, league_key: str, data: SeasonData, week: int, players: list[str]
) -> list[Starter]:
    projections = store.read_projections(data.season, week)
    scoring = resolve_settings(config, league_key, data.league, week)
    candidates = []
    for player_id in players:
        record = projections.get(player_id)
        if record is None or not record.get("position"):
            continue  # no projection this week: bye, out, or unprojected -> 0 points, never starts over a projected player
        positions = tuple(record.get("fantasy_positions") or [record["position"]])
        candidates.append(Candidate(player_id, record["position"], positions, record_points(record, scoring)))
    return best_lineup(starter_slots(data.league), candidates)


def build_inputs(
    store: Store, config: Config, league_key: str, data: SeasonData, as_of: int, *, current: bool
) -> SimInputs:
    rules = BracketRules.from_league(data.league)
    if not rules.supported():
        raise ValueError(f"{league_key} {data.season}: unsupported bracket ({rules.playoff_teams} teams)")
    team_ids = sorted(int(r["roster_id"]) for r in data.rosters)
    fixed = fixed_records(data, as_of)
    schedule = {}
    for week in regular_season_range(data.league):
        if week <= as_of:
            continue
        pairs = [(int(a["roster_id"]), int(b["roster_id"])) for a, b in pairings(data.matchups.get(week, []))]
        if not pairs:
            raise ValueError(f"{league_key} {data.season}: no schedule stored for week {week}")
        schedule[week] = pairs
    rosters = rosters_as_of(data, as_of, current=current)
    future_weeks = [w for w in list(schedule) + [rules.week_for_round(r) for r in range(1, rules.rounds + 1)] if w > as_of]
    starters = {
        rid: {week: projected_lineup(store, config, league_key, data, week, players) for week in future_weeks}
        for rid, players in rosters.items()
    }
    real_points = {}
    for round in range(1, rules.rounds + 1):
        week = rules.week_for_round(round)
        if week <= as_of:
            real_points[week] = {int(t["roster_id"]): float(t.get("points") or 0.0) for t in data.matchups.get(week, [])}
    return SimInputs(
        league_key=league_key,
        season=data.season,
        completed_weeks=as_of,
        rules=rules,
        team_ids=team_ids,
        fixed=fixed,
        schedule=schedule,
        starters=starters,
        real_points=real_points,
    )


# -- 5.6 odds history --------------------------------------------------------------


def default_seed(league_key: str, season: str, as_of: int) -> int:
    return zlib.crc32(f"{league_key}:{season}:{as_of}".encode())


def run_as_of(
    store: Store,
    config: Config,
    league_key: str,
    data: SeasonData,
    as_of: int,
    *,
    current: bool,
    noise: NoiseModel,
    runs: int = 10_000,
    seed: int | None = None,
) -> dict:
    """Simulate one league-season as of ``as_of`` completed weeks and store the results."""
    inputs = build_inputs(store, config, league_key, data, as_of, current=current)
    seed = default_seed(league_key, data.season, as_of) if seed is None else seed
    result = simulate(inputs, noise, runs=runs, seed=seed)
    owner_of = owners(data.users, data.rosters)
    teams = []
    for row in summarize(result):
        rid = row["roster_id"]
        rec = inputs.fixed[rid]
        owner = owner_of.get(rid)
        teams.append(
            {
                **row,
                "user_id": owner.user_id if owner else None,
                "display_name": owner.display_name if owner else None,
                "team_name": owner.team_name if owner else f"Roster {rid}",
                "wins": rec.wins,
                "losses": rec.losses,
                "ties": rec.ties,
                "points_for": round(rec.points_for, 2),
                "points_against": round(rec.points_against, 2),
            }
        )
    teams.sort(key=lambda t: (-t["playoffs"], -t["title"], -t["proj_wins"]))
    payload = {
        "league_key": league_key,
        "season": data.season,
        "as_of_week": as_of,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": runs,
        "seed": seed,
        "simulated_weeks": sorted(inputs.schedule) + [w for w in inputs.playoff_weeks if w not in inputs.real_points],
        "teams": teams,
    }
    store.write_odds(league_key, data.season, as_of, payload)
    log.info("odds %s %s as of week %d: %d runs, seed %d", league_key, data.season, as_of, runs, seed)
    return payload


def current_season(store: Store, league_key: str) -> str | None:
    seasons = store.seasons(league_key)
    return seasons[-1] if seasons else None


def simulate_league(
    store: Store,
    config: Config,
    league_key: str,
    *,
    backfill_season: bool = False,
    runs: int = 10_000,
    seed: int | None = None,
) -> list[dict]:
    """Run the current as-of point for a league (and, optionally, every earlier one this season)."""
    season = current_season(store, league_key)
    if season is None:
        raise ValueError(f"{league_key}: nothing synced yet")
    data = store.read_season(league_key, season)
    as_of = completed_weeks(data.league)
    payloads = []
    if backfill_season:
        for earlier in range(0, as_of):
            noise = build_pools(store, config, exclude_after=(season, earlier))
            payloads.append(run_as_of(store, config, league_key, data, earlier, current=False, noise=noise, runs=runs, seed=seed))
    noise = build_pools(store, config)
    payloads.append(run_as_of(store, config, league_key, data, as_of, current=True, noise=noise, runs=runs, seed=seed))
    return payloads
