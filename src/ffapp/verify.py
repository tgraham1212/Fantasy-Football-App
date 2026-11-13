"""Check the bracket logic against every completed season's real Sleeper brackets."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ffapp.bracket import BracketOutcome, BracketRules
from ffapp.config import Config
from ffapp.standings import regular_season_records, seed_order
from ffapp.store import SeasonData, Store


@dataclass
class SeasonCheck:
    league_key: str
    season: str
    mismatches: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatches


def _sleeper_pairs_by_round(bracket: list[dict]) -> dict[int, set[frozenset[int]]]:
    rounds: dict[int, set[frozenset[int]]] = {}
    for game in bracket:
        if game.get("t1") is None or game.get("t2") is None:
            continue
        rounds.setdefault(int(game["r"]), set()).add(frozenset((int(game["t1"]), int(game["t2"]))))
    return rounds


def _our_pairs_by_round(outcome: BracketOutcome) -> dict[int, set[frozenset[int]]]:
    rounds: dict[int, set[frozenset[int]]] = {}
    for game in outcome.games:
        rounds.setdefault(game.round, set()).add(game.pair())
    return rounds


def _points_decider(data: SeasonData, rules: BracketRules):
    """Decide games by the real points each roster scored that playoff week."""
    points = {}
    for round in range(1, rules.rounds + 1):
        week = rules.week_for_round(round)
        points[round] = {int(t["roster_id"]): float(t.get("points") or 0.0) for t in data.matchups.get(week, [])}

    def decide(round: int, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        pa = np.array([points[round].get(int(x), 0.0) for x in a])
        pb = np.array([points[round].get(int(x), 0.0) for x in b])
        return np.where(pa >= pb, a, b)  # a is always the better seed; it keeps a tie

    return decide


def check_season(league_key: str, data: SeasonData) -> SeasonCheck:
    check = SeasonCheck(league_key, data.season)
    rules = BracketRules.from_league(data.league)
    if not rules.supported():
        check.mismatches.append(f"unsupported bracket: {rules.playoff_teams} playoff teams")
        return check
    if not data.winners_bracket:
        check.notes.append("no bracket stored")
        return check

    start = int(data.league.get("settings", {}).get("start_week") or 1)
    records = regular_season_records(data.matchups, range(start, rules.playoff_week_start))
    order = seed_order(records)
    if len(order) < 12:
        check.mismatches.append(f"only {len(order)} teams in standings")
        return check
    seeds = np.array(order)
    decide = _points_decider(data, rules)

    for label, outcome, real in (
        ("winners", rules.run_winners(seeds, decide), data.winners_bracket),
        ("losers", rules.run_losers(seeds, decide), data.losers_bracket),
    ):
        ours = _our_pairs_by_round(outcome)
        theirs = _sleeper_pairs_by_round(real)
        for round in sorted(set(ours) | set(theirs)):
            if ours.get(round, set()) != theirs.get(round, set()):
                seed_of = {rid: i + 1 for i, rid in enumerate(order)}

                def fmt(pairs):
                    return sorted(sorted(seed_of.get(r, r) for r in p) for p in pairs)

                check.mismatches.append(
                    f"{label} round {round}: ours {fmt(ours.get(round, set()))} vs sleeper {fmt(theirs.get(round, set()))}"
                )
        # placement games: Sleeper marks the game that decides place p
        for game in real:
            place = game.get("p")
            if place and game.get("w") is not None and label == "winners":
                ours_place = int(outcome.places[place][0])
                if ours_place != int(game["w"]):
                    check.mismatches.append(
                        f"{label} place {place}: ours roster {ours_place} vs sleeper roster {game['w']}"
                    )
    check.notes.append(f"reseed={rules.reseed} toilet_bowl={rules.toilet_bowl}")
    return check


def verify_all(store: Store, config: Config) -> list[SeasonCheck]:
    checks: list[SeasonCheck] = []
    for key in config.leagues:
        for season in store.seasons(key):
            data = store.read_season(key, season)
            if data.status != "complete":
                continue
            checks.append(check_season(key, data))
    return checks
