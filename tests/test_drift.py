import copy
import json

import numpy as np
import pytest

from ffapp.config import Config, LeagueConfig
from ffapp.drift import DriftModel, diagnostic, estimate, estimate_for_league, fit, model_path, strength_pairs
from ffapp.noise import GaussianNoise
from ffapp.odds import run_as_of, simulate_as_of, simulate_league
from ffapp.projections import upsert_week
from ffapp.simulate import simulate, summarize
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from ffapp.sync import sync_league
from tests.fixtures import DYNASTY, FixtureSession, load
from tests.test_simulate import TEAMS, make_inputs

CFG = LeagueConfig(key="dynasty", league_id=DYNASTY["2026"], name="Taco Tuesdays")
CONFIG = Config(leagues={"dynasty": CFG})


@pytest.fixture
def store_two_seasons(tmp_path):
    """Dynasty fixtures with the 2025 week-1 projections reused for every week of 2024, 2025 and 2026."""
    store = Store(tmp_path / "data")
    sync_league(SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None), store, CFG)
    rows = load("projections/2025/1.json")
    for season in ("2024", "2025", "2026"):
        for week in range(1, 18):
            reused = copy.deepcopy(rows)
            for row in reused:
                row["season"] = season
                row["week"] = week
            upsert_week(store, season, week, reused)
    return store


# -- estimation -------------------------------------------------------------------------


def synthetic_pairs(slope_by_k, noise_sd=0.0, n=200, seed=0):
    rng = np.random.default_rng(seed)
    pairs = {}
    for k, slope in slope_by_k.items():
        x = rng.normal(0, 15, n)
        y = slope * x + rng.normal(0, noise_sd, n)
        pairs[k] = list(zip(x.tolist(), y.tolist()))
    return pairs


def test_identity_when_rosters_never_change():
    pairs = synthetic_pairs({k: 1.0 for k in range(1, 14)})
    model = estimate(pairs, "x", ["2024", "2025"], top_n=3, floor=True)
    assert model.slopes == [1.0] * 13 and model.sds == [0.0] * 13
    assert not model.identity and model.seasons == ["2024", "2025"]


def test_slope_recovered_and_smoothed():
    pairs = synthetic_pairs({1: 1.0, 2: 0.8, 3: 0.9, 4: 0.8}, noise_sd=2.0)
    raw_slopes, raw_sds = fit(pairs)
    assert raw_slopes[1] == pytest.approx(0.8, abs=0.03) and raw_slopes[2] == pytest.approx(0.9, abs=0.03)
    model = estimate(pairs, "x", ["a", "b"], top_n=3, floor=True)
    assert model.slope(1) == 1.0 and model.sd(1) == 0.0, "k = 1 is fixed"
    assert model.slope(2) == pytest.approx(0.8, abs=0.03)
    assert model.slope(3) <= model.slope(2), "slopes are forced non-increasing"
    assert model.sd(2) == pytest.approx(2.0, abs=0.4) and model.sd(3) >= model.sd(2)
    assert model.slope(40) == model.slope(4) and model.sd(40) == model.sd(4), "horizons past the data reuse the last"
    assert model.step_sd(2) == pytest.approx(model.sd(2)) and model.step_sd(1) == 0.0


def test_one_season_gives_identity_model():
    model = estimate(synthetic_pairs({1: 1.0, 2: 0.5}), "x", ["2025"], top_n=3, floor=True)
    assert model.identity and "identity" in model.note and model.slope(5) == 1.0 and model.sd(5) == 0.0
    assert DriftModel.from_dict(model.to_dict()) == model


def test_strength_pairs_on_fixture_seasons(store_two_seasons):
    pairs = strength_pairs(store_two_seasons, CONFIG, "dynasty", ["2024", "2025"], floor=True, n=3)
    assert sorted(pairs) == list(range(1, 15)), "preseason to week 14 is 14 weeks ahead"
    assert all(a == pytest.approx(b) for a, b in pairs[1]), "one week ahead the held roster is the true roster"
    assert len(pairs[1]) == 2 * 14 * 12 and len(pairs[14]) == 2 * 1 * 12
    model = estimate_for_league(store_two_seasons, CONFIG, "dynasty")
    assert model.seasons == ["2022", "2023", "2024", "2025"] and len(model.slopes) == 14
    left_out = estimate_for_league(store_two_seasons, CONFIG, "dynasty", exclude_season="2025")
    assert "2025" not in left_out.seasons
    diag = diagnostic(store_two_seasons, CONFIG, "dynasty", ["2024", "2025"])
    assert set(diag["frozen"]) == {"2", "3", "5", "8", "12"} == set(diag["floored"]) and diag["top_n"] == 3


# -- simulation ---------------------------------------------------------------------------


def with_strength(inputs, offsets):
    """Give every future week a floored strength: team t sits at 100 + offsets[t]."""
    weeks = sorted(set(inputs.schedule) | set(inputs.playoff_weeks))
    inputs.strength = {w: {t: 100.0 + offsets.get(t, 0.0) for t in TEAMS} for w in weeks}
    return inputs


def test_identity_drift_leaves_results_bit_identical():
    base = simulate(make_inputs(completed=9), GaussianNoise(6.0), runs=500, seed=4)
    inputs = with_strength(make_inputs(completed=9), {1: 20.0})
    inputs.drift = DriftModel("x", slopes=[1.0] * 13, sds=[0.0] * 13, seasons=["a", "b"])
    same = simulate(inputs, GaussianNoise(6.0), runs=500, seed=4)
    assert np.array_equal(base.wins, same.wins) and np.array_equal(base.points, same.points)
    off = with_strength(make_inputs(completed=9), {1: 20.0})
    off.drift = None
    assert np.array_equal(simulate(off, GaussianNoise(6.0), runs=500, seed=4).points, base.points)


def test_slope_shrinks_edge_toward_mean():
    inputs = with_strength(make_inputs(completed=9), {1: 24.0, 2: -24.0})  # league mean stays 100
    inputs.drift = DriftModel("x", slopes=[1.0] + [0.5] * 12, sds=[0.0] * 13, seasons=["a", "b"])
    result = simulate(inputs, GaussianNoise(0.0001), runs=200, seed=1)
    week10 = result.weekly_scores[10]  # k = 1: no shrink
    week11 = result.weekly_scores[11]  # k = 2: half the edge
    assert week10[:, 0].mean() == pytest.approx(100.0, abs=0.01), "every team projects 100 in the test lineups"
    assert week11[:, 0].mean() == pytest.approx(100.0 - 12.0, abs=0.01), "team 1 is +24 in strength: shrunk by (0.5-1)*24"
    assert week11[:, 1].mean() == pytest.approx(100.0 + 12.0, abs=0.01)
    assert week11[:, 5].mean() == pytest.approx(100.0, abs=0.01), "an average team is untouched"


def test_drift_noise_grows_and_persists():
    inputs = with_strength(make_inputs(completed=9), {})
    inputs.drift = DriftModel("x", slopes=[1.0] * 13, sds=[0.0, 3.0, 4.0, 5.0, 6.0] + [6.0] * 8, seasons=["a", "b"])
    result = simulate(inputs, GaussianNoise(0.0001), runs=4000, seed=2)
    w = result.weekly_scores
    assert w[10][:, 0].std() < 0.01, "k = 1: no drift yet"
    assert w[11][:, 0].std() == pytest.approx(3.0, abs=0.2)
    assert w[13][:, 0].std() == pytest.approx(5.0, abs=0.3)
    assert w[13][:, 0].std() > w[11][:, 0].std()
    step = w[12][:, 0] - w[11][:, 0]
    assert step.std() == pytest.approx(np.sqrt(4.0**2 - 3.0**2), abs=0.2), "week-to-week change is the random-walk step"
    assert np.corrcoef(w[11][:, 0], w[12][:, 0])[0, 1] > 0.6, "drift carries over within a run"
    assert sum(r["playoffs"] for r in summarize(result)) == pytest.approx(6.0, abs=0.02)


# -- payload and model file ---------------------------------------------------------------------


def test_simulate_league_records_model_and_writes_file(store_two_seasons):
    payloads = simulate_league(store_two_seasons, CONFIG, "dynasty", runs=100)
    payload = payloads[-1]
    model = payload["model"]
    assert model["replacement_top_n"] == 3 and model["replacement_floor"] is True
    assert model["roster_drift"] is True and len(model["drift"]["slopes"]) == 14
    assert model["drift"]["seasons"] == ["2022", "2023", "2024", "2025"]
    assert payload["residual_scale"] == 1.0
    saved = json.loads(model_path(store_two_seasons, "dynasty").read_text(encoding="utf-8"))
    assert saved["slopes"] == model["drift"]["slopes"] and saved["generated_at"]


def test_switches_recorded_when_off(store_two_seasons):
    data = store_two_seasons.read_season("dynasty", "2026")
    _, _, payload = simulate_as_of(store_two_seasons, CONFIG, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=50,
                                   replacement_floor=False, drift=None)
    assert payload["model"] == {"replacement_top_n": 3, "replacement_floor": False, "roster_drift": False, "drift": None}
    stored = run_as_of(store_two_seasons, CONFIG, "dynasty", data, 9, current=True, noise=GaussianNoise(5.0), runs=50)
    assert stored["model"]["roster_drift"] is False and stored["model"]["replacement_floor"] is True
