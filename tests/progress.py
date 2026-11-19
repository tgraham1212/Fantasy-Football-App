"""Progress lines for long test runs (the browser layout check takes about 15 minutes).

About once a minute (PROGRESS_SECONDS overrides it, 0 turns it off) the run prints one line:
tests done out of the total, time so far, an estimate of the time left from the pace so far,
failures so far, and the test running now. It shows in the terminal, in GitHub Actions' live
log and in a background run's output file. Runs shorter than the interval print nothing.
"""

from __future__ import annotations

import os
import time

import pytest


def _clock(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


class Progress:
    def __init__(self, config: pytest.Config, every: float):
        self.config = config
        self.every = every
        self.total = 0
        self.done = 0
        self.failed = 0
        self.start = time.monotonic()
        self.last = self.start

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.total = len(session.items)
        self.start = self.last = time.monotonic()

    def pytest_runtest_logstart(self, nodeid: str, location) -> None:
        self._maybe_report(nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.failed:
            self.failed += 1
        if report.when == "teardown":
            self.done += 1

    def line(self, now: float, current: str) -> str:
        elapsed = now - self.start
        pct = 100 * self.done // self.total if self.total else 0
        left = ""
        if self.done:
            remaining = elapsed / self.done * (self.total - self.done)
            left = " · under 1 min left" if remaining < 60 else f" · about {round(remaining / 60)} min left"
        name = current.split("/")[-1]
        return (f"progress: {self.done}/{self.total} tests ({pct}%) · {_clock(elapsed)} elapsed{left}"
                f" · {self.failed} failed · now {name}")

    def _maybe_report(self, current: str) -> None:
        now = time.monotonic()
        if now - self.last < self.every:
            return
        self.last = now
        reporter = self.config.pluginmanager.get_plugin("terminalreporter")
        if reporter is not None:
            tw = getattr(reporter, "_tw", None)  # end the row of progress dots first
            if tw is not None and getattr(tw, "width_of_current_line", 0):
                reporter.write("\n")
            reporter.write_line(self.line(now, current))


def pytest_configure(config: pytest.Config) -> None:
    every = float(os.environ.get("PROGRESS_SECONDS", "60"))
    if every > 0:
        config.pluginmanager.register(Progress(config, every), "ffapp-progress")
