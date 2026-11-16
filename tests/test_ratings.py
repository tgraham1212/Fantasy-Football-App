"""Manager ratings: inputs, the Openskill update, reversion, multipliers, z-scores and the file."""

import json

import pytest

from ffapp.config import Config, RatingsConfig
from ffapp.ratings import (
    LeagueResults,
    Rating,
    build_ratings,
    make_model,
    rate_week,
    read_ratings,
    revert,
    run_ratings,
    vacant_id,
    weekly_results,
    write_ratings,
    z_scores,
)
from tests.conftest import DYNASTY_CFG

PARAMS = RatingsConfig()


# -- inputs ------------------------------------------------------------------------------


def test_weekly_results_cover_regular_season_scored_weeks_only(seeded_store):
    results = weekly_results(seeded_store, "dynasty")
    assert results.seasons == ["2022", "2023", "2024", "2025", "2026"]
    by_season = {}
    for season, week, points in results.weeks:
        by_season.setdefault(season, []).append(week)
        assert len(points) == 12 and any(v > 0 for v in points.values())
    assert by_season["2022"] == list(range(1, 15)), "playoff weeks 15-17 are not rated"
    assert by_season["2026"] == list(range(1, 10)), "2026 has nine scored weeks; unplayed weeks are not rated"


def test_ownerless_roster_becomes_a_vacant_manager(seeded_store):
    results = weekly_results(seeded_store, "dynasty")
    vacant = [m for m in results.vacant]
    assert vacant == [vacant_id("2023", 11)]
    assert vacant[0] not in results.current
    for season, week, points in results.weeks:
        assert (vacant[0] in points) == (season == "2023")


def test_managers_keyed_by_user_and_flagged_current(seeded_store):
    results = weekly_results(seeded_store, "dynasty")
    assert len(results.current) == 12 and all(m in results.names for m in results.current)
    former = set(results.names) - results.current - results.vacant
    assert former, "dynasty has former members"
    for m in former:
        assert "2026" not in results.seasons_played[m]
    assert all(isinstance(rid, int) for rid in results.roster_now.values())


# -- the update --------------------------------------------------------------------------


def three_way():
    model = make_model(PARAMS)
    start = Rating(PARAMS.start_mu, PARAMS.start_sigma)
    return model, {"a": start, "b": start, "c": start}


def test_higher_score_raises_mu():
    model, ratings = three_way()
    out = rate_week(model, ratings, {"a": 120.0, "b": 100.0, "c": 80.0})
    assert out["a"].mu > 1000 > out["c"].mu and out["a"].mu > out["b"].mu > out["c"].mu
    assert all(out[m].sigma < PARAMS.start_sigma for m in out)


def test_margin_does_not_matter():
    model, ratings = three_way()
    close = rate_week(model, ratings, {"a": 120.0, "b": 119.0, "c": 80.0})
    wide = rate_week(model, ratings, {"a": 150.0, "b": 100.0, "c": 80.0})
    assert close["a"].mu == pytest.approx(wide["a"].mu) and close["b"].mu == pytest.approx(wide["b"].mu)


def test_multiplier_scales_only_the_mean_change():
    model, ratings = three_way()
    plain = rate_week(model, ratings, {"a": 120.0, "b": 100.0, "c": 80.0})
    doubled = rate_week(model, ratings, {"a": 120.0, "b": 100.0, "c": 80.0}, k=2.0)
    for m in ratings:
        assert doubled[m].mu - 1000 == pytest.approx(2 * (plain[m].mu - 1000))
        assert doubled[m].sigma == pytest.approx(plain[m].sigma)


def test_revert_moves_a_third_toward_the_anchor():
    assert revert(Rating(1300.0, 240.0), 1000.0, 1 / 3).mu == pytest.approx(1200.0)
    assert revert(Rating(700.0, 240.0), 1000.0, 1 / 3).mu == pytest.approx(800.0)
    assert revert(Rating(700.0, 240.0), 1000.0, 1 / 3).sigma == 240.0


def test_z_scores_use_sample_sd():
    pts = {"a": 130.0, "b": 110.0, "c": 90.0}  # mean 110, sample sd 20
    z = z_scores(pts)
    assert z["a"] == pytest.approx(1.0) and z["b"] == pytest.approx(0.0) and z["c"] == pytest.approx(-1.0)
    assert z_scores({"a": 100.0, "b": 100.0}) == {"a": 0.0, "b": 0.0}


# -- the run -------------------------------------------------------------------------------


def synthetic(weeks):
    """weeks: list of (season, week, points) for managers a, b, c."""
    results = LeagueResults(league_key="x", seasons=sorted({s for s, _, _ in weeks}), weeks=weeks)
    for m in ("a", "b", "c"):
        results.names[m] = m
    return results


def test_first_week_doubles_the_model_delta_and_week_five_does_not():
    pts = {"a": 120.0, "b": 100.0, "c": 80.0}
    weeks = [("2024", w, pts) for w in range(1, 6)]
    hist = run_ratings(synthetic(weeks), PARAMS)
    model, ratings = three_way()
    plain = rate_week(model, ratings, pts)
    assert hist["a"][0]["mu"] == pytest.approx(1000 + 2 * (plain["a"].mu - 1000), abs=0.01)
    # week 5: multiplier 1, so the step equals the model's own step from the week-4 state
    state = {m: Rating(hist[m][3]["mu"], hist[m][3]["sigma"]) for m in "abc"}
    expected = rate_week(model, state, pts)
    assert hist["a"][4]["mu"] == pytest.approx(expected["a"].mu, abs=0.01)


def test_schedule_follows_rated_week_order_not_calendar_week():
    pts = {"a": 120.0, "b": 100.0, "c": 80.0}
    late_start = run_ratings(synthetic([("2024", w, pts) for w in range(2, 7)]), PARAMS)
    normal = run_ratings(synthetic([("2024", w, pts) for w in range(1, 6)]), PARAMS)
    assert [h["mu"] for h in late_start["a"]] == [h["mu"] for h in normal["a"]]


def test_preseason_reversion_and_fresh_start():
    pts = {"a": 120.0, "b": 100.0, "c": 80.0}
    weeks = [("2023", w, pts) for w in range(1, 15)] + [("2024", 1, pts)]
    hist = run_ratings(synthetic(weeks), RatingsConfig(early_k=(1.0,)))
    end_2023 = Rating(hist["a"][13]["mu"], hist["a"][13]["sigma"])
    model = make_model(PARAMS)
    reverted = {m: revert(Rating(hist[m][13]["mu"], hist[m][13]["sigma"]), 1000.0, 1 / 3) for m in "abc"}
    expected = rate_week(model, reverted, pts)
    assert hist["a"][14]["mu"] == pytest.approx(expected["a"].mu, abs=0.01)
    assert end_2023.mu > 1000
    # fresh-start variant: back to exactly 1000 before 2024 week 1
    start = {m: Rating(1000.0, PARAMS.start_sigma) for m in "abc"}
    assert hist["a"][14]["fresh_mu"] == pytest.approx(rate_week(model, start, pts)["a"].mu, abs=0.01)


def test_newcomer_starts_at_1000_and_does_not_move_the_others():
    pts3 = {"a": 120.0, "b": 100.0, "c": 80.0}
    hist = run_ratings(synthetic([("2023", 1, pts3), ("2024", 1, {**pts3, "d": 90.0})]), RatingsConfig(early_k=(1.0,)))
    assert "d" in hist and len(hist["d"]) == 1
    # d entered at 1000: its first-week result is what a 1000-rated player gets from that week
    model = make_model(PARAMS)
    reverted = {m: revert(Rating(hist[m][0]["mu"], hist[m][0]["sigma"]), 1000.0, 1 / 3) for m in "abc"}
    reverted["d"] = Rating(1000.0, PARAMS.start_sigma)
    expected = rate_week(model, reverted, {**pts3, "d": 90.0})
    assert hist["d"][0]["mu"] == pytest.approx(expected["d"].mu, abs=0.01)


def test_career_z_spans_seasons_and_season_z_resets():
    weeks = [
        ("2023", 1, {"a": 130.0, "b": 110.0, "c": 90.0}),  # a: z = 1
        ("2023", 2, {"a": 100.0, "b": 120.0, "c": 80.0}),  # a: z = 0
        ("2024", 1, {"a": 100.0, "b": 120.0, "c": 110.0}),  # a: z = -1
    ]
    hist = run_ratings(synthetic(weeks), PARAMS)
    a = hist["a"]
    assert [h["z"] for h in a] == pytest.approx([1.0, 0.0, -1.0])
    assert [h["career_z"] for h in a] == pytest.approx([1.0, 0.5, 0.0])
    assert [h["season_z"] for h in a] == pytest.approx([1.0, 0.5, -1.0])
    assert a[2]["ewma_z"] == pytest.approx(0.8 * 0.8 * 1.0 + 0.2 * -1.0, abs=1e-3)


def test_career_z_is_the_mean_of_weekly_z():
    weeks = [
        ("2023", 1, {"a": 130.0, "b": 110.0, "c": 90.0}),
        ("2023", 2, {"a": 110.0, "b": 130.0, "c": 90.0}),
        ("2024", 1, {"a": 100.0, "b": 125.0, "c": 115.0, "d": 100.0, "e": 110.0}),
    ]
    hist = run_ratings(synthetic(weeks), PARAMS)
    zs = [h["z"] for h in hist["a"]]
    assert zs[0] == pytest.approx(1.0) and zs[1] == pytest.approx(0.0) and -1 < zs[2] < 0
    assert hist["a"][2]["career_z"] == pytest.approx(sum(zs) / 3, abs=1e-3)


# -- the file ----------------------------------------------------------------------------------


def test_ratings_file_written_for_every_week_and_manager(seeded_store):
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    path = write_ratings(seeded_store, config, "dynasty")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["seasons"] == ["2022", "2023", "2024", "2025", "2026"]
    assert len(payload["weeks"]) == 14 * 4 + 9
    assert payload["parameters"]["early_k"] == [2, 1.75, 1.5, 1.25] and payload["parameters"]["revert"] == pytest.approx(1 / 3)
    managers = payload["managers"]
    current = [m for m, v in managers.items() if v["current"]]
    former = [m for m, v in managers.items() if not v["current"] and not v["vacant"]]
    vacant = [m for m, v in managers.items() if v["vacant"]]
    assert len(current) == 12 and former and vacant == [vacant_id("2023", 11)]
    for m, v in managers.items():
        played = {(h["season"], h["week"]) for h in v["history"]}
        expected = {(w["season"], w["week"]) for w in payload["weeks"] if w["season"] in v["seasons"]}
        assert played == expected, f"{m} has a history entry for every rated week of their seasons"
        assert set(v["history"][0]) == {"season", "week", "mu", "sigma", "z", "career_z", "season_z", "ewma_z", "fresh_mu"}
    for m in current:
        assert managers[m]["roster_id"] in range(1, 13) and managers[m]["display_name"]
    for m in former:
        assert managers[m]["roster_id"] is None and "2026" not in managers[m]["seasons"]
    assert read_ratings(seeded_store, "dynasty")["league_key"] == "dynasty"
    mus = [v["history"][-1]["mu"] for v in managers.values() if v["current"]]
    assert 700 < sum(mus) / len(mus) < 1300, "ratings stay centred near 1000"


def test_ratings_deterministic(seeded_store):
    config = Config(leagues={"dynasty": DYNASTY_CFG})
    first = build_ratings(seeded_store, config, "dynasty")
    second = build_ratings(seeded_store, config, "dynasty")
    first.pop("generated_at"), second.pop("generated_at")
    assert first == second
