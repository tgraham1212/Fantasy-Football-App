import json

import pytest

from ffapp.export import (
    HISTORY_KEYS,
    RATE_KEYS,
    ExportError,
    avoid_losers_bye,
    bottom_column,
    export_site,
    league_export,
)
from ffapp.noise import GaussianNoise
from ffapp.odds import run_as_of
from ffapp.replacement import write_replacement
from ffapp.store import write_json

TEAM_KEYS = {
    "roster_id", "team_name", "display_name", "user_id", "wins", "losses", "ties", "points_for",
    "proj_wins", "proj_losses", "seed_distribution", "change", "elo", "elo_change", *RATE_KEYS,
}


def league_with(playoff_type, league_type=None):
    settings = {"playoff_type": playoff_type}
    if league_type is not None:
        settings["type"] = league_type
    return {"settings": settings}


def test_avoid_losers_bye_is_one_minus_bottom_two():
    dist = [0.5, 0.2, 0.1, 0.08, 0.04, 0.02, 0.01, 0.005, 0.005, 0.01, 0.03, 0.01]
    assert avoid_losers_bye({"seed_distribution": dist}) == 0.96
    assert avoid_losers_bye({}) is None
    assert avoid_losers_bye({"seed_distribution": [1.0]}) is None


def test_bottom_column_follows_league_settings():
    assert bottom_column(league_with(playoff_type=0, league_type=0))["key"] == "avoid_losers_bye"  # redraft toilet bowl
    assert bottom_column(league_with(playoff_type=0, league_type=2))["key"] == "avoid_losers_bye"  # dynasty toilet bowl
    dynasty = bottom_column(league_with(playoff_type=1, league_type=2))
    assert dynasty["key"] == "last" and dynasty["label"] == "#1 Pick"
    assert bottom_column(league_with(playoff_type=1, league_type=0))["key"] == "avoid_losers_bye"  # consolation, redraft
    assert bottom_column(league_with(playoff_type=1))["key"] == "avoid_losers_bye"  # no type field
    assert bottom_column({})["key"] == "avoid_losers_bye"
    for col in (bottom_column(league_with(0)), dynasty):
        assert set(col) == {"key", "label", "description"} and col["description"]


def simulate_weeks(store, config, weeks):
    data = store.read_season("dynasty", "2026")
    for as_of in weeks:
        run_as_of(store, config, "dynasty", data, as_of, current=False, noise=GaussianNoise(5.0), runs=200)


def test_export_requires_odds(seeded_store, dynasty_config):
    with pytest.raises(ExportError, match="no odds stored"):
        league_export(seeded_store, dynasty_config, "dynasty")


def test_exported_schema(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1, 2, 3])
    out = tmp_path / "site-data"
    written = export_site(seeded_store, dynasty_config, out)
    assert {p.name for p in written} == {"dynasty.json", "index.json"}

    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["calibration"] is None, "no calibration report stored yet"
    assert index["leagues"][0] == {
        "key": "dynasty", "name": "Taco Tuesdays", "season": "2026", "as_of_week": 3,
        "generated_at": index["leagues"][0]["generated_at"], "file": "dynasty.json",
    }

    payload = json.loads((out / "dynasty.json").read_text(encoding="utf-8"))
    assert payload["league_key"] == "dynasty" and payload["season"] == "2026"
    assert payload["as_of_week"] == 3 and payload["previous_as_of_week"] == 2
    assert payload["regular_season_weeks"] == 14 and payload["playoff_teams"] == 6
    assert payload["runs"] == 200 and payload["generated_at"]
    assert payload["simulated_weeks"][0] == 4

    assert payload["bottom_column"] == {
        "key": "last", "label": "#1 Pick", "description": payload["bottom_column"]["description"],
    }, "the dynasty fixture is a dynasty league with a consolation bracket"

    assert len(payload["teams"]) == 12
    for team in payload["teams"]:
        assert TEAM_KEYS <= set(team), TEAM_KEYS - set(team)
        assert set(team["change"]) == set(RATE_KEYS)
        assert all(isinstance(v, float) for v in team["change"].values()), "previous week exists, so every change is a number"
        assert 0.0 <= team["playoffs"] <= 1.0
        assert team["avoid_losers_bye"] == round(1 - sum(team["seed_distribution"][-2:]), 4)
        assert team["elo"] is None and team["elo_change"] is None, "no rating file yet"
        assert team["wins"] + team["losses"] + team["ties"] == 3
    assert "ratings" not in payload
    assert payload["teams"] == sorted(payload["teams"], key=lambda t: -t["playoffs"])

    history = payload["history"]
    assert history["weeks"] == [0, 1, 2, 3]
    assert set(history["teams"]) == {str(t["roster_id"]) for t in payload["teams"]}
    for series in history["teams"].values():
        assert set(series) == set(HISTORY_KEYS)
        assert all(len(v) == 4 for v in series.values())
        assert all(isinstance(v, float) for v in series["avoid_losers_bye"]), "derived for every stored week"
    # the last history point equals the current table
    for team in payload["teams"]:
        assert history["teams"][str(team["roster_id"])]["playoffs"][-1] == team["playoffs"]


def test_single_week_has_null_changes(seeded_store, dynasty_config):
    simulate_weeks(seeded_store, dynasty_config, [0])
    payload = league_export(seeded_store, dynasty_config, "dynasty")
    assert payload["previous_as_of_week"] is None
    assert all(v is None for t in payload["teams"] for v in t["change"].values())


def test_export_includes_calibration_report_when_present(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    report = {"generated_at": "2026-11-14T10:00:00+00:00", "runs": 10000, "residual_scale": 1.0, "seasons": [], "overall": {}}
    write_json(seeded_store.root / "calibration" / "report.json", report)
    out = tmp_path / "site-data"
    written = export_site(seeded_store, dynasty_config, out)
    assert {p.name for p in written} == {"dynasty.json", "index.json", "calibration.json"}
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["calibration"] == {"generated_at": "2026-11-14T10:00:00+00:00", "file": "calibration.json"}
    assert json.loads((out / "calibration.json").read_text(encoding="utf-8")) == report


def test_export_carries_replacement_levels_and_model_when_present(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1, 2])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    payload = json.loads((out / "dynasty.json").read_text(encoding="utf-8"))
    assert "replacement" not in payload, "no replacement file yet"
    assert payload["model"]["replacement_floor"] is True and payload["model"]["roster_drift"] is False

    write_replacement(seeded_store, dynasty_config, "dynasty")
    export_site(seeded_store, dynasty_config, out)
    payload = json.loads((out / "dynasty.json").read_text(encoding="utf-8"))
    rep = payload["replacement"]
    assert rep["as_of_week"] == 2 and rep["week"] == 3 and rep["top_n"] == 3
    assert set(rep["levels"]) == {"QB", "RB", "WR", "TE", "K", "DEF"} == set(rep["season"])
    assert all(isinstance(v, float) for v in rep["levels"].values())


def test_export_carries_ratings_when_present(seeded_store, dynasty_config, tmp_path):
    from ffapp.ratings import read_ratings, write_ratings

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    write_ratings(seeded_store, dynasty_config, "dynasty")
    stored = read_ratings(seeded_store, "dynasty")
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    payload = json.loads((out / "dynasty.json").read_text(encoding="utf-8"))

    by_roster = {v["roster_id"]: v for v in stored["managers"].values() if v["current"]}
    for team in payload["teams"]:
        entry = by_roster[team["roster_id"]]
        assert team["elo"] == round(entry["history"][-1]["mu"])
        assert team["elo_change"] == round(entry["history"][-1]["mu"] - entry["history"][-2]["mu"])

    ratings = payload["ratings"]
    assert ratings["seasons"] == ["2022", "2023", "2024", "2025", "2026"]
    assert len(ratings["weeks"]) == len(stored["weeks"]) and ratings["weeks"][0] == {"season": "2022", "week": 1}
    assert not any(k.startswith("vacant:") for k in ratings["managers"]), "vacant rosters are not charted"
    assert sum(1 for m in ratings["managers"].values() if m["current"]) == 12
    former = [m for m in ratings["managers"].values() if not m["current"]]
    assert former and all(m["roster_id"] is None for m in former)
    for manager_id, m in ratings["managers"].items():
        assert len(m["mu"]) == len(ratings["weeks"]) == len(m["career_z"])
        played = {(h["season"], h["week"]) for h in stored["managers"][manager_id]["history"]}
        for wk, mu in zip(ratings["weeks"], m["mu"]):
            assert (mu is not None) == ((wk["season"], wk["week"]) in played), "series aligned to the league week list"


def test_newcomer_with_one_rated_week_has_no_elo_change(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0])
    team = seeded_store.read_odds("dynasty", "2026", 0)["teams"][0]
    write_json(
        seeded_store.root / "ratings" / "dynasty.json",
        {
            "league_key": "dynasty", "seasons": ["2026"], "weeks": [{"season": "2026", "week": 1}],
            "managers": {
                "u1": {"display_name": "New", "current": True, "vacant": False, "roster_id": team["roster_id"], "seasons": ["2026"],
                       "history": [{"season": "2026", "week": 1, "mu": 1057.4, "sigma": 330, "z": 0.5, "career_z": 0.5, "season_z": 0.5, "ewma_z": 0.5, "fresh_mu": 1057.4}]},
            },
        },
    )
    payload = league_export(seeded_store, dynasty_config, "dynasty")
    row = next(t for t in payload["teams"] if t["roster_id"] == team["roster_id"])
    assert row["elo"] == 1057 and row["elo_change"] is None
    others = [t for t in payload["teams"] if t["roster_id"] != team["roster_id"]]
    assert all(t["elo"] is None for t in others)
