"""Views over a stored league-season: owners, settings, roster slots."""

from __future__ import annotations

from dataclasses import dataclass

from ffapp.config import Config

STARTER_SLOTS = ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF", "SUPER_FLEX", "REC_FLEX", "WRRB_FLEX", "IDP_FLEX", "DL", "LB", "DB")
NON_STARTER_SLOTS = {"BN", "IR", "TAXI"}
FLEX_ELIGIBLE = {
    "FLEX": ("RB", "WR", "TE"),
    "SUPER_FLEX": ("QB", "RB", "WR", "TE"),
    "REC_FLEX": ("WR", "TE"),
    "WRRB_FLEX": ("RB", "WR"),
}


@dataclass(frozen=True)
class Owner:
    roster_id: int
    user_id: str
    display_name: str
    team_name: str


def owners(users: list[dict], rosters: list[dict]) -> dict[int, Owner]:
    """Map roster_id -> owner, identified by Sleeper user ID.

    Team names come from the user's league metadata; a user without one is
    shown as "Team <display name>", which is how Sleeper renders it.
    """
    by_user = {str(u["user_id"]): u for u in users}
    result: dict[int, Owner] = {}
    for roster in rosters:
        roster_id = int(roster["roster_id"])
        user_id = str(roster.get("owner_id") or "")
        user = by_user.get(user_id, {})
        display = str(user.get("display_name") or f"Unknown owner {user_id or roster_id}")
        team = str((user.get("metadata") or {}).get("team_name") or f"Team {display}")
        result[roster_id] = Owner(roster_id=roster_id, user_id=user_id, display_name=display, team_name=team)
    return result


def resolve_settings(config: Config, league_key: str, league: dict, week: int) -> dict[str, float]:
    """Scoring settings in force for ``week`` of a stored league-season.

    Sleeper's stored scoring settings are the base; configured overrides for the
    same league-season apply where ``from_week <= week``, later ones winning.
    """
    season = str(league["season"])
    scoring = {k: float(v) for k, v in (league.get("scoring_settings") or {}).items()}
    for override in config.overrides_for(league_key, season):
        if override.from_week <= week:
            scoring.update(override.scoring)
    return scoring


def starter_slots(league: dict) -> list[str]:
    """Starting lineup slots for a league-season, in Sleeper's order (bench, IR, taxi removed)."""
    return [slot for slot in league.get("roster_positions", []) if slot not in NON_STARTER_SLOTS]
