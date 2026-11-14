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
        assert team["elo"] is None and team["elo_change"] is None
        assert team["wins"] + team["losses"] + team["ties"] == 3
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
