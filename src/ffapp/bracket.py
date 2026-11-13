"""Six-team playoff brackets, written to run on arrays so the simulation can
play thousands of brackets at once.

Shape (Sleeper's 6-team bracket, verified against both leagues' history):

    round 1 (m1: seed 4 v 5, m2: seed 3 v 6; seeds 1 and 2 sit out)
    round 2 (m3: seed 1 v ?, m4: seed 2 v ?, m5: round-1 losers play for 5th)
    round 3 (m6: final, m7: 3rd place)

``reseed`` decides round 2: True pairs seed 1 with the lowest surviving seed
(Sleeper playoff_seed_type 1); False keeps a fixed bracket where seed 1 meets
the 4v5 winner and seed 2 the 3v6 winner (playoff_seed_type 0).

The same machinery runs the losers bracket. A consolation bracket passes seeds
7..12 with the higher scorer advancing; a toilet bowl passes 12..7 with
``advance_loser=True`` so the lower scorer moves on.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np

# decide(round, team_a, team_b) -> the HIGHER scorer of each pair, as an array like team_a.
Decide = Callable[[int, np.ndarray, np.ndarray], np.ndarray]


@dataclass
class Game:
    round: int
    match: int
    t1: np.ndarray
    t2: np.ndarray
    higher: np.ndarray  # higher scorer
    advancer: np.ndarray  # team that moves on (== higher unless advance_loser)
    place: int | None = None  # the place this game decides (1, 3 or 5), if any

    def pair(self, run: int = 0) -> frozenset[int]:
        return frozenset((int(self.t1[run]), int(self.t2[run])))


@dataclass
class BracketOutcome:
    games: list[Game] = field(default_factory=list)
    places: dict[int, np.ndarray] = field(default_factory=dict)  # place -> team per run

    @property
    def champion(self) -> np.ndarray:
        return self.places[1]

    @property
    def runner_up(self) -> np.ndarray:
        return self.places[2]

    def game(self, round: int, match: int) -> Game:
        return next(g for g in self.games if g.round == round and g.match == match)


def _as_arrays(seeds: Sequence) -> list[np.ndarray]:
    arrays = [np.atleast_1d(np.asarray(s)) for s in seeds]
    if len(arrays) != 6:
        raise ValueError(f"a six-team bracket needs 6 seeds, got {len(arrays)}")
    return arrays


def run_six_team_bracket(
    seeds: Sequence,
    decide: Decide,
    *,
    reseed: bool,
    advance_loser: bool = False,
) -> BracketOutcome:
    """Play a 6-team bracket. ``seeds[0]`` is the top seed; each seed is a team per run."""
    s1, s2, s3, s4, s5, s6 = _as_arrays(seeds)
    out = BracketOutcome()

    def play(round: int, match: int, a: np.ndarray, b: np.ndarray, place: int | None = None) -> Game:
        higher = decide(round, a, b)
        lower = np.where(higher == a, b, a)
        advancer = lower if advance_loser else higher
        game = Game(round, match, a, b, higher, advancer, place)
        out.games.append(game)
        return game

    def eliminated(game: Game) -> np.ndarray:
        return np.where(game.advancer == game.t1, game.t2, game.t1)

    m1 = play(1, 1, s4, s5)
    m2 = play(1, 2, s3, s6)
    a1, a2 = m1.advancer, m2.advancer

    if reseed:
        # seed 1 meets the lowest surviving seed: s6 if it is still in, else the 4/5 survivor
        six_alive = a2 == s6
        m3_opp = np.where(six_alive, s6, a1)
        m4_opp = np.where(six_alive, a1, s3)
    else:
        m3_opp, m4_opp = a1, a2
    m3 = play(2, 3, s1, m3_opp)
    m4 = play(2, 4, s2, m4_opp)
    m5 = play(2, 5, eliminated(m1), eliminated(m2), place=5)

    m6 = play(3, 6, m3.advancer, m4.advancer, place=1)
    m7 = play(3, 7, eliminated(m3), eliminated(m4), place=3)

    out.places = {
        1: m6.advancer,
        2: eliminated(m6),
        3: m7.advancer,
        4: eliminated(m7),
        5: m5.advancer,
        6: eliminated(m5),
    }
    return out


@dataclass(frozen=True)
class BracketRules:
    """How a league-season runs its brackets, read from Sleeper settings.

    Derived from the two leagues' nine completed seasons and checked by
    ``ffapp verify-brackets``: playoff_seed_type 1 re-seeds round 2;
    playoff_type 1 makes the losers bracket a consolation bracket (seeds 7-12,
    higher scorer advances), 0 a toilet bowl (reverse-seeded, lower scorer advances).
    """

    playoff_teams: int
    playoff_week_start: int
    reseed: bool
    toilet_bowl: bool

    @classmethod
    def from_league(cls, league: dict) -> BracketRules:
        settings = league.get("settings", {})
        return cls(
            playoff_teams=int(settings.get("playoff_teams") or 6),
            playoff_week_start=int(settings.get("playoff_week_start") or 15),
            reseed=int(settings.get("playoff_seed_type") or 0) == 1,
            toilet_bowl=int(settings.get("playoff_type") or 0) == 0,
        )

    @property
    def rounds(self) -> int:
        return 3

    def week_for_round(self, round: int) -> int:
        return self.playoff_week_start + round - 1

    def supported(self) -> bool:
        return self.playoff_teams == 6

    def winners_seeds(self, seed_order: Sequence) -> list:
        return list(seed_order[:6])

    def losers_seeds(self, seed_order: Sequence) -> list:
        rest = list(seed_order[6:12])
        return rest[::-1] if self.toilet_bowl else rest

    def run_winners(self, seed_order: Sequence, decide: Decide) -> BracketOutcome:
        return run_six_team_bracket(self.winners_seeds(seed_order), decide, reseed=self.reseed)

    def run_losers(self, seed_order: Sequence, decide: Decide) -> BracketOutcome:
        return run_six_team_bracket(
            self.losers_seeds(seed_order), decide, reseed=self.reseed, advance_loser=self.toilet_bowl
        )
