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


# ---- managers-moves: Moves stories --------------------------------------------------------------

from ffapp.moves import Bid, LeagueMoves  # noqa: E402

BUDGET_LEAGUE = {**LEAGUE, "settings": {"waiver_budget": 100}}


def _moves_ctx(moves=None, bids=None, budget=100, **over):
    data = SimpleNamespace(league={**LEAGUE, "settings": {"waiver_budget": budget}}, matchups={})
    lm = LeagueMoves(moves={"u1": {"2026": moves}} if moves else {}, bids=bids or [])
    return _ctx(seasons={"2026": data}, moves=lm, **over)


def _row(pid, week, **kw):
    return {"pid": pid, "name": {"p1": "Pat One", "p2": "Sam Two"}.get(pid, pid), "pos": None, "week": week, **kw}


def _moves_types(ctx):
    return [s["type"] for s in manager_stories(None, "x", _manager(), ctx) if s["type"] in {"trade", "big_bid", "pays_off", "got_away", "outbid"}]


def test_trade_story_names_both_sides():
    side = {"week": 6, "with": ["u2"], "got": {"players": [_row("p1", 6, war=1.1)], "picks": [{"season": "2027", "round": 2}], "faab": 0},
            "gave": {"players": [_row("p2", 6, war=0.7)], "picks": [], "faab": 5}}
    stories = manager_stories(None, "x", _manager(), _moves_ctx({"added": [], "dropped": [], "trades": [side]}))
    trade = next(s for s in stories if s["type"] == "trade")
    assert trade["fields"] == {"opp": "them", "opp_user": "u2", "got": ["Pat One"], "got_picks": [{"season": "2027", "round": 2}], "got_faab": 0,
                               "gave": ["Sam Two"], "gave_picks": [], "gave_faab": 5}


def test_big_bid_by_share_of_budget_or_the_seasons_biggest():
    added = [_row("p1", 3, via="waiver", bid=41, next=12, war=1.0), _row("p2", 5, via="waiver", bid=20, war=0.1), _row("p3", 6, via="waiver", bid=8, war=0.1)]
    assert _moves_types(_moves_ctx({"added": added, "dropped": [], "trades": []})) == ["big_bid"]   # $41 is both
    added = [_row("p2", 5, via="waiver", bid=20, war=0.1), _row("p3", 6, via="waiver", bid=8, war=0.1)]
    stories = manager_stories(None, "x", _manager(), _moves_ctx({"added": added, "dropped": [], "trades": []}))
    assert [s["fields"]["bid"] for s in stories if s["type"] == "big_bid"] == [20], "the season's biggest, though under 25%"
    added = [_row("p1", 3, via="waiver", bid=30, war=0.1)]
    assert _moves_types(_moves_ctx({"added": added, "dropped": [], "trades": []}, budget=150)) == ["big_bid"], "biggest of the season"


def test_outbid_big_close_tied_and_small():
    bids = [Bid("2026", 4, "p1", "u1", 40, False, 1, winner="u2", winning_bid=55),     # big: 40% of the budget
            Bid("2026", 5, "p2", "u1", 6, False, 2, winner="u2", winning_bid=8),       # close and at least 5%
            Bid("2026", 6, "p1", "u1", 29, False, 3, winner="u2", winning_bid=29),     # tied, lost on priority
            Bid("2026", 7, "p2", "u1", 2, False, 4, winner="u2", winning_bid=4)]       # small: skipped
    stories = [s for s in manager_stories(None, "x", _manager(), _moves_ctx(bids=bids)) if s["type"] == "outbid"]
    assert sorted((s["week"], s["fields"]["bid"], s["fields"]["tied"]) for s in stories) == [(4, 40, False), (5, 6, False), (6, 29, True)]
    big_budget = [Bid("2026", 4, "p1", "u1", 25, False, 1, winner="u2", winning_bid=40)]   # 25 of 150 is under 20%
    assert not _moves_types(_moves_ctx(bids=big_budget, budget=150))


def test_pickup_pays_off_once_when_passing_one_war():
    held = {("2026", w, 1): {"p1"} for w in range(3, 12)}
    war = {("2026", w, "p1"): 0.3 for w in range(3, 12)}
    added = [_row("p1", 3, via="free_agent", war=2.7)]
    stories = manager_stories(None, "x", _manager(), _moves_ctx({"added": added, "dropped": [], "trades": []}, held_weeks=held, weekly_war=war))
    pays = [s for s in stories if s["type"] == "pays_off"]
    assert [(s["week"], s["fields"]["since"]) for s in pays] == [(6, 3)], "0.3 x 4 weeks passes +1.0 in week 6, once"


def test_got_away_names_the_team_he_plays_for():
    held = {("2026", w, 1): {"p1"} for w in (1, 2)} | {("2026", w, 2): {"p1"} for w in range(3, 9)} | {("2026", w, 1): set() for w in range(3, 9)}
    war = {("2026", w, "p1"): 0.5 for w in range(3, 9)}
    dropped = [_row("p1", 3, via="free_agent", war=3.0)]
    stories = manager_stories(None, "x", _manager(), _moves_ctx({"added": [], "dropped": dropped, "trades": []}, held_weeks=held, weekly_war=war))
    away = next(s for s in stories if s["type"] == "got_away")
    assert away["week"] == 4 and away["fields"]["team"] == "them"


def test_moves_stories_have_their_own_cap():
    sides = [{"week": 9, "with": ["u2"], "got": {"players": [_row(f"g{i}", 9)], "picks": [], "faab": 0},
              "gave": {"players": [_row(f"x{i}", 9)], "picks": [], "faab": 0}} for i in range(4)]
    statuses = {"2026": {8: {}, 9: {"p1": "Out"}}}
    stories = manager_stories(None, "x", _manager(), _moves_ctx({"added": [], "dropped": [], "trades": sides}, statuses=statuses))
    week9 = [s["type"] for s in stories if s["week"] == 9]
    assert week9.count("trade") == 3 and "injury" in week9
