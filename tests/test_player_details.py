"""Player details (body part, practice, depth chart) and trending adds, saved for the Managers page's news."""

import json
from datetime import datetime, timezone

from ffapp.injuries import details_from_players, save_player_details, save_trending
from ffapp.store import Store

PLAYERS = {
    "1": {"position": "WR", "injury_body_part": "Hamstring", "practice_participation": "Limited", "depth_chart_order": 1, "depth_chart_position": "LWR"},
    "2": {"position": "RB", "depth_chart_order": 2},
    "3": {"position": "OL", "depth_chart_order": 1},            # not a fantasy position
    "4": {"position": "TE", "injury_body_part": None},           # nothing set
    "5": {"position": "QB", "practice_participation": "DNP"},    # not rostered
}
IN_SEASON = {"season": "2026", "week": 11, "season_type": "regular"}


def test_details_keep_rostered_fantasy_players_with_something_set():
    out = details_from_players(PLAYERS, {"1", "2", "3", "4"})
    assert out == {"1": {"body_part": "Hamstring", "practice": "Limited", "depth": 1, "depth_pos": "LWR"}, "2": {"depth": 2}}


def test_last_save_of_the_week_wins_and_earlier_weeks_stay(tmp_path):
    store = Store(tmp_path / "data")
    save_player_details(store, {**IN_SEASON, "week": 10}, {"2": {"position": "RB", "depth_chart_order": 2}}, {"2"})
    save_player_details(store, IN_SEASON, {"2": {"position": "RB", "depth_chart_order": 2}}, {"2"})
    save_player_details(store, IN_SEASON, {"2": {"position": "RB", "depth_chart_order": 1}}, {"2"})
    assert store.read_player_details("2026", 10) == {"2": {"depth": 2}}
    assert store.read_player_details("2026", 11) == {"2": {"depth": 1}}


def test_no_details_saved_in_the_offseason(tmp_path):
    store = Store(tmp_path / "data")
    assert save_player_details(store, {"season": "2026", "week": 0, "season_type": "off"}, PLAYERS, {"1"}) is None
    assert not (tmp_path / "data" / "players").exists()


class _Client:
    def __init__(self, adds):
        self.adds = adds

    def trending_adds(self):
        return self.adds


def test_trending_saved_with_the_time(tmp_path):
    store = Store(tmp_path / "data")
    now = datetime(2026, 11, 19, 20, 3, tzinfo=timezone.utc)
    path = save_trending(store, _Client([{"player_id": "1", "count": 900}]), IN_SEASON, now)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "2026-11-19.json" and saved == {"saved_at": "2026-11-19T20:03:00+00:00", "adds": [{"player_id": "1", "count": 900}]}
