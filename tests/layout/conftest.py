"""Fixtures for the browser layout check: a stamped copy of the site served locally, the installed
Chrome driven by Playwright, and simulated external services (the refresh relay, version.json,
data/index.json) so the check never starts a refresh.

The check is skipped when Playwright or Chrome is not available, unless LAYOUT_REQUIRED=1 (the
code-push workflow sets it), in which case a missing browser is a failure."""

from __future__ import annotations

import functools
import http.server
import json
import os
import shutil
import socketserver
import threading
from pathlib import Path

import pytest

from ffapp.stamp import stamp_site

SITE = Path(__file__).resolve().parents[2] / "site"
# Phone widths from StatCounter's US mobile screen statistics (October 2026: 414, 390, 384, 360,
# 402 and 393 px wide); 440 is the largest current iPhone. Re-check the statistics yearly.
WIDTHS = (360, 390, 414, 440, 768, 1000, 1280)
PHONE_WIDTHS = tuple(w for w in WIDTHS if w < 600)
# Chromium stands for Chrome and Edge; WebKit for Safari. WebKit and Firefox run the
# engine-sensitive tests at these widths.
ENGINES = ("chromium", "webkit", "firefox")
OTHER_ENGINE_WIDTHS = (440, 1280)  # kept to two widths so the code-push run stays under 20 minutes


def engine_cases(widths=WIDTHS, other_widths=OTHER_ENGINE_WIDTHS):
    """(engine, width) pairs: Chromium at every width, WebKit and Firefox at a subset."""
    return [("chromium", w) for w in widths] + [(e, w) for e in ENGINES[1:] for w in other_widths if w in widths or w in other_widths]
HEIGHT = 860


def _unavailable(reason: str):
    if os.environ.get("LAYOUT_REQUIRED") == "1":
        pytest.fail(f"layout check required but {reason}")
    pytest.skip(f"layout check skipped: {reason} (pip install -e \".[browser]\" and install Chrome)")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep test output clean
        pass


@pytest.fixture(scope="session")
def site_copy(tmp_path_factory) -> Path:
    """The site with its data, stamped exactly as a deploy stamps it."""
    dest = tmp_path_factory.mktemp("layout") / "site"
    shutil.copytree(SITE, dest, ignore=shutil.ignore_patterns("__pycache__", "version.json"))
    stamp_site(dest)
    return dest


@pytest.fixture(scope="session")
def base_url(site_copy):
    handler = functools.partial(_Quiet, directory=str(site_copy))
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="session")
def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _unavailable("Playwright is not installed")
    pw = sync_playwright().start()
    launched = {}
    yield pw, launched
    for b in launched.values():
        b.close()
    pw.stop()


@pytest.fixture
def engine(request):
    """The browser engine a test runs in: Chromium unless the test is parametrized with one."""
    return getattr(request, "param", "chromium")


@pytest.fixture
def browser(_playwright, engine):
    """One browser per engine for the whole session: the installed Chrome for Chromium,
    Playwright's own builds for WebKit (Safari's engine) and Firefox."""
    pw, launched = _playwright
    if engine not in launched:
        try:
            launched[engine] = pw.chromium.launch(channel="chrome") if engine == "chromium" else getattr(pw, engine).launch()
        except Exception as exc:  # engine not installed on this machine
            _unavailable(f"{engine} could not start ({str(exc).splitlines()[0]}); run python -m playwright install webkit firefox")
    return launched[engine]


@pytest.fixture(scope="session")
def relay_url(site_copy) -> str | None:
    index = json.loads((site_copy / "data" / "index.json").read_text(encoding="utf-8"))
    return (index.get("refresh_url") or "").rstrip("/") or None


class Relay:
    """Simulated refresh relay: what /status and /refresh answer."""

    def __init__(self):
        self.status = {"available": True}
        self.refresh = (202, {"started": True, "minutes": 15})  # or (code, body), or "abort"


@pytest.fixture
def open_page(browser, base_url, relay_url):
    """open_page(path, width) -> (page, relay). Every request to the relay is simulated."""
    pages = []

    def _open(path: str, width: int, relay: Relay | None = None):
        relay = relay or Relay()
        page = browser.new_page(viewport={"width": width, "height": HEIGHT})
        page.set_default_timeout(8000)
        pages.append(page)
        if relay_url:
            cors = {"Access-Control-Allow-Origin": "*"}

            def handle(route):
                url = route.request.url
                if url.endswith("/status"):
                    return route.fulfill(status=200, json=relay.status, headers=cors)
                if relay.refresh == "abort":
                    return route.abort()
                code, body = relay.refresh
                return route.fulfill(status=code, json=body, headers=cors)

            page.route(f"{relay_url}/**", handle)
        page.goto(f"{base_url}/{path}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(300)
        return page, relay

    yield _open
    for page in pages:
        page.close()
