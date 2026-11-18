from ffapp.injuries import not_playing, save_injuries, statuses_from_players
from ffapp.store import Store

PLAYERS = {
    "1": {"position": "WR", "injury_status": "Questionable", "team": "IND"},
    "2": {"position": "RB", "injury_status": None, "team": "HOU"},
    "3": {"position": "CB", "injury_status": "Out", "team": "HOU"},  # not a fantasy position
    "4": {"position": "TE", "injury_status": "IR", "team": "KC"},
}


def state(week, season_type="regular", season="2026"):
    return {"week": week, "season": season, "season_type": season_type}


def test_statuses_keep_fantasy_positions_with_a_status():
    assert statuses_from_players(PLAYERS) == {"1": "Questionable", "4": "IR"}


def test_save_overwrites_the_current_week_and_keeps_earlier_weeks(tmp_path):
    store = Store(tmp_path / "data")
    assert save_injuries(store, state(11), PLAYERS) == ("2026", 11)
    later = {**PLAYERS, "1": {**PLAYERS["1"], "injury_status": "Out"}}
    save_injuries(store, state(11), later)  # Saturday's run replaces Thursday's
    assert store.read_injuries("2026", 11)["1"] == "Out"
    save_injuries(store, state(12), PLAYERS)  # week rolls over
    assert store.read_injuries("2026", 11)["1"] == "Out" and store.read_injuries("2026", 12)["1"] == "Questionable"


def test_save_does_nothing_in_the_offseason(tmp_path):
    store = Store(tmp_path / "data")
    assert save_injuries(store, state(0, "off"), PLAYERS) is None
    assert not (store.root / "injuries").exists()


SCORING = {"rec": 1.0, "rec_yd": 0.1, "rush_yd": 0.1}


def proj(team, **stats):
    return {"position": "WR", "team": team, "stats": stats}


def week_store(tmp_path, saved=None):
    store = Store(tmp_path / "data")
    store.write_nfl_week("2026", 9, {"games": [{"home": "HOU", "away": "IND", "kickoff_utc": "2026-11-08T18:00:00+00:00", "state": "final"}], "byes": ["KC"]})
    if saved is not None:
        store.write_injuries("2026", 9, saved)
    return store


def test_saved_statuses_and_bye_take_precedence(tmp_path):
    store = week_store(tmp_path, saved={"a": "Doubtful", "b": "Questionable", "c": "Sus", "k": "Out"})
    projections = {"a": proj("IND", rec=5), "b": proj("HOU", rec=4), "c": proj("HOU", rec=3), "k": proj("KC", rec=6)}
    out = not_playing(store, "2026", 9, ["a", "b", "c", "k"], projections, SCORING, {})
    assert out == [
        {"player_id": "a", "reason": "Doubtful"},
        {"player_id": "c", "reason": "Suspended"},  # suspended counts as out, with its own label
        {"player_id": "k", "reason": "Bye"},  # bye wins over any status
    ]


def test_inferred_out_for_weeks_without_saved_statuses(tmp_path):
    store = week_store(tmp_path)
    projections = {"zero": proj("IND"), "fine": proj("HOU", rec=5)}
    teams = {"none": "HOU", "unknown": None}
    out = not_playing(store, "2026", 9, ["zero", "fine", "none", "unknown"], projections, SCORING, teams)
    # projected 0 with a game, and no projection with a game, are inferred out; an unknown team is not guessed
    assert out == [{"player_id": "zero", "reason": "Inferred out"}, {"player_id": "none", "reason": "Inferred out"}]


def test_future_weeks_use_the_latest_saved_statuses(tmp_path):
    store = week_store(tmp_path, saved={"a": "Out"})  # week 9 saved
    store.write_nfl_week("2026", 12, {"games": [{"home": "IND", "away": "HOU", "kickoff_utc": "2026-11-29T18:00:00+00:00", "state": "scheduled"}], "byes": []})
    projections = {"a": proj("IND"), "b": proj("HOU")}  # no projections yet for week 12: must not be inferred out
    out = not_playing(store, "2026", 12, ["a", "b"], projections, SCORING, {})
    assert out == [{"player_id": "a", "reason": "Out"}]
    assert not_playing(store, "2026", 8, ["a"], {"a": proj("IND", rec=3)}, SCORING, {}) == []  # before saving began


def test_defense_bye_by_team_key(tmp_path):
    store = week_store(tmp_path)
    out = not_playing(store, "2026", 9, ["KC", "HOU"], {"HOU": {"position": "DEF", "team": "HOU", "stats": {"pts_allow": 1}}}, SCORING, {})
    assert out == [{"player_id": "KC", "reason": "Bye"}]


def test_shared_out_statuses_and_labels(tmp_path):
    store = week_store(tmp_path, saved={"n": "NA", "p": "PUP", "d": "DNR", "q": "Questionable"})
    projections = {pid: proj("HOU", rec=3) for pid in "npdq"}
    out = not_playing(store, "2026", 9, list("npdq"), projections, SCORING, {})
    assert out == [
        {"player_id": "n", "reason": "Not active"},
        {"player_id": "p", "reason": "PUP"},
        {"player_id": "d", "reason": "Did not report"},
    ]
