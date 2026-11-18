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
WIDTHS = (375, 768, 1000, 1280)
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
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _unavailable("Playwright is not installed")
    pw = sync_playwright().start()
    try:
        chrome = pw.chromium.launch(channel="chrome")
    except Exception as exc:  # no Chrome on this machine
        pw.stop()
        _unavailable(f"Chrome could not start ({str(exc).splitlines()[0]})")
    yield chrome
    chrome.close()
    pw.stop()


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
