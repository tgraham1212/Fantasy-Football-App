"""The open page's update check (site-updates 5.3.x): how often it checks while visible, quiet or live,
and that it makes no checks while the tab is hidden, checking once when it is shown again. Time is
fast-forwarded with Playwright's clock; checks are counted as fetches of data/index.json."""

from __future__ import annotations

import json

import pytest

from tests.layout.conftest import HEIGHT

HIDE = """(() => {
  let hidden = false;
  Object.defineProperty(document, 'visibilityState', { get: () => (hidden ? 'hidden' : 'visible') });
  Object.defineProperty(document, 'hidden', { get: () => hidden });
  window.__setHidden = (h) => { hidden = h; document.dispatchEvent(new Event('visibilitychange')); };
})();"""


def open_counting(browser, base_url, relay_url, live_bundle=None):
    """A page whose relay is simulated, with a fake clock, counting the update checks."""
    page = browser.new_page(viewport={"width": 1280, "height": HEIGHT})
    page.add_init_script(HIDE)
    page.clock.install()
    checks = {"n": 0}

    def count(route):
        checks["n"] += 1
        route.continue_()

    page.route("**/data/index.json*", count)
    if relay_url:
        cors = {"Access-Control-Allow-Origin": "*"}

        def relay(route):
            url = route.request.url
            if url.endswith("/status"):
                return route.fulfill(status=200, json={"available": True, "mode": "live" if live_bundle else "quiet"}, headers=cors)
            if "/live" in url and live_bundle:
                return route.fulfill(status=200, json=live_bundle, headers=cors)
            return route.fulfill(status=204, body="", headers=cors)

        page.route(f"{relay_url}/**", relay)
    page.goto(f"{base_url}/index.html#dynasty")
    page.wait_for_load_state("networkidle")
    return page, checks


def run_minutes(page, minutes: float, step_s: int = 15):
    """Advance the clock in steps, letting each check's fetches finish before the next timer is due."""
    for _ in range(int(minutes * 60 / step_s)):
        page.clock.run_for(step_s * 1000)
        page.wait_for_timeout(150)


def test_checks_once_a_minute_while_quiet(browser, base_url, relay_url):
    """5.3: about one check a minute while the tab is visible and no game is live."""
    page, checks = open_counting(browser, base_url, relay_url)
    start = checks["n"]
    run_minutes(page, 5)
    assert 4 <= checks["n"] - start <= 6, checks["n"] - start
    page.close()


def test_checks_every_thirty_seconds_while_live(browser, base_url, relay_url, site_copy):
    """5.3: about two checks a minute while a game is in progress."""
    if not relay_url:
        pytest.skip("no relay configured in the exported data")
    index = json.loads((site_copy / "data" / "index.json").read_text(encoding="utf-8"))
    league = json.loads((site_copy / "data" / "dynasty.json").read_text(encoding="utf-8"))
    bundle = {"generated_at": "2099-01-01T00:00:00+00:00", "games": {"2099-01-KC@BUF": "in_progress"},
              "files": {"dynasty.json": league}, "base_commit": "x", "hash": "x", "season": index["leagues"][0]["season"], "week": 11, "version": 1}
    page, checks = open_counting(browser, base_url, relay_url, live_bundle=bundle)
    run_minutes(page, 0.5)
    start = checks["n"]
    run_minutes(page, 5)
    assert 9 <= checks["n"] - start <= 11, checks["n"] - start
    page.close()


def test_no_checks_while_hidden_and_one_when_shown(browser, base_url, relay_url):
    """5.3.1"""
    page, checks = open_counting(browser, base_url, relay_url)
    page.evaluate("window.__setHidden(true)")
    start = checks["n"]
    run_minutes(page, 10)
    assert checks["n"] == start, "no checks while the tab is hidden"
    page.evaluate("window.__setHidden(false)")
    page.wait_for_timeout(300)
    assert checks["n"] == start + 1, "one check when the tab is shown again"
    page.close()
