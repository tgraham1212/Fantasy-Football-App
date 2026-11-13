"""Fetch weekly player projections and keep the latest version of each one.

Storage: ``data/projections/<season>/week_NN.json`` holds ``{player_id: record}``
where a record keeps the raw projected stat line plus the player's position,
name, NFL team, opponent, source company and the source's last-modified time.
Only players with real projections (a ``pts_*`` total in their stats) are kept;
Sleeper returns a row for every player on a roster, most carrying only ADP.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ffapp.scoring import PRECOMPUTED_KEYS
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store

log = logging.getLogger(__name__)

REGULAR_SEASON_WEEKS = range(1, 18)
REQUIRED_ROW_KEYS = ("player_id", "season", "week", "stats")


class ProjectionsError(RuntimeError):
    """The projections source returned something other than the expected shape."""


def validate_rows(payload: object, season: str, week: int) -> list[dict]:
    """Check a raw response before anything is written. Returns the rows."""
    if not isinstance(payload, list):
        raise ProjectionsError(f"{season} week {week}: expected a list, got {type(payload).__name__}")
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise ProjectionsError(f"{season} week {week}: row {index} is not an object")
        missing = [k for k in REQUIRED_ROW_KEYS if k not in row]
        if missing:
            raise ProjectionsError(f"{season} week {week}: row {index} is missing {', '.join(missing)}")
        if not isinstance(row["stats"], dict):
            raise ProjectionsError(f"{season} week {week}: row {index} stats is not an object")
        if str(row["season"]) != str(season) or int(row["week"]) != int(week):
            raise ProjectionsError(
                f"{season} week {week}: row {index} is for {row['season']} week {row['week']}"
            )
    return payload


def is_projection(row: dict) -> bool:
    """A row is a projection when the source computed a points total for it."""
    return any(key in PRECOMPUTED_KEYS for key in row.get("stats") or {})


def to_record(row: dict) -> dict:
    player = row.get("player") or {}
    return {
        "player_id": str(row["player_id"]),
        "position": player.get("position"),
        "fantasy_positions": player.get("fantasy_positions") or [],
        "first_name": player.get("first_name"),
        "last_name": player.get("last_name"),
        "team": row.get("team"),
        "opponent": row.get("opponent"),
        "company": row.get("company"),
        "last_modified": int(row.get("last_modified") or 0),
        "stats": row["stats"],
    }


@dataclass
class UpsertResult:
    season: str
    week: int
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    dropped: int = 0
    written: bool = False

    @property
    def kept(self) -> int:
        return self.added + self.updated + self.unchanged


def upsert_week(store: Store, season: str, week: int, rows: list[dict]) -> UpsertResult:
    """Merge one week's rows into the store, keeping only the newest version per player.

    - rows without a points projection are dropped
    - a stored record is replaced only when the incoming ``last_modified`` is newer
    - players already stored but absent from ``rows`` are kept
    - a response with no projections at all leaves the stored file untouched
    """
    result = UpsertResult(season=str(season), week=int(week))
    incoming: dict[str, dict] = {}
    for row in rows:
        if not is_projection(row):
            result.dropped += 1
            continue
        incoming[str(row["player_id"])] = to_record(row)
    if not incoming:
        return result

    stored = store.read_projections(season, week)
    merged = dict(stored)
    for player_id, record in incoming.items():
        existing = stored.get(player_id)
        if existing is None:
            merged[player_id] = record
            result.added += 1
        elif record["last_modified"] > int(existing.get("last_modified") or 0):
            merged[player_id] = record
            result.updated += 1
        else:
            result.unchanged += 1
    if result.added or result.updated:
        store.write_projections(season, week, merged)
        result.written = True
    return result


def fetch_week(client: SleeperClient, season: str, week: int) -> list[dict]:
    """Fetch and validate one season-week. Raises SleeperError or ProjectionsError."""
    payload = client.projections(season, week)
    return validate_rows(payload, season, week)


@dataclass
class RefreshReport:
    results: list[UpsertResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def refresh_season(client: SleeperClient, store: Store, season: str, weeks=REGULAR_SEASON_WEEKS) -> RefreshReport:
    """Fetch every week of a season, then write. A failure anywhere writes nothing for that season."""
    report = RefreshReport()
    fetched: dict[int, list[dict]] = {}
    for week in weeks:
        try:
            fetched[week] = fetch_week(client, season, week)
        except (SleeperError, ProjectionsError) as exc:
            report.errors.append(f"{season} week {week}: {exc}")
            log.error("projections %s week %s failed: %s", season, week, exc)
            return report
    for week, rows in fetched.items():
        result = upsert_week(store, season, week, rows)
        report.results.append(result)
        log.info(
            "projections %s week %02d: +%d ~%d =%d (dropped %d)%s",
            season, week, result.added, result.updated, result.unchanged, result.dropped,
            "" if result.written else " unchanged",
        )
    return report


def seasons_in_scope(store: Store, league_keys) -> list[str]:
    """Every season any configured league has stored, oldest first."""
    seasons: set[str] = set()
    for key in league_keys:
        seasons.update(store.seasons(key))
    return sorted(seasons)


def refresh_projections(client: SleeperClient, store: Store, league_keys, *, backfill: bool = False) -> RefreshReport:
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
