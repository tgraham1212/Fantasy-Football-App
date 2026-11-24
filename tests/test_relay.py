"""The refresh relay's own tests (relay/worker.test.mjs, Node's test runner), run from pytest so they
run with the rest of the suite and in CI, and so the requirements can cite them by name.

The Node suite runs once per session; each function below checks that its named Node test passed.
Without Node the module is skipped, except under CI, where a missing Node is a failure."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RELAY = Path(__file__).resolve().parents[1] / "relay"


@pytest.fixture(scope="module")
def results() -> dict[str, bool]:
    node = shutil.which("node")
    if not node:
        if os.environ.get("CI"):
            pytest.fail("Node is required in CI to run the relay tests")
        pytest.skip("Node is not installed: the relay tests (relay/worker.test.mjs) were not run")
    run = subprocess.run([node, "--test", "--test-reporter=tap", "worker.test.mjs"], cwd=RELAY,
                         capture_output=True, text=True, encoding="utf-8", timeout=300)
    found = {m.group(2): m.group(1) is None for m in re.finditer(r"^(not )?ok \d+ - (.+)$", run.stdout, re.M)}
    assert found, f"no relay test results:\n{run.stdout}\n{run.stderr}"
    return found


def check(results: dict[str, bool], name: str):
    assert name in results, f"relay test not found: {name}"
    assert results[name], f"relay test failed: {name}"


def test_every_relay_test_passes(results):
    failed = [n for n, ok in results.items() if not ok]
    assert not failed, "failed relay tests: " + ", ".join(failed)


def test_modes_follow_the_games(results):
    check(results, "modes: off-season, quiet before kickoff, live after kickoff, quiet when all final")
    check(results, "live stays live while the late slate plays, after the early slate is final")


def test_stuck_game_counts_as_final_after_six_hours(results):
    check(results, "a game not seen final 6 hours after kickoff counts as final")


def test_live_cadence(results):
    check(results, "live: starts a hot run when none is going, and a cold run every 15 minutes in live mode")
    check(results, "live: no second hot run while one is queued or running, and none twice in a minute")


def test_quiet_cadence(results):
    check(results, "quiet: hot and cold runs every 15 minutes")


def test_offseason_clock_starts_nothing(results):
    check(results, "off-season: the clock starts nothing")


def test_final_slate_starts_one_cold_run(results):
    check(results, "a final slate starts one cold run in slate mode, once")


def test_hot_runs_stop_at_the_write_cap(results):
    check(results, "hot runs stop at the daily write cap; cold runs carry on")
    check(results, "bundle writes are counted per UTC day and stop at the cap")


def test_button_refresh_and_hold(results):
    check(results, "quiet: the button starts a hot run and a manual cold run, then holds for 5 minutes")
    check(results, "off-season: the button starts a cold run only")


def test_two_clicks_start_one_refresh(results):
    check(results, "two clicks at once start one refresh")


def test_button_held_while_a_hot_run_is_going(results):
    check(results, "the button is held while a hot run is going")


def test_button_refused_in_live(results):
    check(results, "live: the button is held and a refresh is refused")


def test_failed_dispatch_does_not_hold(results):
    check(results, "a failed dispatch does not hold the button")


def test_other_origins_refused(results):
    check(results, "browser requests from another origin are refused without calling GitHub")


def test_one_bundle_per_hot_run(results):
    check(results, "the hot run stores one bundle with its game states; an unchanged bundle is not written")


def test_bundle_writes_need_the_secret(results):
    check(results, "writes need the hot run's secret")


def test_schedule_summary_stored(results):
    check(results, "the schedule summary is stored for the clock")


def test_page_gets_the_newer_bundle(results):
    check(results, "the page gets the bundle, or 204 when none is newer than it has")
