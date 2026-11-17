"""Load and validate ``config/leagues.yaml``."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("config") / "leagues.yaml"


@dataclass(frozen=True)
class SiteConfig:
    """Website settings. ``refresh_url``: the refresh relay (see relay/README.md); no button without it."""

    refresh_url: str | None = None


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
class SimulationConfig:
    """Optional tuning of the Monte Carlo. Defaults reproduce the untuned model exactly."""

    residual_scale: float = 1.0  # multiplies every sampled score residual
    replacement_top_n: int = 3  # free agents averaged per position for the replacement level
    prior_weeks: float = 4.0  # shrinkage weight (in weeks) toward earlier seasons for the season replacement value


@dataclass(frozen=True)
class RatingsConfig:
    """Manager rating parameters. Defaults come from the rating spike; they apply to every league alike."""

    revert: float = 1.0 / 3.0  # fraction of the way each rating mean moves toward start_mu every preseason
    early_k: tuple[float, ...] = (2.0, 1.75, 1.5, 1.25)  # multipliers on the mean update in the first rated weeks
    start_mu: float = 1000.0  # every manager's first rating
    start_sigma: float = 1000.0 / 3.0  # starting uncertainty
    ewma_weight: float = 0.2  # weight of the newest week in the exponentially weighted z-score


@dataclass(frozen=True)
class Config:
    leagues: dict[str, LeagueConfig]
    overrides: list[ScoringOverride] = field(default_factory=list)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    ratings: RatingsConfig = field(default_factory=RatingsConfig)
    site: SiteConfig = field(default_factory=lambda: SiteConfig())

    def overrides_for(self, league_key: str, season: str) -> list[ScoringOverride]:
        """Overrides for one league-season, ordered by from_week ascending."""
        matching = [o for o in self.overrides if o.league == league_key and o.season == season]
        return sorted(matching, key=lambda o: o.from_week)


_TOP_KEYS = {"leagues", "overrides", "simulation", "ratings", "site"}
_SITE_KEYS = {"refresh_url"}
_LEAGUE_KEYS = {"league_id", "name"}
_OVERRIDE_KEYS = {"league", "season", "from_week", "scoring"}
_SIMULATION_KEYS = {"residual_scale", "replacement_top_n", "prior_weeks"}
_RATINGS_KEYS = {"revert", "early_k", "start_mu", "start_sigma", "ewma_weight"}


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


def _parse_simulation(raw: Any) -> SimulationConfig:
    if raw is None:
        return SimulationConfig()
    mapping = _require_mapping(raw, "simulation")
    _reject_unknown(mapping, _SIMULATION_KEYS, "simulation")
    scale = mapping.get("residual_scale", 1.0)
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not scale > 0:
        raise ConfigError(f"simulation.residual_scale must be a positive number, got {scale!r}")
    top_n = mapping.get("replacement_top_n", 3)
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ConfigError(f"simulation.replacement_top_n must be a positive integer, got {top_n!r}")
    prior_weeks = mapping.get("prior_weeks", 4.0)
    if isinstance(prior_weeks, bool) or not isinstance(prior_weeks, (int, float)) or prior_weeks < 0:
        raise ConfigError(f"simulation.prior_weeks must be a non-negative number, got {prior_weeks!r}")
    return SimulationConfig(residual_scale=float(scale), replacement_top_n=int(top_n), prior_weeks=float(prior_weeks))


def _number(mapping: dict, key: str, default: float, where: str, *, low: float, high: float | None = None, low_open: bool = False) -> float:
    value = mapping.get(key, default)
    ok = not isinstance(value, bool) and isinstance(value, (int, float))
    if ok:
        ok = (value > low) if low_open else (value >= low)
        if high is not None:
            ok = ok and value <= high
    if not ok:
        bounds = f"{'>' if low_open else '>='} {low}" + (f" and <= {high}" if high is not None else "")
        raise ConfigError(f"{where}.{key} must be a number {bounds}, got {value!r}")
    return float(value)


def _parse_ratings(raw: Any) -> RatingsConfig:
    if raw is None:
        return RatingsConfig()
    mapping = _require_mapping(raw, "ratings")
    _reject_unknown(mapping, _RATINGS_KEYS, "ratings")
    defaults = RatingsConfig()
    revert = _number(mapping, "revert", defaults.revert, "ratings", low=0.0, high=1.0)
    start_mu = _number(mapping, "start_mu", defaults.start_mu, "ratings", low=0.0, low_open=True)
    start_sigma = _number(mapping, "start_sigma", start_mu / 3.0, "ratings", low=0.0, low_open=True)
    ewma = _number(mapping, "ewma_weight", defaults.ewma_weight, "ratings", low=0.0, high=1.0, low_open=True)
    early = mapping.get("early_k", list(defaults.early_k))
    if not isinstance(early, list) or not early or any(isinstance(k, bool) or not isinstance(k, (int, float)) or k < 1 for k in early):
        raise ConfigError(f"ratings.early_k must be a non-empty list of numbers >= 1, got {early!r}")
    if any(b > a for a, b in zip(early, early[1:])):
        raise ConfigError(f"ratings.early_k must not increase from week to week, got {early!r}")
    return RatingsConfig(revert=revert, early_k=tuple(float(k) for k in early), start_mu=start_mu, start_sigma=start_sigma, ewma_weight=ewma)


def _parse_site(raw: Any) -> SiteConfig:
    if raw is None:
        return SiteConfig()
    mapping = _require_mapping(raw, "site")
    _reject_unknown(mapping, _SITE_KEYS, "site")
    url = mapping.get("refresh_url")
    if url is None or url == "":
        return SiteConfig()
    if not isinstance(url, str) or not url.startswith("https://") or any(c.isspace() for c in url):
        raise ConfigError(f"site.refresh_url must be an https:// address, got {url!r}")
    return SiteConfig(refresh_url=url.rstrip("/"))


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
    return Config(
        leagues=leagues,
        overrides=overrides,
        simulation=_parse_simulation(top.get("simulation")),
        ratings=_parse_ratings(top.get("ratings")),
        site=_parse_site(top.get("site")),
    )


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
