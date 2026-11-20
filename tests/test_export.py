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
    assert {p.name for p in written if "positions" not in p.parts} == {"dynasty.json", "index.json", "managers.json"}

    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["calibration"] is None, "no calibration report stored yet"
    assert index["leagues"][0] == {
        "key": "dynasty", "name": "Taco Tuesdays", "season": "2026", "as_of_week": 3,
        "generated_at": index["leagues"][0]["generated_at"], "file": "dynasty.json", "war": None, "games": None,
        "positions": {"file": "dynasty/positions/index.json", "current": "2026"},
        "managers": {"file": "dynasty/managers.json", "count": 16},
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
    assert {p.name for p in written if "positions" not in p.parts} == {"dynasty.json", "index.json", "calibration.json", "managers.json"}
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
    assert len(ratings["weeks"]) == len(stored["weeks"]) and ratings["weeks"][:2] == [{"season": "2022", "week": 0}, {"season": "2022", "week": 1}]
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


def test_preseason_rating_shows_with_no_change_until_week_one(seeded_store, dynasty_config):
    simulate_weeks(seeded_store, dynasty_config, [0])
    team = seeded_store.read_odds("dynasty", "2026", 0)["teams"][0]
    entry = lambda season, week, mu: {"season": season, "week": week, "mu": mu, "sigma": 240, "z": None, "career_z": 0.1, "season_z": None, "ewma_z": 0.1, "fresh_mu": 1000}
    stored = {
        "league_key": "dynasty", "seasons": ["2025", "2026"],
        "weeks": [{"season": "2025", "week": 14}, {"season": "2026", "week": 0}],
        "managers": {"u1": {"display_name": "Vet", "current": True, "vacant": False, "roster_id": team["roster_id"], "seasons": ["2025", "2026"],
                            "history": [entry("2025", 14, 1300.0), entry("2026", 0, 1200.0)]}},
    }
    write_json(seeded_store.root / "ratings" / "dynasty.json", stored)
    row = next(t for t in league_export(seeded_store, dynasty_config, "dynasty")["teams"] if t["roster_id"] == team["roster_id"])
    assert row["elo"] == 1200 and row["elo_change"] is None, "after the draft, before week 1"
    stored["weeks"].append({"season": "2026", "week": 1})
    stored["managers"]["u1"]["history"].append(entry("2026", 1, 1240.0))
    write_json(seeded_store.root / "ratings" / "dynasty.json", stored)
    row = next(t for t in league_export(seeded_store, dynasty_config, "dynasty")["teams"] if t["roster_id"] == team["roster_id"])
    assert row["elo"] == 1240 and row["elo_change"] == 40, "week 1 change is measured from the preseason rating"


def war_payload(season, players, cut="yearly", through_week=2):
    return {
        "league_key": "dynasty", "season": season, "generated_at": "2026-11-16T00:00:00+00:00", "cut": cut,
        "through_week": through_week, "weeks": [1, 2],
        "constants": {"slot_mean": {"TE": 9.2}, "slot_var": {"TE": 1.0}, "opponent_mean": 100.0, "opponent_sd": 20.7},
        "replacement": {"TE": {"level": 6.1, "baseline_wins": 0.88}},
        "players": players, "unmatched": [],
    }


def war_player(name, owner, holders, war=1.0):
    return {
        "name": name, "position": "TE", "team": "LV", "games": 2, "points": 30.0, "stats": {"rec": 10.0}, "exp_wins": 1.2 + war, "war": war,
        "owner": owner, "holders": holders,
        "weekly": [{"week": 1, "score": 20.0, "played": True, "p": 0.7}, {"week": 2, "score": 10.0, "played": True, "p": 0.5}],
    }


def test_export_writes_war_leaderboards_index_and_walkthrough(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    users = seeded_store.read_users("dynasty", "2026")
    a, b = str(users[0]["user_id"]), str(users[1]["user_id"])
    write_json(seeded_store.root / "war" / "dynasty" / "2024.json", war_payload("2024", {
        "4217": war_player("George Kittle", a, [a], 1.68), "11604": war_player("Brock Bowers", b, [b], 1.54), "1": war_player("Nobody", None, [], -0.5),
    }, through_week=14))
    write_json(seeded_store.root / "war" / "dynasty" / "2026.json", war_payload("2026", {
        "11604": war_player("Brock Bowers", b, [a, b], 0.9), "2": war_player("Free Agent", None, [], 0.1),
    }, cut="weekly", through_week=2))
    out = tmp_path / "site-data"
    written = {p.relative_to(out).as_posix() for p in export_site(seeded_store, dynasty_config, out) if "positions" not in p.parts}
    assert written == {"dynasty.json", "index.json", "dynasty/managers.json", "dynasty/war/2024.json", "dynasty/war/2026.json", "dynasty/war/index.json"}

    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["war"] == {"file": "dynasty/war/index.json", "seasons": 2, "current": "2026"}
    war_index = json.loads((out / "dynasty" / "war" / "index.json").read_text(encoding="utf-8"))
    assert war_index == {
        "seasons": [{"season": "2024", "cut": "yearly", "through_week": 14, "file": "2024.json"}, {"season": "2026", "cut": "weekly", "through_week": 2, "file": "2026.json"}],
        "current": "2026", "first_weekly": "2026",
    }
    names = {str(u["user_id"]): u["display_name"] for u in users}
    s2024 = json.loads((out / "dynasty" / "war" / "2024.json").read_text(encoding="utf-8"))
    assert s2024["cut"] == "yearly" and s2024["through_week"] == 14 and s2024["replacement"]["TE"]["level"] == 6.1
    rows = {r["id"]: r for r in s2024["players"]}
    assert rows["4217"] == {"id": "4217", "name": "George Kittle", "position": "TE", "team": "LV", "games": 2, "points": 30.0, "stats": {"rec": 10.0}, "exp_wins": 2.88, "war": 1.68, "owner": names[a], "others": []}
    assert rows["1"]["owner"] is None and rows["1"]["others"] == []
    assert "weekly" not in rows["4217"]
    assert set(s2024["walkthrough"]) == {"4217", "11604"} and s2024["walkthrough"]["4217"]["weekly"][0]["p"] == 0.7
    s2026 = json.loads((out / "dynasty" / "war" / "2026.json").read_text(encoding="utf-8"))
    bowers = next(r for r in s2026["players"] if r["id"] == "11604")
    assert bowers["owner"] == names[b] and bowers["others"] == [names[a]]
    assert "walkthrough" not in s2026


def test_export_without_war_files_has_no_war_entry(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["war"] is None and not (out / "dynasty" / "war").exists()


def test_live_result_drives_the_table_and_history_stays_on_as_of_files(seeded_store, dynasty_config, tmp_path):
    import copy

    simulate_weeks(seeded_store, dynasty_config, [0, 1, 2])
    live = copy.deepcopy(seeded_store.read_odds("dynasty", "2026", 2))
    for team in live["teams"]:
        team["playoffs"] = 0.5
    live["live"] = {"week": 3, "games_final": 1, "games_total": 14, "at": "2026-11-21T12:00:00+00:00"}
    seeded_store.write_live("dynasty", "2026", live)
    payload = league_export(seeded_store, dynasty_config, "dynasty")
    assert payload["live"]["games_final"] == 1 and payload["as_of_week"] == 2 and payload["previous_as_of_week"] == 2
    assert all(t["playoffs"] == 0.5 for t in payload["teams"])
    frozen = {t["roster_id"]: t["playoffs"] for t in seeded_store.read_odds("dynasty", "2026", 2)["teams"]}
    assert all(t["change"]["playoffs"] == round(0.5 - frozen[t["roster_id"]], 4) for t in payload["teams"])
    assert payload["history"]["weeks"] == [0, 1, 2]  # the live result is not a history point
    seeded_store.delete_live("dynasty", "2026")
    assert league_export(seeded_store, dynasty_config, "dynasty")["live"] is None


def test_index_carries_the_refresh_url_and_last_refresh(seeded_store, dynasty_config, tmp_path):
    import dataclasses

    from ffapp.config import SiteConfig

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["refresh_url"] is None and index["last_refresh"] is None
    write_json(seeded_store.root / "refresh" / "last_run.json", {"started_at": "2026-11-22T17:20:00+00:00"})
    config = dataclasses.replace(dynasty_config, site=SiteConfig(refresh_url="https://relay.example"))
    export_site(seeded_store, config, out)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["refresh_url"] == "https://relay.example" and index["last_refresh"] == "2026-11-22T17:20:00+00:00"


def test_merged_cut_season_is_not_counted_as_weekly(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    users = seeded_store.read_users("dynasty", "2026")
    a = str(users[0]["user_id"])
    write_json(seeded_store.root / "war" / "dynasty" / "2026.json", war_payload("2026", {
        "11604": war_player("Brock Bowers", a, [a], 0.9),
    }, cut="merged", through_week=2))
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    war_index = json.loads((out / "dynasty" / "war" / "index.json").read_text(encoding="utf-8"))
    assert war_index["seasons"][0]["cut"] == "merged" and war_index["first_weekly"] is None


def test_export_writes_positional_rankings(seeded_store, dynasty_config, tmp_path):
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    written = {p.relative_to(out).as_posix() for p in export_site(seeded_store, dynasty_config, out)}
    seasons = seeded_store.seasons("dynasty")
    assert {f"dynasty/positions/{s}.json" for s in seasons} | {"dynasty/positions/index.json"} <= written
    pos_index = json.loads((out / "dynasty" / "positions" / "index.json").read_text(encoding="utf-8"))
    assert pos_index["current"] == seasons[-1] and [s["season"] for s in pos_index["seasons"]] == seasons
    current = json.loads((out / "dynasty" / "positions" / f"{seasons[-1]}.json").read_text(encoding="utf-8"))
    assert current["teams"] and all("axis" in info for info in current["positions"].values())
    # deterministic: a second export writes the same files
    again = tmp_path / "again"
    export_site(seeded_store, dynasty_config, again)
    assert (again / "dynasty" / "positions" / f"{seasons[-1]}.json").read_text(encoding="utf-8") == (out / "dynasty" / "positions" / f"{seasons[-1]}.json").read_text(encoding="utf-8")


def test_refresh_export_shows_this_runs_start_not_the_previous_one(seeded_store, dynasty_config, tmp_path):
    """Inside `refresh`, last_run.json still holds the previous run until the export (the last step)
    succeeds, so the export is handed this run's start time instead."""
    from datetime import datetime, timezone

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    write_json(seeded_store.root / "refresh" / "last_run.json", {"started_at": "2026-11-19T01:06:53+00:00"})
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out, last_refresh=datetime(2026, 11, 19, 18, 3, 29, tzinfo=timezone.utc))
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["last_refresh"] == "2026-11-19T18:03:29+00:00"


def test_export_writes_the_managers_file_with_every_manager(seeded_store, dynasty_config, tmp_path):
    from ffapp.managers import managers_for_league

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    payload = json.loads((out / "dynasty" / "managers.json").read_text(encoding="utf-8"))
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    expected = {m.user_id for m in managers_for_league(seeded_store, "dynasty").values()}
    assert {m["user_id"] for m in payload["managers"]} == expected
    assert index["leagues"][0]["managers"] == {"file": "dynasty/managers.json", "count": len(expected)}
    keys = {"name", "current", "team_names", "banners", "form", "all_time", "rival", "tiles", "roster", "history", "head_to_head", "records", "faab", "players", "news"}
    for manager in payload["managers"]:
        assert keys <= set(manager), manager["name"]
        assert (manager["form"] is None) == (not manager["current"])
