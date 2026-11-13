from ffapp.league import starter_slots
from ffapp.lineup import Candidate, best_lineup, lineup_points
from tests.fixtures import DYNASTY, REDRAFT, load

DYNASTY_SLOTS = starter_slots(load(f"league/{DYNASTY['2026']}.json"))
REDRAFT_SLOTS = starter_slots(load(f"league/{REDRAFT['2026']}.json"))


def c(pid, pos, pts, positions=None):
    return Candidate(pid, pos, tuple(positions or [pos]), pts)


def base_roster():
    return [
        c("qb1", "QB", 18.0), c("qb2", "QB", 15.0),
        c("rb1", "RB", 16.0), c("rb2", "RB", 12.0), c("rb3", "RB", 9.1),
        c("wr1", "WR", 15.0), c("wr2", "WR", 13.0), c("wr3", "WR", 11.4),
        c("te1", "TE", 8.0), c("te2", "TE", 5.0),
        c("k1", "K", 8.5), c("def1", "DEF", 7.0),
    ]


def test_flex_takes_the_better_of_third_rb_and_third_wr():
    lineup = best_lineup(DYNASTY_SLOTS, base_roster())
    by_slot = {}
    for s in lineup:
        by_slot.setdefault(s.slot, []).append(s.player_id)
    assert by_slot["FLEX"] == ["wr3"], "WR3 at 11.4 beats RB3 at 9.1"
    assert set(by_slot["RB"]) == {"rb1", "rb2"} and set(by_slot["WR"]) == {"wr1", "wr2"}
    assert by_slot["QB"] == ["qb1"] and by_slot["TE"] == ["te1"] and by_slot["DEF"] == ["def1"]
    assert "K" not in by_slot, "dynasty has no kicker slot"
    assert len(lineup) == len(DYNASTY_SLOTS)
    assert lineup_points(lineup) == 18 + 16 + 12 + 15 + 13 + 11.4 + 8 + 7


def test_redraft_layout_includes_kicker():
    lineup = best_lineup(REDRAFT_SLOTS, base_roster())
    slots = sorted(s.slot for s in lineup)
    assert slots == sorted(REDRAFT_SLOTS)
    assert next(s for s in lineup if s.slot == "K").player_id == "k1"


def test_bye_week_starter_is_replaced_by_bench_player():
    roster = base_roster()
    roster = [c("te1", "TE", 0.0) if x.player_id == "te1" else x for x in roster]
    lineup = best_lineup(DYNASTY_SLOTS, roster)
    assert next(s for s in lineup if s.slot == "TE").player_id == "te2"


def test_zero_projection_only_when_nothing_else_fits():
    roster = [c("qb1", "QB", 0.0), c("rb1", "RB", 10.0), c("rb2", "RB", 9.0), c("wr1", "WR", 8.0)]
    lineup = best_lineup(["QB", "RB", "FLEX"], roster)
    assert [s.player_id for s in lineup] == ["qb1", "rb1", "rb2"]


def test_unfilled_slots_are_left_empty_rather_than_misfilled():
    lineup = best_lineup(["QB", "QB", "DEF"], [c("qb1", "QB", 20.0), c("rb1", "RB", 15.0)])
    assert [(s.slot, s.player_id) for s in lineup] == [("QB", "qb1")]


def test_multi_position_player_can_fill_either_slot():
    roster = [c("x", "RB", 14.0, positions=["RB", "WR"]), c("wr1", "WR", 9.0), c("rb1", "RB", 13.0)]
    lineup = best_lineup(["RB", "WR"], roster)
    assert {(s.slot, s.player_id) for s in lineup} == {("RB", "x"), ("WR", "wr1")}
