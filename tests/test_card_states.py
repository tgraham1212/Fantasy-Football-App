"""Game card states (src/ffapp/card_states.py, docs/games-page-states.md): every state, the real
transitions, a snapshot skip and the edge rules."""

import pytest

from ffapp.card_states import DOC_NAMES, STATES, card_state, impact_ranked

S, P, F, N = "scheduled", "in_progress", "final", "none"


def state(starters_a, bench_a=(), starters_b=(S,), bench_b=(), kind="current", projected=False):
    return card_state(kind, projected, [{"starters": list(starters_a), "bench": list(bench_a)},
                                        {"starters": list(starters_b), "bench": list(bench_b)}])


# one fixture per state, by its documentation name
CASES = {
    "F1": dict(starters_a=(S,), kind="upcoming", projected=True),
    "F2": dict(starters_a=(S,), kind="upcoming"),
    "C": dict(starters_a=(S, S), bench_a=(S,)),
    "L1": dict(starters_a=(P, S)),
    "L2": dict(starters_a=(F, S), bench_a=(P,)),
    "P1": dict(starters_a=(F, S), bench_a=(S,)),
    "P2": dict(starters_a=(S, S), bench_a=(F,)),
    "O1": dict(starters_a=(F, F), bench_a=(S,), starters_b=(F,)),
    "O2": dict(starters_a=(F, F), bench_a=(P,), starters_b=(F,)),
    "O3": dict(starters_a=(F, F), bench_a=(F,), starters_b=(F,), bench_b=(F,)),
    "PW": dict(starters_a=(F,), kind="final"),
}


@pytest.mark.parametrize("doc", list(CASES))
def test_every_state(doc):
    code = state(**CASES[doc])
    assert DOC_NAMES[code] == doc
    assert code in STATES


@pytest.mark.parametrize("before, after, change", [
    ("C", "L1", dict(starters_a=(P, S))),                                   # 3: a starter kicks off
    ("C", "L2", dict(starters_a=(S, S), bench_a=(P,))),                     # 4: only a bench player kicks off
    ("L1", "L2", dict(starters_a=(F, S), bench_a=(P,))),                    # 5
    ("L1", "P1", dict(starters_a=(F, S))),                                  # 7
    ("L2", "P2", dict(starters_a=(S, S), bench_a=(F,))),                    # 9
    ("L2", "P1", dict(starters_a=(F, S), bench_a=(F,))),                    # 11
    ("P2", "L1", dict(starters_a=(P, S), bench_a=(F,))),                    # 13
    ("L1", "O1", dict(starters_a=(F, F), bench_a=(S,), starters_b=(F,))),   # 14
    ("L1", "O2", dict(starters_a=(F, F), bench_a=(P,), starters_b=(F,))),   # 15
    ("L1", "O3", dict(starters_a=(F, F), starters_b=(F,))),                 # 16: Monday night, everyone done together
    ("O1", "O2", dict(starters_a=(F,), bench_a=(P, S), starters_b=(F,))),   # 18
    ("O2", "O3", dict(starters_a=(F,), bench_a=(F,), starters_b=(F,))),     # 20
])
def test_real_transitions_land_on_the_right_state(before, after, change):
    assert DOC_NAMES[state(**change)] == after


def test_snapshot_skip_from_not_started_to_paused():
    """Thursday: the first refresh after kickoff sees the game already over (C -> P1, transition A)."""
    assert DOC_NAMES[state(starters_a=(F, S))] == "P1"


def test_bye_and_empty_slot_count_as_finished():
    assert DOC_NAMES[state(starters_a=(F, N), starters_b=(F, N))] == "O3"


def test_ruled_out_starter_finishes_only_when_his_game_ends():
    # a ruled-out starter is just scheduled until his team's game is over
    assert DOC_NAMES[state(starters_a=(F, S), starters_b=(F,))] == "P1"
    assert DOC_NAMES[state(starters_a=(F, F), starters_b=(F,))] == "O3"


def test_postponed_stays_open_and_cancelled_finishes():
    assert DOC_NAMES[state(starters_a=(F, S), starters_b=(F,))] == "P1"     # postponed: still scheduled
    assert DOC_NAMES[state(starters_a=(F, F), starters_b=(F,))] == "O3"     # cancelled: ESPN reports it over


def test_model_picks_play_no_part():
    """Only the real starters and bench are passed in, so a Model pick on the bench counts as bench."""
    assert DOC_NAMES[state(starters_a=(F, S), bench_a=(P,))] == "L2"


def test_impact_ranking_and_ties():
    rows = [{"name": "a", "position": "WR", "wpa": 0.13}, {"name": "b", "position": "QB", "wpa": 0.131},
            {"name": "c", "position": "RB", "wpa": -0.15}, {"name": "d", "position": "RB", "wpa": 0.31},
            {"name": "e", "position": "TE", "wpa": 0.23}, {"name": "f", "position": "K", "wpa": None}]
    assert [r["name"] for r in impact_ranked(rows)] == ["d", "e", "c", "b"]
