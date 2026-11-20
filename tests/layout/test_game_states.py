"""Every Games page card state looks as decided (docs/games-page-states.md): LIVE badge, chips, winner
check, Model / Actual toggle, and key players or the full lineup, on the fixture week with one card
per state, at every tested width and with the wide-font pass."""

from __future__ import annotations

import pytest

from ffapp.card_states import DOC_NAMES, STATES, impact_ranked
from tests.layout.conftest import WIDE_FONT, WIDTHS
from tests.layout.game_states import EXPECT
from tests.layout.test_layout import OVERFLOW_JS, open_view

LOOK_JS = """() => [...document.querySelectorAll('.game-card[data-state]')].map((c) => ({
  state: c.dataset.state,
  badge: !!c.querySelector('.live-badge'),
  chips: [...c.querySelectorAll('.state-chip')].map((x) => x.textContent.trim()),
  check: !!c.querySelector('.check'),
  toggle: !!c.querySelector('.view-toggle'),
  key: c.querySelectorAll('ul.key').length,
  full: c.querySelectorAll('ul.lineup-full').length,
  summary: c.querySelectorAll('details.lineup summary').length,
  keys: [...c.querySelectorAll('ul.key')].map((u) => [...u.querySelectorAll('.nm')].map((n) => n.dataset.full || n.textContent.trim())),
}))"""


def _lineup_ok(card, lineup):
    if lineup == "full":
        return card["full"] == 2 and card["key"] == 0 and card["summary"] == 0
    return card["key"] == 2 and card["summary"] == 2 and card["full"] == 0    # key (and impact, Actual view)


@pytest.mark.parametrize("wide", [False, True], ids=["font", "wide-font"])
@pytest.mark.parametrize("width", WIDTHS)
def test_every_state_looks_as_decided(open_page, width, wide):
    page, _, _ = open_view(open_page, "games-states", width)
    if wide:
        page.add_style_tag(content=WIDE_FONT)
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        page.wait_for_timeout(300)
    cards = {c["state"]: c for c in page.evaluate(LOOK_JS)}
    assert sorted(cards) == sorted(STATES), "the fixture shows one card per state"
    problems = []
    for state, want in EXPECT.items():
        got = cards[state]
        name = DOC_NAMES[state]
        for field in ("badge", "check", "toggle"):
            if got[field] != want[field]:
                problems.append(f"{name}: {field} {got[field]}, expected {want[field]}")
        if got["chips"] != want["chips"]:
            problems.append(f"{name}: chips {got['chips']}, expected {want['chips']}")
        if not _lineup_ok(got, want["lineup"]):
            problems.append(f"{name}: lineup shows key {got['key']} / full {got['full']} / control {got['summary']}, expected {want['lineup']}")
    problems += [f"overflow: {p}" for p in page.evaluate(OVERFLOW_JS, ["main section.card", ".game-card"])]
    assert not problems, f"{width}px:\n  " + "\n  ".join(problems)


def test_finished_states_rank_key_players_by_impact(open_page):
    """O1 to O3 and PW: the Actual view's key players are the four largest win probabilities added."""
    from tests.layout.game_states import fixture_week

    page, _, _ = open_view(open_page, "games-states", 1280)
    week = fixture_week()
    cards = {c["state"]: c for c in page.evaluate(LOOK_JS)}
    for g in week["games"]:
        if EXPECT[g["state"]]["lineup"] != "impact":
            continue
        want = [[r["name"] for r in impact_ranked([r for r in t["lineup"] if r.get("player_id")])] for t in g["views"]["actual"]["teams"]]
        assert cards[g["state"]]["keys"] == want, DOC_NAMES[g["state"]]


def test_finished_states_show_the_full_lineup_in_the_model_view(open_page):
    page, _, _ = open_view(open_page, "games-states", 1280)
    for state in ("starters_done", "final"):
        page.locator(f".game-card[data-state='{state}'] .view-toggle button[data-view='model']").click()
        page.wait_for_timeout(300)
        card = next(c for c in page.evaluate(LOOK_JS) if c["state"] == state)
        assert _lineup_ok(card, "full"), f"{DOC_NAMES[state]} Model view: {card}"
