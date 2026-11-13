"""Pick the best legal starting lineup from projected points."""

from __future__ import annotations

from dataclasses import dataclass

from ffapp.league import FLEX_ELIGIBLE


@dataclass(frozen=True)
class Candidate:
    player_id: str
    position: str  # primary position, used for the noise pool
    positions: tuple[str, ...]  # every position the player may fill
    projected: float


@dataclass(frozen=True)
class Starter:
    slot: str
    player_id: str
    position: str
    projected: float


def best_lineup(slots: list[str], candidates: list[Candidate]) -> list[Starter]:
    """Greedy lineup: fill single-position slots with the top projections, then flex slots.

    Flex slots accept a superset of the positions filled before them, so greedy is
    optimal for QB/RB/WR/TE/FLEX/K/DEF layouts. Players projected for 0 points
    (byes, players ruled out, no projection) are only used when nobody with a
    positive projection can fill the slot, because candidates are taken in
    descending projection order.
    """
    remaining = sorted(candidates, key=lambda c: -c.projected)
    fixed = [s for s in slots if s not in FLEX_ELIGIBLE]
    flex = sorted((s for s in slots if s in FLEX_ELIGIBLE), key=lambda s: len(FLEX_ELIGIBLE[s]))
    lineup: list[Starter] = []
    for slot in fixed + flex:
        eligible = set(FLEX_ELIGIBLE.get(slot, (slot,)))
        for index, candidate in enumerate(remaining):
            if eligible & set(candidate.positions):
                lineup.append(Starter(slot, candidate.player_id, candidate.position, candidate.projected))
                del remaining[index]
                break
    return lineup


def lineup_points(lineup: list[Starter]) -> float:
    return sum(s.projected for s in lineup)
