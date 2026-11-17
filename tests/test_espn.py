import pytest

from ffapp.espn import (
    ALIASES,
    EspnClient,
    EspnError,
    capture_snapshots,
    match,
    normalise,
    refresh_crosswalk,
    slim_players,
    slim_snapshot,
    teams_from_stats,
)
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store
from tests.fixtures import FixtureSession, load


def client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def espn_rows():
    return load("espn/players.json")


# -- slim snapshot ----------------------------------------------------------------------


def test_slim_snapshot_keeps_fantasy_positions_with_ownership_only():
    players = slim_snapshot(espn_rows())
    assert len(players) == 232  # 6 positions x 40, minus the IDP row and the row without ownership
    assert "3915189" not in players and "99999901" not in players
    bowers = next(p for p in players.values() if p["name"] == "Brock Bowers")
    assert bowers["position"] == "TE" and bowers["team"] == "LV" and bowers["started"] == 90.94
    assert all(set(p) == {"name", "position", "team", "started", "owned"} for p in players.values())


def test_slim_snapshot_maps_team_28_to_was_and_defenses_by_team():
    rows = [
        {"id": -16028, "fullName": "Commanders D/ST", "defaultPositionId": 16, "proTeamId": 28, "ownership": {"percentStarted": 12.5, "percentOwned": 20}},
        {"id": 1, "fullName": "Some Kicker", "defaultPositionId": 5, "proTeamId": 28, "ownership": {"percentStarted": "3.25", "percentOwned": None}},
    ]
    players = slim_snapshot(rows)
    assert players["-16028"]["team"] == "WAS" and players["-16028"]["position"] == "DEF"
    assert players["1"] == {"name": "Some Kicker", "position": "K", "team": "WAS", "started": 3.25, "owned": 0.0}


@pytest.mark.parametrize(
    "payload",
    [{"players": []}, [{"fullName": "no id"}], [{"id": 1, "defaultPositionId": 1, "ownership": {"percentStarted": "lots"}}]],
)
def test_slim_snapshot_rejects_unexpected_shapes(payload):
    with pytest.raises(EspnError):
        slim_snapshot(payload)


def test_espn_client_url_and_filter_header():
    session = FixtureSession()
    espn = EspnClient(SleeperClient(session, min_interval=0, sleep=lambda s: None))
    rows = espn.players("2024", 9)
    assert isinstance(rows, list)
    assert session.calls[0].endswith("/seasons/2024/players?scoringPeriodId=9&view=kona_player_info")


# -- store paths -------------------------------------------------------------------------


def test_store_round_trips_snapshots_and_crosswalk(tmp_path):
    store = Store(tmp_path / "data")
    assert store.read_espn_season("2024") is None and store.espn_weeks("2024") == [] and store.read_crosswalk() is None
    store.write_espn_season("2024", {"season": "2024", "week": None, "players": {}})
    store.write_espn_week("2024", 3, {"season": "2024", "week": 3, "players": {}})
    store.write_espn_week("2024", 11, {"season": "2024", "week": 11, "players": {}})
    store.write_crosswalk({"1": {"espn_id": "2", "name": "A B", "position": "QB"}})
    assert store.read_espn_season("2024")["week"] is None
    assert store.espn_weeks("2024") == [3, 11]
    assert store.read_espn_week("2024", 11)["week"] == 11 and store.read_espn_week("2024", 4) is None
    assert store.read_crosswalk() == {"1": {"espn_id": "2", "name": "A B", "position": "QB"}}


# -- capture -----------------------------------------------------------------------------


def state(week, season="2026", season_type="regular"):
    return {"state/nfl.json": {"week": week, "season": season, "season_type": season_type, "league_season": season}}


def test_capture_backfills_missing_seasons_and_writes_current_week(seeded_store):
    sleeper = client(state(10))
    report = capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    assert report.ok
    assert report.seasons_written == ["2022", "2023", "2024", "2025", "2026"]
    assert report.week_written == ("2026", 10)
    assert seeded_store.read_espn_season("2023")["players"]
    assert seeded_store.espn_weeks("2026") == [10]


def test_capture_skips_stored_seasons_and_overwrites_only_the_current_week(seeded_store):
    sleeper = client(state(10))
    capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    seeded_store.write_espn_season("2024", {"season": "2024", "week": None, "players": {"marker": True}})
    seeded_store.write_espn_week("2026", 10, {"season": "2026", "week": 10, "players": {"old": True}})
    session = FixtureSession(state(10))
    sleeper = SleeperClient(session, min_interval=0, sleep=lambda s: None)
    report = capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    assert report.ok and report.seasons_written == [] and report.week_written == ("2026", 10)
    assert seeded_store.read_espn_season("2024")["players"] == {"marker": True}
    assert "old" not in seeded_store.read_espn_week("2026", 10)["players"]
    assert sum(1 for c in session.calls if "/seasons/" in c) == 1  # only the weekly fetch


def test_capture_week_rollover_keeps_the_earlier_week(seeded_store):
    sleeper = client(state(11))
    capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    seeded_store.write_espn_week("2026", 11, {"season": "2026", "week": 11, "players": {"kept": True}})
    sleeper = client(state(12))
    report = capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    assert report.week_written == ("2026", 12)
    assert seeded_store.espn_weeks("2026") == [11, 12]
    assert seeded_store.read_espn_week("2026", 11)["players"] == {"kept": True}


def test_capture_offseason_writes_no_week(seeded_store):
    sleeper = client(state(1, season="2027", season_type="off"))
    report = capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    assert report.ok and report.week_written is None
    assert seeded_store.espn_weeks("2027") == [] and seeded_store.espn_weeks("2026") == []


def test_capture_failure_writes_nothing(seeded_store):
    sleeper = client({**state(10), "espn/players.json": 503})
    report = capture_snapshots(EspnClient(sleeper), sleeper, seeded_store, ["dynasty"])
    assert not report.ok and "season 2022" in report.errors[0]
    assert not (seeded_store.root / "espn").exists()


# -- crosswalk ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [("Travis Etienne Jr.", "travisetienne"), ("Ja'Marr Chase", "jamarrchase"), ("Kenneth Walker III", "kennethwalker"), ("Amon-Ra St. Brown", "amonrastbrown")],
)
def test_normalise(name, expected):
    assert normalise(name) == expected


def test_refresh_crosswalk_writes_once(seeded_store):
    sleeper = client()
    assert refresh_crosswalk(sleeper, seeded_store) is True
    cw = seeded_store.read_crosswalk()
    assert cw["7543"] == {"espn_id": None, "name": "Travis Etienne Jr.", "position": "RB"}
    assert cw["4984"]["espn_id"] == "3918298"
    assert refresh_crosswalk(sleeper, seeded_store) is False


def test_slim_players_rejects_non_map():
    with pytest.raises(SleeperError):
        slim_players([])


def test_match_by_espn_id_alias_name_and_team():
    crosswalk = {
        "100": {"espn_id": "9", "name": "Veteran Guy", "position": "QB"},
        "101": {"espn_id": None, "name": "Travis Etienne", "position": "RB"},
        "102": {"espn_id": None, "name": "Mike Davis", "position": "RB"},
        "103": {"espn_id": None, "name": "Mike Davis", "position": "RB"},
        "104": {"espn_id": None, "name": "Twin A", "position": "WR"},
        "105": {"espn_id": None, "name": "Twin A", "position": "WR"},
        ALIASES["Kenneth Gainwell"]: {"espn_id": None, "name": "Kenny Gainwell", "position": "RB"},
    }
    players = {
        "9": {"name": "Veteran Guy Renamed", "position": "QB", "team": "BUF", "started": 50.0, "owned": 90.0},
        "10": {"name": "Travis Etienne Jr.", "position": "RB", "team": "NO", "started": 40.0, "owned": 90.0},
        "11": {"name": "Mike Davis", "position": "RB", "team": "CAR", "started": 5.0, "owned": 9.0},
        "12": {"name": "Twin A", "position": "WR", "team": "KC", "started": 3.0, "owned": 4.0},
        "13": {"name": "Kenneth Gainwell", "position": "RB", "team": "PIT", "started": 64.4, "owned": 80.0},
        "14": {"name": "Nobody Known", "position": "TE", "team": "DAL", "started": 1.9, "owned": 2.0},
        "15": {"name": "Nobody Famous", "position": "TE", "team": "DAL", "started": 2.0, "owned": 2.0},
        "-16028": {"name": "Commanders D/ST", "position": "DEF", "team": "WAS", "started": 30.0, "owned": 40.0},
    }
    teams = {"102": "CAR", "103": "NYG", "104": "KC", "105": "KC"}
    mapping, unmatched = match(players, crosswalk, teams)
    assert mapping == {"9": "100", "10": "101", "11": "102", "13": ALIASES["Kenneth Gainwell"], "-16028": "WAS"}
    # 1.9 is below the report threshold; the twins are ambiguous and also below it
    assert [(u.name, u.position, u.started) for u in unmatched] == [("Twin A", "WR", 3.0), ("Nobody Famous", "TE", 2.0)]


def test_match_real_fixture_leaves_nothing_relevant_unmatched(seeded_store):
    sleeper = client()
    refresh_crosswalk(sleeper, seeded_store)
    players = slim_snapshot(espn_rows())
    mapping, unmatched = match(players, seeded_store.read_crosswalk(), teams_from_stats(seeded_store, "2025"))
    assert [u.name for u in unmatched] == []
    unmapped = [p["name"] for e, p in players.items() if e not in mapping]
    assert unmapped == ["John Parker Romo"]  # a kicker started in 1.2% of leagues, below the report threshold
    assert mapping[next(e for e, p in players.items() if p["name"] == "Brock Bowers")] == "11604"


def test_teams_from_stats_uses_last_week(seeded_store):
    seeded_store.write_stats("2026", 1, {"7543": {"team": "JAX", "stats": {}}})
    seeded_store.write_stats("2026", 2, {"7543": {"team": "NO", "stats": {}}})
    assert teams_from_stats(seeded_store, "2026")["7543"] == "NO"
