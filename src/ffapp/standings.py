"""Regular-season standings and playoff seeding from stored matchups."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TeamRecord:
    roster_id: int
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    results: list[str] = field(default_factory=list)  # "W", "L", "T" per played week

    @property
    def win_value(self) -> float:
        """Wins with a tie counting as half a win, the sorting key Sleeper uses."""
        return self.wins + 0.5 * self.ties

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

    def sort_key(self) -> tuple[float, float]:
        return (self.win_value, round(self.points_for, 2))


def pairings(matchups: list[dict]) -> list[tuple[dict, dict]]:
    """Group one week's matchup rows into (team, opponent) pairs. Unpaired rows (byes) are skipped."""
    by_id: dict[int, list[dict]] = {}
    for team in matchups:
        if team.get("matchup_id") is None:
            continue
        by_id.setdefault(int(team["matchup_id"]), []).append(team)
    return [(a, b) for group in by_id.values() if len(group) == 2 for a, b in [group]]


def regular_season_records(
    matchups_by_week: dict[int, list[dict]],
    weeks,
    roster_ids=None,
) -> dict[int, TeamRecord]:
    """Tally W/L/T and points over ``weeks`` from stored matchups.

    Only weeks present in ``matchups_by_week`` count; a week with all-zero
    points (not yet played) must be excluded by the caller via ``weeks``.
    """
    records: dict[int, TeamRecord] = {}
    if roster_ids is not None:
        for rid in roster_ids:
            records[int(rid)] = TeamRecord(int(rid))
    for week in weeks:
        for a, b in pairings(matchups_by_week.get(week, [])):
            ra = records.setdefault(int(a["roster_id"]), TeamRecord(int(a["roster_id"])))
            rb = records.setdefault(int(b["roster_id"]), TeamRecord(int(b["roster_id"])))
            pa, pb = float(a.get("points") or 0.0), float(b.get("points") or 0.0)
            ra.points_for += pa
            ra.points_against += pb
            rb.points_for += pb
            rb.points_against += pa
            if pa > pb:
                ra.wins += 1
                rb.losses += 1
                ra.results.append("W")
                rb.results.append("L")
            elif pb > pa:
                rb.wins += 1
                ra.losses += 1
                rb.results.append("W")
                ra.results.append("L")
            else:
                ra.ties += 1
                rb.ties += 1
                ra.results.append("T")
                rb.results.append("T")
    return records


def seed_order(records: dict[int, TeamRecord]) -> list[int]:
    """Roster IDs from the 1 seed down: most wins (ties = half), then most points scored.

    A residual tie (same wins and points to the cent) falls to the lower roster_id,
    which keeps the order deterministic.
    """
    return sorted(records, key=lambda rid: (records[rid].sort_key(), -rid), reverse=True)


def seeds(records: dict[int, TeamRecord]) -> dict[int, int]:
    """roster_id -> seed number (1 = best)."""
    return {rid: i + 1 for i, rid in enumerate(seed_order(records))}
