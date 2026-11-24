"""Behaviour of the Games sub-tab's week control and linked full lineups (games-page 2.1.1.x, 2.1.5.1.1),
checked in the browser against the published games index."""

from __future__ import annotations

from tests.layout.test_layout import open_view


def games_index(page) -> dict:
    return page.evaluate("async () => (await fetch('data/dynasty/games/index.json')).json()")


def shown_week(page) -> int:
    return int(page.eval_on_selector("#games-week", "s => s.value"))


def test_opens_on_the_current_week(open_page):
    """2.1.1"""
    page, _, _ = open_view(open_page, "games", 1280)
    assert shown_week(page) == games_index(page)["current"]


def test_week_list_covers_every_week_of_the_season(open_page):
    """2.1.1.1: every regular-season and playoff week, in order."""
    page, _, _ = open_view(open_page, "games", 1280)
    options = page.eval_on_selector_all("#games-week option", "o => o.map(x => Number(x.value))")
    assert options == [w["week"] for w in games_index(page)["weeks"]]
    assert options == list(range(1, len(options) + 1)) and len(options) == 17, "14 regular-season weeks and 3 playoff rounds"


def test_arrows_step_one_week_and_stop_at_the_ends(open_page):
    """2.1.1.2"""
    page, _, _ = open_view(open_page, "games", 1280)
    weeks = [w["week"] for w in games_index(page)["weeks"]]
    start = shown_week(page)
    page.click("#games-prev")
    page.wait_for_timeout(300)
    assert shown_week(page) == start - 1
    page.click("#games-next")
    page.wait_for_timeout(300)
    assert shown_week(page) == start
    page.select_option("#games-week", str(weeks[0]))
    page.wait_for_timeout(300)
    assert page.is_disabled("#games-prev") and not page.is_disabled("#games-next")
    page.select_option("#games-week", str(weeks[-1]))
    page.wait_for_timeout(300)
    assert page.is_disabled("#games-next") and not page.is_disabled("#games-prev")


def test_full_lineup_opens_both_teams_together(open_page):
    """2.1.5.1.1: one team's Full Lineup control opens and closes both teams' lineups in that card."""
    page, _, _ = open_view(open_page, "games-final", 1280)
    card = page.locator(".game-card:has(details.lineup)").first
    assert card.count() == 1, "a card with Full Lineup controls"
    details = card.locator("details.lineup")
    assert details.count() == 2
    details.nth(0).locator("summary").click()
    page.wait_for_timeout(200)
    assert details.nth(0).evaluate("d => d.open") and details.nth(1).evaluate("d => d.open"), "both lineups open"
    details.nth(1).locator("summary").click()
    page.wait_for_timeout(200)
    assert not details.nth(0).evaluate("d => d.open") and not details.nth(1).evaluate("d => d.open"), "both lineups close"
