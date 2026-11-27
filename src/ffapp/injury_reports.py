"""Past injury reports from nflverse: each fantasy Player's weekly IR, PUP and Out statuses for every
season, keyed by Sleeper Player id, stored as ``data/injury-reports/<season>.json`` (a record). The
draft grades read them to tell an injured pick (Unlucky) from one who simply was not playing.

Sources (nflverse-data GitHub release files, one per season):
- ``weekly_rosters/roster_weekly_<season>.csv``: each team's roster every week with ``sleeper_id``,
  ``status`` and ``status_description_abbr`` (R01 injured reserve, R48 IR designated to return,
  R04 PUP);
- ``injuries/injuries_<season>.csv``: the weekly injury report, ``report_status`` Out, by ``gsis_id``
  (mapped to Sleeper ids through the roster file).

The saved Sleeper statuses in ``data/injuries/`` (which Player WAR reads) are separate and unchanged.
A completed season is fetched once; the current season at most once every 20 hours (the roster file
is about 15 MB). A failure keeps the stored file and only warns.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store, read_json, write_json

log = logging.getLogger(__name__)

NFLVERSE_BASE = "https://github.com/nflverse/nflverse-data/releases/download"
FANTASY = {"QB", "RB", "WR", "TE", "K", "FB"}
IR_CODES = {"R01": "IR", "R48": "IR", "R04": "PUP"}
REFETCH_AFTER = timedelta(hours=20)
FIRST_SEASON = 2021


def rosters_url(season: str) -> str:
    return f"{NFLVERSE_BASE}/weekly_rosters/roster_weekly_{season}.csv"


def reports_url(season: str) -> str:
    return f"{NFLVERSE_BASE}/injuries/injuries_{season}.csv"


def statuses(rosters_csv: str, reports_csv: str) -> dict[str, dict[str, str]]:
    """``{week: {sleeper_id: "IR" | "PUP" | "Out"}}``: IR and PUP from the weekly rosters, Out from the
    injury report (IR and PUP win when a Player has both)."""
    out: dict[str, dict[str, str]] = {}
    gsis_to_sleeper: dict[str, str] = {}
    for row in csv.DictReader(io.StringIO(rosters_csv)):
        sid, gsis = (row.get("sleeper_id") or "").strip(), (row.get("gsis_id") or "").strip()
        if sid and gsis:
            gsis_to_sleeper[gsis] = sid
        if not sid or row.get("position") not in FANTASY:
            continue
        code = IR_CODES.get((row.get("status_description_abbr") or "").strip())
        if code and (row.get("status") or "").strip() == "RES":
            out.setdefault(str(int(row["week"])), {})[sid] = code
    for row in csv.DictReader(io.StringIO(reports_csv)):
        if (row.get("report_status") or "").strip() != "Out" or row.get("position") not in FANTASY:
            continue
        sid = gsis_to_sleeper.get((row.get("gsis_id") or "").strip())
        if sid:
            out.setdefault(str(int(row["week"])), {}).setdefault(sid, "Out")
    return {w: dict(sorted(v.items())) for w, v in sorted(out.items(), key=lambda kv: int(kv[0]))}


def path(store: Store, season: str):
    return store.root / "injury-reports" / f"{season}.json"


def read_reports(store: Store, season: str) -> dict[str, dict[str, str]]:
    """Week -> Sleeper id -> status; empty when the season is not stored."""
    p = path(store, season)
    return (read_json(p) or {}).get("weeks", {}) if p.exists() else {}


def fetch_log(store: Store):
    """When each season was last fetched: rebuilt state under data/refresh/, never committed, so a
    daily refetch with no new statuses changes no record."""
    return store.root / "refresh" / "injury-reports.json"


@dataclass
class ReportsRun:
    saved: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def due(store: Store, season: str, current: bool, now: datetime) -> bool:
    """A completed season once; the current season when its file is missing or 20 hours old (6.6.5.1)."""
    p = path(store, season)
    if not p.exists():
        return True
    if not current:
        return False
    log_path = fetch_log(store)
    fetched = (read_json(log_path) or {}).get(season) if log_path.exists() else None
    try:
        return fetched is None or now - datetime.fromisoformat(fetched) >= REFETCH_AFTER
    except ValueError:
        return True


def sync_reports(client: SleeperClient, store: Store, seasons: list[str], current: str | None, now: datetime | None = None) -> ReportsRun:
    """Fetch and store each due season's injury reports; a failure keeps the stored file (6.6.5.2)."""
    now = now or datetime.now(timezone.utc)
    run = ReportsRun()
    for season in sorted(s for s in seasons if int(s) >= FIRST_SEASON):
        if not due(store, season, season == current, now):
            continue
        try:
            weeks = statuses(client.get_text(rosters_url(season)), client.get_text(reports_url(season)))
        except SleeperError as exc:
            log.warning("injury reports %s failed: %s", season, exc)
            run.warnings.append(f"injury reports for season {season} not updated: {exc}")
            continue
        if not weeks:
            run.warnings.append(f"injury reports for season {season} not updated: nflverse returned none")
            continue
        record = {"season": season, "weeks": weeks}
        if not path(store, season).exists() or read_json(path(store, season)) != record:
            write_json(path(store, season), record)
        log_path = fetch_log(store)
        fetched = read_json(log_path) if log_path.exists() else {}
        write_json(log_path, {**fetched, season: now.isoformat(timespec="seconds")})
        run.saved.append(season)
    return run
