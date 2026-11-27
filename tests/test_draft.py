"""Draft grades (league-draft): Steal/Reach against ADP, Hit/Bust against slot WAR, Unlucky, summaries, export."""
from __future__ import annotations

import json

import pytest

from ffapp.draft import REDRAFT, ROOKIE, adp_differences, draft_export, grade_draft, pick_label, season_facts, slot_war, summary
from ffapp.store import Store, write_json


def pick(no, pid, pos="WR", rnd=None, slot=None, roster=1, keeper=False, team="NYJ", first="Pat", last=None):
    rnd = rnd or (no - 1) // 12 + 1
    slot = slot or (no - 1) % 12 + 1
    return {"pick_no": no, "round": rnd, "draft_slot": slot, "roster_id": roster, "player_id": pid, "is_keeper": keeper or None,
            "metadata": {"position": pos, "team": team, "first_name": first, "last_name": last or f"P{pid}", "years_exp": "0"}}


def adp_of(**values):
    return {pid: {"position": pos, "adp_half_ppr": a, "adp_dynasty_half_ppr": a} for pid, (pos, a) in values.items()}


# -- 4.11.1 ADP difference, steals and reaches ----------------------------------------------------


def test_adp_difference():
    picks = [pick(70, "a")]
    out = adp_differences(picks, adp_of(a=("WR", 55.3)), REDRAFT)
    assert out["a"]["adp_diff"] == 14.7 and out["a"]["steal_reach"] == "steal"
    # rookie draft: pick number minus ADP rank among the draft's Players
    picks = [pick(1, "x"), pick(2, "y"), pick(3, "z")]
    out = adp_differences(picks, adp_of(x=("RB", 30.0), y=("WR", 10.0), z=("TE", 20.0)), ROOKIE)
    assert [out[k]["adp_rank"] for k in "xyz"] == [3, 1, 2]
    assert [out[k]["adp_diff"] for k in "xyz"] == [-2, 1, 1]


def test_steal_thresholds():
    assert adp_differences([pick(66, "a")], adp_of(a=("WR", 55.0)), REDRAFT)["a"]["steal_reach"] is None   # +11
    assert adp_differences([pick(67, "a")], adp_of(a=("WR", 55.0)), REDRAFT)["a"]["steal_reach"] == "steal"  # +12
    # rookie: ADP rank 24 taken with pick 34 is +10
    picks = [pick(n, str(n)) for n in range(1, 37)]
    adp = {str(n): {"position": "WR", "adp_dynasty_half_ppr": float(n)} for n in range(1, 37)}
    adp["34"]["adp_dynasty_half_ppr"] = 23.5   # ranks 24th among the draft's Players
    out = adp_differences(picks, adp, ROOKIE)
    assert out["34"]["adp_rank"] == 24 and out["34"]["adp_diff"] == 10 and out["34"]["steal_reach"] == "steal"


def test_reach_thresholds_and_position_exception():
    # a TE 12 picks early is a reach
    assert adp_differences([pick(40, "t", "TE")], adp_of(t=("TE", 52.0)), REDRAFT)["t"]["steal_reach"] == "reach"
    # an RB 15 picks early while the second-lowest ADP of the RBs still available is not
    adp = adp_of(r=("RB", 90.0), a=("RB", 85.0), b=("RB", 95.0), c=("RB", 99.0))
    assert adp_differences([pick(75, "r", "RB")], adp, REDRAFT)["r"]["steal_reach"] is None
    # ... but the third-lowest is
    adp["d"] = {"position": "RB", "adp_half_ppr": 80.0}
    assert adp_differences([pick(75, "r", "RB")], adp, REDRAFT)["r"]["steal_reach"] == "reach"
    # Players already taken are no longer available: once a and d are gone, r is the best RB left
    picks = [pick(60, "a", "RB"), pick(61, "d", "RB"), pick(75, "r", "RB")]
    assert adp_differences(picks, adp, REDRAFT)["r"]["steal_reach"] is None


def test_keepers_and_missing_adp_ungraded():
    picks = [pick(4, "k", keeper=True), pick(5, "n")]
    out = adp_differences(picks, adp_of(k=("RB", 40.0)), REDRAFT)
    assert out["k"]["adp_diff"] is None and out["k"]["steal_reach"] is None
    assert out["n"]["adp"] is None and out["n"]["steal_reach"] is None


# -- fixtures for the WAR side --------------------------------------------------------------------


def league(season, kind="redraft", status="complete", playoff=15):
    return {"season": season, "status": status, "league_id": f"L{season}", "draft_id": f"D{season}",
            "settings": {"type": 2 if kind == "rookie" else 0, "playoff_week_start": playoff, "start_week": 1}}


def write_season(store, key, season, kind, picks, war, through=14, status="complete", stats=None, users=None):
    base = store.season_dir(key, season)
    write_json(base / "league.json", league(season, kind, status))
    write_json(base / "users.json", users or [{"user_id": f"u{r}", "display_name": f"Mgr{r}"} for r in range(1, 13)])
    write_json(base / "rosters.json", [{"roster_id": r, "owner_id": f"u{r}"} for r in range(1, 13)])
    write_json(base / "brackets.json", {"winners": [], "losers": []})
    store.write_draft(key, season, {"draft": {"status": "complete", "type": "snake", "settings": {"rounds": 1, "teams": 12},
                                              "slot_to_roster_id": {str(s): s for s in range(1, 13)}},
                                    "picks": picks, "traded_picks": []})
    write_json(store.root / "war" / key / f"{season}.json", {"through_week": through, "players": {pid: {"war": w} for pid, w in war.items()}})
    for week in range(1, through + 1):
        rows = (stats or {}).get(week, {})
        write_json(store.stats_path(season, week), rows)


def full_stats(players, weeks=14, team="NYJ", skip=None):
    """Every Player played every week for ``team``, except the weeks in ``skip`` (pid -> weeks missed)."""
    out = {}
    for w in range(1, weeks + 1):
        out[w] = {pid: {"team": team, "stats": {"gp": 1.0}} for pid in players if w not in (skip or {}).get(pid, ())}
        out[w]["teammate"] = {"team": team, "stats": {"gp": 1.0}}
    return out


# -- 4.11.2 windows, slot WAR, hits, busts, unlucky -----------------------------------------------


def test_grading_window(tmp_path):
    store = Store(tmp_path)
    picks = [pick(1, "r", "RB", roster=1)]
    write_season(store, "dyn", "2025", "rookie", picks, {"r": 0.6}, stats=full_stats(["r"]))
    write_json(store.season_dir("dyn", "2026") / "league.json", league("2026", "rookie", "in_season"))
    write_json(store.root / "war" / "dyn" / "2026.json", {"through_week": 12, "players": {"r": {"war": 0.8}}})
    for w in range(1, 13):
        write_json(store.stats_path("2026", w), full_stats(["r"], 12, team="DAL")[w])
    facts = {s: season_facts(store, "dyn", s) for s in ("2025", "2026")}
    out = grade_draft(store.read_draft("dyn", "2025"), "2025", ROOKIE, {}, facts, [], {1: "u1"}, {1: "u1"})
    assert out[0]["war"] == 1.4, "WAR on every roster over the draft season and the next"
    assert out[0]["games"] == 26 and out[0]["games_possible"] == 26


def test_slot_war():
    history = [(n, float(n)) for n in range(1, 40)]
    assert slot_war(20, history, 6) == pytest.approx(sum(range(14, 27)) / 13)
    assert slot_war(20, [], 6) is None


def test_slot_war_scaled_in_season(tmp_path):
    store = Store(tmp_path)
    picks = [pick(20, "p")]
    write_season(store, "red", "2026", "redraft", picks, {"p": 0.10}, through=7, status="in_season", stats=full_stats(["p"], 7))
    facts = {"2026": season_facts(store, "red", "2026")}
    history = [(n, 0.90) for n in range(14, 27)]
    out = grade_draft(store.read_draft("red", "2026"), "2026", REDRAFT, {}, facts, history, {1: "u1"}, {})
    assert out[0]["slot_war"] == 0.45


def test_hit_and_bust_thresholds(tmp_path):
    store = Store(tmp_path)
    picks = [pick(7, "h"), pick(8, "e"), pick(9, "b")]
    write_season(store, "red", "2025", "redraft", picks, {"h": 3.26, "e": 1.80, "b": 0.40}, stats=full_stats(["h", "e", "b"]))
    facts = {"2025": season_facts(store, "red", "2025")}
    history = [(n, 1.23) for n in range(1, 20)]
    out = {p["player"]["id"]: p for p in grade_draft(store.read_draft("red", "2025"), "2025", REDRAFT, {}, facts, history, {1: "u1"}, {})}
    assert out["h"]["war_gap"] == 2.03 and out["h"]["hit_bust"] == "hit"
    assert out["e"]["war_gap"] == 0.57 and out["e"]["hit_bust"] is None
    assert out["b"]["war_gap"] == -0.83 and out["b"]["hit_bust"] == "bust"
    # rookie drafts need 1.0 WAR
    assert ROOKIE["hit"] == 1.0 and REDRAFT["hit"] == 0.75


def injured(store, season, pid, weeks, status="IR"):
    write_json(store.root / "injury-reports" / f"{season}.json", {"season": season, "weeks": {str(w): {pid: status} for w in weeks}})


def test_unlucky_pick(tmp_path):
    """4.11.2.3: more than half the team's games missed while IR, PUP or Out; a healthy absence is not unlucky."""
    store = Store(tmp_path)
    picks = [pick(1, "i")]
    write_season(store, "red", "2024", "redraft", picks, {"i": 0.0}, stats=full_stats(["i"], skip={"i": range(5, 15)}))
    injured(store, "2024", "i", range(5, 15))
    facts = {"2024": season_facts(store, "red", "2024")}
    out = grade_draft(store.read_draft("red", "2024"), "2024", REDRAFT, {}, facts, [(1, 1.0)], {1: "u1"}, {})
    assert (out[0]["games"], out[0]["games_possible"], out[0]["games_injured"]) == (4, 14, 10) and out[0]["hit_bust"] == "unlucky"
    # the same absences with no injury status: not unlucky
    write_json(store.root / "injury-reports" / "2024.json", {"season": "2024", "weeks": {}})
    facts = {"2024": season_facts(store, "red", "2024")}
    out = grade_draft(store.read_draft("red", "2024"), "2024", REDRAFT, {}, facts, [(1, 1.0)], {1: "u1"}, {})
    assert out[0]["games_injured"] == 0 and out[0]["hit_bust"] != "unlucky"
    # exactly half is not more than half
    injured(store, "2024", "i", range(5, 12), "Out")
    facts = {"2024": season_facts(store, "red", "2024")}
    out = grade_draft(store.read_draft("red", "2024"), "2024", REDRAFT, {}, facts, [(1, 1.0)], {1: "u1"}, {})
    assert out[0]["games_injured"] == 7 and out[0]["hit_bust"] != "unlucky"


def test_unlucky_hit_stays_a_hit(tmp_path):
    store = Store(tmp_path)
    picks = [pick(1, "i")]
    write_season(store, "red", "2025", "redraft", picks, {"i": 2.2}, stats=full_stats(["i"], skip={"i": range(6, 15)}))
    injured(store, "2025", "i", range(6, 15))
    facts = {"2025": season_facts(store, "red", "2025")}
    out = grade_draft(store.read_draft("red", "2025"), "2025", REDRAFT, {}, facts, [(1, 1.0)], {1: "u1"}, {})
    assert out[0]["hit_bust"] == "hit"


def test_unlucky_replaces_bust(tmp_path):
    store = Store(tmp_path)
    picks = [pick(1, "i")]
    write_season(store, "red", "2025", "redraft", picks, {"i": -0.2}, stats=full_stats(["i"], skip={"i": range(5, 15)}))
    injured(store, "2025", "i", range(5, 15), "PUP")
    facts = {"2025": season_facts(store, "red", "2025")}
    out = grade_draft(store.read_draft("red", "2025"), "2025", REDRAFT, {}, facts, [(1, 1.0)], {1: "u1"}, {})
    assert out[0]["war_gap"] == -1.2 and out[0]["hit_bust"] == "unlucky"


def test_team_games_follow_the_players_team_and_byes(tmp_path):
    store = Store(tmp_path)
    picks = [pick(1, "m")]
    stats = full_stats(["m"])
    for w in (6, 7):                      # missed two weeks after a trade, the new team still played
        stats[w].pop("m")
    stats[5]["m"]["team"] = "NYJ"
    for w in range(8, 15):
        stats[w]["m"]["team"] = "DAL"
        stats[w]["dal-mate"] = {"team": "DAL", "stats": {"gp": 1.0}}
    stats[10] = {k: v for k, v in stats[10].items() if v["team"] != "DAL"}   # Dallas bye in week 10
    write_season(store, "red", "2025", "redraft", picks, {"m": 0.5}, stats=stats)
    facts = {"2025": season_facts(store, "red", "2025")}
    out = grade_draft(store.read_draft("red", "2025"), "2025", REDRAFT, {}, facts, [], {1: "u1"}, {})
    assert out[0]["games_possible"] == 13 and out[0]["games"] == 11


# -- 4.11.3 position ranks, 4.11.4 summaries ------------------------------------------------------


def test_position_ranks(tmp_path):
    store = Store(tmp_path)
    picks = [pick(1, "w1", "WR"), pick(2, "r1", "RB"), pick(3, "w2", "WR"), pick(4, "q", "QB"), pick(5, "w3", "WR")]
    adp = adp_of(w1=("WR", 1.0), r1=("RB", 2.0), w2=("WR", 6.0), q=("QB", 3.0), w3=("WR", 4.0))
    write_season(store, "red", "2025", "redraft", picks, {"w1": 1.0, "r1": 2.0, "w2": 0.5, "q": 3.0, "w3": 2.5}, stats=full_stats([p["player_id"] for p in picks]))
    facts = {"2025": season_facts(store, "red", "2025")}
    out = {p["player"]["id"]: p for p in grade_draft(store.read_draft("red", "2025"), "2025", REDRAFT, adp, facts, [], {1: "u1"}, {})}
    assert (out["w3"]["adp_rank"], out["w3"]["adp_pos_rank"]) == (4, 2)
    assert (out["w3"]["war_rank"], out["w3"]["war_pos_rank"]) == (2, 1)


def graded(user, label, diff, gap, war, hb=None, pid="x"):
    return {"user": user, "label": label, "adp_diff": diff, "war_gap": gap, "war": war, "hit_bust": hb,
            "player": {"id": pid, "first": "A", "last": "B", "pos": "WR"}}


def test_managers_summary():
    picks = [graded("u1", "1.01", 10, 0.5, 2.0), graded("u1", "2.12", -2, -0.3, 0.1, "unlucky"), graded("u1", "3.01", 4, 1.1, 1.5),
             graded("u2", "1.02", None, None, 0.0)]
    rows = {r["user"]: r for r in summary(picks)}
    u1 = rows["u1"]
    assert (u1["picks"], u1["adp_diff"], u1["war_gap"], u1["war"], u1["unlucky"]) == (3, 4.0, 0.43, 3.6, 1)
    assert u1["best"]["label"] == "3.01"
    assert rows["u2"]["adp_diff"] is None and rows["u2"]["war_gap"] is None
    assert [r["user"] for r in summary(picks)] == ["u1", "u2"], "highest mean WAR above slot first"


def test_traded_pick_counts_for_its_maker(tmp_path):
    store = Store(tmp_path)
    picks = [pick(4, "t", roster=3, slot=4)]
    write_season(store, "dyn", "2025", "rookie", picks, {"t": 0.9}, stats=full_stats(["t"]))
    facts = {"2025": season_facts(store, "dyn", "2025"), "2026": None}
    out = grade_draft(store.read_draft("dyn", "2025"), "2025", ROOKIE, {}, facts, [], {3: "z28", 4: "cheef"}, {4: "cheef"})
    assert out[0]["user"] == "z28" and out[0]["slot_user"] == "cheef"
    assert [r["user"] for r in summary(out)] == ["z28"]


# -- 4.11 export ----------------------------------------------------------------------------------


def test_export_writes_draft_file(seeded_store, dynasty_config, tmp_path):
    """4.11: the build writes one draft file per league, an entry per season with a stored draft."""
    from ffapp.export import export_site
    from tests.test_export import simulate_weeks

    for season in seeded_store.seasons("dynasty"):
        if not seeded_store.has_draft("dynasty", season):
            pytest.skip("the seeded store has no drafts")
    simulate_weeks(seeded_store, dynasty_config, [0, 1])
    out = tmp_path / "site-data"
    export_site(seeded_store, dynasty_config, out)
    draft = json.loads((out / "dynasty" / "draft.json").read_text(encoding="utf-8"))
    assert sorted(draft["seasons"]) == ["2022", "2023", "2024", "2025", "2026"] and draft["rules"]["kind"] == "rookie"
    assert all(len(e["picks"]) == 36 for e in draft["seasons"].values())
    assert {p["user"] for e in draft["seasons"].values() for p in e["picks"]} <= set(draft["managers"])
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["leagues"][0]["draft"] == {"file": "dynasty/draft.json"}


def test_export_shape(tmp_path):
    store = Store(tmp_path / "data")
    picks = [pick(n, f"p{n}", roster=(n - 1) % 12 + 1) for n in range(1, 13)]
    for season in ("2024", "2025"):
        write_season(store, "red", season, "redraft", picks, {f"p{n}": 1.0 - n / 10 for n in range(1, 13)},
                     stats=full_stats([p["player_id"] for p in picks]))
    payload = draft_export(store, None, "red")
    assert sorted(payload["seasons"]) == ["2024", "2025"] and payload["latest"] == "2025"
    assert len(payload["seasons"]["2025"]["picks"]) == 12 and payload["all_drafts"]
    assert payload["rules"]["kind"] == "redraft"
    json.dumps(payload)


def test_snake_pick_labels_count_within_the_round():
    """A snake draft's 24th pick is made from slot 1 but is the 12th pick of round 2."""
    assert pick_label(2, 24, 12) == "2.12" and pick_label(2, 13, 12) == "2.01" and pick_label(1, 1, 12) == "1.01"


# -- keepers and keeper eligibility (redraft) -------------------------------------------------------

from types import SimpleNamespace  # noqa: E402

from ffapp.draft import keeper_eligible  # noqa: E402


def keeper_config(**seasons):
    return SimpleNamespace(leagues={"red": SimpleNamespace(keepers={s[1:]: tuple(ids) for s, ids in seasons.items()})})


def keeper_season(store, season, picks, rosters, status="complete", drops=()):
    """A redraft season with its draft, final rosters ({roster: [ids]}) and drops [(week, pid, roster)]."""
    write_season(store, "red", season, "redraft", picks, {p["player_id"]: 0.0 for p in picks}, status=status,
                 stats=full_stats([p["player_id"] for p in picks]))
    write_json(store.season_dir("red", season) / "rosters.json",
               [{"roster_id": r, "owner_id": f"u{r}", "players": rosters.get(r, [])} for r in range(1, 13)])
    weeks = {}
    for week, pid, rid in drops:
        weeks.setdefault(week, []).append({"type": "free_agent", "status": "complete", "adds": None, "drops": {pid: rid}})
    store.write_transactions("red", season, weeks)


def eligible(store, config):
    ke = keeper_eligible(store, config, "red")
    return {pl["player"]["id"]: pl for row in ke["rows"] for pl in row["players"]}, ke


def test_configured_keepers_marked(tmp_path):
    """4.11.5: configured keepers from 2025 on are keepers with no Steal/Reach or Hit/Bust grade."""
    store = Store(tmp_path / "data")
    picks = [pick(n, f"p{n}", roster=(n - 1) % 12 + 1) for n in range(1, 25)]
    keeper_season(store, "2025", picks, {})
    keeper_season(store, "2026", picks, {}, status="in_season")
    write_json(store.adp_path("2026"), {f"p{n}": {"position": "WR", "adp_half_ppr": 40.0} for n in range(1, 25)})
    payload = draft_export(store, keeper_config(s2026=["p13"], s2024=["p14"]), "red")
    by_id = {p["player"]["id"]: p for p in payload["seasons"]["2026"]["picks"]}
    assert by_id["p13"]["keeper"] and by_id["p13"]["steal_reach"] is None and by_id["p13"]["hit_bust"] is None
    assert not by_id["p14"]["keeper"], "only this season's list counts"
    assert by_id["p12"]["adp_diff"] == -28.0, "other picks are graded against ADP"


def test_keeper_eligible_needs_the_whole_season(tmp_path):
    """4.11.6: drafted and on the drafting roster through the championship week; a drop or trade away ends it."""
    store = Store(tmp_path / "data")
    picks = [pick(14, "kept", roster=1, rnd=2), pick(15, "dropped", roster=1, rnd=2), pick(16, "traded", roster=1, rnd=2),
             pick(17, "gone", roster=1, rnd=2)]
    keeper_season(store, "2026", picks, {1: ["kept", "dropped"], 2: ["traded"]}, drops=[(9, "dropped", 1), (16, "traded", 1)])
    found, ke = eligible(store, keeper_config())
    assert set(found) == {"kept"}, "dropped in week 9 (and picked back up), traded away in a playoff week, or no longer on the roster"
    assert ke["for_season"] == "2027" and ke["final"] is True


def test_keeper_price(tmp_path):
    """4.11.6.1: one round higher than drafted; round 1 not eligible."""
    store = Store(tmp_path / "data")
    picks = [pick(1, "first", roster=1, rnd=1), pick(80, "seventh", roster=1, rnd=7), pick(14, "second", roster=1, rnd=2)]
    keeper_season(store, "2026", picks, {1: ["first", "seventh", "second"]})
    found, _ = eligible(store, keeper_config())
    assert "first" not in found
    assert found["seventh"]["price_round"] == 6 and found["second"]["price_round"] == 1


def test_second_year_keeper(tmp_path):
    """4.11.6.2: kept this season costs a 1st; kept this season and last is not eligible."""
    store = Store(tmp_path / "data")
    picks25 = [pick(30, "twice", roster=1, rnd=3)]
    picks26 = [pick(13, "jsn", roster=1, rnd=2), pick(26, "twice", roster=1, rnd=3)]
    keeper_season(store, "2025", picks25, {1: ["twice"]})
    keeper_season(store, "2026", picks26, {1: ["jsn", "twice"]})
    found, _ = eligible(store, keeper_config(s2025=["twice"], s2026=["jsn", "twice"]))
    assert found["jsn"]["price_round"] == 1 and found["jsn"]["second_year"]
    assert "twice" not in found


def test_keeper_eligible_in_progress(tmp_path):
    """4.11.6.3: in season, eligibility runs through the latest week and is not final."""
    store = Store(tmp_path / "data")
    picks = [pick(20, "p", roster=1, rnd=2)]
    keeper_season(store, "2026", picks, {1: ["p"]}, status="in_season")
    found, ke = eligible(store, keeper_config())
    assert "p" in found and ke["final"] is False
