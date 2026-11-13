import json

import pytest

from ffapp.export import HISTORY_KEYS, RATE_KEYS, ExportError, export_site, league_export
from ffapp.noise import GaussianNoise
from ffapp.odds import run_as_of

TEAM_KEYS = {
    "roster_id", "team_name", "display_name", "user_id", "wins", "losses", "ties", "points_for",
    "proj_wins", "proj_losses", "seed_distribution", "change", *RATE_KEYS,
}


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

    assert len(payload["teams"]) == 12
    for team in payload["teams"]:
        assert TEAM_KEYS <= set(team), TEAM_KEYS - set(team)
        assert set(team["change"]) == set(RATE_KEYS)
        assert all(isinstance(v, float) for v in team["change"].values()), "previous week exists, so every change is a number"
        assert 0.0 <= team["playoffs"] <= 1.0
        assert team["wins"] + team["losses"] + team["ties"] == 3
    assert payload["teams"] == sorted(payload["teams"], key=lambda t: -t["playoffs"])

    history = payload["history"]
    assert history["weeks"] == [0, 1, 2, 3]
    assert set(history["teams"]) == {str(t["roster_id"]) for t in payload["teams"]}
    for series in history["teams"].values():
        assert set(series) == set(HISTORY_KEYS)
        assert all(len(v) == 4 for v in series.values())
    # the last history point equals the current table
    for team in payload["teams"]:
        assert history["teams"][str(team["roster_id"])]["playoffs"][-1] == team["playoffs"]


def test_single_week_has_null_changes(seeded_store, dynasty_config):
    simulate_weeks(seeded_store, dynasty_config, [0])
    payload = league_export(seeded_store, dynasty_config, "dynasty")
    assert payload["previous_as_of_week"] is None
    assert all(v is None for t in payload["teams"] for v in t["change"].values())
