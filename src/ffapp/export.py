"""Write the JSON files the static website reads from ``site/data/``."""

from __future__ import annotations

import logging
from pathlib import Path

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.odds import current_season
from ffapp.ratings import read_ratings
from ffapp.replacement import read_replacement
from ffapp.store import Store, read_json, write_json
from ffapp.games_export import games_export
from ffapp.war import read_war, war_seasons

log = logging.getLogger(__name__)

DEFAULT_SITE_DATA = Path("site") / "data"
CALIBRATION_FILE = "calibration.json"
BOTTOM_TWO_KEY = "avoid_losers_bye"
RATE_KEYS = ("playoffs", "bye", "semifinal", "final", "title", "losers_bracket", "last", BOTTOM_TWO_KEY)
HISTORY_KEYS = ("playoffs", "bye", "final", "title", "last", BOTTOM_TWO_KEY)
DYNASTY_LEAGUE_TYPE = 2  # Sleeper settings.type: 0 redraft, 1 keeper, 2 dynasty
WALKTHROUGH_SEASON = "2024"
WALKTHROUGH_PLAYERS = ("4217", "11604")  # George Kittle, Brock Bowers: the worked example on the WAR page

BOTTOM_COLUMNS = {
    BOTTOM_TWO_KEY: {
        "key": BOTTOM_TWO_KEY,
        "label": "Avoid Loser's Bye",
        "description": "Chance of finishing outside the bottom two of the regular-season standings",
    },
    "last": {
        "key": "last",
        "label": "#1 Pick",
        "description": "Chance of finishing last in the regular season and earning next year's 1.01 pick",
    },
}


class ExportError(RuntimeError):
    pass


def avoid_losers_bye(team: dict) -> float | None:
    """1 minus the chance of the two worst regular-season finishes; None without a seed distribution."""
    dist = team.get("seed_distribution")
    if not dist or len(dist) < 2:
        return None
    return round(1.0 - dist[-1] - dist[-2], 4)


def bottom_column(league: dict) -> dict:
    """Which 'bottom' chance the site shows for this league, from its Sleeper settings.

    Toilet bowl → avoid the loser's bye (bottom two). Dynasty with a consolation
    bracket → chance of last place (the 1.01 pick). Anything else → avoid the loser's bye.
    """
    settings = league.get("settings", {})
    toilet_bowl = BracketRules.from_league(league).toilet_bowl
    dynasty = int(settings.get("type") or 0) == DYNASTY_LEAGUE_TYPE
    key = "last" if dynasty and not toilet_bowl else BOTTOM_TWO_KEY
    return dict(BOTTOM_COLUMNS[key])


def _enrich(team: dict) -> dict:
    """A stored odds row plus the rates and placeholders the site needs."""
    return {**team, BOTTOM_TWO_KEY: avoid_losers_bye(team), "elo": None, "elo_change": None}


def _change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 4)


def league_export(store: Store, config: Config, league_key: str) -> dict:
    season = current_season(store, league_key)
    if season is None:
        raise ExportError(f"{league_key}: nothing synced yet")
    weeks = store.odds_weeks(league_key, season)
    live = store.read_live(league_key, season)
    if not weeks and not live:
        raise ExportError(f"{league_key} {season}: no odds stored, run `ffapp simulate` first")
    league = store.read_league(league_key, season) or {}
    rules = BracketRules.from_league(league)
    if live:
        # the week in progress: live chances, compared with the frozen result the live run started from
        latest = live
        previous = store.read_odds(league_key, season, live["as_of_week"])
    else:
        latest = store.read_odds(league_key, season, weeks[-1])
        previous = store.read_odds(league_key, season, weeks[-2]) if len(weeks) > 1 else None
    prev_by_roster = {t["roster_id"]: _enrich(t) for t in (previous or {}).get("teams", [])}

    teams = []
    for stored in latest["teams"]:
        team = _enrich(stored)
        prev = prev_by_roster.get(team["roster_id"])
        change = {k: (_change(team.get(k), prev.get(k)) if prev else None) for k in RATE_KEYS}
        teams.append({**team, "change": change})

    history_payloads = {w: store.read_odds(league_key, season, w) for w in weeks}
    history_teams: dict[str, dict[str, list[float | None]]] = {}
    for team in latest["teams"]:
        rid = team["roster_id"]
        series = {k: [] for k in HISTORY_KEYS}
        for w in weeks:
            row = next((t for t in history_payloads[w]["teams"] if t["roster_id"] == rid), None)
            row = _enrich(row) if row else None
            for k in HISTORY_KEYS:
                series[k].append(row.get(k) if row else None)
        history_teams[str(rid)] = series

    ratings = ratings_summary(store, league_key)
    if ratings:
        for team in teams:
            current = ratings["current"].get(str(team["roster_id"]))
            if current:
                team["elo"], team["elo_change"] = current["elo"], current["elo_change"]

    payload = {
        "league_key": league_key,
        "league_name": config.leagues[league_key].name,
        "sleeper_league_id": league.get("league_id"),
        "season": season,
        "as_of_week": latest["as_of_week"],
        "previous_as_of_week": previous["as_of_week"] if previous else None,
        "generated_at": latest["generated_at"],
        "runs": latest["runs"],
        "live": latest.get("live"),
        "regular_season_weeks": rules.playoff_week_start - 1,
        "playoff_teams": rules.playoff_teams,
        "bottom_column": bottom_column(league),
        "simulated_weeks": latest.get("simulated_weeks", []),
        "teams": teams,
        "history": {"weeks": weeks, "teams": history_teams},
    }
    replacement = replacement_summary(store, league_key, season, latest["as_of_week"])
    if replacement:
        payload["replacement"] = replacement
    if latest.get("model"):
        payload["model"] = latest["model"]
    if ratings:
        payload["ratings"] = ratings["history"]
    return payload


def ratings_summary(store: Store, league_key: str) -> dict | None:
    """Current ELO per roster plus the chart history for every non-vacant manager, or None without a file."""
    stored = read_ratings(store, league_key)
    if not stored:
        return None
    weeks = [(w["season"], w["week"]) for w in stored.get("weeks", [])]
    index = {wk: i for i, wk in enumerate(weeks)}
    current: dict[str, dict] = {}
    managers: dict[str, dict] = {}
    for manager_id, entry in (stored.get("managers") or {}).items():
        if entry.get("vacant"):
            continue
        history = entry.get("history") or []
        mu: list[float | None] = [None] * len(weeks)
        career_z: list[float | None] = [None] * len(weeks)
        for h in history:
            i = index.get((h["season"], h["week"]))
            if i is not None:
                mu[i], career_z[i] = h["mu"], h["career_z"]
        managers[manager_id] = {
            "display_name": entry.get("display_name"),
            "current": bool(entry.get("current")),
            "roster_id": entry.get("roster_id"),
            "mu": mu,
            "career_z": career_z,
        }
        if entry.get("current") and entry.get("roster_id") is not None and history:
            last = history[-1]["mu"]
            # no change before the season's first scored week (a week-0 entry is the preseason rating)
            prev = history[-2]["mu"] if len(history) > 1 and history[-1].get("week", 0) != 0 else None
            current[str(entry["roster_id"])] = {"elo": round(last), "elo_change": None if prev is None else round(last - prev)}
    return {
        "current": current,
        "history": {
            "weeks": [{"season": s, "week": w} for s, w in weeks],
            "seasons": stored.get("seasons", []),
            "managers": managers,
        },
    }


def replacement_summary(store: Store, league_key: str, season: str, as_of_week: int) -> dict | None:
    """The next unplayed week's projected replacement levels and the season values, or None without a file."""
    stored = read_replacement(store, league_key, season)
    if not stored:
        return None
    weeks = stored.get("weeks") or {}
    week = as_of_week + 1
    if str(week) not in weeks and weeks:
        week = max(int(w) for w in weeks)
    levels = weeks.get(str(week), {})
    return {
        "as_of_week": as_of_week,
        "week": week,
        "levels": {pos: level["projected"] for pos, level in levels.items()},
        "season": {pos: value["value"] for pos, value in (stored.get("season_values") or {}).items()},
        "top_n": stored.get("top_n"),
    }


def war_export(store: Store, league_key: str) -> dict | None:
    """Per season: slim leaderboard rows with owner names, plus an index; None when the league has no WAR files."""
    seasons = war_seasons(store, league_key)
    if not seasons:
        return None
    files: dict[str, dict] = {}
    index = {"seasons": [], "current": seasons[-1], "first_weekly": None}
    for season in seasons:
        stored = read_war(store, league_key, season)
        if not stored:
            continue
        names = {str(u.get("user_id")): str(u.get("display_name") or u.get("user_id")) for u in store.read_users(league_key, season)}
        rows = []
        for pid, player in stored.get("players", {}).items():
            owner = player.get("owner")
            rows.append(
                {
                    "id": pid,
                    "name": player["name"],
                    "position": player["position"],
                    "team": player.get("team"),
                    "games": player["games"],
                    "points": player["points"],
                    "stats": player.get("stats", {}),
                    "exp_wins": player["exp_wins"],
                    "war": player["war"],
                    "owner": names.get(owner, owner) if owner else None,
                    "others": [names.get(h, h) for h in player.get("holders", []) if h != owner],
                }
            )
        payload = {
            "league_key": league_key,
            "season": season,
            "cut": stored.get("cut"),
            "through_week": stored.get("through_week"),
            "generated_at": stored.get("generated_at"),
            "constants": stored.get("constants"),
            "replacement": stored.get("replacement"),
            "players": rows,
        }
        if season == WALKTHROUGH_SEASON and all(pid in stored.get("players", {}) for pid in WALKTHROUGH_PLAYERS):
            payload["walkthrough"] = {pid: stored["players"][pid] for pid in WALKTHROUGH_PLAYERS}
        files[season] = payload
        index["seasons"].append({"season": season, "cut": payload["cut"], "through_week": payload["through_week"], "file": f"{season}.json"})
        if payload["cut"] == "weekly" and index["first_weekly"] is None:
            index["first_weekly"] = season
    return {"index": index, "files": files}


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
        war = war_export(store, key)
        war_entry = None
        if war:
            for season, season_payload in war["files"].items():
                season_path = out_dir / key / "war" / f"{season}.json"
                write_json(season_path, season_payload)
                written.append(season_path)
            index_path = out_dir / key / "war" / "index.json"
            write_json(index_path, war["index"])
            written.append(index_path)
            war_entry = {"file": f"{key}/war/index.json", "seasons": len(war["files"]), "current": war["index"]["current"]}
        owners = {t["roster_id"]: {"display_name": t.get("display_name"), "team_name": t.get("team_name")} for t in payload["teams"]}
        games = games_export(store, config, key, owners)
        games_entry = None
        if games:
            for week, week_payload in games["weeks"].items():
                week_path = out_dir / key / "games" / f"week_{week:02d}.json"
                write_json(week_path, week_payload)
                written.append(week_path)
            games_index = out_dir / key / "games" / "index.json"
            write_json(games_index, games["index"])
            written.append(games_index)
            games_entry = {"file": f"{key}/games/index.json", "current": games["index"]["current"]}
        index["leagues"].append(
            {
                "key": key,
                "name": payload["league_name"],
                "season": payload["season"],
                "as_of_week": payload["as_of_week"],
                "generated_at": payload["generated_at"],
                "file": path.name,
                "war": war_entry,
                "games": games_entry,
            }
        )
    index["refresh_url"] = config.site.refresh_url
    last_run = store.root / "refresh" / "last_run.json"
    index["last_refresh"] = (read_json(last_run) or {}).get("started_at") if last_run.exists() else None
    index["calibration"] = None
    report_path = store.root / "calibration" / "report.json"
    if report_path.exists():
        report = read_json(report_path)
        path = out_dir / CALIBRATION_FILE
        write_json(path, report)
        written.append(path)
        index["calibration"] = {"generated_at": report.get("generated_at"), "file": path.name}
    index_path = out_dir / "index.json"
    write_json(index_path, index)
    written.append(index_path)
    log.info("exported %d league files to %s", len(exports), out_dir)
    return written
