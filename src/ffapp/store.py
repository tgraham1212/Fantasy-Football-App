"""On-disk layout of everything ffapp stores, as plain JSON under ``data/``.

data/
  leagues/<league_key>/<season>/league.json          raw Sleeper league object
                                /users.json           raw users list
                                /rosters.json         raw rosters list
                                /brackets.json        {"winners": [...], "losers": [...]}
                                /matchups/week_NN.json raw matchups list
                                /transactions/week_NN.json raw transactions list
                                /draft.json           {"draft", "picks", "traded_picks"} raw Sleeper draft
  adp/<season>.json                                   {player_id: {position, adp_half_ppr, adp_dynasty_half_ppr}}
  projections/<season>/week_NN.json                   {player_id: projection record}
  odds/<league_key>/<season>/asof_NN.json             simulation results
  odds/<league_key>/<season>/slates_NN.json           forecast as each slate of week NN went final
  games/<league_key>/<season>/week_NN.json            game log and prediction of record

Derived data is rebuilt by every run and never committed (docs/refresh-modes.md, "Where
Data Lives"); ``DERIVED_PATHS`` lists it, relative to the data root:

  projections-future/<season>/week_NN.json            projections for weeks after the current one
  games-derived/<league_key>/<season>/week_NN.json    game files' forecast, views and baseline
  nfl-live/<season>/week_NN.json                      the latest scoreboard, with live clocks and scores
  ratings/, replacement/, war/, model/                recomputed from the records
  odds/<league_key>/<season>/live.json                the latest live forecast
  refresh/                                            last run time, schedule summary, site hash

Every write goes to a temp file in the same directory and is swapped in with
``os.replace`` so a crash never leaves a half-written file behind.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_DATA_ROOT = Path("data")
# Rebuilt by every run, never committed (glob patterns relative to the data root).
DERIVED_PATHS = ("projections-future", "games-derived", "nfl-live", "model", "ratings", "replacement", "war", "odds/*/*/live.json", "refresh")
# The parts of a game file that are records; everything else in it is rebuilt.
GAME_RECORD_KEYS = ("league_key", "season", "week", "log", "record")
_SEASON_RE = re.compile(r"^\d{4}$")
_WEEK_RE = re.compile(r"^week_(\d{2})\.json$")
_ASOF_RE = re.compile(r"^asof_(\d{2})\.json$")


def write_json(path: Path, payload: Any) -> None:
    """Atomically write ``payload`` as pretty JSON to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_if_changed(path: Path, payload: dict, ignore: tuple[str, ...]) -> bool:
    """Write ``payload`` unless the stored file differs from it only in the ``ignore`` keys (times),
    so a run that found nothing new leaves the record, and git, unchanged. True when written."""
    if path.exists():
        old = read_json(path)
        if isinstance(old, dict) and {k: v for k, v in old.items() if k not in ignore} == {k: v for k, v in payload.items() if k not in ignore}:
            return False
    write_json(path, payload)
    return True


@dataclass
class SeasonData:
    """Everything stored for one league-season."""

    league: dict
    users: list
    rosters: list
    matchups: dict[int, list] = field(default_factory=dict)
    winners_bracket: list = field(default_factory=list)
    losers_bracket: list = field(default_factory=list)

    @property
    def season(self) -> str:
        return str(self.league["season"])

    @property
    def league_id(self) -> str:
        return str(self.league["league_id"])

    @property
    def status(self) -> str:
        return str(self.league.get("status", ""))


def nfl_record(payload: dict) -> dict:
    """The committed part of a stored NFL week: no fetch time; clocks and scores only once final."""
    games = []
    for game in payload.get("games") or []:
        kept = {k: game[k] for k in ("home", "away", "kickoff_utc", "state") if k in game}
        if game.get("state") == "final":
            kept.update({k: game.get(k) for k in ("home_score", "away_score") if k in game})
        games.append(kept)
    return {"season": payload.get("season"), "week": payload.get("week"), "games": games, "byes": payload.get("byes") or []}


class Store:
    def __init__(self, root: Path | str = DEFAULT_DATA_ROOT):
        self.root = Path(root)
        self._owners_cache: dict[str, dict[str, dict[int, str]]] = {}  # league -> season -> roster id -> owner

    # -- paths ---------------------------------------------------------------

    def league_dir(self, league_key: str) -> Path:
        return self.root / "leagues" / league_key

    def season_dir(self, league_key: str, season: str) -> Path:
        return self.league_dir(league_key) / str(season)

    def matchup_path(self, league_key: str, season: str, week: int) -> Path:
        return self.season_dir(league_key, season) / "matchups" / f"week_{int(week):02d}.json"

    def transactions_path(self, league_key: str, season: str, week: int) -> Path:
        return self.season_dir(league_key, season) / "transactions" / f"week_{int(week):02d}.json"

    def projections_path(self, season: str, week: int) -> Path:
        return self.root / "projections" / str(season) / f"week_{int(week):02d}.json"

    def stats_path(self, season: str, week: int) -> Path:
        return self.root / "stats" / str(season) / f"week_{int(week):02d}.json"

    def odds_path(self, league_key: str, season: str, as_of_week: int) -> Path:
        return self.root / "odds" / league_key / str(season) / f"asof_{int(as_of_week):02d}.json"

    def live_path(self, league_key: str, season: str) -> Path:
        return self.root / "odds" / league_key / str(season) / "live.json"

    def read_live(self, league_key: str, season: str) -> dict | None:
        path = self.live_path(league_key, season)
        return read_json(path) if path.exists() else None

    def write_live(self, league_key: str, season: str, payload: dict) -> None:
        write_json(self.live_path(league_key, season), payload)

    def delete_live(self, league_key: str, season: str) -> bool:
        path = self.live_path(league_key, season)
        if path.exists():
            path.unlink()
            return True
        return False

    def espn_season_path(self, season: str) -> Path:
        return self.root / "espn" / str(season) / "season.json"

    def espn_week_path(self, season: str, week: int) -> Path:
        return self.root / "espn" / str(season) / f"week_{int(week):02d}.json"

    def crosswalk_path(self) -> Path:
        return self.root / "espn" / "crosswalk.json"

    def nfl_week_path(self, season: str, week: int) -> Path:
        return self.root / "nfl" / str(season) / f"week_{int(week):02d}.json"

    def nfl_live_path(self, season: str, week: int) -> Path:
        return self.root / "nfl-live" / str(season) / f"week_{int(week):02d}.json"

    def injuries_path(self, season: str, week: int) -> Path:
        return self.root / "injuries" / str(season) / f"week_{int(week):02d}.json"

    def player_details_path(self, season: str, week: int) -> Path:
        return self.root / "players" / str(season) / f"week_{int(week):02d}.json"

    def trending_path(self, season: str, day: str) -> Path:
        return self.root / "trending" / str(season) / f"{day}.json"

    def games_path(self, league_key: str, season: str, week: int) -> Path:
        return self.root / "games" / league_key / str(season) / f"week_{int(week):02d}.json"

    def games_derived_path(self, league_key: str, season: str, week: int) -> Path:
        return self.root / "games-derived" / league_key / str(season) / f"week_{int(week):02d}.json"

    def future_projections_path(self, season: str, week: int) -> Path:
        return self.root / "projections-future" / str(season) / f"week_{int(week):02d}.json"

    def slates_path(self, league_key: str, season: str, week: int) -> Path:
        return self.root / "odds" / league_key / str(season) / f"slates_{int(week):02d}.json"

    # -- league seasons ------------------------------------------------------

    def seasons(self, league_key: str) -> list[str]:
        """Stored seasons for a league, oldest first."""
        base = self.league_dir(league_key)
        if not base.exists():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_dir() and _SEASON_RE.match(p.name))

    def has_season(self, league_key: str, season: str) -> bool:
        return (self.season_dir(league_key, season) / "league.json").exists()

    def read_league(self, league_key: str, season: str) -> dict | None:
        path = self.season_dir(league_key, season) / "league.json"
        return read_json(path) if path.exists() else None

    def read_users(self, league_key: str, season: str) -> list:
        """The season's users, plus the stored record of any owner a vacant roster inherits."""
        users = read_json(self.season_dir(league_key, season) / "users.json")
        known = {str(u.get("user_id")) for u in users}
        for roster in self.read_rosters(league_key, season):
            source = roster.get("owner_inherited")
            uid = str(roster.get("owner_id") or "")
            if source and uid and uid not in known:
                for user in read_json(self.season_dir(league_key, source) / "users.json"):
                    if str(user.get("user_id")) == uid:
                        users.append(user)
                        known.add(uid)
                        break
        return users

    def read_rosters(self, league_key: str, season: str) -> list:
        """The season's rosters, with each vacant roster read as owned by the owner it inherits.

        Sleeper reports a roster with no owner when its manager left before the league year
        officially ended, although they played the season (dynasty 2023 roster 11). Such a roster
        reads as owned by the most recent owner of that roster slot in an earlier stored season,
        else the first later owner, and carries ``owner_inherited`` naming the season the owner
        came from. A slot with no owner in any stored season stays vacant. Stored files are never
        changed.
        """
        rosters = read_json(self.season_dir(league_key, season) / "rosters.json")
        if all(r.get("owner_id") for r in rosters):
            return rosters
        owners = self._roster_owners(league_key)
        seasons = sorted(owners)
        out = []
        for roster in rosters:
            if roster.get("owner_id"):
                out.append(roster)
                continue
            rid = int(roster["roster_id"])
            earlier = [s for s in seasons if s < season and owners[s].get(rid)]
            later = [s for s in seasons if s > season and owners[s].get(rid)]
            source = earlier[-1] if earlier else (later[0] if later else None)
            if source is None:
                out.append(roster)
                continue
            out.append({**roster, "owner_id": owners[source][rid], "owner_inherited": source})
        return out

    def _roster_owners(self, league_key: str) -> dict[str, dict[int, str]]:
        """Season -> roster id -> owner user id as stored (vacant rosters left out), cached."""
        if league_key not in self._owners_cache:
            table: dict[str, dict[int, str]] = {}
            for season in self.seasons(league_key):
                path = self.season_dir(league_key, season) / "rosters.json"
                if path.exists():
                    table[season] = {int(r["roster_id"]): str(r["owner_id"]) for r in read_json(path) if r.get("owner_id")}
            self._owners_cache[league_key] = table
        return self._owners_cache[league_key]

    def read_brackets(self, league_key: str, season: str) -> dict:
        path = self.season_dir(league_key, season) / "brackets.json"
        return read_json(path) if path.exists() else {"winners": [], "losers": []}

    def matchup_weeks(self, league_key: str, season: str) -> list[int]:
        base = self.season_dir(league_key, season) / "matchups"
        if not base.exists():
            return []
        weeks = []
        for p in base.iterdir():
            m = _WEEK_RE.match(p.name)
            if m:
                weeks.append(int(m.group(1)))
        return sorted(weeks)

    def read_matchups(self, league_key: str, season: str, week: int) -> list:
        path = self.matchup_path(league_key, season, week)
        return read_json(path) if path.exists() else []

    def has_transactions(self, league_key: str, season: str) -> bool:
        return (self.season_dir(league_key, season) / "transactions").is_dir()

    def read_transactions(self, league_key: str, season: str) -> dict[int, list]:
        """Week -> the raw transactions Sleeper filed under it; empty when none are stored."""
        base = self.season_dir(league_key, season) / "transactions"
        out: dict[int, list] = {}
        if base.is_dir():
            for p in sorted(base.iterdir()):
                m = _WEEK_RE.match(p.name)
                if m:
                    out[int(m.group(1))] = read_json(p)
        return out

    def write_transactions(self, league_key: str, season: str, weeks: dict[int, list]) -> None:
        for week, rows in sorted(weeks.items()):
            write_json(self.transactions_path(league_key, season, week), rows)

    # -- drafts and ADP --------------------------------------------------------

    def draft_path(self, league_key: str, season: str) -> Path:
        return self.season_dir(league_key, season) / "draft.json"

    def has_draft(self, league_key: str, season: str) -> bool:
        return self.draft_path(league_key, season).exists()

    def read_draft(self, league_key: str, season: str) -> dict | None:
        """``{draft, picks, traded_picks}`` as fetched from Sleeper, or None when not stored."""
        path = self.draft_path(league_key, season)
        return read_json(path) if path.exists() else None

    def write_draft(self, league_key: str, season: str, payload: dict) -> None:
        write_json(self.draft_path(league_key, season), payload)

    def adp_path(self, season: str) -> Path:
        return self.root / "adp" / f"{season}.json"

    def has_adp(self, season: str) -> bool:
        return self.adp_path(season).exists()

    def read_adp(self, season: str) -> dict[str, dict]:
        """Player id -> ``{position, adp_half_ppr, adp_dynasty_half_ppr}``; empty when not stored."""
        path = self.adp_path(season)
        return read_json(path) if path.exists() else {}

    def write_adp(self, season: str, payload: dict[str, dict]) -> None:
        write_json(self.adp_path(season), payload)

    def read_season(self, league_key: str, season: str) -> SeasonData:
        league = self.read_league(league_key, season)
        if league is None:
            raise FileNotFoundError(f"no stored season {season} for league {league_key}")
        brackets = self.read_brackets(league_key, season)
        return SeasonData(
            league=league,
            users=self.read_users(league_key, season),
            rosters=self.read_rosters(league_key, season),
            matchups={w: self.read_matchups(league_key, season, w) for w in self.matchup_weeks(league_key, season)},
            winners_bracket=brackets.get("winners", []),
            losers_bracket=brackets.get("losers", []),
        )

    def write_season(self, league_key: str, data: SeasonData) -> None:
        """Store a fully fetched season. Each file is swapped in atomically."""
        base = self.season_dir(league_key, data.season)
        self._owners_cache.pop(league_key, None)
        write_json(base / "league.json", data.league)
        write_json(base / "users.json", data.users)
        write_json(base / "rosters.json", data.rosters)
        write_json(base / "brackets.json", {"winners": data.winners_bracket, "losers": data.losers_bracket})
        for week, matchups in sorted(data.matchups.items()):
            write_json(self.matchup_path(league_key, data.season, week), matchups)

    # -- projections ---------------------------------------------------------

    def read_projections(self, season: str, week: int) -> dict[str, dict]:
        """The committed week if there is one, else the rebuilt future week, else nothing."""
        for path in (self.projections_path(season, week), self.future_projections_path(season, week)):
            if path.exists():
                return read_json(path)
        return {}

    def write_projections(self, season: str, week: int, records: dict[str, dict], *, future: bool = False) -> None:
        """A week after the current one goes to the rebuilt (uncommitted) folder; the current and
        earlier weeks are records. Once a week becomes current its future copy is removed."""
        if future:
            write_json(self.future_projections_path(season, week), records)
            return
        write_json(self.projections_path(season, week), records)
        self.future_projections_path(season, week).unlink(missing_ok=True)

    def projection_seasons(self) -> list[str]:
        base = self.root / "projections"
        if not base.exists():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_dir() and _SEASON_RE.match(p.name))

    def projection_weeks(self, season: str) -> list[int]:
        weeks: set[int] = set()
        for base in (self.root / "projections" / str(season), self.root / "projections-future" / str(season)):
            if base.exists():
                weeks.update(int(m.group(1)) for p in base.iterdir() if (m := _WEEK_RE.match(p.name)))
        return sorted(weeks)

    # -- actual stats ---------------------------------------------------------

    def read_stats(self, season: str, week: int) -> dict[str, dict]:
        path = self.stats_path(season, week)
        return read_json(path) if path.exists() else {}

    def write_stats(self, season: str, week: int, records: dict[str, dict]) -> None:
        write_json(self.stats_path(season, week), records)

    def stats_weeks(self, season: str) -> list[int]:
        base = self.root / "stats" / str(season)
        if not base.exists():
            return []
        return sorted(int(m.group(1)) for p in base.iterdir() if (m := _WEEK_RE.match(p.name)))

    # -- ESPN snapshots -------------------------------------------------------

    def read_espn_season(self, season: str) -> dict | None:
        path = self.espn_season_path(season)
        return read_json(path) if path.exists() else None

    def write_espn_season(self, season: str, payload: dict) -> None:
        write_if_changed(self.espn_season_path(season), payload, ("captured_at",))

    def read_espn_week(self, season: str, week: int) -> dict | None:
        path = self.espn_week_path(season, week)
        return read_json(path) if path.exists() else None

    def write_espn_week(self, season: str, week: int, payload: dict) -> None:
        write_if_changed(self.espn_week_path(season, week), payload, ("captured_at",))

    def espn_weeks(self, season: str) -> list[int]:
        base = self.root / "espn" / str(season)
        if not base.exists():
            return []
        return sorted(int(m.group(1)) for p in base.iterdir() if (m := _WEEK_RE.match(p.name)))

    def read_crosswalk(self) -> dict[str, dict] | None:
        path = self.crosswalk_path()
        return read_json(path) if path.exists() else None

    def write_crosswalk(self, players: dict[str, dict]) -> None:
        write_json(self.crosswalk_path(), players)

    # -- NFL schedule, injuries, game logs ----------------------------------------

    def read_nfl_week(self, season: str, week: int) -> dict | None:
        """The latest scoreboard copy (with live clocks and scores) when this run has one, else the record."""
        for path in (self.nfl_live_path(season, week), self.nfl_week_path(season, week)):
            if path.exists():
                return read_json(path)
        return None

    def write_nfl_week(self, season: str, week: int, payload: dict) -> None:
        """Write the full scoreboard copy (rebuilt, uncommitted) and, only when it changed, the
        record: teams, kickoff, state and final scores, without the fetch time or live clocks."""
        write_json(self.nfl_live_path(season, week), payload)
        record = nfl_record(payload)
        path = self.nfl_week_path(season, week)
        if not path.exists() or nfl_record(read_json(path)) != record:
            write_json(path, record)

    def read_injuries(self, season: str, week: int) -> dict[str, str] | None:
        path = self.injuries_path(season, week)
        return read_json(path) if path.exists() else None

    def write_injuries(self, season: str, week: int, statuses: dict[str, str]) -> None:
        write_json(self.injuries_path(season, week), statuses)

    def read_player_details(self, season: str, week: int) -> dict[str, dict] | None:
        path = self.player_details_path(season, week)
        return read_json(path) if path.exists() else None

    def write_player_details(self, season: str, week: int, details: dict[str, dict]) -> None:
        write_json(self.player_details_path(season, week), details)

    def read_games(self, league_key: str, season: str, week: int) -> dict | None:
        """The week's game file: its committed record part merged with its rebuilt part."""
        path = self.games_path(league_key, season, week)
        derived = self.games_derived_path(league_key, season, week)
        if not path.exists() and not derived.exists():
            return None
        merged = read_json(path) if path.exists() else {}
        if derived.exists():
            merged.update(read_json(derived))
        return merged

    def write_games(self, league_key: str, season: str, week: int, payload: dict) -> None:
        """Split the game file: records (log, prediction of record) to ``games/``, written only
        when they changed; the forecast, views and baseline to ``games-derived/``."""
        record = {k: payload[k] for k in GAME_RECORD_KEYS if k in payload}
        derived = {k: v for k, v in payload.items() if k not in GAME_RECORD_KEYS}
        path = self.games_path(league_key, season, week)
        if not path.exists() or read_json(path) != record:
            write_json(path, record)
        dpath = self.games_derived_path(league_key, season, week)
        if derived and (not dpath.exists() or read_json(dpath) != derived):
            write_json(dpath, derived)

    def read_slates(self, league_key: str, season: str, week: int) -> dict:
        path = self.slates_path(league_key, season, week)
        return read_json(path) if path.exists() else {}

    def write_slates(self, league_key: str, season: str, week: int, payload: dict) -> None:
        write_json(self.slates_path(league_key, season, week), payload)

    # -- odds history --------------------------------------------------------

    def odds_weeks(self, league_key: str, season: str) -> list[int]:
        base = self.root / "odds" / league_key / str(season)
        if not base.exists():
            return []
        return sorted(int(m.group(1)) for p in base.iterdir() if (m := _ASOF_RE.match(p.name)))

    def read_odds(self, league_key: str, season: str, as_of_week: int) -> dict | None:
        path = self.odds_path(league_key, season, as_of_week)
        return read_json(path) if path.exists() else None

    def write_odds(self, league_key: str, season: str, as_of_week: int, payload: dict) -> None:
        """Skipped when only the time changed, so an unchanged forecast is not a new record."""
        write_if_changed(self.odds_path(league_key, season, as_of_week), payload, ("generated_at",))
