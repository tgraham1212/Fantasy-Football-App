"""Redraw the Games page state gallery (docs/games-page-states.md).

Serves the site locally, replaces the Games week with the fixture week that has one card per
state (tests/layout/game_states.py), and saves a screenshot of each card, plus the Model view of
a past week, to docs/images/games-states/. Run it after any change to how game cards look:

    python -X utf8 tools/games_states_gallery.py
"""

from __future__ import annotations

import functools
import http.server
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

from ffapp.card_states import DOC_NAMES, STATES  # noqa: E402
from tests.layout.game_states import LEAGUE, open_states  # noqa: E402

OUT = ROOT / "docs" / "images" / "games-states"
WIDTH = 1280


def image_name(state: str, suffix: str = "") -> str:
    return f"{DOC_NAMES[state]}-{state.replace('_', '-')}{suffix}.png"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    http.server.SimpleHTTPRequestHandler.log_message = lambda *a, **k: None
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:   # no installed Chrome: Playwright's own Chromium
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 1100}, color_scheme="light")
        page.goto(f"http://127.0.0.1:{server.server_port}/index.html#{LEAGUE}/games")
        page.wait_for_load_state("networkidle")
        open_states(page)
        for state in STATES:
            page.locator(f".game-card[data-state='{state}']").screenshot(path=str(OUT / image_name(state)))
            print("saved", image_name(state))
        page.locator(".game-card[data-state='final'] .view-toggle button[data-view='model']").click()
        page.wait_for_timeout(400)
        page.locator(".game-card[data-state='final']").screenshot(path=str(OUT / image_name("final", "-model")))
        print("saved", image_name("final", "-model"))
        browser.close()
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
