import copy
import math

import pytest

from ffapp.games import live_wpa, margin_stats, win_probability_added
from ffapp.noise import GaussianNoise


def test_spec_example_big_game():
    # pre-kickoff margin +4, spread 24; a starter projected for 10 (own sd 7) scores 25
    assert win_probability_added(4.0, 24.0, 10.0, 25.0, 7.0) * 100 == pytest.approx(22, abs=2)


def test_dud_is_negative_and_a_projection_hit_is_near_zero():
    assert win_probability_added(4.0, 24.0, 10.0, 2.0, 7.0) < -0.1
    assert abs(win_probability_added(4.0, 24.0, 10.0, 10.0, 7.0)) < 0.01  # only the narrower spread moves it


def test_opponent_side_reads_from_its_own_margin():
    # the same 25-point game from the underdog's side (margin -4) is still a big positive swing
    assert win_probability_added(-4.0, 24.0, 10.0, 25.0, 7.0) > 0.2


def test_in_progress_keeps_the_remaining_variance():
    done = win_probability_added(0.0, 24.0, 10.0, 20.0, 7.0, share=0.0)
    half = win_probability_added(0.0, 24.0, 10.0, 20.0, 7.0, share=0.5)
    assert 0 < half < done  # same projected final, more uncertainty left


def test_margin_stats_from_stored_fields_or_histograms():
    assert margin_stats({"margin_mean": 3.5, "margin_sd": 20.0}) == (3.5, 20.0)
    game = {"teams": [{"mean": 110.0}, {"mean": 100.0}], "hist": {"start": 90.0, "width": 2.0, "shares": [[0, 500, 500, 0], [250, 250, 250, 250]]}}
    mean, sd = margin_stats(game)
    assert mean == 10.0 and sd == pytest.approx(math.sqrt(1.0 + 5.0), rel=1e-6)  # variances 1 and 5 on 2-point bins


def live_forecast(points_a2):
    lineup_a = [["QB", "a1", "QB", 20.0, "final", 31.0, None, 0.0], ["WR", "a2", "WR", 12.0, "in_progress", points_a2, "Q3 4:12", 0.32], ["TE", "a3", "TE", 8.0]]
    lineup_b = [["QB", "b1", "QB", 18.0, "final", 9.0, None, 0.0]]
    return {"games": [{"key": "1-2", "teams": [{"roster_id": 1, "lineup": lineup_a}, {"roster_id": 2, "lineup": lineup_b}]}]}


BASELINE = {"1-2": {"margin_mean": 2.0, "margin_sd": 25.0, "lineups": {"1": [["QB", "a1", "QB", 19.0], ["WR", "a2", "WR", 12.0], ["TE", "a3", "TE", 8.0]], "2": [["QB", "b1", "QB", 18.0]]}}}


def test_live_wpa_uses_the_pre_kickoff_baseline_and_skips_players_not_started():
    forecast = live_forecast(4.0)
    live_wpa(forecast, BASELINE, GaussianNoise(7.0))
    a, b = forecast["games"][0]["teams"]
    assert set(a["wpa"]) == {"a1", "a2"}  # a3 has not kicked off
    # a1: final 31 against his pre-kickoff 19 (not the live row's 20)
    assert a["wpa"]["a1"] == win_probability_added(2.0, 25.0, 19.0, 31.0, 7.0)
    # a2: in progress, projected final 4 + 0.32 * 12
    assert a["wpa"]["a2"] == win_probability_added(2.0, 25.0, 12.0, 4.0 + 0.32 * 12.0, 7.0, share=0.32)
    assert b["wpa"]["b1"] == win_probability_added(-2.0, 25.0, 18.0, 9.0, 7.0) < 0


def test_a_teammates_score_does_not_change_a_players_wpa():
    one, two = live_forecast(4.0), live_forecast(15.0)
    live_wpa(one, copy.deepcopy(BASELINE), GaussianNoise(7.0))
    live_wpa(two, copy.deepcopy(BASELINE), GaussianNoise(7.0))
    assert one["games"][0]["teams"][0]["wpa"]["a1"] == two["games"][0]["teams"][0]["wpa"]["a1"]
    assert one["games"][0]["teams"][0]["wpa"]["a2"] != two["games"][0]["teams"][0]["wpa"]["a2"]


def test_records_carry_margins_and_wpa(seeded_store, dynasty_config):
    from tests.test_games import AS_OF, prepare
    from ffapp.games import update_games
    from datetime import datetime, timezone

    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    record = seeded_store.read_games("dynasty", "2026", AS_OF)["record"]  # pre-week record
    g = record["games"][0]
    data = seeded_store.read_season("dynasty", "2026")
    row = next(r for r in data.matchups[AS_OF] if int(r["roster_id"]) == g["teams"][0]["roster_id"])
    starters = {str(p) for p in row["starters"] if str(p) not in ("0", "")}
    assert set(g["teams"][0]["wpa"]) == starters  # every real starter, scored
    assert all(-1 < v < 1 for v in g["teams"][0]["wpa"].values())
    forecast_game = seeded_store.read_games("dynasty", "2026", AS_OF + 1)["forecast"]["games"][0]
    assert forecast_game["margin_mean"] == pytest.approx(forecast_game["teams"][0]["mean"] - forecast_game["teams"][1]["mean"], abs=0.05)
    assert forecast_game["margin_sd"] > 0
