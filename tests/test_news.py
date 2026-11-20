"""Team News stories (src/ffapp/news.py): each story type, ordering, the feature pick and the weekly cap."""

from types import SimpleNamespace

from ffapp.config import Rivals
from ffapp.managers import Game
from ffapp.news import Story, manager_stories, order_stories, team_of_the_week, week_date

LEAGUE = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF", "BN"]}


def _manager(current=True):
    return SimpleNamespace(user_id="u1", last="2026", current=current, roster_by_season={"2026": 1})


def _ctx(**over):
    data = SimpleNamespace(league=LEAGUE, matchups={})
    ctx = {"games": [], "rivals": None, "names_by_user": {"u1": "me", "u2": "them"}, "seasons": {"2026": data},
           "names": {"2026": ({"p1": "Pat One", "p2": "Sam Two"}, {"p1": "WR", "p2": "RB"})}, "totw": {}, "odds": {},
           "statuses": {}, "details": {}, "trending": {}, "roster_players": {("2026", 1): {"p1", "p2"}},
           "starters_now": {("2026", 1): {"p1"}}, "owners": {"2026": {1: "u1", 2: "u2"}}, "places": {"2026": {1: 4}},
           "held_weeks": {}, "weekly_war": {}, "current_week": 11, "league_scores": [], "best_before": {}}
    ctx.update(over)
    return ctx


def _types(stories):
    return [s["type"] for s in stories]


def _game(week, pts, opp_pts, opp_roster=2):
    return Game("2026", week, False, "u1", "u2", 1, opp_roster, pts, opp_pts)


def test_week_dates_follow_labor_day():
    assert week_date("2026", 1) == "2026-09-14" and week_date("2026", 1, "thu") == "2026-09-10"


def test_result_and_streak_stories():
    games = [_game(w, 110.0, 90.0) for w in (1, 2, 3)]
    stories = manager_stories(None, "x", _manager(), _ctx(games=games))
    assert _types(stories).count("result") == 3 and _types(stories).count("streak") == 1
    streak = next(s for s in stories if s["type"] == "streak")
    assert streak["fields"] == {"result": "W", "length": 3} and streak["link"] == "managers"


def test_forecast_move_needs_ten_points():
    odds = {"2026": {8: {1: 0.50}, 9: {1: 0.55}, 10: {1: 0.71}}}
    stories = manager_stories(None, "x", _manager(), _ctx(odds=odds))
    moves = [s for s in stories if s["type"] == "forecast"]
    assert [(s["week"], s["fields"]["change"]) for s in moves] == [(10, 0.16)]


def test_new_team_high_is_a_record_with_its_league_rank():
    games = [_game(10, 183.5, 120.0)]
    ctx = _ctx(games=games, best_before={"u1": {"high_score": 171.2}}, league_scores=[202.4, 193.7, 183.5, 150.0])
    record = next(s for s in manager_stories(None, "x", _manager(), ctx) if s["type"] == "record")
    assert record["fields"] == {"kind": "high_score", "value": 183.5, "previous": 171.2, "rank": 3}


def test_injury_story_only_when_newly_out():
    statuses = {"2026": {10: {"p1": "Questionable"}, 11: {"p1": "Out", "p2": "IR"}, 12: {"p1": "Out"}}}
    details = {"2026": {11: {"p1": {"body_part": "Hamstring"}}}}
    stories = manager_stories(None, "x", _manager(), _ctx(statuses=statuses, details=details))
    injuries = [(s["week"], s["fields"]["player"], s["fields"]["status"], s["fields"]["body_part"]) for s in stories if s["type"] == "injury"]
    assert sorted(injuries) == [(11, "Pat One", "Out", "Hamstring"), (11, "Sam Two", "IR", None)]


def test_practice_report_for_starters_and_depth_chart_moves():
    details = {"2026": {10: {"p2": {"depth": 2}}, 11: {"p1": {"practice": "DNP"}, "p2": {"depth": 1, "depth_pos": "RB"}}}}
    stories = manager_stories(None, "x", _manager(), _ctx(details=details))
    assert {"type": "practice", "player": "Pat One", "practice": "DNP"} in [{"type": s["type"], **s["fields"]} for s in stories if s["type"] == "practice"]
    depth = next(s for s in stories if s["type"] == "depth")
    assert depth["fields"] == {"player": "Sam Two", "from": 2, "to": 1, "depth_pos": "RB"}


def test_trending_add_in_the_top_ten():
    trending = {"2026": {"saved_at": "2026-11-19T20:00:00+00:00", "adds": [{"player_id": "x"}, {"player_id": "p2"}]}}
    story = next(s for s in manager_stories(None, "x", _manager(), _ctx(trending=trending)) if s["type"] == "trending")
    assert story["fields"] == {"player": "Sam Two", "rank": 2} and story["at"] == "2026-11-19"


def test_war_milestone_counts_only_weeks_on_the_team():
    war = {("2026", 1, "p1"): 0.6, ("2026", 2, "p1"): 0.6, ("2026", 3, "p1"): 0.6}
    held = {("2026", 1, 1): {"p1"}, ("2026", 3, 1): {"p1"}}   # week 2 on another team
    stories = manager_stories(None, "x", _manager(), _ctx(weekly_war=war, held_weeks=held))
    assert [(s["week"], s["fields"]["war"]) for s in stories if s["type"] == "milestone"] == [(3, 1)]


def test_team_of_the_week_only_with_their_player():
    rows = [{"roster_id": 1, "players": ["p1"], "players_points": {"p1": 30.0}, "starters": ["p1"], "starters_points": [30.0]}]
    data = SimpleNamespace(league=LEAGUE, matchups={5: rows})
    with_player = _ctx(games=[_game(5, 100.0, 90.0)], seasons={"2026": data}, totw={("2026", 5): {"p1"}})
    without = _ctx(games=[_game(5, 100.0, 90.0)], seasons={"2026": data}, totw={("2026", 5): {"zz"}})
    assert "totw" in _types(manager_stories(None, "x", _manager(), with_player))
    assert "totw" not in _types(manager_stories(None, "x", _manager(), without))


def test_team_of_the_week_picks_the_best_lineup():
    positions = {f"wr{i}": "WR" for i in range(4)} | {"qb": "QB"}
    rows = [{"players_points": {"wr0": 30, "wr1": 25, "wr2": 20, "wr3": 2, "qb": 18}}]
    totw = team_of_the_week({"roster_positions": ["QB", "WR", "WR", "FLEX"]}, rows, positions)
    assert totw == {"qb", "wr0", "wr1", "wr2"}


def test_rivalry_preview_and_result():
    rivals = Rivals(pairs=((1, 2),), rivalry_week={"2026": 7})
    preview = manager_stories(None, "x", _manager(), _ctx(rivals=rivals, current_week=7))
    assert any(s["type"] == "rivalry_preview" and s["fields"]["opp"] == "them" for s in preview)
    result = manager_stories(None, "x", _manager(), _ctx(rivals=rivals, games=[_game(7, 90.0, 80.0)]))
    assert result[0]["type"] == "rivalry_result"


def test_retired_manager_ends_with_the_final_season():
    stories = manager_stories(None, "x", _manager(current=False), _ctx(games=[_game(14, 90.0, 80.0)]))
    assert stories[0]["type"] == "final_season" and stories[0]["fields"] == {"season": "2026", "place": 4}


def test_record_beats_result_for_the_feature_and_player_stories_are_capped():
    week = [Story("result", "2026", 10, "2026-11-16"), Story("record", "2026", 10, "2026-11-16")]
    players = [Story("injury", "2026", 10, "2026-11-12") for _ in range(5)]
    ordered = order_stories(week + players)
    assert ordered[0].type == "record"
    assert sum(1 for s in ordered if s.type == "injury") == 3
