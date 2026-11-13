"""Write the JSON files the static website reads from ``site/data/``."""

from __future__ import annotations

import logging
from pathlib import Path

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.odds import current_season
from ffapp.store import Store, write_json

log = logging.getLogger(__name__)

DEFAULT_SITE_DATA = Path("site") / "data"
RATE_KEYS = ("playoffs", "bye", "semifinal", "final", "title", "losers_bracket", "last")
HISTORY_KEYS = ("playoffs", "bye", "final", "title", "last")


class ExportError(RuntimeError):
    pass


def league_export(store: Store, config: Config, league_key: str) -> dict:
    season = current_season(store, league_key)
    if season is None:
        raise ExportError(f"{league_key}: nothing synced yet")
    weeks = store.odds_weeks(league_key, season)
    if not weeks:
        raise ExportError(f"{league_key} {season}: no odds stored, run `ffapp simulate` first")
    league = store.read_league(league_key, season) or {}
    rules = BracketRules.from_league(league)
    latest = store.read_odds(league_key, season, weeks[-1])
    previous = store.read_odds(league_key, season, weeks[-2]) if len(weeks) > 1 else None
    prev_by_roster = {t["roster_id"]: t for t in (previous or {}).get("teams", [])}

    teams = []
    for team in latest["teams"]:
        prev = prev_by_roster.get(team["roster_id"])
        change = {k: (round(team[k] - prev[k], 4) if prev else None) for k in RATE_KEYS}
        teams.append({**team, "change": change})

    history_payloads = {w: store.read_odds(league_key, season, w) for w in weeks}
    history_teams: dict[str, dict[str, list[float | None]]] = {}
    for team in latest["teams"]:
        rid = team["roster_id"]
        series = {k: [] for k in HISTORY_KEYS}
        for w in weeks:
            row = next((t for t in history_payloads[w]["teams"] if t["roster_id"] == rid), None)
            for k in HISTORY_KEYS:
                series[k].append(row[k] if row else None)
        history_teams[str(rid)] = series

    return {
        "league_key": league_key,
        "league_name": config.leagues[league_key].name,
        "sleeper_league_id": league.get("league_id"),
        "season": season,
        "as_of_week": latest["as_of_week"],
        "previous_as_of_week": previous["as_of_week"] if previous else None,
        "generated_at": latest["generated_at"],
        "runs": latest["runs"],
        "regular_season_weeks": rules.playoff_week_start - 1,
        "playoff_teams": rules.playoff_teams,
        "simulated_weeks": latest.get("simulated_weeks", []),
        "teams": teams,
        "history": {"weeks": weeks, "teams": history_teams},
    }


def export_site(store: Store, config: Config, out_dir: Path | str = DEFAULT_SITE_DATA) -> list[Path]:
    """Write one file per league plus an index. Raises ExportError if any league has no odds."""
    out_dir = Path(out_dir)
    exports = {key: league_export(store, config, key) for key in config.leagues}  # all or nothing
    written = []
    index = {"leagues": []}
    for key, payload in exports.items():
        path = out_dir / f"{key}.json"
        write_json(path, payload)
        written.append(path)
        index["leagues"].append(
            {
                "key": key,
                "name": payload["league_name"],
                "season": payload["season"],
                "as_of_week": payload["as_of_week"],
                "generated_at": payload["generated_at"],
                "file": path.name,
            }
        )
    index_path = out_dir / "index.json"
    write_json(index_path, index)
    written.append(index_path)
    log.info("exported %d league files to %s", len(exports), out_dir)
    return written
