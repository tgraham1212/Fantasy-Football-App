"""The layout check's registry: every control on the site, the view it lives in, the states the
check drives it through, and what each control is designed to change.

Every new button, toggle, selector, expander or link on the site must be listed here
(test_every_control_is_listed fails otherwise). A control's declared effect:

- ``regions``: elements inside these may change in any way (a page's content when a tab switches);
- ``grow``: these may change height only (a card whose Full Lineup opens);
- ``below``: anything whose top is at or under the bottom of this element (``"self"`` = the
  control) may move down or up (content pushed by an expander).

Everything else, the control itself included, must keep its position and size, and no state
may make the page scroll sideways.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

LEAGUE = "dynasty"
SITE_DATA = Path(__file__).resolve().parents[2] / "site" / "data"  # what the layout check serves
FINAL_WEEK = 10  # a finished week: cards have the Model | Actual toggle

# Elements whose boxes are compared before and after every state.
LANDMARKS = (
    "header.top > *", "#refresh-btn", "#theme-toggle", "#subtabs", "#subtabs button",
    "main section.card", ".card-head", "#games-controls > *", ".game-card", ".game-card .view-toggle",
    ".war-table", "#war-controls", "#war-dialog", "#war-dialog .dialog-head", "#war-dialog-close",
    "#outcome-switcher", "footer", "#positions-controls", ".pos-card",
    "#mgr-picker", ".mgr-bar", ".mgr-season", ".mgr-cardtabs", ".mgr-card",
)
# Elements that must stay inside the screen horizontally.
INSIDE = ("header.top > *", "#refresh-note", "#version-note", "#subtabs")
# What the coverage test treats as a control.
CONTROL_QUERY = "button, select, summary, a[href], [tabindex]:not([tabindex='-1'])"


@dataclass(frozen=True)
class View:
    name: str
    path: str
    setup: Callable | None = None  # extra steps after the page loads


def _war_all(page):
    page.select_option("#war-season", "all")
    page.wait_for_timeout(400)


def _war_dialog(page):
    page.click("button.expand")
    page.wait_for_timeout(300)


def _games_final(page):
    page.wait_for_selector(".view-toggle")


def _games_states(page):
    """The fixture week with one card per state (tests/layout/game_states.py)."""
    from tests.layout.game_states import open_states
    open_states(page)


PAST_SEASON = "2024"
RETIRED = "TateFM"  # a dynasty manager who left after 2023


def _moves_card(page):
    """On a phone only one card shows: open the Moves card (desktop shows all four anyway)."""
    page.locator("[data-card-tab='moves']").first.evaluate("e => e.click()")
    page.wait_for_timeout(200)


def _positions_past(page):
    page.select_option("#positions-season", PAST_SEASON)
    page.wait_for_timeout(500)


VIEWS = {
    "predictions": View("predictions", f"index.html#{LEAGUE}"),
    "games": View("games", f"index.html#{LEAGUE}/games"),
    "games-final": View("games-final", f"index.html#{LEAGUE}/games/{FINAL_WEEK}", _games_final),
    "games-states": View("games-states", f"index.html#{LEAGUE}/games", _games_states),
    "positions": View("positions", f"index.html#{LEAGUE}/positions"),
    "positions-past": View("positions-past", f"index.html#{LEAGUE}/positions", _positions_past),
    "war": View("war", f"index.html#{LEAGUE}/war"),
    "war-all": View("war-all", f"index.html#{LEAGUE}/war", _war_all),
    "war-dialog": View("war-dialog", f"index.html#{LEAGUE}/war", _war_dialog),
    "calibration": View("calibration", "calibration.html"),
    "managers": View("managers", f"index.html#{LEAGUE}/managers"),
    "managers-retired": View("managers-retired", f"index.html#{LEAGUE}/managers/{RETIRED}"),
    "managers-redraft": View("managers-redraft", "index.html#redraft/managers"),
    "managers-moves": View("managers-moves", f"index.html#{LEAGUE}/managers", _moves_card),
}


@dataclass(frozen=True)
class State:
    name: str
    act: Callable  # act(page, relay, ctx)


@dataclass(frozen=True)
class Control:
    name: str
    view: str
    selector: str
    states: tuple[State, ...] = ()
    regions: tuple[str, ...] = ()
    grow: tuple[str, ...] = ()
    below: str | None = None
    self_moves: bool = False  # the control itself is replaced or hidden by its own action


# -- actions -------------------------------------------------------------------------------------

def click(selector: str, wait: int = 400):
    """A script click: unlike a pointer click it does not scroll the control into view, so the
    page and any scrolling table stay where the visitor had them."""
    def act(page, relay, ctx):
        page.locator(selector).first.evaluate("e => e.click()")
        page.wait_for_timeout(wait)
    return act


def focus_first(selector: str):
    """Keyboard focus without scrolling (SVG dots have no click() method; focus shows the popup)."""
    def act(page, relay, ctx):
        page.locator(selector).first.evaluate("e => e.focus({ preventScroll: true })")
        page.wait_for_timeout(200)
    return act


def blur_active(page, relay, ctx):
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(200)


def select_first_other(selector: str):
    def act(page, relay, ctx):
        values = page.eval_on_selector(selector, "s => [...s.options].map(o => o.value).filter(v => v !== s.value)")
        page.select_option(selector, values[0])
        page.wait_for_timeout(500)
    return act


def select_value(selector: str, value: str):
    """Choose an option by script, as a visitor's change would (like ``click``: no actionability
    wait, which timed out on the CI runner's WebKit while the select was on screen)."""
    def act(page, relay, ctx):
        page.locator(selector).first.evaluate("(s, v) => { s.value = v; s.dispatchEvent(new Event('change', { bubbles: true })); }", value)
        page.wait_for_timeout(500)
    return act


def refresh_answer(code, body=None):
    def act(page, relay, ctx):
        relay.refresh = "abort" if code == "abort" else (code, body or {})
        page.locator("#refresh-btn").evaluate("e => e.click()")
        page.wait_for_timeout(500)
    return act


def relay_status(status):
    """The relay reports this /status (held after a press, a refresh running, games live)."""
    def act(page, relay, ctx):
        relay.status = status
        page.reload()
        page.wait_for_load_state("networkidle")
        ctx["setup"](page)
        page.wait_for_timeout(400)
    return act


relay_held = relay_status({"available": False, "minutes": 3, "reason": "cooldown", "mode": "quiet"})


def live_bundle(site_data: Path, league: str, week: int, label: str, generated_at: str = "2099-01-01T00:00:00+00:00") -> dict:
    """A live bundle as the hot run builds it, from the deployed files, with week ``week``'s label in
    the games index changed to ``label`` so a test can see which copy the page shows."""
    games_index = json.loads((site_data / league / "games" / "index.json").read_text(encoding="utf-8"))
    for entry in games_index["weeks"]:
        if entry["week"] == week:
            entry["label"] = label
    week_file = f"{league}/games/week_{week:02d}.json"
    return {
        "generated_at": generated_at,
        "games": {"2099-01-KC@BUF": "in_progress"},
        "files": {
            f"{league}.json": json.loads((site_data / f"{league}.json").read_text(encoding="utf-8")),
            f"{league}/games/index.json": games_index,
            week_file: json.loads((site_data / week_file).read_text(encoding="utf-8")),
        },
    }


def new_bundle(page, relay, ctx):
    """The hot run writes a newer live bundle: the page swaps it in place."""
    relay.live = live_bundle(SITE_DATA, LEAGUE, FINAL_WEEK, "Week 10 (live)")
    _trigger_check(page)


def _trigger_check(page):
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    page.wait_for_timeout(800)


def new_data(page, relay, ctx):
    """A newer data/index.json is deployed: the page swaps it in place."""
    def handle(route):
        body = json.loads(route.fetch().text())
        body["last_refresh"] = "2099-01-01T00:00:00+00:00"
        route.fulfill(status=200, json=body)
    page.route("**/data/index.json", handle)
    _trigger_check(page)


def new_version(page, relay, ctx):
    """New site code is deployed: the page pins the new version note."""
    page.route("**/version.json", lambda route: route.fulfill(status=200, json={"code": "0000000000"}))
    _trigger_check(page)


# failures first: a started refresh disables the button for the cooldown
REFRESH_STATES = (
    State("failed", refresh_answer(500)),
    State("unreachable", refresh_answer("abort")),
    State("started", refresh_answer(202, {"started": True, "minutes": 5, "mode": "quiet"})),
)
UPDATE_STATES = (State("new data", new_data), State("new bundle", new_bundle), State("new version", new_version))
HELD_STATES = (
    State("held", relay_held),
    State("running", relay_status({"available": False, "minutes": 1, "reason": "running", "mode": "quiet"})),
    State("live", relay_status({"available": False, "minutes": 0, "reason": "live", "mode": "live"})),
)


# -- the registry ------------------------------------------------------------------------------------

CONTROLS: tuple[Control, ...] = (
    # header, on every page
    Control("refresh", "predictions", "#refresh-btn", REFRESH_STATES),
    Control("refresh held", "predictions", "#refresh-btn", HELD_STATES),
    Control("refresh (calibration)", "calibration", "#refresh-btn", REFRESH_STATES),
    Control("theme", "predictions", "#theme-toggle", (State("toggled", click("#theme-toggle")), State("back", click("#theme-toggle")))),
    Control("theme (calibration)", "calibration", "#theme-toggle", (State("toggled", click("#theme-toggle")),)),
    Control("league switcher", "predictions", "#league-switcher button",
            (State("other league", click("#league-switcher button[aria-pressed='false']", 900)),),
            regions=("#page-predictions", "#page-games", "#page-positions", "#page-managers", "#page-war"), below="#subtabs"),
    Control("odds link", "calibration", ".pages a.nav-link"),
    Control("footer link", "predictions", "footer a"),
    Control("footer link (calibration)", "calibration", "footer a"),
    # on a phone the sub-tab strip scrolls to keep the picked tab in view, so the tabs move inside it
    Control("sub-tabs", "predictions", "#subtabs button",
            (State("games", click("#subtabs [data-page='games']", 900)), State("positions", click("#subtabs [data-page='positions']", 900)),
             State("managers", click("#subtabs [data-page='managers']", 900)),
             State("war", click("#subtabs [data-page='war']", 900)), State("predictions", click("#subtabs [data-page='predictions']", 900))),
            regions=("#page-predictions", "#page-games", "#page-positions", "#page-managers", "#page-war", "#subtabs"), below="self", self_moves=True),
    Control("update check", "predictions", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("update check (games)", "games-final", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("update check (calibration)", "calibration", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("version note", "predictions", "#version-note button"),
    # scrolling table boxes are focusable so keyboard users can scroll them (no states of their own)
    Control("table scroll region", "predictions", ".table-wrap[tabindex], .war-scroll[tabindex]"),

    # Predictions page
    Control("odds sort", "predictions", "#odds-table thead button.sort",
            (State("sorted", click("#odds-table thead button.sort >> nth=2")), State("flipped", click("#odds-table thead button.sort >> nth=2")))),
    Control("odds row", "predictions", "#odds-body tr",
            (State("highlight", click("#odds-body tr >> nth=0")), State("clear", click("#odds-body tr >> nth=0"))),
            grow=("main section.card",), below="#chart-note"),
    Control("chart metric", "predictions", "#metric-switcher button",
            (State("other metric", click("#metric-switcher button[aria-pressed='false']")),),
            grow=("main section.card",), below="#metric-switcher"),
    Control("rating metric", "predictions", "#rating-metric button",
            (State("other metric", click("#rating-metric button[aria-pressed='false']")),),
            grow=("main section.card",), below="#rating-card .card-head"),
    # the range buttons sit below the rating chart; picking a range redraws the chart above them
    Control("rating range", "predictions", "#rating-range button",
            (State("other range", click("#rating-range button[aria-pressed='false']")),),
            grow=("main section.card",), below="#rating-range"),

    # Games page
    Control("week arrows", "games", "#games-prev, #games-next",
            (State("previous", click("#games-prev", 700)), State("next", click("#games-next", 700))),
            regions=("#games-content",), grow=("main section.card",), below="#games-note"),
    Control("week select", "games", "#games-week", (State("other week", select_first_other("#games-week")),),
            regions=("#games-content",), grow=("main section.card",), below="#games-note"),
    # the Full Lineup control exists only in states with key players: checked on the fixture week, which always has them
    Control("full lineup", "games-states", "details.lineup summary",
            (State("open", click("details.lineup summary")), State("close", click("details.lineup summary"))),
            grow=(".game-card",), below="self"),
    Control("lineup view", "games-final", ".view-toggle button",
            (State("model", click(".game-card[data-card='0'] .view-toggle button[data-view='model']")),
             State("actual", click(".game-card[data-card='0'] .view-toggle button[data-view='actual']"))),
            grow=(".game-card",), below=".game-card[data-card='0'] .view-toggle", self_moves=False),
    Control("full lineup (final)", "games-final", "details.lineup summary",
            (State("open", click("details.lineup summary")),), grow=(".game-card",), below="self"),

    # Positions page
    Control("positions season", "positions", "#positions-season", (State("other season", select_first_other("#positions-season")),),
            regions=("#positions-content", "#positions-note"), grow=("main section.card",), below="#positions-controls"),
    Control("position dot", "positions", ".pos-dot",
            (State("focused", focus_first(".pos-card[data-pos='RB'] .pos-dot")), State("blurred", blur_active),
             State("injured", focus_first(".pos-dot[data-status]")), State("taxi", focus_first(".pos-dot[data-taxi]"))),
            # a focused dot draws a thicker outline (its designed focus state); Firefox counts it in the box
            regions=(".pos-pop",), self_moves=True),
    Control("position dot (past)", "positions-past", ".pos-dot",
            (State("focused", focus_first(".pos-card[data-pos='QB'] .pos-dot")),), regions=(".pos-pop",), self_moves=True),

    # Player WAR page
    Control("war season", "war", "#war-season", (State("other season", select_first_other("#war-season")),),
            regions=("#war-content", "#war-note", "#war-controls"), grow=("main section.card",), below="#war-controls"),
    Control("war mode", "war-all", "#war-mode button",
            (State("careers", click("#war-mode button[aria-pressed='false']", 600)),),
            regions=("#war-content", "#war-note"), grow=("main section.card",), below="#war-controls"),
    Control("full list", "war", "button.expand", (State("open", click("button.expand")),), regions=("#war-dialog",)),
    Control("full list sort", "war-dialog", "#war-full thead button.sort",
            (State("sorted", click("#war-full thead button.sort >> nth=4")), State("flipped", click("#war-full thead button.sort >> nth=4"))),
            regions=("#war-full",)),
    Control("full list close", "war-dialog", "#war-dialog-close", (State("closed", click("#war-dialog-close")),),
            regions=("#war-dialog",), self_moves=True),

    # Managers page
    Control("manager arrows", "managers", "#mgr-prev, #mgr-next",
            (State("previous", click("#mgr-prev", 600)), State("next", click("#mgr-next", 600))), regions=("#mgr-content",), below="#mgr-picker"),
    Control("manager select", "managers", "#mgr-select", (State("other manager", select_first_other("#mgr-select")),), regions=("#mgr-content",), below="#mgr-picker"),
    Control("manager link", "managers", "#mgr-content a[data-manager]",
            (State("rival", click("#mgr-content .mgr-fact a[data-manager]", 600)),), regions=("#mgr-content",), below="#mgr-picker", self_moves=True),
    Control("manager page link", "managers", "#mgr-content a[data-goto], #mgr-content a.mgr-story, #mgr-content a.mgr-feat"),
    Control("history tabs", "managers", ".mgr-htabs button",
            (State("head to head", click(".mgr-htabs [data-htab='h2h']")), State("records", click(".mgr-htabs [data-htab='rec']")),
             State("history", click(".mgr-htabs [data-htab='hist']"))), regions=(".mgr-history .mgr-scroll",), below=".mgr-cardtabs"),
    Control("card tabs", "managers", ".mgr-cardtabs button",
            (State("history", click(".mgr-cardtabs [data-card-tab='history']")), State("moves", click(".mgr-cardtabs [data-card-tab='moves']")),
             State("news", click(".mgr-cardtabs [data-card-tab='news']")), State("roster", click(".mgr-cardtabs [data-card-tab='roster']"))),
            regions=(".mgr-cards",), below=".mgr-cardtabs"),
    Control("moves season arrows", "managers-moves", ".mgr-moves-prev, .mgr-moves-next",
            (State("older", click(".mgr-moves-prev")), State("newer", click(".mgr-moves-next"))), regions=("#mgr-moves",), below=".mgr-cardtabs"),
    Control("moves season", "managers-moves", "#mgr-moves-season", (State("other season", select_first_other("#mgr-moves-season")),), regions=("#mgr-moves",), below=".mgr-cardtabs"),
    Control("moves all seasons", "managers-moves", "#mgr-moves-season", (State("all seasons", select_value("#mgr-moves-season", "all")),),
            regions=("#mgr-moves",), below=".mgr-cardtabs"),
    Control("moves filter", "managers-moves", "#mgr-moves-filter",
            (State("waivers", select_value("#mgr-moves-filter", "waiver")), State("free agents", select_value("#mgr-moves-filter", "free_agent")),
             State("trades", select_value("#mgr-moves-filter", "trade"))), regions=("#mgr-moves",), below=".mgr-cardtabs"),
    Control("manager scroll region", "managers", ".mgr-scroll[tabindex]"),
    Control("news show more", "managers", ".mgr-showmore", (State("shown", click(".mgr-showmore")),), regions=(".mgr-news",), below=".mgr-cardtabs", self_moves=True),
    # manager names elsewhere link here (inline text links; app.js opens the Managers page)
    Control("manager name links", "predictions", "a.manager-link"),
    Control("manager name links (games)", "games", "a.manager-link"),
    Control("manager name links (game states)", "games-states", "a.manager-link"),
    Control("lineup view (game states)", "games-states", ".view-toggle button",
            (State("model", click(".game-card[data-state='scoring'] .view-toggle button[data-view='model']")),
             State("actual", click(".game-card[data-state='scoring'] .view-toggle button[data-view='actual']"))),
            grow=(".game-card",), below=".game-card[data-state='scoring'] .view-toggle", self_moves=False),
    Control("manager name links (positions)", "positions", "a.manager-link"),
    Control("manager name links (war)", "war", "a.manager-link"),
    Control("manager arrows (retired)", "managers-retired", "#mgr-prev, #mgr-next", (State("next", click("#mgr-next", 600)),), regions=("#mgr-content",), below="#mgr-picker"),

    # Calibration page
    Control("outcome", "calibration", "#outcome-switcher button",
            (State("other outcome", click("#outcome-switcher button[aria-pressed='false']", 600)),),
            grow=("main section.card",), below="#outcome-switcher"),
)


def controls_for(view: str) -> list[Control]:
    return [c for c in CONTROLS if c.view == view]
