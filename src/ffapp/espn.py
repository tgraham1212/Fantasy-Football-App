"""ESPN start-percentage snapshots and the ESPN-to-Sleeper player crosswalk.

ESPN's public fantasy player endpoint returns, per player, how many ESPN leagues
start and roster them. For a finished season the value is one frozen number; for
the season in progress it is live. Each run stores a slim snapshot (fantasy
positions with an ownership block only) per season that has none yet, and one for
the current regular-season week, overwriting that week until it rolls over.

Storage: ``data/espn/<season>/season.json``, ``data/espn/<season>/week_NN.json`` and
``data/espn/crosswalk.json`` (Sleeper's player list trimmed to id, ESPN id, name and
position). Matching an ESPN player to a Sleeper id goes: Sleeper's ESPN id, the alias
table, then normalised name and position with the NFL team as tiebreak. Defenses map
by team. Anyone unmatched is reported rather than guessed.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ffapp.projections import seasons_in_scope
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store

log = logging.getLogger(__name__)

ESPN_BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
FILTER_HEADER = {"X-Fantasy-Filter": '{"players":{"limit":5000}}'}
ESPN_POSITIONS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DEF"}
ESPN_TEAMS = {
    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET", 9: "GB", 10: "TEN",
    11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN", 17: "NE", 18: "NO", 19: "NYG", 20: "NYJ",
    21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC", 25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX",
    33: "BAL", 34: "HOU",
}
FANTASY_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
REPORT_THRESHOLD = 2.0  # percent started at or above which an unmatched player is reported

# ESPN full name -> Sleeper player id, for names the normalised match cannot bridge.
ALIASES = {
    "Kenneth Gainwell": "7567",  # Sleeper: Kenny Gainwell
    "Chigoziem Okonkwo": "8210",  # Sleeper: Chig Okonkwo
    "Bam Knight": "8122",  # Sleeper: Zonovan Knight
    "Travis Hunter": "12530",  # Sleeper lists him at DB
}

_SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")


class EspnError(RuntimeError):
    """ESPN returned something other than the expected shape."""


class EspnClient:
    """Requests to ESPN through the Sleeper client's throttle and retry plumbing."""

    def __init__(self, http: SleeperClient | None = None, base: str = ESPN_BASE):
        self.http = http or SleeperClient()
        self._base = base.rstrip("/")

    def players(self, season: str | int, scoring_period: int = 1) -> list:
        url = f"{self._base}/seasons/{season}/players?scoringPeriodId={int(scoring_period)}&view=kona_player_info"
        return self.http.get_json(url, headers=FILTER_HEADER)


# -- snapshots -------------------------------------------------------------------------


def slim_snapshot(payload) -> dict[str, dict]:
    """``{espn_id: {name, position, team, started, owned}}`` for fantasy-position players with an ownership block."""
    if not isinstance(payload, list):
        raise EspnError(f"expected a list of players, got {type(payload).__name__}")
    players: dict[str, dict] = {}
    for item in payload:
        if not isinstance(item, dict) or "id" not in item:
            raise EspnError("player row without an id")
        position = ESPN_POSITIONS.get(item.get("defaultPositionId"))
        ownership = item.get("ownership")
        if position is None or not isinstance(ownership, dict):
            continue
        try:
            started = float(ownership.get("percentStarted") or 0.0)
            owned = float(ownership.get("percentOwned") or 0.0)
        except (TypeError, ValueError) as exc:
            raise EspnError(f"bad ownership for player {item['id']}: {exc}") from exc
        players[str(item["id"])] = {
            "name": str(item.get("fullName") or item["id"]),
            "position": position,
            "team": ESPN_TEAMS.get(item.get("proTeamId")),
            "started": round(started, 2),
            "owned": round(owned, 2),
        }
    return players


def snapshot_payload(season: str, week: int | None, players: dict[str, dict]) -> dict:
    return {
        "season": str(season),
        "week": week,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "players": players,
    }


@dataclass
class CaptureReport:
    seasons_written: list[str] = field(default_factory=list)
    week_written: tuple[str, int] | None = None
    crosswalk_written: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def season_in_progress(store: Store, league_keys, season: str) -> bool:
    """True when any configured league stores ``season`` with a status other than complete."""
    for key in league_keys:
        league = store.read_league(key, season)
        if league is not None and league.get("status") != "complete":
            return True
    return False


def capture_snapshots(espn: EspnClient, sleeper: SleeperClient, store: Store, league_keys) -> CaptureReport:
    """Season snapshots for stored seasons lacking one or still in progress, then the current week's snapshot.

    A season in progress for any league is re-fetched every run so its frozen value ends up being the
    end-of-season one; a season every league has complete is never fetched again. Every fetch happens
    before any write, so a failure leaves the stored snapshots exactly as they were.
    """
    report = CaptureReport()
    seasons = [
        s for s in seasons_in_scope(store, league_keys)
        if store.read_espn_season(s) is None or season_in_progress(store, league_keys, s)
    ]
    fetched_seasons: dict[str, dict] = {}
    for season in seasons:
        try:
            fetched_seasons[season] = slim_snapshot(espn.players(season))
        except (SleeperError, EspnError) as exc:
            report.errors.append(f"season {season}: {exc}")
            log.error("espn season snapshot %s failed: %s", season, exc)
            return report
    weekly: tuple[str, int, dict] | None = None
    try:
        state = sleeper.state()
    except SleeperError as exc:
        report.errors.append(f"state: {exc}")
        return report
    if state.get("season_type") == "regular" and state.get("week"):
        season, week = str(state.get("season")), int(state["week"])
        try:
            weekly = (season, week, slim_snapshot(espn.players(season, week)))
        except (SleeperError, EspnError) as exc:
            report.errors.append(f"week {week}: {exc}")
            log.error("espn week snapshot %s week %s failed: %s", season, week, exc)
            return report
    for season, players in fetched_seasons.items():
        store.write_espn_season(season, snapshot_payload(season, None, players))
        report.seasons_written.append(season)
        log.info("espn season snapshot %s: %d players", season, len(players))
    if weekly:
        season, week, players = weekly
        store.write_espn_week(season, week, snapshot_payload(season, week, players))
        report.week_written = (season, week)
        log.info("espn week snapshot %s week %d: %d players", season, week, len(players))
    return report


# -- crosswalk -------------------------------------------------------------------------


def normalise(name: str) -> str:
    """Lowercase letters only, generational suffixes removed: "Travis Etienne Jr." -> "travisetienne"."""
    return re.sub(r"[^a-z]", "", _SUFFIX.sub("", str(name).lower()))


def slim_players(payload) -> dict[str, dict]:
    """Sleeper's player list trimmed to fantasy positions: ``{sleeper_id: {espn_id, name, position}}``."""
    if not isinstance(payload, dict):
        raise SleeperError(f"expected a player map, got {type(payload).__name__}", "players")
    out: dict[str, dict] = {}
    for pid, rec in payload.items():
        if not isinstance(rec, dict) or rec.get("position") not in FANTASY_POSITIONS:
            continue
        espn_id = rec.get("espn_id")
        name = rec.get("full_name") or " ".join(x for x in (rec.get("first_name"), rec.get("last_name")) if x)
        out[str(pid)] = {"espn_id": str(espn_id) if espn_id else None, "name": name, "position": rec["position"], "team": rec.get("team")}
    return out


def refresh_crosswalk(sleeper: SleeperClient, store: Store, payload: dict | None = None) -> bool:
    """Store the slim crosswalk from Sleeper's player list (fetched unless ``payload`` is given);
    returns True when the file changed."""
    players = slim_players(sleeper.players() if payload is None else payload)
    if store.read_crosswalk() == players:
        return False
    store.write_crosswalk(players)
    return True


def teams_from_stats(store: Store, season: str) -> dict[str, str]:
    """Each Sleeper player's NFL team in their last stat line of the season."""
    teams: dict[str, str] = {}
    for week in store.stats_weeks(season):
        for pid, rec in store.read_stats(season, week).items():
            if rec.get("team"):
                teams[str(pid)] = str(rec["team"])
    return teams


@dataclass
class Unmatched:
    espn_id: str
    name: str
    position: str
    started: float


def match(players: dict[str, dict], crosswalk: dict[str, dict], season_teams: dict[str, str]) -> tuple[dict[str, str], list[Unmatched]]:
    """Map snapshot players to Sleeper ids; unmatched players at or above the report threshold are listed."""
    by_espn = {rec["espn_id"]: sid for sid, rec in crosswalk.items() if rec.get("espn_id")}
    by_name: dict[tuple[str, str], list[str]] = {}
    for sid, rec in crosswalk.items():
        by_name.setdefault((normalise(rec.get("name") or ""), rec.get("position")), []).append(sid)
    mapping: dict[str, str] = {}
    unmatched: list[Unmatched] = []
    for espn_id, rec in players.items():
        sid = _match_one(espn_id, rec, by_espn, by_name, season_teams)
        if sid is not None:
            mapping[espn_id] = sid
        elif rec.get("started", 0.0) >= REPORT_THRESHOLD:
            unmatched.append(Unmatched(espn_id, rec["name"], rec["position"], rec["started"]))
    return mapping, unmatched


def _match_one(espn_id: str, rec: dict, by_espn: dict, by_name: dict, season_teams: dict[str, str]) -> str | None:
    if rec.get("position") == "DEF":
        return rec.get("team")
    if espn_id in by_espn:
        return by_espn[espn_id]
    if rec["name"] in ALIASES:
        return ALIASES[rec["name"]]
    candidates = by_name.get((normalise(rec["name"]), rec["position"]), [])
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1 and rec.get("team"):
        same_team = [sid for sid in candidates if season_teams.get(sid) == rec["team"]]
        if len(same_team) == 1:
            return same_team[0]
    return None
