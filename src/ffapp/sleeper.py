"""Thin HTTP client for Sleeper's public API and its projections endpoint.

Only the request plumbing lives here: throttling, retries with backoff,
timeouts and error reporting. Interpreting responses is up to callers.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Protocol
from urllib.parse import urlencode

import requests

API_BASE = "https://api.sleeper.app/v1"
PROJECTIONS_BASE = "https://api.sleeper.com/projections/nfl"
USER_AGENT = "ffapp/0.1 (fantasy league odds; +https://github.com)"
PROJECTION_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


class SleeperError(RuntimeError):
    """A Sleeper request failed after retries, or returned a non-2xx status."""

    def __init__(self, message: str, url: str, status: int | None = None):
        super().__init__(message)
        self.url = url
        self.status = status


class _Response(Protocol):
    status_code: int

    def json(self) -> Any: ...


class _Session(Protocol):
    def get(self, url: str, *, timeout: float, headers: dict[str, str]) -> _Response: ...


class SleeperClient:
    """Fetches JSON from Sleeper with a request throttle and retry policy.

    ``session`` is any object with ``get(url, timeout=, headers=)`` returning
    something with ``status_code`` and ``json()`` - a ``requests.Session`` in
    production, a fake in tests. ``sleep`` and ``clock`` are injectable so tests
    run instantly.
    """

    def __init__(
        self,
        session: _Session | None = None,
        *,
        api_base: str = API_BASE,
        projections_base: str = PROJECTIONS_BASE,
        timeout: float = 30.0,
        min_interval: float = 0.2,
        retries: int = 3,
        backoff: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._session = session or requests.Session()
        self._api_base = api_base.rstrip("/")
        self._projections_base = projections_base.rstrip("/")
        self._timeout = timeout
        self._min_interval = min_interval
        self._retries = retries
        self._backoff = backoff
        self._sleep = sleep
        self._clock = clock
        self._last_request: float | None = None
        self.request_count = 0

    # -- plumbing -----------------------------------------------------------

    def _throttle(self) -> None:
        if self._last_request is not None:
            wait = self._min_interval - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()

    def get_json(self, url: str) -> Any:
        """GET ``url`` and decode JSON, retrying transient failures."""
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        attempt = 0
        while True:
            self._throttle()
            self.request_count += 1
            try:
                response = self._session.get(url, timeout=self._timeout, headers=headers)
            except (requests.ConnectionError, requests.Timeout) as exc:
                failure: str | None = f"{type(exc).__name__}: {exc}"
                status: int | None = None
            else:
                status = response.status_code
                if 200 <= status < 300:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise SleeperError(f"invalid JSON from {url}: {exc}", url, status) from exc
                if status not in RETRY_STATUSES:
                    raise SleeperError(f"HTTP {status} from {url}", url, status)
                failure = f"HTTP {status}"

            if attempt >= self._retries:
                raise SleeperError(f"{failure} from {url} after {attempt + 1} attempts", url, status)
            self._sleep(self._backoff * (2**attempt))
            attempt += 1

    # -- documented v1 endpoints ---------------------------------------------

    def league(self, league_id: str) -> dict:
        return self.get_json(f"{self._api_base}/league/{league_id}")

    def users(self, league_id: str) -> list:
        return self.get_json(f"{self._api_base}/league/{league_id}/users")

    def rosters(self, league_id: str) -> list:
        return self.get_json(f"{self._api_base}/league/{league_id}/rosters")

    def matchups(self, league_id: str, week: int) -> list:
        return self.get_json(f"{self._api_base}/league/{league_id}/matchups/{week}")

    def winners_bracket(self, league_id: str) -> list:
        return self.get_json(f"{self._api_base}/league/{league_id}/winners_bracket")

    def losers_bracket(self, league_id: str) -> list:
        return self.get_json(f"{self._api_base}/league/{league_id}/losers_bracket")

    def state(self, sport: str = "nfl") -> dict:
        return self.get_json(f"{self._api_base}/state/{sport}")

    # -- undocumented projections endpoint -----------------------------------

    def projections(self, season: str | int, week: int) -> Any:
        """Raw weekly projections for the fantasy positions, as returned by Sleeper."""
        query = urlencode(
            [("season_type", "regular")] + [("position[]", p) for p in PROJECTION_POSITIONS]
        )
        return self.get_json(f"{self._projections_base}/{season}/{week}?{query}")
