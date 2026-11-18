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
from dataclasses import dataclass, field
from typing import Callable

LEAGUE = "dynasty"
FINAL_WEEK = 10  # a finished week: cards have the Model | Actual toggle

# Elements whose boxes are compared before and after every state.
LANDMARKS = (
    "header.top > *", "#refresh-btn", "#theme-toggle", "#subtabs", "#subtabs button",
    "main section.card", ".card-head", "#games-controls > *", ".game-card", ".game-card .view-toggle",
    ".war-table", "#war-controls", "#war-dialog", "#war-dialog .dialog-head", "#war-dialog-close",
    "#outcome-switcher", "footer",
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


VIEWS = {
    "predictions": View("predictions", f"index.html#{LEAGUE}"),
    "games": View("games", f"index.html#{LEAGUE}/games"),
    "games-final": View("games-final", f"index.html#{LEAGUE}/games/{FINAL_WEEK}", _games_final),
    "war": View("war", f"index.html#{LEAGUE}/war"),
    "war-all": View("war-all", f"index.html#{LEAGUE}/war", _war_all),
    "war-dialog": View("war-dialog", f"index.html#{LEAGUE}/war", _war_dialog),
    "calibration": View("calibration", "calibration.html"),
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


def select_first_other(selector: str):
    def act(page, relay, ctx):
        values = page.eval_on_selector(selector, "s => [...s.options].map(o => o.value).filter(v => v !== s.value)")
        page.select_option(selector, values[0])
        page.wait_for_timeout(500)
    return act


def refresh_answer(code, body=None):
    def act(page, relay, ctx):
        relay.refresh = "abort" if code == "abort" else (code, body or {})
        page.locator("#refresh-btn").evaluate("e => e.click()")
        page.wait_for_timeout(500)
    return act


def relay_held(page, relay, ctx):
    relay.status = {"available": False, "minutes": 9}
    page.reload()
    page.wait_for_load_state("networkidle")
    ctx["setup"](page)
    page.wait_for_timeout(400)


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
    State("started", refresh_answer(202, {"started": True, "minutes": 15})),
)
UPDATE_STATES = (State("new data", new_data), State("new version", new_version))


# -- the registry ------------------------------------------------------------------------------------

CONTROLS: tuple[Control, ...] = (
    # header, on every page
    Control("refresh", "predictions", "#refresh-btn", REFRESH_STATES),
    Control("refresh held", "predictions", "#refresh-btn", (State("held", relay_held),)),
    Control("refresh (calibration)", "calibration", "#refresh-btn", REFRESH_STATES),
    Control("theme", "predictions", "#theme-toggle", (State("toggled", click("#theme-toggle")), State("back", click("#theme-toggle")))),
    Control("theme (calibration)", "calibration", "#theme-toggle", (State("toggled", click("#theme-toggle")),)),
    Control("league switcher", "predictions", "#league-switcher button",
            (State("other league", click("#league-switcher button[aria-pressed='false']", 900)),),
            regions=("#page-predictions", "#page-games", "#page-war"), below="#subtabs"),
    Control("calibration link", "predictions", "a.nav-link[href='calibration.html']"),
    Control("odds link", "calibration", ".pages a.nav-link"),
    Control("footer link", "predictions", "footer a"),
    Control("footer link (calibration)", "calibration", "footer a"),
    Control("sub-tabs", "predictions", "#subtabs button",
            (State("games", click("#subtabs [data-page='games']", 900)), State("war", click("#subtabs [data-page='war']", 900)),
             State("predictions", click("#subtabs [data-page='predictions']", 900))),
            regions=("#page-predictions", "#page-games", "#page-war"), below="self"),
    Control("update check", "predictions", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("update check (games)", "games-final", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("update check (calibration)", "calibration", "body", UPDATE_STATES, regions=("#version-note",)),
    Control("version note", "predictions", "#version-note button"),

    # Predictions page
    Control("odds sort", "predictions", "#odds-table thead button.sort",
            (State("sorted", click("#odds-table thead button.sort >> nth=2")), State("flipped", click("#odds-table thead button.sort >> nth=2")))),
    Control("odds row", "predictions", "#odds-body tr",
            (State("highlight", click("#odds-body tr >> nth=0")), State("clear", click("#odds-body tr >> nth=0"))),
            grow=("main section.card",), below="#chart-note"),
    Control("chart metric", "predictions", "#metric-switcher button",
            (State("other metric", click("#metric-switcher button[aria-pressed='false']")),),
            grow=("main section.card",), below="#chart-title"),
    Control("rating metric", "predictions", "#rating-metric button",
            (State("other metric", click("#rating-metric button[aria-pressed='false']")),),
            grow=("main section.card",), below="#rating-title"),
    Control("rating range", "predictions", "#rating-range button",
            (State("other range", click("#rating-range button[aria-pressed='false']")),),
            grow=("main section.card",), below="#rating-title"),

    # Games page
    Control("week arrows", "games", "#games-prev, #games-next",
            (State("previous", click("#games-prev", 700)), State("next", click("#games-next", 700))),
            regions=("#games-content",), grow=("main section.card",), below="#games-note"),
    Control("week select", "games", "#games-week", (State("other week", select_first_other("#games-week")),),
            regions=("#games-content",), grow=("main section.card",), below="#games-note"),
    Control("full lineup", "games", "details.lineup summary",
            (State("open", click("details.lineup summary")), State("close", click("details.lineup summary"))),
            grow=(".game-card",), below="self"),
    Control("lineup view", "games-final", ".view-toggle button",
            (State("model", click(".game-card[data-card='0'] .view-toggle button[data-view='model']")),
             State("actual", click(".game-card[data-card='0'] .view-toggle button[data-view='actual']"))),
            grow=(".game-card",), below=".game-card[data-card='0'] .view-toggle", self_moves=False),
    Control("full lineup (final)", "games-final", "details.lineup summary",
            (State("open", click("details.lineup summary")),), grow=(".game-card",), below="self"),

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

    # Calibration page
    Control("outcome", "calibration", "#outcome-switcher button",
            (State("other outcome", click("#outcome-switcher button[aria-pressed='false']", 600)),),
            grow=("main section.card",), below="#outcome-switcher"),
)


def controls_for(view: str) -> list[Control]:
    return [c for c in CONTROLS if c.view == view]
