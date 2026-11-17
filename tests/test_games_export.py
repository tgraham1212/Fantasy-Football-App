import json
from datetime import datetime, timezone

from ffapp.export import export_site
from ffapp.games import update_games
from ffapp.games_export import key_players, week_label
from ffapp.bracket import BracketRules
from tests.test_games import AS_OF, prepare


def test_key_players_rule():
    lineup = [
        ["QB", "q", "QB", 20.0],
        ["RB", "r1", "RB", 11.0],
        ["RB", "r2", "RB", 18.0],
        ["WR", "w1", "WR", 16.0],
        ["WR", "w2", "WR", 13.0],
        ["TE", "t", "TE", 9.0],
        ["FLEX", None, "RB", 8.0],  # replacement fill
    ]
    assert [r[1] for r in key_players(lineup)] == ["q", "r2", "w1", "w2"]


def test_key_players_keep_a_replacement_quarterback():
    lineup = [["QB", None, "QB", 16.9], ["RB", "r", "RB", 21.3], ["WR", "w", "WR", 13.8], ["TE", "t", "TE", 9.3]]
    assert key_players(lineup) == [["QB", None, "QB", 16.9], ["RB", "r", "RB", 21.3], ["WR", "w", "WR", 13.8], ["TE", "t", "TE", 9.3]]


def test_week_labels():
    rules = BracketRules(playoff_teams=6, playoff_week_start=15, reseed=False, toilet_bowl=True)
    assert [week_label(w, rules) for w in (3, 15, 16, 17)] == ["Week 3", "Playoffs round 1 (week 15)", "Semifinals (week 16)", "Final (week 17)"]


def test_export_writes_games_index_and_weeks(seeded_store, dynasty_config, tmp_path):
    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    out = tmp_path / "site-data"
    written = {p.relative_to(out).as_posix() for p in export_site(seeded_store, dynasty_config, out)}
    assert "dynasty/games/index.json" in written and f"dynasty/games/week_{AS_OF + 1:02d}.json" in written
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["games"] == {"file": "dynasty/games/index.json", "current": AS_OF + 1}
    games_index = json.loads((out / "dynasty" / "games" / "index.json").read_text(encoding="utf-8"))
    kinds = {w["week"]: w["kind"] for w in games_index["weeks"]}
    assert kinds[AS_OF] == "final" and kinds[AS_OF + 1] == "current" and kinds[AS_OF + 2] == "upcoming"

    finished = json.loads((out / "dynasty" / "games" / f"week_{AS_OF:02d}.json").read_text(encoding="utf-8"))
    assert finished["kind"] == "final" and finished["source"] == "pre-week" and len(finished["games"]) == 6
    g = finished["games"][0]
    assert g["winner"] in [t["roster_id"] for t in g["teams"]] and all(t["actual"] is not None for t in g["teams"])
    assert all(t["display_name"] for t in g["teams"])

    current = json.loads((out / "dynasty" / "games" / f"week_{AS_OF + 1:02d}.json").read_text(encoding="utf-8"))
    team = current["games"][0]["teams"][0]
    assert current["kind"] == "current" and current["source"] == "forecast" and current["forecast_as_of"] == AS_OF
    assert team["actual"] is None and len(team["lineup"]) == 8 and 1 <= len(team["key_players"]) <= 4
    assert set(team["lineup"][0]) == {"slot", "player_id", "name", "position", "projected", "replacement", "status", "points", "clock", "kickoff", "wpa"}
    assert team["lineup"][0]["status"] is None and team["lineup"][0]["wpa"] is None  # nothing kicked off in this fixture week
    assert finished["games"][0]["teams"][0]["lineup"][0]["status"] == "final"
    finished_wpa = [r["wpa"] for t in finished["games"][0]["teams"] for r in t["lineup"] if r["wpa"] is not None]
    assert finished_wpa, "starters in a finished week carry win probability added"
    assert isinstance(team["not_playing"], list)

    playoff = json.loads((out / "dynasty" / "games" / "week_15.json").read_text(encoding="utf-8"))
    assert playoff["playoffs"] and playoff["label"] == "Playoffs round 1 (week 15)"
    assert [g["match"] for g in playoff["games"]] == [1, 2] and all(g["projected"] and g["frequency"] for g in playoff["games"])
    assert [b["seed"] for b in playoff["byes"]] == [1, 2]  # consolation league: winners-bracket byes only


def test_export_without_game_files_has_no_games_entry(seeded_store, dynasty_config, tmp_path):
    prepare(seeded_store, dynasty_config)
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["games"] is None and not (out / "dynasty" / "games").exists()


def test_export_lineup_views(seeded_store, dynasty_config, tmp_path):
    from ffapp.store import write_json

    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    read = lambda w: json.loads((out / "dynasty" / "games" / f"week_{w:02d}.json").read_text(encoding="utf-8"))

    rebuilt = read(AS_OF)["games"][0]
    assert rebuilt["default_view"] == "actual" and set(rebuilt["views"]) == {"model", "actual"}
    assert rebuilt["views"]["actual"]["source"] == "rebuilt" and rebuilt["views"]["model"]["source"] == "pre-week"
    actual_rows = [r for t in rebuilt["views"]["actual"]["teams"] for r in t["lineup"]]
    model_rows = [r for t in rebuilt["views"]["model"]["teams"] for r in t["lineup"]]
    assert any(r["wpa"] is not None for r in actual_rows) and all(r["wpa"] is None for r in model_rows)
    assert all("benched" in r for r in model_rows) and all("benched" not in r for r in actual_rows)
    assert all(isinstance(t["lineup_choices"], float) for t in rebuilt["views"]["actual"]["teams"])
    assert rebuilt["teams"] == rebuilt["views"]["actual"]["teams"]  # top level mirrors the default view

    upcoming = read(AS_OF + 1)["games"][0]
    assert list(upcoming["views"]) == ["model"] and upcoming["default_view"] == "model"

    # a finished week without views falls back to its record as the actual view
    stored = seeded_store.read_games("dynasty", "2026", AS_OF)
    stored.pop("views")
    write_json(seeded_store.games_path("dynasty", "2026", AS_OF), stored)
    export_site(seeded_store, dynasty_config, out)
    fallback = read(AS_OF)["games"][0]
    assert list(fallback["views"]) == ["actual"] and fallback["views"]["actual"]["source"] == "pre-week"


def test_export_logged_week_views(seeded_store, dynasty_config, tmp_path):
    from tests.test_games import WEEK

    prepare(seeded_store, dynasty_config)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 19, 12, tzinfo=timezone.utc))
    data = seeded_store.read_season("dynasty", "2026")
    data.matchups[WEEK] = data.matchups[AS_OF]
    data.league["settings"]["last_scored_leg"] = WEEK
    seeded_store.write_season("dynasty", data)
    update_games(seeded_store, dynasty_config, "dynasty", now=datetime(2026, 11, 24, tzinfo=timezone.utc))
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    game = json.loads((out / "dynasty" / "games" / f"week_{WEEK:02d}.json").read_text(encoding="utf-8"))["games"][0]
    assert game["views"]["actual"]["source"] == "log" and game["views"]["model"]["source"] == "model"
    assert game["default_view"] == "actual"
