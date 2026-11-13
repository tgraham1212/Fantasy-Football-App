"""Load and validate ``config/leagues.yaml``."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("config") / "leagues.yaml"


class ConfigError(ValueError):
    """Raised when the leagues configuration is malformed."""


@dataclass(frozen=True)
class LeagueConfig:
    key: str
    league_id: str
    name: str


@dataclass(frozen=True)
class ScoringOverride:
    league: str
    season: str
    from_week: int
    scoring: dict[str, float]


@dataclass(frozen=True)
class Config:
    leagues: dict[str, LeagueConfig]
    overrides: list[ScoringOverride] = field(default_factory=list)

    def overrides_for(self, league_key: str, season: str) -> list[ScoringOverride]:
        """Overrides for one league-season, ordered by from_week ascending."""
        matching = [o for o in self.overrides if o.league == league_key and o.season == season]
        return sorted(matching, key=lambda o: o.from_week)


_TOP_KEYS = {"leagues", "overrides"}
_LEAGUE_KEYS = {"league_id", "name"}
_OVERRIDE_KEYS = {"league", "season", "from_week", "scoring"}


def _require_mapping(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"{where} must be a mapping")
    return value


def _reject_unknown(mapping: dict, allowed: set[str], where: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise ConfigError(f"{where} has unknown keys: {', '.join(sorted(unknown))}")


def _parse_league(key: str, raw: Any) -> LeagueConfig:
    where = f"leagues.{key}"
    mapping = _require_mapping(raw, where)
    _reject_unknown(mapping, _LEAGUE_KEYS, where)
    if not isinstance(key, str) or not key or not key.replace("-", "").replace("_", "").isalnum():
        raise ConfigError(f"league key {key!r} must be a short alphanumeric name")
    league_id = mapping.get("league_id")
    if league_id is None:
        raise ConfigError(f"{where}.league_id is required")
    league_id = str(league_id)
    if not league_id.isdigit():
        raise ConfigError(f"{where}.league_id must be a numeric Sleeper league ID, got {league_id!r}")
    name = mapping.get("name", key)
    if not isinstance(name, str) or not name:
        raise ConfigError(f"{where}.name must be a non-empty string")
    return LeagueConfig(key=key, league_id=league_id, name=name)


def _parse_override(index: int, raw: Any, league_keys: set[str]) -> ScoringOverride:
    where = f"overrides[{index}]"
    mapping = _require_mapping(raw, where)
    _reject_unknown(mapping, _OVERRIDE_KEYS, where)
    missing = _OVERRIDE_KEYS - set(mapping)
    if missing:
        raise ConfigError(f"{where} is missing: {', '.join(sorted(missing))}")
    league = mapping["league"]
    if league not in league_keys:
        raise ConfigError(f"{where}.league {league!r} is not a configured league")
    season = str(mapping["season"])
    if not (season.isdigit() and len(season) == 4):
        raise ConfigError(f"{where}.season must be a 4-digit year, got {season!r}")
    from_week = mapping["from_week"]
    if isinstance(from_week, bool) or not isinstance(from_week, int) or from_week < 1:
        raise ConfigError(f"{where}.from_week must be a positive integer")
    scoring = _require_mapping(mapping["scoring"], f"{where}.scoring")
    if not scoring:
        raise ConfigError(f"{where}.scoring must list at least one scoring key")
    parsed: dict[str, float] = {}
    for k, v in scoring.items():
        if not isinstance(k, str) or isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ConfigError(f"{where}.scoring.{k} must be a number")
        parsed[k] = float(v)
    return ScoringOverride(league=league, season=season, from_week=from_week, scoring=parsed)


def parse_config(raw: Any) -> Config:
    """Validate an already-parsed YAML document."""
    top = _require_mapping(raw, "config")
    _reject_unknown(top, _TOP_KEYS, "config")
    leagues_raw = _require_mapping(top.get("leagues"), "leagues")
    if not leagues_raw:
        raise ConfigError("leagues must list at least one league")
    leagues = {key: _parse_league(key, value) for key, value in leagues_raw.items()}
    ids = [league.league_id for league in leagues.values()]
    if len(ids) != len(set(ids)):
        raise ConfigError("two leagues share the same league_id")

    overrides_raw = top.get("overrides", []) or []
    if not isinstance(overrides_raw, list):
        raise ConfigError("overrides must be a list")
    overrides = [_parse_override(i, o, set(leagues)) for i, o in enumerate(overrides_raw)]
    return Config(leagues=leagues, overrides=overrides)


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> Config:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    return parse_config(raw)
