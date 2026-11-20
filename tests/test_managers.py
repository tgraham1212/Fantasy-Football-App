"""Managers page figures (src/ffapp/managers.py), on the recorded dynasty league and small hand-built seasons."""

from ffapp.managers import bracket_places, final_places, managers_for_league, roster_owners
from ffapp.store import SeasonData


def _names_by_place(store, season):
    data = store.read_season("dynasty", season)
    places, from_brackets = final_places(data)
    owners = roster_owners(store, "dynasty", season)
    managers = managers_for_league(store, "dynasty")
    by_place = {place: managers[owners[rid]].name for rid, place in places.items()}
    return by_place, from_brackets


def test_dynasty_champions_and_runners_up_match_league_history(seeded_store):
    expected = {"2022": ("alwaysflexin", "corygraham12"), "2023": ("Gixxersean1", "corygraham12"),
                "2024": ("Gixxersean1", "Jdeguire"), "2025": ("corygraham12", "Z28kid86")}
    for season, (champ, second) in expected.items():
        by_place, from_brackets = _names_by_place(seeded_store, season)
        assert from_brackets and by_place[1] == champ and by_place[2] == second, season


def test_dynasty_retired_managers(seeded_store):
    managers = managers_for_league(seeded_store, "dynasty")
    retired = {m.name: (m.first, m.last) for m in managers.values() if not m.current}
    assert retired == {"KoPe17": ("2022", "2022"), "Hildebrand009": ("2022", "2022"), "DeekBurg": ("2022", "2023"), "TateFM": ("2022", "2023")}


def test_unfinished_season_falls_back_to_standings(seeded_store):
    places, from_brackets = final_places(seeded_store.read_season("dynasty", "2026"))
    assert not from_brackets and sorted(places.values()) == list(range(1, 13))


def _season(playoff_type, winners, losers):
    league = {"season": "2025", "league_id": "1", "status": "complete", "settings": {"playoff_type": playoff_type, "playoff_teams": 6}}
    rosters = [{"roster_id": r, "settings": {}} for r in range(1, 13)]
    return SeasonData(league=league, users=[], rosters=rosters, winners_bracket=winners, losers_bracket=losers)


WINNERS = [{"p": 1, "w": 7, "l": 9}, {"p": 3, "w": 10, "l": 4}, {"p": 5, "w": 11, "l": 6}]


def test_toilet_bowl_winner_is_last_place():
    # Sleeper's toilet bowl "winner" is the lower scorer, who advanced: the p-1 winner finishes 12th
    data = _season(0, WINNERS, [{"p": 1, "w": 8, "l": 5}, {"p": 3, "w": 12, "l": 3}, {"p": 5, "w": 1, "l": 2}])
    places = bracket_places(data)
    assert places[8] == 12 and places[5] == 11 and places[12] == 10 and places[3] == 9 and places[1] == 8 and places[2] == 7
    assert places[7] == 1 and places[9] == 2


def test_consolation_winner_is_seventh():
    data = _season(1, WINNERS, [{"p": 1, "w": 3, "l": 12}, {"p": 3, "w": 2, "l": 1}, {"p": 5, "w": 8, "l": 5}])
    places = bracket_places(data)
    assert places[3] == 7 and places[12] == 8 and places[2] == 9 and places[1] == 10 and places[8] == 11 and places[5] == 12


def test_incomplete_brackets_give_no_places():
    assert bracket_places(_season(0, WINNERS[:1], [])) == {}


# ---- history figures on hand-built games ------------------------------------------------------

from ffapp.config import Rivals  # noqa: E402
from ffapp.managers import (  # noqa: E402
    Game, all_play, form, head_to_head, luck, nemesis, records, rivalry_record, roster_bench_points, season_points,
)


def _games(rows):
    """rows: (season, week, a, b, pa, pb[, playoff]) -> both sides; roster ids equal the user number."""
    out = []
    for row in rows:
        season, week, a, b, pa, pb = row[:6]
        playoff = len(row) > 6 and row[6]
        out.append(Game(season, week, playoff, f"u{a}", f"u{b}", a, b, pa, pb))
        out.append(Game(season, week, playoff, f"u{b}", f"u{a}", b, a, pb, pa))
    return out


GAMES = _games([
    ("2024", 1, 1, 2, 120.0, 100.0), ("2024", 1, 3, 4, 90.0, 95.0),
    ("2024", 2, 1, 3, 80.0, 81.0), ("2024", 2, 2, 4, 110.0, 70.0),
    ("2024", 3, 1, 4, 150.0, 60.0), ("2024", 3, 2, 3, 99.0, 99.0),
    ("2024", 15, 1, 2, 130.0, 125.0, True),
])


def test_head_to_head_counts_regular_and_playoff_games():
    h = head_to_head(GAMES, "u1")
    assert h["u2"]["wins"] == 2 and h["u2"]["playoff_wins"] == 1 and h["u2"]["pf"] == 250.0 and h["u2"]["pa"] == 225.0
    assert h["u2"]["last"] == {"season": "2024", "week": 15, "result": "W", "points": 130.0, "opp_points": 125.0}
    assert h["u3"]["losses"] == 1


def test_form_is_the_last_five_of_the_season_oldest_first():
    assert form(GAMES, "u1", "2024") == ["W", "L", "W", "W"]
    assert form(GAMES, "u1", "2025") == []


def test_records_rank_against_every_game_in_league_history():
    rec = records(GAMES, season_points(GAMES))
    assert rec["u1"]["high_score"]["value"] == 150.0 and rec["u1"]["high_score"]["rank"] == 1
    assert rec["u1"]["biggest_win"]["value"] == 90.0 and rec["u1"]["biggest_win"]["rank"] == 1
    assert rec["u1"]["closest_loss"]["value"] == 1.0 and rec["u1"]["closest_loss"]["rank"] == 1   # smallest margin ranks first
    assert rec["u4"]["low_score"]["value"] == 60.0 and rec["u4"]["low_score"]["rank"] == 1         # lowest ranks first
    assert rec["u1"]["win_streak"]["value"] == 2 and rec["u1"]["win_streak"]["from"] == 3   # W, L, then W in weeks 3 and 15


def test_ties_share_the_better_rank():
    three_way = _games([("2024", 1, 1, 2, 140.0, 10.0), ("2024", 1, 3, 4, 140.0, 20.0), ("2024", 1, 5, 6, 140.0, 30.0)])
    rec = records(three_way, season_points(three_way))
    assert [rec[u]["high_score"]["rank"] for u in ("u1", "u3", "u5")] == [1, 1, 1]
    assert rec["u6"]["high_score"]["rank"] == 4


def test_all_play_and_luck():
    ap = all_play(GAMES)
    assert ap["u1"] == {"wins": 7, "losses": 2, "ties": 0}   # weeks 1-3: 3-0, 1-2, 3-0; the playoff week is left out
    lk = luck(GAMES, {"u1": 113.46})
    assert lk["u1"]["bench_points"] == 113.46
    # u1 won 2 of 3 regular games against an all-play pace of 7/9 * 3 = 2.33
    assert lk["u1"]["wins_above_pace"] == -0.33


def test_bench_points_example():
    assert roster_bench_points({"ppts": 1610, "ppts_decimal": 46, "fpts": 1497, "fpts_decimal": 0}) == 113.46


def test_nemesis_needs_four_games_and_breaks_ties_by_deficit():
    h = {"a": {"wins": 1, "losses": 3, "ties": 0, "games": 4, "pf": 400.0, "pa": 420.0},
         "b": {"wins": 1, "losses": 3, "ties": 0, "games": 4, "pf": 380.0, "pa": 450.0},
         "c": {"wins": 0, "losses": 3, "ties": 0, "games": 3, "pf": 300.0, "pa": 400.0}}
    assert nemesis(h) == "b"
    assert nemesis({"c": h["c"]}) is None


def test_rivalry_week_record_follows_the_roster():
    rivals = Rivals(pairs=((1, 2),), rivalry_week={"2024": 1, "2025": None})
    games = GAMES + _games([("2025", 1, 1, 2, 50.0, 60.0)])
    assert rivalry_record(games, rivals, "u1") == {"wins": 1, "losses": 0, "ties": 0, "seasons": ["2024"]}


def test_rivals_naming_a_missing_roster_are_rejected(seeded_store):
    import pytest

    from ffapp.managers import config_rival, managers_for_league

    manager = next(m for m in managers_for_league(seeded_store, "dynasty").values() if m.current)
    with pytest.raises(ValueError, match="roster 99 does not exist"):
        config_rival(seeded_store, "dynasty", Rivals(pairs=((1, 99),)), manager)


# ---- move windows ---------------------------------------------------------------------------

from ffapp.managers import players_block, windows  # noqa: E402

TIMELINE = [("2024", w) for w in range(1, 15)] + [("2025", w) for w in range(1, 15)]


def _held(weeks_on):
    return {wk: ({"p1"} if wk in weeks_on else {"other"}) for wk in TIMELINE}


def test_dropped_twice_gives_two_departed_windows_and_one_added():
    on = {("2024", w) for w in (1, 2)} | {("2024", w) for w in range(7, 12)}   # dropped in week 3, back in week 7, dropped in week 12
    war = {("2024", w, "p1"): 0.1 for w in range(1, 15)}
    ws = [w for w in windows(TIMELINE, _held(on), war, carry_over=False) if w.player == "p1"]
    kinds = [(w.kind, w.start, w.end, w.returned) for w in ws]
    assert kinds == [("added", ("2024", 1), ("2024", 2), False), ("departed", ("2024", 3), ("2024", 6), True),
                     ("added", ("2024", 7), ("2024", 11), False), ("departed", ("2024", 12), ("2024", 14), False)]
    assert [w.war for w in ws] == [0.2, 0.4, 0.5, 0.3]


def test_redraft_windows_end_with_the_season():
    on = {("2024", w) for w in range(1, 15)}
    ws = [w for w in windows(TIMELINE, _held(on), {}, carry_over=False) if w.player == "p1"]
    assert [(w.kind, w.end) for w in ws] == [("added", ("2024", 14))]   # no departed window into 2025


def test_dynasty_windows_carry_over():
    on = {("2024", w) for w in range(10, 15)} | {("2025", w) for w in range(1, 4)}
    war = {("2025", 8, "p1"): 1.5}
    ws = [w for w in windows(TIMELINE, _held(on), war, carry_over=True) if w.player == "p1"]
    assert [(w.kind, w.start, w.end) for w in ws] == [("added", ("2024", 10), ("2025", 3)), ("departed", ("2025", 4), ("2025", 14))]
    block = players_block(ws, {"p1": "Pat One"})
    assert block["got_away"] == {"player_id": "p1", "name": "Pat One", "war": 1.5, "from": ["2025", 4], "returned": False}
    assert block["most_seasons"]["seasons"] == 2


def test_faab_by_season_reads_budget_and_used(seeded_store):
    from ffapp.managers import faab_by_season, managers_for_league

    manager = next(iter(managers_for_league(seeded_store, "dynasty").values()))
    faab = faab_by_season(seeded_store, "dynasty", manager.user_id)
    assert faab and all(0 <= v["spent"] <= v["budget"] * 1.5 and v["budget"] > 0 for v in faab.values())
