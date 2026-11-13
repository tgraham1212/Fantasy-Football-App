import time

import numpy as np
import pytest

from ffapp.bracket import BracketRules
from ffapp.lineup import Starter
from ffapp.noise import GaussianNoise
from ffapp.simulate import SimInputs, simulate, summarize
from ffapp.standings import TeamRecord

RULES = BracketRules(playoff_teams=6, playoff_week_start=15, reseed=True, toilet_bowl=False)
TEAMS = list(range(1, 13))


def round_robin_schedule(weeks):
    """Deterministic pairings for 12 teams over the given weeks."""
    schedule = {}
    for k, week in enumerate(weeks):
        rotated = TEAMS[1:]
        rotated = rotated[k % 11 :] + rotated[: k % 11]
        line = [TEAMS[0]] + rotated
        schedule[week] = [(line[i], line[11 - i]) for i in range(6)]
    return schedule


def lineup_for(team, week, strength):
    # 9 starters whose projections add up to roughly 100 + strength
    base = (100.0 + strength) / 9
    return [Starter("SLOT", f"{team}-{i}", "WR", base) for i in range(9)]


def make_inputs(completed, fixed_wins=None, strengths=None):
    remaining = [w for w in range(1, 15) if w > completed]
    fixed = {}
    for t in TEAMS:
        w = (fixed_wins or {}).get(t, completed // 2)
        fixed[t] = TeamRecord(t, wins=w, losses=completed - w, points_for=100.0 * completed + t)
    strengths = strengths or {t: 0.0 for t in TEAMS}
    weeks = remaining + [15, 16, 17]
    starters = {t: {w: lineup_for(t, w, strengths[t]) for w in weeks} for t in TEAMS}
    return SimInputs(
        league_key="test",
        season="2026",
        completed_weeks=completed,
        rules=RULES,
        team_ids=TEAMS,
        fixed=fixed,
        schedule=round_robin_schedule(remaining),
        starters=starters,
    )


def test_outcome_rates_sum_correctly():
    result = simulate(make_inputs(completed=9), GaussianNoise(6.0), runs=4000, seed=1)
    rows = summarize(result)
    sums = {k: sum(r[k] for r in rows) for k in ("playoffs", "bye", "final", "title", "losers_bracket", "last", "semifinal")}
    assert sums["playoffs"] == pytest.approx(6.0, abs=0.01)
    assert sums["bye"] == pytest.approx(2.0, abs=0.01)
    assert sums["semifinal"] == pytest.approx(4.0, abs=0.01)
    assert sums["final"] == pytest.approx(2.0, abs=0.01)
    assert sums["title"] == pytest.approx(1.0, abs=0.01)
    assert sums["losers_bracket"] == pytest.approx(6.0, abs=0.01)
    assert sums["last"] == pytest.approx(1.0, abs=0.01)
    for row in rows:
        assert row["proj_wins"] + row["proj_losses"] + row["proj_ties"] == pytest.approx(14.0, abs=0.01)
        assert sum(row["seed_distribution"]) == pytest.approx(1.0, abs=0.01)


def test_clinched_team_has_certain_playoff_spot():
    # 9 weeks done: team 1 is 9-0, everyone else 2-7. With 5 weeks left nobody can catch 9 wins... except
    # several teams could reach 7; team 1 has 9 already, so it is locked into the top 6.
    fixed_wins = {t: 2 for t in TEAMS}
    fixed_wins[1] = 9
    result = simulate(make_inputs(completed=9, fixed_wins=fixed_wins), GaussianNoise(10.0), runs=2000, seed=3)
    rows = {r["roster_id"]: r for r in summarize(result)}
    assert rows[1]["playoffs"] == 1.0
    assert rows[1]["last"] == 0.0


def test_stronger_rosters_win_more():
    strengths = {t: 0.0 for t in TEAMS}
    strengths[5] = 30.0
    strengths[9] = -30.0
    result = simulate(make_inputs(completed=0, strengths=strengths), GaussianNoise(8.0), runs=3000, seed=7)
    rows = {r["roster_id"]: r for r in summarize(result)}
    assert rows[5]["title"] > 0.5 and rows[5]["playoffs"] > 0.99
    assert rows[9]["playoffs"] < 0.01 and rows[9]["last"] > 0.7


def test_same_seed_gives_identical_results():
    inputs = make_inputs(completed=5)
    a = summarize(simulate(inputs, GaussianNoise(5.0), runs=1500, seed=42))
    b = summarize(simulate(inputs, GaussianNoise(5.0), runs=1500, seed=42))
    c = summarize(simulate(inputs, GaussianNoise(5.0), runs=1500, seed=43))
    assert a == b
    assert a != c


def test_completed_playoff_round_uses_real_points():
    inputs = make_inputs(completed=15)
    # regular season over; seeds come straight from fixed records (wins equal, points decide: team 12 highest)
    inputs.real_points = {15: {t: float(t) for t in TEAMS}}  # higher roster id scored more in week 15
    result = simulate(inputs, GaussianNoise(0.0), runs=50, seed=0)
    rows = {r["roster_id"]: r for r in summarize(result)}
    # seeds by points_for: 12 is the 1 seed ... 7 is the 6 seed. Round 1: 10v9 and 9? -> seeds 3v6 = 10 v 7, 4v5 = 9 v 8
    # with real week-15 points, 10 beats 7 and 9 beats 8, so 7 and 8 cannot reach the final
    assert rows[7]["final"] == 0.0 and rows[8]["final"] == 0.0
    assert rows[12]["bye"] == 1.0 and rows[11]["bye"] == 1.0


def test_full_season_runs_fast_enough():
    inputs = make_inputs(completed=0)
    start = time.perf_counter()
    simulate(inputs, GaussianNoise(7.0), runs=10_000, seed=1)
    elapsed = time.perf_counter() - start
    assert elapsed < 60, f"took {elapsed:.1f}s"
