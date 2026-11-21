"""The NFL schedule from ESPN's public scoreboard, and when each team kicks off.

Storage: ``data/nfl/<season>/week_NN.json`` holds ``{season, week, fetched_at, games:
[{home, away, kickoff_utc, state}], byes: [team]}`` with Sleeper's team abbreviations
and ``state`` one of ``scheduled``, ``in_progress``, ``final``. The refresh stores the
current and the next week on every run; ``--all`` stores every week of the season.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store

log = logging.getLogger(__name__)

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
NFL_WEEKS = range(1, 19)
STATES = {"pre": "scheduled", "in": "in_progress", "post": "final"}
TEAM_ALIASES = {"WSH": "WAS", "JAC": "JAX", "LA": "LAR"}  # ESPN -> Sleeper


class ScheduleError(RuntimeError):
    """The scoreboard returned something other than the expected shape."""


def team(abbr: str) -> str:
    abbr = str(abbr).upper()
    return TEAM_ALIASES.get(abbr, abbr)


def parse_iso(value: str) -> datetime:
    """ESPN dates look like 2026-11-20T01:15Z; always returned timezone-aware in UTC."""
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _int(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clock_seconds(status: dict) -> float | None:
    """Seconds left in the period: ESPN's numeric ``clock``, else its ``displayClock`` (m:ss)."""
    value = status.get("clock")
    if isinstance(value, (int, float)):
        return float(value)
    display = status.get("displayClock")
    if isinstance(display, str) and ":" in display:
        minutes, seconds = display.split(":", 1)
        try:
            return int(minutes) * 60 + float(seconds)
        except ValueError:
            return None
    return None


QUARTER_SECONDS = 15 * 60
GAME_SECONDS = 4 * QUARTER_SECONDS


def share_left(game: dict | None) -> float:
    """Share of a 60-minute game still to play: 1 before kickoff, 0 when final, in overtime or without a clock."""
    if game is None or game.get("state") == "scheduled":
        return 1.0
    if game.get("state") != "in_progress":
        return 0.0
    quarter, clock = game.get("quarter"), game.get("clock")
    if quarter is None or clock is None or not 1 <= quarter <= 4:
        return 0.0
    left = (4 - quarter) * QUARTER_SECONDS + max(0.0, min(float(clock), QUARTER_SECONDS))
    return round(left / GAME_SECONDS, 4)


def parse_scoreboard(payload) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ScheduleError("scoreboard without an events list")
    games = []
    for event in payload["events"]:
        try:
            competitors = event["competitions"][0]["competitors"]
            sides = {c["homeAway"]: team(c["team"]["abbreviation"]) for c in competitors}
            scores = {c["homeAway"]: _int(c.get("score")) for c in competitors}
            status = event["status"]
            state = STATES[status["type"]["state"]]
            kickoff = parse_iso(event["date"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ScheduleError(f"unexpected scoreboard event: {exc}") from exc
        if "home" not in sides or "away" not in sides:
            raise ScheduleError("scoreboard event without both teams")
        games.append(
            {
                "home": sides["home"],
                "away": sides["away"],
                "kickoff_utc": kickoff.isoformat(),
                "state": state,
                "quarter": _int(status.get("period")),
                "clock": _clock_seconds(status),
                "home_score": scores.get("home"),
                "away_score": scores.get("away"),
            }
        )
    games.sort(key=lambda g: (g["kickoff_utc"], g["home"]))
    byes = sorted(team(t["abbreviation"]) for t in (payload.get("week") or {}).get("teamsOnBye") or [] if t.get("abbreviation"))
    return {"games": games, "byes": byes}


def fetch_week(client: SleeperClient, season: str, week: int) -> dict:
    url = f"{SCOREBOARD}?seasontype=2&week={int(week)}&dates={season}"
    return parse_scoreboard(client.get_json(url))


@dataclass
class ScheduleReport:
    written: list[tuple[str, int]]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def refresh_schedule(client: SleeperClient, store: Store, *, all_weeks: bool = False) -> ScheduleReport:
    """Store the current and next NFL week (or every week); a failure writes nothing."""
    report = ScheduleReport(written=[], errors=[])
    try:
        state = client.state()
    except SleeperError as exc:
        report.errors.append(f"state: {exc}")
        return report
    season = str(state.get("season") or state.get("league_season") or "")
    week = int(state.get("week") or 0)
    if not season:
        report.errors.append("state without a season")
        return report
    if all_weeks:
        weeks = list(NFL_WEEKS)
    elif state.get("season_type") in ("regular", "post") and week:
        weeks = [w for w in (week, week + 1) if w in NFL_WEEKS]
    else:
        weeks = []
    fetched = {}
    for w in weeks:
        try:
            fetched[w] = fetch_week(client, season, w)
        except (SleeperError, ScheduleError) as exc:
            report.errors.append(f"week {w}: {exc}")
            log.error("schedule %s week %s failed: %s", season, w, exc)
            return report
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for w, parsed in fetched.items():
        store.write_nfl_week(season, w, {"season": season, "week": w, "fetched_at": now, **parsed})
        report.written.append((season, w))
    return report


class Schedule:
    """Kickoff lookups for one season, read from the stored week files."""

    def __init__(self, store: Store, season: str):
        self.store = store
        self.season = str(season)
        self._weeks: dict[int, dict | None] = {}

    def week(self, week: int) -> dict | None:
        if week not in self._weeks:
            self._weeks[week] = self.store.read_nfl_week(self.season, week)
        return self._weeks[week]

    def has_week(self, week: int) -> bool:
        return self.week(week) is not None

    def game_for(self, week: int, nfl_team: str | None) -> dict | None:
        data = self.week(week)
        if not data or not nfl_team:
            return None
        abbr = team(nfl_team)
        return next((g for g in data["games"] if abbr in (g["home"], g["away"])), None)

    def on_bye(self, week: int, nfl_team: str | None) -> bool | None:
        """True on bye, False with a game, None when the week is not stored or the team is in neither list."""
        if not self.has_week(week) or not nfl_team:
            return None
        if self.game_for(week, nfl_team) is not None:
            return False
        return True if team(nfl_team) in (self.week(week).get("byes") or []) else None

    def is_team(self, week: int, code: str) -> bool:
        """Whether ``code`` is an NFL team in this week's schedule (playing or on bye): how defenses are keyed."""
        data = self.week(week) or {}
        return code in self.teams_playing(week) or code in (data.get("byes") or [])

    def kickoff(self, week: int, nfl_team: str | None) -> datetime | None:
        game = self.game_for(week, nfl_team)
        return parse_iso(game["kickoff_utc"]) if game else None

    def kicked_off(self, week: int, nfl_team: str | None, at: datetime) -> bool:
        """Whether the team's game had started by ``at`` (a game already in progress or final counts)."""
        game = self.game_for(week, nfl_team)
        if game is None:
            return False
        return game["state"] != "scheduled" or parse_iso(game["kickoff_utc"]) <= at

    def teams_playing(self, week: int) -> set[str]:
        data = self.week(week) or {"games": []}
        return {t for g in data["games"] for t in (g["home"], g["away"])}


# -- the run record and the schedule summary ----------------------------------------------------
#
# Both live under data/refresh/, which is rebuilt each run and never committed. The summary is
# what the refresh relay's clock decides the refresh mode from (docs/refresh-modes.md); the cold
# run uploads it to the relay when its hash changes.

SUMMARY_FILE = "schedule_summary.json"


def last_run_path(store: Store):
    return store.root / "refresh" / "last_run.json"


def read_last_run(store: Store) -> datetime | None:
    path = last_run_path(store)
    if not path.exists():
        return None
    from ffapp.store import read_json

    started = (read_json(path) or {}).get("started_at")
    return parse_iso(started) if started else None


def write_last_run(store: Store, at: datetime) -> None:
    from ffapp.store import write_json

    write_json(last_run_path(store), {"started_at": at.isoformat(timespec="seconds")})


def schedule_summary(store: Store, league_keys, state: dict | None) -> dict:
    """What the relay's clock needs: whether it is the off-season, and every stored game of the
    current and next NFL week with its kickoff (epoch ms), slate (its kickoff time) and state.

    Off-season: no configured league's latest stored season is in season (Sleeper's league status
    ``in_season``). Without Sleeper's NFL state the summary carries no games.
    """
    statuses = []
    for key in league_keys:
        seasons = store.seasons(key)
        league = store.read_league(key, seasons[-1]) if seasons else None
        statuses.append(str((league or {}).get("status") or ""))
    offseason = "in_season" not in statuses
    season = str((state or {}).get("season") or "")
    week = int((state or {}).get("week") or 0)
    games = []
    if season and week and not offseason:
        for w in (week, week + 1):
            for game in (store.read_nfl_week(season, w) or {}).get("games") or []:
                kickoff = parse_iso(game["kickoff_utc"])
                games.append({
                    "id": f"{season}-{w:02d}-{game['away']}@{game['home']}",
                    "week": w,
                    "kickoff": int(kickoff.timestamp() * 1000),
                    "slate": kickoff.isoformat(),
                    "state": game.get("state") or "scheduled",
                })
    games.sort(key=lambda g: (g["kickoff"], g["id"]))
    return {"season": season, "week": week, "offseason": offseason, "games": games}


def summary_hash(summary: dict) -> str:
    import hashlib
    import json

    return hashlib.sha256(json.dumps(summary, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def write_summary(store: Store, summary: dict) -> bool:
    """Write the summary; True when it differs from the one stored (so the relay needs it)."""
    from ffapp.store import read_json, write_json

    path = store.root / "refresh" / SUMMARY_FILE
    old = read_json(path) if path.exists() else None
    write_json(path, summary)
    return old is None or summary_hash(old) != summary_hash(summary)
