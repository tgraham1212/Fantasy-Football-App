"""Strength of Schedule (strength-of-schedule, 4.10): Weekly Ranks and Schedule Swap.

A four-team league with three regular-season weeks (two played, one upcoming from the Forecast) and a
playoff week that must be ignored.
"""

import json

import pytest

from ffapp import schedule_strength as SS
from ffapp.store import SeasonData

SCHEDULE = {1: [(1, 2), (3, 4)], 2: [(1, 3), (2, 4)], 3: [(1, 4), (2, 3)], 4: [(1, 2), (3, 4)]}
POINTS = {1: {1: 100.0, 2: 90.0, 3: 120.0, 4: 90.0}, 2: {1: 80.0, 2: 110.0, 3: 95.0, 4: 70.0}, 4: {1: 300.0, 2: 0.0, 3: 0.0, 4: 300.0}}
MEANS = {1: 100.0, 2: 105.0, 3: 95.0, 4: 90.0}
WIN = {(1, 2): 0.45, (1, 3): 0.47, (1, 4): 0.60, (2, 3): 0.62, (2, 4): 0.70, (3, 4): 0.55}
OWNERS = {1: "u1", 2: "u2", 3: "u3", 4: "u4"}


def win_share(a, b):
    return WIN[(a, b)] if (a, b) in WIN else round(1 - WIN[(b, a)], 3)


def season(last_scored=2):
    matchups = {}
    for week, pairs in SCHEDULE.items():
        rows = []
        for m, pair in enumerate(pairs, start=1):
            for rid in pair:
                rows.append({"roster_id": rid, "matchup_id": m, "points": (POINTS.get(week) or {}).get(rid, 0.0)})
        matchups[week] = rows
    league = {"season": "2026", "league_id": "L", "settings": {"start_week": 1, "playoff_week_start": 4, "last_scored_leg": last_scored}}
    return SeasonData(league=league, users=[], rosters=[], matchups=matchups)


def forecast():
    teams = list(MEANS)
    return {"upcoming": {"3": {"mean": {str(t): MEANS[t] for t in teams},
                               "win": {str(a): {str(b): win_share(a, b) for b in teams if b != a} for a in teams}}}}


def weeks():
    return SS.season_weeks(season(), forecast())


def test_regular_season_only():
    """4.10.1: playoff weeks are left out."""
    assert [w.week for w in weeks()] == [1, 2, 3]
    assert SS.season_export(season(), OWNERS, forecast())["weeks"] == [1, 2, 3]


def test_weekly_rank_ties_share_the_better_rank():
    """4.10.2: rank = 1 + teams that scored more, so equal scores share the better rank."""
    rank = SS.weekly_ranks(weeks())
    assert rank[(1, 3)] == 1 and rank[(1, 1)] == 2
    assert rank[(1, 2)] == rank[(1, 4)] == 3, "both scored 90"


def test_opponent_rank_averages():
    """4.10.2.1: team 1 faced ranks 3 and 2 (played) and 4 (upcoming)."""
    row = next(r for r in SS.season_export(season(), OWNERS, forecast())["ranks"] if r["user"] == "u1")
    assert (row["played"], row["upcoming"], row["season"]) == (2.5, 4.0, 3.0)
    assert [c["opp_rank"] for c in row["cells"]] == [3, 2, 4]
    assert [c["upcoming"] for c in row["cells"]] == [False, False, True]


def test_weekly_ranks_order():
    """4.10.2.2: lowest season mean first, as the hardest schedule; equal means share a rank."""
    ranks = SS.season_export(season(), OWNERS, forecast())["ranks"]
    means = [r["season"] for r in ranks]
    assert means == sorted(means)
    for r in ranks:
        assert r["rank"] == 1 + sum(m < r["season"] for m in means)


def test_upcoming_weeks_use_the_forecast():
    """4.10.3: a week not yet final takes the Forecast's mean scores; with no Forecast it is left out."""
    week3 = weeks()[-1]
    assert week3.upcoming and week3.points == MEANS
    assert [w.week for w in SS.season_weeks(season(), None)] == [1, 2]
    assert SS.season_export(season(last_scored=0), OWNERS, None) is None, "no played weeks and no Forecast"


def test_swap_substitutes_the_schedule_manager():
    """4.10.4: team 1 on team 2's schedule plays team 2 in week 1, when team 2's opponent is team 1."""
    ws = weeks()
    assert SS.swap_wins(ws, 1, 2) == pytest.approx(1.0 + 1.0 + win_share(1, 3))  # beat 2, beat 4, then P(1 > 3)
    own = SS.swap_wins(ws, 1, 1)
    assert own == pytest.approx(1.0 + 0.0 + win_share(1, 4)), "own schedule: actual wins plus projected wins"


def test_played_week_wins():
    """4.10.4.1: 1 for more points, 0.5 for equal, 0 for fewer."""
    week1 = weeks()[0]
    assert SS.game_win(week1, 1, 2) == 1.0
    assert SS.game_win(week1, 2, 4) == 0.5
    assert SS.game_win(week1, 2, 1) == 0.0


def test_upcoming_week_wins_use_pair_probabilities():
    """4.10.4.2: an upcoming game counts the pair's win share."""
    assert SS.game_win(weeks()[-1], 1, 3) == pytest.approx(0.47)


def test_difficulty_index():
    """4.10.4.3: mean wins over all N schedules, own included, minus own wins."""
    ws = weeks()
    rows = {r["user"]: r for r in SS.season_export(season(), OWNERS, forecast())["swap"]["rows"]}
    for rid, user in OWNERS.items():
        table = [SS.swap_wins(ws, rid, b) for b in OWNERS]
        own = SS.swap_wins(ws, rid, rid)
        assert rows[user]["index"] == pytest.approx(sum(table) / len(table) - own, abs=0.005)
        assert rows[user]["own"] == pytest.approx(own, abs=0.005)


def test_swap_order_and_range():
    """4.10.4.4: highest index first, with the lowest and highest wins across schedules."""
    swap = SS.season_export(season(), OWNERS, forecast())["swap"]
    indexes = [r["index"] for r in swap["rows"]]
    assert indexes == sorted(indexes, reverse=True)
    assert swap["order"] == [r["user"] for r in swap["rows"]], "schedule columns follow the row order"
    for r in swap["rows"]:
        assert (r["lo"], r["hi"]) == (min(r["wins"]), max(r["wins"]))
        assert r["wins"][swap["order"].index(r["user"])] == r["own"], "own schedule on the diagonal"


def test_export_writes_schedule_file(seeded_store, dynasty_config, tmp_path):
    """4.10: the build writes one strength of schedule file per league, an entry per season with weeks."""
    from ffapp.export import export_site
    from tests.test_export import simulate_weeks

    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    schedule = json.loads((out / "dynasty" / "schedule.json").read_text(encoding="utf-8"))
    assert set(schedule) >= {"managers", "seasons", "current_season"}
    assert schedule["seasons"], "every stored season with weeks has an entry"
    for entry in schedule["seasons"].values():
        assert set(entry) == {"weeks", "played_through", "ranks", "swap"}
        users = {r["user"] for r in entry["ranks"]}
        assert users <= set(schedule["managers"]) and len(entry["swap"]["rows"]) == len(users)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["schedule"] == {"file": "dynasty/schedule.json"}
