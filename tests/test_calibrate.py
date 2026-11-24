import copy
import json

import numpy as np
import pytest

from ffapp.bracket import BracketRules
from ffapp.calibrate import (
    INTERVALS,
    OUTCOMES,
    baseline_probability,
    brier,
    build_report,
    completed_seasons,
    included_as_of_weeks,
    interval_coverage,
    lineup_gap,
    mean_bias,
    pit,
    reliability_bins,
    render_markdown,
    replay_season,
    run_calibration,
    season_outcomes,
    season_rows,
    skill,
    win_probability,
    write_report,
)
from ffapp.config import Config, LeagueConfig
from ffapp.odds import projected_lineup
from ffapp.projections import upsert_week
from ffapp.sleeper import SleeperClient
from ffapp.standings import TeamRecord
from ffapp.store import Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, FixtureSession, load

CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
CONFIG = Config(leagues={"dynasty": CFG})
RULES = BracketRules(playoff_teams=6, playoff_week_start=15, reseed=True, toilet_bowl=False)


@pytest.fixture
def store_2025(tmp_path):
    """Dynasty fixtures synced, with the 2025 week-1 projections reused for every 2025 week."""
    store = Store(tmp_path / "data")
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, CFG)
    rows = load("projections/2025/1.json")
    for week in range(1, 18):
        reused = copy.deepcopy(rows)
        for row in reused:
            row["week"] = week
        upsert_week(store, "2025", week, reused)
    return store


# -- which seasons -------------------------------------------------------------


def test_completed_seasons_excludes_the_season_in_progress(store_2025):
    found = completed_seasons(store_2025, CONFIG)
    assert ("dynasty", "2026") not in found
    assert ("dynasty", "2025") in found
    assert all(league == "dynasty" for league, _ in found)
    assert [s for _, s in found] == sorted(s for _, s in found)


# -- ground truth ----------------------------------------------------------------


def test_season_outcomes_from_standings_and_bracket(store_2025):
    data = store_2025.read_season("dynasty", "2025")
    outcomes = season_outcomes(data)
    assert len(outcomes) == 12
    totals = {o: sum(team[o] for team in outcomes.values()) for o in OUTCOMES}
    assert totals == {"playoffs": 6, "bye": 2, "final": 2, "title": 1, "losers_bracket": 6, "last": 1, "avoid_losers_bye": 10}
    champion = next(g["w"] for g in data.winners_bracket if g.get("p") == 1)
    assert outcomes[int(champion)]["title"] is True
    assert outcomes[int(champion)]["final"] is True and outcomes[int(champion)]["playoffs"] is True
    assert sum(1 for t in outcomes.values() if t["title"]) == 1


def test_included_as_of_weeks_stop_before_the_deciding_week():
    for outcome in ("playoffs", "bye", "losers_bracket", "last", "avoid_losers_bye"):
        assert list(included_as_of_weeks(outcome, RULES)) == list(range(0, 14))
    assert list(included_as_of_weeks("final", RULES)) == list(range(0, 16))
    assert list(included_as_of_weeks("title", RULES)) == list(range(0, 17))


# -- score metrics -----------------------------------------------------------------


def test_pit_and_coverage_on_calibrated_noise():
    rng = np.random.default_rng(0)
    hits = {str(int(l * 100)): 0 for l in INTERVALS}
    pits = []
    trials = 400
    for _ in range(trials):
        samples = rng.normal(0.0, 1.0, size=10_000)
        actual = rng.normal(0.0, 1.0)
        pits.append(pit(samples, actual))
        for key, hit in interval_coverage(samples, actual).items():
            hits[key] += hit
    for level in INTERVALS:
        assert abs(hits[str(int(level * 100))] / trials - level) < 0.05
    assert abs(np.mean(pits) - 0.5) < 0.05


def test_pit_edge_cases():
    assert pit(np.full(100, 5.0), 5.0) == 0.5
    assert pit(np.arange(100.0), 1000.0) == 1.0
    assert pit(np.arange(100.0), -1.0) == 0.0
    assert mean_bias(np.array([10.0, 12.0]), 9.0) == 2.0


# -- game metrics ------------------------------------------------------------------


def test_win_probability_counts_ties_half():
    assert win_probability(np.array([1.0, 2.0, 3.0, 4.0]), np.array([2.0, 2.0, 1.0, 1.0])) == 0.5 * 0.25 + 0.5


def test_reliability_bins_and_brier():
    p = np.array([0.0, 0.0, 1.0, 1.0])
    y = np.array([0, 0, 1, 1])
    assert brier(p, y) == 0.0
    assert brier(np.full(4, 0.5), np.array([1, 0, 1, 0])) == 0.25
    assert brier([], []) is None
    bins = reliability_bins([0.05, 0.95, 0.96, 1.0], [0, 1, 1, 0])
    assert len(bins) == 10
    assert bins[0] == {"lo": 0.0, "hi": 0.1, "count": 1, "predicted": 0.05, "observed": 0.0}
    assert bins[9]["count"] == 3 and bins[9]["observed"] == pytest.approx(2 / 3, abs=1e-4)
    empty = bins[5]
    assert empty["count"] == 0 and empty["observed"] is None and empty["predicted"] is None
    assert skill(0.1, 0.2) == 0.5 and skill(None, 0.2) is None and skill(0.1, 0.0) is None


# -- baseline ------------------------------------------------------------------------


def records_with(wins_by_team, games):
    return {t: TeamRecord(t, wins=w, losses=games - w, points_for=1000.0 - t) for t, w in wins_by_team.items()}


def test_baseline_is_base_rate_before_the_season():
    recs = records_with({t: 0 for t in range(1, 13)}, 0)
    playoffs = baseline_probability("playoffs", recs, 14, 14, 12)
    title = baseline_probability("title", recs, 14, 14, 12)
    assert all(v == pytest.approx(0.5) for v in playoffs.values())
    assert all(v == pytest.approx(1 / 12) for v in title.values())


def test_baseline_follows_standings_when_the_season_is_over():
    wins = {t: 14 - t for t in range(1, 13)}  # team 1 best, team 12 worst
    recs = records_with(wins, 14)
    playoffs = baseline_probability("playoffs", recs, 0, 14, 12)
    last = baseline_probability("last", recs, 0, 14, 12)
    bye = baseline_probability("bye", recs, 0, 14, 12)
    assert [playoffs[t] for t in range(1, 13)] == [1.0] * 6 + [0.0] * 6
    assert last[12] == 1.0 and last[1] == 0.0
    assert bye[1] == bye[2] == 1.0 and bye[3] == 0.0
    assert baseline_probability("title", recs, 0, 14, 12)[1] == pytest.approx(1 / 6)


def test_baseline_mid_season_lies_between_base_rate_and_indicator():
    wins = {t: 7 - (t - 1) // 2 for t in range(1, 13)}
    recs = records_with(wins, 7)
    p = baseline_probability("playoffs", recs, 7, 14, 12)
    assert 0.5 < p[1] < 1.0
    assert 0.0 < p[12] < 0.5


# -- lineup gap ------------------------------------------------------------------------


def test_lineup_gap_is_zero_when_starters_are_optimal_and_positive_when_not(store_2025):
    data = store_2025.read_season("dynasty", "2025")
    week = 3
    team = data.matchups[week][0]
    best = projected_lineup(store_2025, CONFIG, "dynasty", data, week, [str(p) for p in team["players"]])
    optimal = copy.deepcopy(data)
    row = optimal.matchups[week][0]
    row["starters"] = [s.player_id for s in best]
    row["points"] = sum(float((row.get("players_points") or {}).get(s.player_id) or 0.0) for s in best)
    rows = lineup_gap(store_2025, CONFIG, "dynasty", optimal, week)
    mine = next(r for r in rows if r["roster_id"] == int(row["roster_id"]))
    assert mine["projected_gap"] == 0.0 and mine["actual_gap"] == 0.0

    benched = copy.deepcopy(optimal)
    row = benched.matchups[week][0]
    projections = store_2025.read_projections("2025", week)
    bench_players = [p for p in (str(x) for x in row["players"]) if p not in row["starters"] and projections.get(p, {}).get("position")]
    top, bench = next(
        (s, b) for s in sorted(best, key=lambda s: -s.projected) for b in bench_players if projections[b]["position"] == s.position
    )
    row["starters"] = [bench if s == top.player_id else s for s in row["starters"]]
    gap = next(r for r in lineup_gap(store_2025, CONFIG, "dynasty", benched, week) if r["roster_id"] == int(row["roster_id"]))
    expected = top.projected - projected_lineup(store_2025, CONFIG, "dynasty", data, week, [bench])[0].projected
    assert gap["projected_gap"] == pytest.approx(expected, abs=0.01)
    assert gap["projected_gap"] > 0


# -- replay and rows ---------------------------------------------------------------------


def test_replay_season_stores_every_as_of_week_and_leaves_other_seasons_alone(store_2025):
    store_2025.write_odds("dynasty", "2026", 9, {"marker": True})
    results = list(replay_season(store_2025, CONFIG, "dynasty", "2025", runs=300, scale=1.1))
    assert [as_of for as_of, *_ in results] == list(range(17))
    assert store_2025.odds_weeks("dynasty", "2025") == list(range(17))
    for as_of, inputs, result, payload in results:
        assert payload["season"] == "2025" and payload["as_of_week"] == as_of
        assert payload["residual_scale"] == 1.1 and payload["runs"] == 300
        assert result.weekly_scores.keys() == {w for w in range(as_of + 1, 18)}
    assert store_2025.read_odds("dynasty", "2026", 9) == {"marker": True}
    assert store_2025.odds_weeks("dynasty", "2026") == [9]


def test_season_rows_have_expected_shape(store_2025):
    rows = season_rows(store_2025, CONFIG, "dynasty", "2025", runs=200, seed=5, scale=1.0)
    assert len(rows["score_rows"]) == 12 * 14
    assert len(rows["game_rows"]) == 6 * 14
    playoffs = [r for r in rows["season_rows"] if r["outcome"] == "playoffs"]
    title = [r for r in rows["season_rows"] if r["outcome"] == "title"]
    assert max(r["as_of"] for r in playoffs) == 13 and len(playoffs) == 14 * 12
    assert max(r["as_of"] for r in title) == 16 and len(title) == 17 * 12
    assert all(0.0 <= r["predicted"] <= 1.0 and 0.0 <= r["baseline"] <= 1.0 for r in rows["season_rows"])
    assert all(r["p_favourite"] >= 0.5 for r in rows["game_rows"])
    assert all(0.0 <= r["pit"] <= 1.0 and set(r["in"]) == {"50", "80", "95"} for r in rows["score_rows"])
    week0 = [r for r in playoffs if r["as_of"] == 0]
    assert all(r["baseline"] == 0.5 for r in week0)
    assert rows["residual_scale"] == 1.0 and rows["seed"] == 5


# -- report ---------------------------------------------------------------------------------


def fake_season(league, season, predicted_hit=True):
    season_rows = []
    for outcome in OUTCOMES:
        for rid in range(1, 13):
            actual = rid <= 6 if outcome == "playoffs" else rid == 1
            season_rows.append({"as_of": 3, "roster_id": rid, "outcome": outcome, "predicted": 0.9 if (actual and predicted_hit) else 0.1, "baseline": 0.5, "actual": actual})
    game_rows = [{"as_of": 3, "week": 4, "favourite": 1, "underdog": 2, "p_favourite": 0.75, "favourite_won": 1.0}]
    score_rows = [
        {"as_of": 3, "week": 4, "roster_id": 1, "actual": 100.0, "sim_lineup_actual": 101.0, "sim_mean": 102.0, "sim_sd": 20.0, "pit": 0.45,
         "pit_sim_lineup": 0.5, "in": {"50": True, "80": True, "95": True}, "in_sim_lineup": {"50": False, "80": True, "95": True}, "starters": 9},
    ]
    return {"league_key": league, "season": season, "runs": 100, "seed": None, "residual_scale": 1.0,
            "season_rows": season_rows, "game_rows": game_rows, "score_rows": score_rows}


def test_report_json_and_markdown_agree_and_rerun_replaces(tmp_path):
    store = Store(tmp_path / "data")
    files = [fake_season("dynasty", "2024"), fake_season("redraft", "2024")]
    lineups = {"dynasty": [{"week": 1, "roster_id": 1, "projected_gap": 3.2, "actual_gap": -1.5}], "redraft": []}
    report = build_report(files, lineups, runs=100, seed=None, scale=1.0)
    assert set(report["leagues"]) == {"dynasty", "redraft"}
    assert report["overall"]["season"]["playoffs"]["cases"] == 24
    assert report["overall"]["season"]["playoffs"]["team_seasons"] == 24
    assert report["overall"]["season"]["playoffs"]["brier"] == pytest.approx(0.01)
    assert report["overall"]["season"]["playoffs"]["baseline_brier"] == pytest.approx(0.25)
    assert report["overall"]["season"]["playoffs"]["skill"] == pytest.approx(0.96)
    assert report["overall"]["game"]["games"] == 2 and report["overall"]["game"]["brier"] == pytest.approx(0.0625)
    assert report["overall"]["score"]["coverage"] == {"50": 1.0, "80": 1.0, "95": 1.0}
    assert report["overall"]["score"]["coverage_sim_lineup"]["50"] == 0.0
    assert report["leagues"]["dynasty"]["lineup"] == {"team_weeks": 1, "projected_gap": 3.2, "actual_gap": -1.5}
    assert report["leagues"]["redraft"]["lineup"]["projected_gap"] is None

    md = render_markdown(report)
    for value in ("0.0100", "0.2500", "0.960", "0.0625", "3.20", "-1.50", "100.0%"):
        assert value in md, value
    assert "dynasty 2024" in md and "## Caveats" in md

    json_path, md_path = write_report(store, report)
    assert json.loads(json_path.read_text(encoding="utf-8"))["residual_scale"] == 1.0
    assert md_path.read_text(encoding="utf-8") == md
    second = build_report(files, lineups, runs=100, seed=None, scale=0.9)
    write_report(store, second)
    assert json.loads(json_path.read_text(encoding="utf-8"))["residual_scale"] == 0.9
    assert "residual scale 0.9" in md_path.read_text(encoding="utf-8")


def test_same_data_runs_and_seed_give_an_identical_report(store_2025):
    """odds-calibration 7.8.1"""
    first = run_calibration(store_2025, CONFIG, runs=40, seed=7)
    second = run_calibration(store_2025, CONFIG, runs=40, seed=7)
    strip = lambda r: {k: v for k, v in r.items() if k != "generated_at"}
    assert strip(first) == strip(second)


def test_run_calibration_end_to_end_on_fixture(store_2025):
    seen = []
    report = run_calibration(store_2025, CONFIG, runs=150, seed=1, progress=lambda league, season, rows: seen.append((league, season)))
    assert ("dynasty", "2025") in seen and ("dynasty", "2026") not in seen
    assert report["runs"] == 150 and report["residual_scale"] == 1.0
    assert (store_2025.root / "calibration" / "report.json").exists()
    assert (store_2025.root / "calibration" / "report.md").exists()
    assert (store_2025.root / "calibration" / "rows" / "dynasty" / "2025.json").exists()
    assert report["leagues"]["dynasty"]["score"]["team_weeks"] >= 12 * 14
    assert report["leagues"]["dynasty"]["lineup"]["team_weeks"] > 0
    assert store_2025.odds_weeks("dynasty", "2025") == list(range(17))
