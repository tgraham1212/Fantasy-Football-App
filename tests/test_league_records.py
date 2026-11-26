"""League records for the League sub-tab's Records page (src/ffapp/league_records.py; league-records 4.8.x
and 3.6.x): games that matter, ranking and ties, champions, all-time standings, weekly and season league
records and Player league records, on small hand-built leagues and the recorded dynasty league."""

from __future__ import annotations

import json

from ffapp import league_records as LR
from ffapp.bracket import BracketRules
from ffapp.managers import Manager, managers_for_league
from ffapp.store import SeasonData, read_json, write_json
from tests.test_export import simulate_weeks


# ---- hand-built leagues ------------------------------------------------------------------------

def P(season, week, a, b, pa, pb, kind=LR.REGULAR):
    """A game between rosters a and b (users u<a>, u<b>)."""
    return LR.Played(season, week, kind, f"u{a}", f"u{b}", a, b, pa, pb)


def ctx_for(games, places=None, current=None, playoff_teams=2, toilet=True, former=(), settings=None):
    """A league context over hand-built games: every user holds roster <n> in every season."""
    seasons = sorted({g.season for g in games})
    users = sorted({u for g in games for u in (g.a, g.b)}, key=lambda u: int(u[1:]))
    c = LR._Context.__new__(LR._Context)
    c.seasons, c.games, c.current = seasons, games, current
    c.managers = {u: Manager(user_id=u, name=u, seasons=list(seasons), roster_by_season={s: int(u[1:]) for s in seasons}, current=u not in former)
                  for u in users}
    league = lambda s: {"season": s, "league_id": "1", "status": "complete",  # noqa: E731
                        "settings": {"playoff_teams": playoff_teams, "playoff_type": 0 if toilet else 1, "playoff_week_start": 15}}
    c.data = {s: SeasonData(league=league(s), users=[], rosters=[{"roster_id": int(u[1:]), "settings": (settings or {}).get((u, s), {})} for u in users])
              for s in seasons}
    c.places = places or {}
    c.complete = set(c.places)
    c.rules = {s: BracketRules.from_league(c.data[s].league) for s in seasons}
    c.owners = {s: {int(u[1:]): u for u in users} for s in seasons}
    return c


def test_only_games_that_matter_count():
    """4.8.1: winners-bracket path, the final and the 3rd place game count, the 5th place game does not;
    in a toilet-bowl league the toilet bowl path and final count, its other placement games do not."""
    winners = [{"r": 1, "m": 1, "t1": 3, "t2": 6, "w": 3, "l": 6}, {"r": 2, "m": 3, "t1": 1, "t2": 3, "w": 1, "l": 3},
               {"r": 3, "m": 5, "t1": 1, "t2": 2, "w": 1, "l": 2, "p": 1}, {"r": 3, "m": 6, "t1": 3, "t2": 4, "w": 4, "l": 3, "p": 3},
               {"r": 3, "m": 7, "t1": 5, "t2": 6, "w": 5, "l": 6, "p": 5}]
    losers = [{"r": 1, "m": 1, "t1": 7, "t2": 10, "w": 10, "l": 7}, {"r": 3, "m": 5, "t1": 10, "t2": 12, "w": 12, "l": 10, "p": 1},
              {"r": 3, "m": 6, "t1": 8, "t2": 9, "w": 9, "l": 8, "p": 3}]

    def season(playoff_type):
        league = {"season": "2024", "league_id": "1", "settings": {"playoff_type": playoff_type, "playoff_teams": 6, "playoff_week_start": 15}}
        return SeasonData(league=league, users=[], rosters=[], winners_bracket=winners, losers_bracket=losers)

    kinds = LR.bracket_kinds(season(0))
    assert kinds[(15, frozenset((3, 6)))] == LR.PLAYOFFS and kinds[(16, frozenset((1, 3)))] == LR.PLAYOFFS
    assert kinds[(17, frozenset((1, 2)))] == LR.CHAMPIONSHIP and kinds[(17, frozenset((3, 4)))] == LR.THIRD
    assert (17, frozenset((5, 6))) not in kinds, "the 5th place game decides nothing"
    assert kinds[(15, frozenset((7, 10)))] == LR.TOILET and kinds[(17, frozenset((10, 12)))] == LR.TOILET_FINAL
    assert (17, frozenset((8, 9))) not in kinds, "a toilet bowl placement game"
    consolation = LR.bracket_kinds(season(1))
    assert not any(k[1] & {7, 8, 9, 10, 12} for k in consolation), "a consolation bracket counts for nothing"


def test_ties_share_a_rank_oldest_first():
    """4.8.2: equal values share a rank and the oldest is listed first; distinct ranks with a tie-break."""
    entries = [{"value": 49.9, "season": "2025", "week": 12, "id": "gibbs"}, {"value": 53.1, "season": "2022", "week": 9, "id": "mixon"},
               {"value": 49.9, "season": "2024", "week": 10, "id": "chase"}, {"value": 40.0, "season": "2021", "week": 1, "id": "low"}]
    top = LR.ranked(entries)
    assert [(e["id"], e["rank"]) for e in top] == [("mixon", 1), ("chase", 2), ("gibbs", 2), ("low", 4)]
    assert [e["id"] for e in LR.ranked(entries, low=True)][:1] == ["low"]
    assert [e["rank"] for e in LR.ranked(entries, distinct=True)] == [1, 2, 3, 4]
    assert len(LR.ranked([{"value": i, "season": "2024", "week": 1} for i in range(40)])) == 25


def test_weekly_records_example():
    """4.8.5, 4.8.5.1 and 4.8.5.2."""
    games = [P("2023", 3, 1, 2, 202.42, 102.44), P("2023", 4, 3, 4, 90.0, 89.5), P("2023", 4, 1, 2, 70.0, 75.0),
             P("2022", 17, 3, 4, 147.0, 62.4, LR.TOILET_FINAL), P("2024", 2, 1, 3, 100.0, 60.0)]
    weekly = LR._weekly(ctx_for(games, current="2024"))
    top = {k: v[0] for k, v in weekly.items()}
    assert (top["high_team"]["value"], top["high_team"]["user"], top["high_team"]["opp"]) == (202.42, "u1", "u2")
    assert (top["low_team"]["value"], top["low_team"]["user"]) == (60.0, "u3")
    assert top["high_matchup"]["value"] == 304.86 and top["low_matchup"]["value"] == 145.0
    assert (top["blowout"]["value"], top["blowout"]["user"]) == (99.98, "u1")
    assert sum(1 for e in weekly["blowout"] if e["value"] == 99.98) == 1, "one entry per game, under its winner"
    assert (top["closest"]["value"], top["closest"]["user"], top["closest"]["opp"]) == (0.5, "u3", "u4")
    assert (top["high_loss"]["value"], top["high_loss"]["user"]) == (102.44, "u2")
    assert (top["low_win"]["value"], top["low_win"]["user"]) == (75.0, "u2")
    toilet = next(e for e in weekly["blowout"] if e["value"] == 84.6)
    assert toilet["kind"] == LR.TOILET_FINAL and toilet["score"] == [147.0, 62.4]
    assert next(e for e in weekly["high_team"] if e["season"] == "2024")["current"] is True


def test_all_time_standings_example():
    """4.8.4 and 4.8.4.1: regular-season record, win % and point differential; playoff record over
    winners-bracket games that matter, the 3rd place game included; finishes."""
    games = [P("2024", 1, 1, 2, 120.0, 100.0), P("2024", 2, 1, 3, 90.0, 95.0), P("2024", 3, 1, 4, 110.0, 80.0),
             P("2024", 15, 1, 4, 100.0, 90.0, LR.PLAYOFFS), P("2024", 16, 1, 2, 80.0, 99.0, LR.PLAYOFFS),
             P("2024", 16, 1, 3, 120.0, 100.0, LR.THIRD), P("2024", 16, 4, 3, 50.0, 60.0, LR.TOILET)]
    places = {"2024": {2: 1, 3: 2, 1: 3, 4: 4}}
    rows = {r["user"]: r for r in LR._standings(ctx_for(games, places=places, playoff_teams=3))}
    u1 = rows["u1"]
    assert u1["record"] == {"wins": 2, "losses": 1, "ties": 0} and u1["pct"] == round(2 / 3, 4)
    assert u1["diff"] == 45.0, "regular season only: 320 - 275"
    assert u1["playoff_record"] == {"wins": 2, "losses": 1, "ties": 0}, "the 3rd place win counts, the toilet bowl game is not a playoff game"
    assert (u1["playoffs"], u1["third_place"], u1["first_place"]) == (1, 1, 0)
    assert rows["u2"]["first_place"] == 1 and rows["u4"]["last_place"] == 1 and rows["u4"]["playoffs"] == 0


def test_standings_order():
    """4.8.4.2: current Managers first, each group by win %, a tie going to the larger point differential."""
    games = [P("2024", 1, 1, 5, 150.0, 50.0), P("2024", 1, 2, 6, 110.0, 100.0), P("2024", 1, 3, 7, 101.0, 100.0),
             P("2024", 2, 5, 1, 120.0, 100.0), P("2024", 2, 6, 2, 105.0, 100.0), P("2024", 2, 7, 3, 101.0, 100.0),
             P("2024", 3, 4, 8, 200.0, 10.0)]
    rows = LR._standings(ctx_for(games, former=("u4",)))
    current = [r["user"] for r in rows if r["current"]]
    assert current[:3] == ["u1", "u2", "u3"], "three current Managers on .500, by point differential"
    assert rows[-1]["user"] == "u4" or rows[-1]["current"] is False
    former = [r for r in rows if not r["current"]]
    assert [r["user"] for r in former] == ["u4"] and former[0]["rank"] is None
    assert rows[0]["rank"] == 1


def test_streaks_count_games_that_matter():
    """4.8.6.2: losses run on through the toilet bowl games, within one season."""
    games = [P("2024", w, 1, 2, 80.0, 100.0) for w in range(1, 4)] + [
        P("2024", 15, 1, 3, 70.0, 90.0, LR.TOILET), P("2024", 16, 1, 4, 60.0, 90.0, LR.TOILET_FINAL),
        P("2025", 1, 1, 2, 70.0, 90.0)]
    rows = {(r["user"], r["season"]): r for r in LR._season_rows(ctx_for(games), {})}
    assert rows[("u1", "2024")]["loss_streak"] == 5
    assert rows[("u1", "2025")]["loss_streak"] == 1, "a streak stays within its season"
    assert rows[("u1", "2024")]["record"] == {"wins": 0, "losses": 3, "ties": 0}, "the record is the regular season"


def test_luck_example():
    """4.8.6.3: actual wins minus the share of the other teams each week's score beat."""
    games = [P("2024", 1, 1, 4, 100.0, 70.0), P("2024", 1, 2, 3, 90.0, 80.0)]
    luck = {r["user"]: r["luck"] for r in LR._season_rows(ctx_for(games), {})}
    assert luck == {"u1": 0.0, "u2": round(1 - 2 / 3, 2), "u3": round(-1 / 3, 2), "u4": 0.0}


def test_season_records_example():
    """4.8.6, 4.8.6.1 and 4.8.6.5: holders, the regular-season basis and season results."""
    games = [P("2023", 1, 1, 2, 150.0, 60.0), P("2023", 2, 1, 3, 140.0, 70.0), P("2023", 3, 2, 3, 80.0, 75.0),
             P("2023", 15, 2, 3, 300.0, 10.0, LR.TOILET_FINAL)]
    places = {"2023": {1: 1, 2: 2, 3: 3}}
    settings = {("u1", "2023"): {"fpts": 290, "ppts": 330}}
    season = LR._season(ctx_for(games, places=places, playoff_teams=2, settings=settings), {("2023", 1, "u1"): 4.5, ("2023", 2, "u1"): 3.0})
    assert (season["most_points"][0]["user"], season["most_points"][0]["value"]) == ("u1", 290.0)
    assert next(e for e in season["most_points"] if e["user"] == "u2")["value"] == 140.0, "u2's 300-point toilet bowl final is not a regular-season game"
    assert season["fewest_points"][0]["user"] == "u2" and season["fewest_points"][0]["result"] == "second"
    four = [P("2023", 1, 1, 2, 100.0, 90.0), P("2023", 1, 3, 4, 80.0, 70.0)]
    places4 = {"2023": {1: 1, 2: 2, 3: 3, 4: 4}}
    result = lambda toilet: {r["user"]: r["result"] for r in LR._season_rows(ctx_for(four, places=places4, toilet=toilet), {})}  # noqa: E731
    assert result(True) == {"u1": "first", "u2": "second", "u3": "third", "u4": "toilet_bowl"}
    assert result(False)["u4"] == "last", "a league without a toilet bowl"
    assert season["most_points"][0]["result"] == "first" and season["best_record"][0]["record"] == {"wins": 2, "losses": 0, "ties": 0}
    assert season["bench"][0]["value"] == 40.0 and season["lineup_gained"][0]["value"] == 7.5
    assert season["best_missed"][0]["user"] == "u3" and season["worst_made"][0]["user"] == "u2"
    assert set(season) == set(LR.SEASON_KEYS)


def test_current_season_eligibility():
    """4.8.6.4: a part-season is left out of fewest points, worst record and the playoff-line records."""
    games = [P("2025", w, 1, 2, 120.0, 100.0) for w in range(1, 15)] + [P("2026", 1, 1, 2, 30.0, 20.0)]
    season = LR._season(ctx_for(games, places={"2025": {1: 1, 2: 2}}, current="2026"), {})
    for key in LR.FINISHED_ONLY:
        assert all(e["season"] != "2026" for e in season[key]), key
    assert any(e["season"] == "2026" and e["current"] for e in season["most_points"]), "still in the most and best records"
    assert next(e for e in season["most_points"] if e["season"] == "2026")["result"] == "in_progress"


# ---- the recorded dynasty league ----------------------------------------------------------------

def _names(store):
    return {u: m.name for u, m in managers_for_league(store, "dynasty").items()}


def test_champions_list_finished_seasons(seeded_store, dynasty_config):
    """4.8.3 and 4.8.3.1."""
    out = LR.records_export(seeded_store, dynasty_config, "dynasty", lineup={})
    names = _names(seeded_store)
    champs = {c["season"]: c for c in out["champions"]}
    assert [c["season"] for c in out["champions"]] == ["2025", "2024", "2023", "2022"], "newest first, no 2026"
    assert {s: names[c["champion"]] for s, c in champs.items()} == {
        "2022": "alwaysflexin", "2023": "Gixxersean1", "2024": "Gixxersean1", "2025": "corygraham12"}
    assert names[champs["2024"]["runner_up"]] == "Jdeguire" and champs["2024"]["record"] == {"wins": 12, "losses": 2, "ties": 0}
    assert all(c["last"] for c in out["champions"]) and out["toilet_bowl"] is False


def _war_file(store, season, players):
    write_json(store.root / "war" / "dynasty" / f"{season}.json", {"season": season, "players": players})


def test_player_records_example(seeded_store, dynasty_config):
    """3.6, 3.6.1, 3.6.2 and 3.6.4: any roster status, bench games, career scoring and the NFL team that week."""
    data = seeded_store.read_season("dynasty", "2025")
    row = next(r for r in data.matchups[1] if r.get("players"))
    starter = str(row["starters"][0])
    bench = next(str(p) for p in row["players"] if p not in row["starters"])
    weekly = lambda pts: [{"week": 1, "score": pts, "played": True, "p": 0.5}]  # noqa: E731
    _war_file(seeded_store, "2025", {
        starter: {"name": "Started Guy", "position": "QB", "war": 1.0, "weekly": weekly(30.0)},
        bench: {"name": "Bench Guy", "position": "WR", "war": 0.5, "weekly": weekly(36.0)},
        "99999": {"name": "Free Agent", "position": "RB", "war": 0.1, "weekly": weekly(49.3)},
    })
    seeded_store.write_stats("2025", 1, {starter: {"team": "BUF"}, bench: {"team": "CLE"}, "99999": {"team": "MIA"}})
    players = LR.records_export(seeded_store, dynasty_config, "dynasty", lineup={})["players"]
    best = players["best_games"]["ALL"]
    assert [(e["name"], e["status"], e["team"]) for e in best] == [
        ("Free Agent", "free_agent", "MIA"), ("Bench Guy", "bench", "CLE"), ("Started Guy", "started", "BUF")]
    assert best[0]["user"] is None and best[1]["user"]
    assert [e["name"] for e in players["bench_games"]["ALL"]] == ["Bench Guy"]
    assert [e["name"] for e in players["best_games"]["QB"]] == ["Started Guy"] and players["best_games"]["K"] == []
    career = players["career"]["ALL"][0]
    assert (career["name"], career["games"], career["points"], career["ppg"]) == ("Free Agent", 1, 49.3, 49.3)
    assert set(players) == {"best_games", "bench_games", "career", "championships"} and set(players["career"]) == set(LR.POSITIONS)


def test_championships_count_the_whole_roster(seeded_store, dynasty_config):
    """3.6.3 and 3.6.3.1: the title-game roster, bench and IR included; equal titles by WAR in title seasons."""
    data = seeded_store.read_season("dynasty", "2025")
    final = next(g for g in data.winners_bracket if g.get("p") == 1)
    rid = int(final["w"])
    week = BracketRules.from_league(data.league).week_for_round(int(final["r"]))
    row = next(r for r in data.matchups[week] if int(r["roster_id"]) == rid)
    benched = next(str(p) for p in row["players"] if p not in row["starters"])
    starter = str(row["starters"][0])
    path = seeded_store.season_dir("dynasty", "2025") / "rosters.json"
    rosters = read_json(path)
    for r in rosters:
        if int(r["roster_id"]) == rid:
            r["reserve"] = list(r.get("reserve") or []) + ["88888"]
    write_json(path, rosters)
    _war_file(seeded_store, "2025", {benched: {"name": "Low WAR", "position": "WR", "war": 0.5, "weekly": []},
                                     starter: {"name": "High WAR", "position": "QB", "war": 3.0, "weekly": []},
                                     "88888": {"name": "On IR", "position": "RB", "war": 9.0, "weekly": []}})
    champs = LR.records_export(seeded_store, dynasty_config, "dynasty", lineup={})["players"]["championships"]["ALL"]
    titled = {e["player_id"]: e for e in champs}
    assert benched in titled and "2025" in titled[benched]["seasons"], "a bench player earns the title"
    one_title = [e["player_id"] for e in sorted(champs, key=lambda e: e["rank"]) if e["value"] == titled[starter]["value"]]
    assert one_title.index(starter) < one_title.index(benched), "more WAR in the title season first"
    assert "88888" in titled and titled["88888"]["seasons"] == ["2025"], "a Player on IR earns the title"


def test_export_writes_league_records(seeded_store, dynasty_config, tmp_path):
    """4.8: the build writes one league records file per league."""
    from ffapp.export import export_site

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    records = json.loads((out / "dynasty" / "records.json").read_text(encoding="utf-8"))
    assert set(records) >= {"managers", "champions", "standings", "weekly", "season", "players", "current_season", "toilet_bowl"}
    assert set(records["weekly"]) == set(LR.WEEKLY_KEYS) and set(records["season"]) == set(LR.SEASON_KEYS)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["records"] == {"file": "dynasty/records.json"}
