"""Vectorized Monte Carlo of the rest of a season: regular weeks, seeding, brackets."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ffapp.bracket import BracketRules
from ffapp.lineup import Starter
from ffapp.noise import NoiseModel
from ffapp.standings import TeamRecord


@dataclass
class SimInputs:
    league_key: str
    season: str
    completed_weeks: int  # weeks whose results are final (0 = preseason)
    rules: BracketRules
    team_ids: list[int]  # roster ids, index = team position in every array
    fixed: dict[int, TeamRecord]  # records after the completed regular-season weeks
    schedule: dict[int, list[tuple[int, int]]]  # remaining regular week -> (roster_id, roster_id) pairs
    starters: dict[int, dict[int, list[Starter]]]  # roster_id -> week -> projected lineup
    real_points: dict[int, dict[int, float]] = field(default_factory=dict)  # scored playoff weeks -> points

    @property
    def regular_weeks(self) -> list[int]:
        return sorted(self.schedule)

    @property
    def playoff_weeks(self) -> list[int]:
        return [self.rules.week_for_round(r) for r in range(1, self.rules.rounds + 1)]


@dataclass
class SimResult:
    runs: int
    seed: int
    team_ids: list[int]
    wins: np.ndarray  # (runs, n) final regular-season win value (ties = 0.5)
    losses: np.ndarray
    ties: np.ndarray
    points: np.ndarray  # (runs, n) final regular-season points
    seeds: np.ndarray  # (runs, n) seed number per team, 1 = best
    champion: np.ndarray  # (runs,) team index
    runner_up: np.ndarray
    semifinalists: np.ndarray  # (runs, 4) team indices
    losers_winner: np.ndarray  # (runs,) team index that "won" the losers bracket
    weekly_scores: dict[int, np.ndarray]  # week -> (runs, n) simulated scores (unscored weeks only)


def simulate(inputs: SimInputs, noise: NoiseModel, *, runs: int = 10_000, seed: int = 0) -> SimResult:
    rng = np.random.default_rng(seed)
    ids = inputs.team_ids
    n = len(ids)
    index = {rid: i for i, rid in enumerate(ids)}
    run_idx = np.arange(runs)

    def simulated_scores(week: int) -> np.ndarray:
        scores = np.zeros((runs, n))
        for rid, by_week in inputs.starters.items():
            total = np.zeros(runs)
            for starter in by_week.get(week, []):
                total += starter.projected + noise.sample(starter.position, starter.projected, rng, runs)
            scores[:, index[rid]] = total
        return scores

    # -- regular season ------------------------------------------------------
    wins = np.zeros((runs, n))
    losses = np.zeros((runs, n))
    ties = np.zeros((runs, n))
    points = np.zeros((runs, n))
    for rid, rec in inputs.fixed.items():
        i = index[rid]
        wins[:, i] = rec.wins
        losses[:, i] = rec.losses
        ties[:, i] = rec.ties
        points[:, i] = rec.points_for

    weekly: dict[int, np.ndarray] = {}
    for week in inputs.regular_weeks:
        scores = simulated_scores(week)
        weekly[week] = scores
        for rid_a, rid_b in inputs.schedule[week]:
            a, b = index[rid_a], index[rid_b]
            sa, sb = scores[:, a], scores[:, b]
            a_wins = sa > sb
            b_wins = sb > sa
            tie = ~a_wins & ~b_wins
            wins[:, a] += a_wins
            wins[:, b] += b_wins
            losses[:, a] += b_wins
            losses[:, b] += a_wins
            ties[:, a] += tie
            ties[:, b] += tie
            points[:, a] += sa
            points[:, b] += sb

    win_value = wins + 0.5 * ties
    # best first: most wins, then most points, then lowest team index (deterministic)
    order = np.lexsort((np.broadcast_to(np.arange(n), (runs, n)), -np.round(points, 2), -win_value), axis=-1)
    seeds = np.empty((runs, n), dtype=int)
    np.put_along_axis(seeds, order, np.broadcast_to(np.arange(1, n + 1), (runs, n)), axis=1)

    # -- playoffs ------------------------------------------------------------
    for week in inputs.playoff_weeks:
        if week not in inputs.real_points:
            weekly[week] = simulated_scores(week)

    def decide(round: int, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        week = inputs.rules.week_for_round(round)
        if week in inputs.real_points:
            real = np.array([inputs.real_points[week].get(rid, 0.0) for rid in ids])
            pa, pb = real[a], real[b]
        else:
            pa, pb = weekly[week][run_idx, a], weekly[week][run_idx, b]
        return np.where(pa >= pb, a, b)

    seed_arrays = [order[:, k] for k in range(n)]
    winners = inputs.rules.run_winners(seed_arrays, decide)
    losers = inputs.rules.run_losers(seed_arrays, decide)
    semis = np.stack([winners.game(2, 3).t1, winners.game(2, 3).t2, winners.game(2, 4).t1, winners.game(2, 4).t2], axis=1)

    return SimResult(
        runs=runs,
        seed=seed,
        team_ids=ids,
        wins=wins,
        losses=losses,
        ties=ties,
        points=points,
        seeds=seeds,
        champion=winners.champion,
        runner_up=winners.runner_up,
        semifinalists=semis,
        losers_winner=losers.champion,
        weekly_scores=weekly,
    )


def summarize(result: SimResult) -> list[dict]:
    """Per-team outcome rates and projected record, as plain numbers."""
    runs = result.runs
    n = len(result.team_ids)
    playoff_teams = 6
    rows = []
    for i, rid in enumerate(result.team_ids):
        seeds_i = result.seeds[:, i]
        in_final = (result.champion == i) | (result.runner_up == i)
        rows.append(
            {
                "roster_id": rid,
                "proj_wins": round(float(result.wins[:, i].mean()), 2),
                "proj_losses": round(float(result.losses[:, i].mean()), 2),
                "proj_ties": round(float(result.ties[:, i].mean()), 2),
                "proj_points": round(float(result.points[:, i].mean()), 1),
                "playoffs": round(float((seeds_i <= playoff_teams).mean()), 4),
                "bye": round(float((seeds_i <= 2).mean()), 4),
                "semifinal": round(float((result.semifinalists == i).any(axis=1).mean()), 4),
                "final": round(float(in_final.mean()), 4),
                "title": round(float((result.champion == i).mean()), 4),
                "losers_bracket": round(float((seeds_i > playoff_teams).mean()), 4),
                "last": round(float((seeds_i == n).mean()), 4),
                "seed_distribution": [round(float((seeds_i == s).sum() / runs), 4) for s in range(1, n + 1)],
            }
        )
    return rows
