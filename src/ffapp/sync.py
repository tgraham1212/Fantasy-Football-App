"""Pull each configured league's full Sleeper history into the store."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

from ffapp.config import Config, LeagueConfig
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)

_CHAIN_END = {None, "", "0", 0}


def walk_history(client: SleeperClient, league_id: str) -> list[dict]:
    """Follow ``previous_league_id`` from ``league_id`` back to the first season.

    Returns the raw league objects oldest first (newest last). Stops when the
    previous ID is null, empty or ``"0"``, or when a season has already been
    seen (a defensive guard against a malformed cycle).
    """
    chain: list[dict] = []
    seen: set[str] = set()
    current: str | None = str(league_id)
    while current not in _CHAIN_END and current not in seen:
        seen.add(current)  # type: ignore[arg-type]
        league = client.league(current)  # type: ignore[arg-type]
        chain.append(league)
        previous = league.get("previous_league_id")
        current = None if previous in _CHAIN_END else str(previous)
    chain.reverse()
    return chain


def season_weeks(league: dict) -> range:
    """Every week of a league-season, regular season through the last playoff round."""
    settings = league.get("settings", {})
    start = int(settings.get("start_week") or 1)
    playoff_start = int(settings.get("playoff_week_start") or 15)
    playoff_teams = int(settings.get("playoff_teams") or 6)
    rounds = max(1, math.ceil(math.log2(playoff_teams))) if playoff_teams > 1 else 1
    # playoff_round_type 1 = two-week championship, 2 = every round two weeks
    round_type = int(settings.get("playoff_round_type") or 0)
    if round_type == 1:
        rounds += 1
    elif round_type == 2:
        rounds *= 2
    return range(start, playoff_start + rounds)


def fetch_season(client: SleeperClient, league: dict) -> SeasonData:
    """Fetch everything for one league-season. Raises SleeperError on any failure."""
    league_id = str(league["league_id"])
    data = SeasonData(
        league=league,
        users=client.users(league_id),
        rosters=client.rosters(league_id),
    )
    for week in season_weeks(league):
        data.matchups[week] = client.matchups(league_id, week) or []
    data.winners_bracket = client.winners_bracket(league_id) or []
    data.losers_bracket = client.losers_bracket(league_id) or []
    return data


@dataclass
class SyncReport:
    fetched: list[tuple[str, str]] = field(default_factory=list)  # (league_key, season)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (league_key, message)
    warnings: list[tuple[str, str]] = field(default_factory=list)  # (league_key, message): never fail the sync
    transactions: list[tuple[str, str]] = field(default_factory=list)  # (league_key, season) transactions saved

    @property
    def ok(self) -> bool:
        return not self.errors


def sync_transactions(client: SleeperClient, store: Store, league_key: str, league: dict) -> str | None:
    """Fetch and store every week's transactions for one league-season (the season's weeks; Sleeper
    files offseason moves under week 1 and keeps week 0 empty). All weeks are fetched before any is
    written, so a failure keeps the files stored last time. Returns a warning message on failure."""
    league_id = str(league["league_id"])
    season = str(league["season"])
    try:
        weeks = {week: client.transactions(league_id, week) or [] for week in season_weeks(league)}
    except SleeperError as exc:
        log.warning("transactions %s %s failed: %s", league_key, season, exc)
        return f"transactions for season {season} not updated: {exc}"
    store.write_transactions(league_key, season, weeks)
    return None


def sync_league(client: SleeperClient, store: Store, league: LeagueConfig, *, full: bool = False) -> SyncReport:
    """Sync one league. Stored seasons marked complete are skipped unless ``full``.

    A failure while fetching a season leaves that season's stored files untouched:
    everything is fetched into memory first and written only once the whole
    season succeeded.
    """
    report = SyncReport()
    try:
        chain = walk_history(client, league.league_id)
    except SleeperError as exc:
        report.errors.append((league.key, f"history walk failed: {exc}"))
        return report

    for raw in chain:
        season = str(raw["season"])
        stored = store.read_league(league.key, season)
        if not full and stored is not None and stored.get("status") == "complete":
            report.skipped.append((league.key, season))
            if not store.has_transactions(league.key, season):   # once, for seasons stored before transactions were kept
                _transactions(client, store, league.key, raw, report)
            continue
        try:
            data = fetch_season(client, raw)
        except SleeperError as exc:
            report.errors.append((league.key, f"season {season}: {exc}"))
            log.error("sync %s %s failed: %s", league.key, season, exc)
            continue
        store.write_season(league.key, data)
        report.fetched.append((league.key, season))
        log.info("synced %s %s (%s)", league.key, season, data.status)
        _transactions(client, store, league.key, raw, report)
    return report


def _transactions(client: SleeperClient, store: Store, league_key: str, raw: dict, report: SyncReport) -> None:
    warning = sync_transactions(client, store, league_key, raw)
    if warning:
        report.warnings.append((league_key, warning))
    else:
        report.transactions.append((league_key, str(raw["season"])))


def sync_all(client: SleeperClient, store: Store, config: Config, *, full: bool = False) -> SyncReport:
    total = SyncReport()
    for league in config.leagues.values():
        part = sync_league(client, store, league, full=full)
        total.fetched += part.fetched
        total.skipped += part.skipped
        total.errors += part.errors
        total.warnings += part.warnings
        total.transactions += part.transactions
    return total
