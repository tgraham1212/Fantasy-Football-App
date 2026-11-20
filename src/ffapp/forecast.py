"""Per-game forecasts and the projected playoff bracket, read off one simulation run.

Every simulated week becomes a list of games: each team's mean score, a shared 2-point
histogram of both teams' simulated scores, each team's win probability (ties split) and
the lineup the model used. Playoff weeks Sleeper has not paired yet get a projected
bracket: teams seeded by expected seed, the league's bracket rules, and in every game the
team with the higher win probability "scoring higher" (so a toilet bowl advances the team
more likely to score lower, as its rules do). Each projected game carries how often that
pairing happened across the simulations.
"""

from __future__ import annotations

import math

import numpy as np

from ffapp.bracket import Game, run_six_team_bracket
from ffapp.lineup import Starter
from ffapp.simulate import SimInputs, SimResult
from ffapp.store import SeasonData

BIN = 2.0
LOW_PCT, HIGH_PCT = 0.5, 99.5


def win_probability(sa: np.ndarray, sb: np.ndarray) -> float:
    return float(np.mean(sa > sb) + 0.5 * np.mean(sa == sb))


def histogram(*samples: np.ndarray) -> dict:
    """Shared 2-point bins from the 0.5th to the 99.5th percentile; per-mille shares per sample (tails clipped in)."""
    lo = min(float(np.percentile(s, LOW_PCT)) for s in samples)
    hi = max(float(np.percentile(s, HIGH_PCT)) for s in samples)
    start = math.floor(lo / BIN) * BIN
    stop = max(math.ceil(hi / BIN) * BIN, start + BIN)
    edges = np.arange(start, stop + BIN / 2, BIN)
    shares = []
    for s in samples:
        counts, _ = np.histogram(np.clip(s, start, stop - 1e-9), bins=edges)
        shares.append([int(round(1000.0 * float(c) / len(s))) for c in counts])
    return {"start": start, "width": BIN, "shares": shares}


LINEUP_FIELDS = ("slot", "player_id", "position", "projected")  # player_id None = replacement-level free agent
LIVE_FIELDS = ("status", "points", "clock", "share")  # appended for a starter locked in the live week


def lineup_rows(lineup: list[Starter]) -> list[list]:
    """Compact rows ``[slot, player_id, position, projected]``; a replacement fill has player_id None.
    A starter locked in the live week also carries ``status`` (final / in_progress), ``points`` and ``clock``."""
    rows = []
    for s in lineup:
        row = [s.slot, None if s.player_id.startswith("FA:") else s.player_id, s.position, round(float(s.projected), 1)]
        if s.status:
            row += [s.status, round(float(s.fixed), 2), s.clock, round(float(s.share), 4)]
        rows.append(row)
    return rows


def live_totals(lineup: list[Starter]) -> dict:
    """Points already scored and starters still to kick off, for a lineup with locked starters."""
    return {
        "points_so_far": round(sum(float(s.fixed) for s in lineup), 2),
        "to_play": sum(1 for s in lineup if not s.status),
    }


def game(inputs: SimInputs, result: SimResult, week: int, rid_a: int, rid_b: int, **extra) -> dict:
    index = {rid: i for i, rid in enumerate(result.team_ids)}
    sa = result.weekly_scores[week][:, index[rid_a]]
    sb = result.weekly_scores[week][:, index[rid_b]]
    pa = win_probability(sa, sb)
    teams = []
    lineups = {rid: inputs.starters.get(rid, {}).get(week, []) for rid in (rid_a, rid_b)}
    # once either side has a starter under way, both show points so far and starters to play,
    # so a team still waiting on its first kickoff reads 0.0 like its opponent's live score
    started = any(st.status for lineup in lineups.values() for st in lineup)
    for rid, s, p in ((rid_a, sa, pa), (rid_b, sb, 1.0 - pa)):
        lineup = lineups[rid]
        team = {
            "roster_id": rid,
            "mean": round(float(np.mean(s)), 2),
            "win_prob": round(p, 4),
            "lineup": lineup_rows(lineup),
        }
        if started:
            team.update(live_totals(lineup))
        teams.append(team)
    key = extra.pop("key", None) or "-".join(str(r) for r in sorted((rid_a, rid_b)))
    margin = sa - sb
    return {
        "key": key, **extra, "teams": teams, "hist": histogram(sa, sb),
        "margin_mean": round(float(np.mean(margin)), 3), "margin_sd": round(float(np.std(margin)), 3),
    }


# -- playoff brackets --------------------------------------------------------------------


def expected_seed_order(result: SimResult) -> list[int]:
    """Team indices best first by mean simulated seed (ties by index)."""
    means = result.seeds.mean(axis=0)
    return sorted(range(len(result.team_ids)), key=lambda i: (means[i], i))


def favourite_decider(inputs: SimInputs, result: SimResult):
    """A bracket ``decide`` for a single projected bracket: the higher win probability 'scores higher'."""

    def decide(round: int, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        week = inputs.rules.week_for_round(round)
        ia, ib = int(a[0]), int(b[0])
        if week in inputs.real_points:
            real = inputs.real_points[week]
            pa = real.get(result.team_ids[ia], 0.0) >= real.get(result.team_ids[ib], 0.0)
            return a if pa else b
        scores = result.weekly_scores[week]
        return a if win_probability(scores[:, ia], scores[:, ib]) >= 0.5 else b

    return decide


def pairing_frequency(games: list[Game], round: int, match: int, ia: int, ib: int) -> float:
    found = next((g for g in games if g.round == round and g.match == match), None)
    if found is None:
        return 0.0
    hit = ((found.t1 == ia) & (found.t2 == ib)) | ((found.t1 == ib) & (found.t2 == ia))
    return round_share(float(np.mean(hit)))


def round_share(x: float) -> float:
    return round(x, 4)


def real_pairings(entries: list[dict]) -> dict[tuple[int, int], tuple[int, int]]:
    """(round, match) -> (roster_id, roster_id) for Sleeper bracket entries with both teams set."""
    out = {}
    for e in entries or []:
        t1, t2 = e.get("t1"), e.get("t2")
        if isinstance(t1, int) and isinstance(t2, int):
            out[(int(e["r"]), int(e["m"]))] = (t1, t2)
    return out


def playoff_games(inputs: SimInputs, result: SimResult, data: SeasonData, week: int) -> tuple[list[dict], list[dict]]:
    """Games and first-round byes for one unscored playoff week, winners bracket first."""
    rules = inputs.rules
    round_no = week - rules.playoff_week_start + 1
    order = expected_seed_order(result)
    seed_arrays = [np.array([i]) for i in order]
    decide = favourite_decider(inputs, result)
    brackets = [("winners", rules.winners_seeds(seed_arrays), False, result.winners_games, data.winners_bracket)]
    if rules.toilet_bowl:
        brackets.append(("losers", rules.losers_seeds(seed_arrays), True, result.losers_games, data.losers_bracket))
    games, byes = [], []
    # Sleeper fills its bracket from the live standings all season, so a pairing is only real once the
    # week before it is final (the regular season for round 1, the previous round after that).
    settled = inputs.completed_weeks >= week - 1
    for name, seeds, advance_loser, sim_games, sleeper_entries in brackets:
        outcome = run_six_team_bracket(seeds, decide, reseed=rules.reseed, advance_loser=advance_loser)
        real = real_pairings(sleeper_entries) if settled else {}
        seed_of = {int(s[0]): n + 1 for n, s in enumerate(seeds)}
        if round_no == 1:
            for n in (0, 1):
                byes.append({"roster_id": result.team_ids[int(seeds[n][0])], "bracket": name, "seed": n + 1})
        for g in outcome.games:
            if g.round != round_no:
                continue
            ia, ib = int(g.t1[0]), int(g.t2[0])
            pair = real.get((g.round, g.match))
            if pair:
                rid_a, rid_b, projected, freq = pair[0], pair[1], False, None
            else:
                rid_a, rid_b = result.team_ids[ia], result.team_ids[ib]
                projected, freq = True, pairing_frequency(sim_games, g.round, g.match, ia, ib)
            idx = {rid: i for i, rid in enumerate(result.team_ids)}
            games.append(
                game(
                    inputs, result, week, rid_a, rid_b,
                    key=f"{name}-r{g.round}-m{g.match}",
                    bracket=name,
                    round=g.round,
                    match=g.match,
                    place=g.place,
                    projected=projected,
                    frequency=freq,
                    seeds=[seed_of.get(idx[rid_a]), seed_of.get(idx[rid_b])],
                )
            )
    return games, byes


def game_forecasts(inputs: SimInputs, result: SimResult, data: SeasonData) -> dict[str, dict]:
    """``{week: {kind, games, byes}}`` for every week the run simulated."""
    out: dict[str, dict] = {}
    for week in inputs.regular_weeks:
        games = [
            game(inputs, result, week, a, b, bracket="regular", projected=False, frequency=None)
            for a, b in inputs.schedule[week]
        ]
        out[str(week)] = {"kind": "regular", "games": games, "byes": []}
    for week in inputs.playoff_weeks:
        if week in inputs.real_points or week not in result.weekly_scores:
            continue
        games, byes = playoff_games(inputs, result, data, week)
        out[str(week)] = {"kind": "playoff", "games": games, "byes": byes}
    return out
