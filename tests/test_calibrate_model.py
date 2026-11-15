"""Calibration switches, leave-season-out drift and the roster-drift diagnostic."""

import json

from ffapp.calibrate import build_report, render_markdown, replay_season, run_calibration
from tests.test_calibrate import CONFIG, fake_season, store_2025  # noqa: F401  (fixture re-export)
from tests.test_drift import store_two_seasons  # noqa: F401


def test_replay_leaves_the_replayed_season_out_of_the_drift_model(store_two_seasons):
    as_of, inputs, result, payload = next(replay_season(store_two_seasons, CONFIG, "dynasty", "2025", runs=100))
    model = payload["model"]
    assert model["replacement_floor"] is True and model["roster_drift"] is True
    assert "2025" not in model["drift"]["seasons"] and "2024" in model["drift"]["seasons"]
    assert inputs.drift is not None and inputs.floors, "floor and drift reached the inputs"


def test_switches_reach_the_replay(store_two_seasons):
    _, inputs, _, payload = next(replay_season(store_two_seasons, CONFIG, "dynasty", "2025", runs=50, replacement_floor=False, roster_drift=False))
    assert payload["model"] == {"replacement_top_n": 3, "replacement_floor": False, "roster_drift": False, "drift": None}
    assert inputs.floors == {} and inputs.drift is None
    _, inputs, _, payload = next(replay_season(store_two_seasons, CONFIG, "dynasty", "2025", runs=50, roster_drift=False))
    assert payload["model"]["replacement_floor"] is True and payload["model"]["roster_drift"] is False and inputs.floors


def test_report_records_switches_models_and_diagnostic(store_two_seasons):
    report = run_calibration(store_two_seasons, CONFIG, runs=60, seed=3, roster_drift=False)
    assert report["replacement_floor"] is True and report["roster_drift"] is False and report["replacement_top_n"] == 3
    assert set(report["drift_models"]) == {"dynasty"} and set(report["drift_diagnostic"]) == {"dynasty"}
    diag = report["drift_diagnostic"]["dynasty"]
    assert diag["horizons"] == [2, 3, 5, 8, 12]
    for k in ("2", "3", "5", "8", "12"):
        assert set(diag["frozen"][k]) == {"slope", "sd"} and set(diag["floored"][k]) == {"slope", "sd"}
    md = (store_two_seasons.root / "calibration" / "report.md").read_text(encoding="utf-8")
    assert "roster drift off" in md and "replacement floor on (top 3)" in md
    assert "## Roster drift diagnostic" in md
    for k in ("2", "5", "12"):
        assert f"{diag['floored'][k]['slope']:.3f}" in md and f"{diag['frozen'][k]['sd']:.2f}" in md
    rows = json.loads((store_two_seasons.root / "calibration" / "rows" / "dynasty" / "2025.json").read_text(encoding="utf-8"))
    assert rows["model"]["roster_drift"] is False


def test_markdown_without_diagnostic_still_renders():
    report = build_report([fake_season("dynasty", "2024")], {"dynasty": []}, runs=10, seed=None, scale=1.0)
    md = render_markdown(report)
    assert "Roster drift diagnostic" not in md and "replacement floor on" in md
