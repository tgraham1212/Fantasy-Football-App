"""On-disk layout of everything ffapp stores, as plain JSON under ``data/``.

data/
  leagues/<league_key>/<season>/league.json          raw Sleeper league object
                                /users.json           raw users list
                                /rosters.json         raw rosters list
                                /brackets.json        {"winners": [...], "losers": [...]}
                                /matchups/week_NN.json raw matchups list
  projections/<season>/week_NN.json                   {player_id: projection record}
  odds/<league_key>/<season>/asof_NN.json             simulation results

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


class Store:
    def __init__(self, root: Path | str = DEFAULT_DATA_ROOT):
        self.root = Path(root)

    # -- paths ---------------------------------------------------------------

    def league_dir(self, league_key: str) -> Path:
        return self.root / "leagues" / league_key

    def season_dir(self, league_key: str, season: str) -> Path:
        return self.league_dir(league_key) / str(season)

    def matchup_path(self, league_key: str, season: str, week: int) -> Path:
        return self.season_dir(league_key, season) / "matchups" / f"week_{int(week):02d}.json"

    def projections_path(self, season: str, week: int) -> Path:
        return self.root / "projections" / str(season) / f"week_{int(week):02d}.json"

    def odds_path(self, league_key: str, season: str, as_of_week: int) -> Path:
        return self.root / "odds" / league_key / str(season) / f"asof_{int(as_of_week):02d}.json"

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
        return read_json(self.season_dir(league_key, season) / "users.json")

    def read_rosters(self, league_key: str, season: str) -> list:
        return read_json(self.season_dir(league_key, season) / "rosters.json")

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
        write_json(base / "league.json", data.league)
        write_json(base / "users.json", data.users)
        write_json(base / "rosters.json", data.rosters)
        write_json(base / "brackets.json", {"winners": data.winners_bracket, "losers": data.losers_bracket})
        for week, matchups in sorted(data.matchups.items()):
            write_json(self.matchup_path(league_key, data.season, week), matchups)

    # -- projections ---------------------------------------------------------

    def read_projections(self, season: str, week: int) -> dict[str, dict]:
        path = self.projections_path(season, week)
        return read_json(path) if path.exists() else {}

    def write_projections(self, season: str, week: int, records: dict[str, dict]) -> None:
        write_json(self.projections_path(season, week), records)

    def projection_seasons(self) -> list[str]:
        base = self.root / "projections"
        if not base.exists():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_dir() and _SEASON_RE.match(p.name))

    def projection_weeks(self, season: str) -> list[int]:
        base = self.root / "projections" / str(season)
        if not base.exists():
            return []
        return sorted(int(m.group(1)) for p in base.iterdir() if (m := _WEEK_RE.match(p.name)))

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
        write_json(self.odds_path(league_key, season, as_of_week), payload)
