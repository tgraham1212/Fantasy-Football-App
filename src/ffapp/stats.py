"""Fetch weekly actual player stat lines and keep the latest version of each one.

Storage: ``data/stats/<season>/week_NN.json`` holds ``{player_id: record}`` in the
same shape as the projections store: the raw stat line plus position, team,
opponent, source and last-modified time. Only players who played (a ``pts_*``
total in their stats) are kept, so a future week stores nothing. The point is
to have actual points for free agents, which the league matchups do not carry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ffapp.projections import (
    ProjectionsError,
    RefreshReport,
    UpsertResult,
    changed_beyond_time,
    is_projection,
    seasons_in_scope,
    to_record,
    validate_rows,
)
from ffapp.scoring import projected_points
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store

log = logging.getLogger(__name__)

SEASON_WEEKS = range(1, 18)


class StatsError(ProjectionsError):
    """The stats source returned something other than the expected shape."""


def played(row: dict) -> bool:
    """A stat row counts when the source computed a points total, i.e. the player played."""
    return is_projection(row)


def actual_points(record: dict | None, scoring: dict[str, float]) -> float:
    """Actual fantasy points for a stored stat record under a league's scoring; missing record = 0."""
    if record is None:
        return 0.0
    return projected_points(record.get("stats"), scoring)


def upsert_week(store: Store, season: str, week: int, rows: list[dict]) -> UpsertResult:
    """Merge one week's stat rows, keeping the newest version per player (stat corrections win)."""
    result = UpsertResult(season=str(season), week=int(week))
    incoming: dict[str, dict] = {}
    for row in rows:
        if not played(row):
            result.dropped += 1
            continue
        incoming[str(row["player_id"])] = to_record(row)
    if not incoming:
        return result
    stored = store.read_stats(season, week)
    merged = dict(stored)
    for player_id, record in incoming.items():
        existing = stored.get(player_id)
        if existing is None:
            merged[player_id] = record
            result.added += 1
        elif record["last_modified"] > int(existing.get("last_modified") or 0) and changed_beyond_time(existing, record):
            merged[player_id] = record
            result.updated += 1
        else:
            result.unchanged += 1
    if result.added or result.updated:
        store.write_stats(season, week, merged)
        result.written = True
    return result


def fetch_week(client: SleeperClient, season: str, week: int) -> list[dict]:
    payload = client.stats(season, week)
    try:
        return validate_rows(payload, season, week)
    except ProjectionsError as exc:
        raise StatsError(str(exc)) from exc


def refresh_season(client: SleeperClient, store: Store, season: str, weeks=SEASON_WEEKS) -> RefreshReport:
    """Fetch every week of a season, then write. A failure anywhere writes nothing for that season."""
    report = RefreshReport()
    fetched: dict[int, list[dict]] = {}
    for week in weeks:
        try:
            fetched[week] = fetch_week(client, season, week)
        except (SleeperError, ProjectionsError) as exc:
            report.errors.append(f"{season} week {week}: {exc}")
            log.error("stats %s week %s failed: %s", season, week, exc)
            return report
    for week, rows in fetched.items():
        result = upsert_week(store, season, week, rows)
        report.results.append(result)
        log.info(
            "stats %s week %02d: +%d ~%d =%d (not played %d)%s",
            season, week, result.added, result.updated, result.unchanged, result.dropped,
            "" if result.written else " unchanged",
        )
    return report


def refresh_stats(client: SleeperClient, store: Store, league_keys, *, backfill: bool = False) -> RefreshReport:
    seasons = seasons_in_scope(store, league_keys)
    if not seasons:
        report = RefreshReport()
        report.errors.append("no stored league seasons: run `ffapp sync` first")
        return report
    targets = seasons if backfill else seasons[-1:]
    total = RefreshReport()
    for season in targets:
        part = refresh_season(client, store, season)
        total.results += part.results
        total.errors += part.errors
    return total


@dataclass
class StatsCheck:
    """How well our scoring of stored stat lines reproduces Sleeper's credited points."""

    compared: int = 0
    within: int = 0
    worst: float = 0.0
    examples: list[str] = field(default_factory=list)

    @property
    def share(self) -> float:
        return self.within / self.compared if self.compared else 0.0
