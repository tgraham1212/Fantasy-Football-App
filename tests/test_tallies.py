"""Trending and ESPN percentages are committed once a day (src/ffapp/tallies.py)."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from pathlib import Path

import pytest

from ffapp.tallies import hold_tallies, saved_day

TODAY = date(2026, 11, 21)


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=env).stdout


def put(repo: Path, rel: str, payload: dict) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    put(tmp_path, "data/trending/2026/2026-11-21.json", {"saved_at": "2026-11-21T01:00:00+00:00", "adds": [{"count": 1}]})
    put(tmp_path, "data/trending/2026/2026-11-20.json", {"saved_at": "2026-11-20T23:00:00+00:00", "adds": [{"count": 5}]})
    put(tmp_path, "data/espn/2026/week_11.json", {"captured_at": "2026-11-20T23:30:00+00:00", "players": {"1": 40.0}})
    put(tmp_path, "data/espn/2026/season.json", {"captured_at": "2026-11-21T02:00:00+00:00", "players": {"1": 40.0}})
    put(tmp_path, "data/espn/crosswalk.json", {"1": {"team": "IND"}})
    put(tmp_path, "data/stats/2026/week_11.json", {"1": {"pts": 1}})
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "records")
    return tmp_path


def staged(repo: Path) -> set[str]:
    return set(git(repo, "diff", "--cached", "--name-only").split())


def test_same_day_tallies_are_held_and_restored(repo):
    put(repo, "data/trending/2026/2026-11-21.json", {"saved_at": "2026-11-21T15:00:00+00:00", "adds": [{"count": 9}]})
    put(repo, "data/espn/2026/season.json", {"captured_at": "2026-11-21T15:00:00+00:00", "players": {"1": 41.0}})
    git(repo, "add", "data")
    held = hold_tallies(repo, today=TODAY)
    assert sorted(held) == ["data/espn/2026/season.json", "data/trending/2026/2026-11-21.json"]
    assert staged(repo) == set() and git(repo, "status", "--porcelain") == "", "held files are restored, so the pull before the push stays clean"


def test_a_tally_from_an_earlier_day_is_committed(repo):
    put(repo, "data/espn/2026/week_11.json", {"captured_at": "2026-11-21T15:00:00+00:00", "players": {"1": 41.0}})
    git(repo, "add", "data")
    assert hold_tallies(repo, today=TODAY) == []
    assert staged(repo) == {"data/espn/2026/week_11.json"}


def test_new_tally_files_and_other_records_are_never_held(repo):
    put(repo, "data/trending/2026/2026-11-22.json", {"saved_at": "2026-11-21T15:00:00+00:00", "adds": []})
    put(repo, "data/stats/2026/week_11.json", {"1": {"pts": 2}})
    put(repo, "data/espn/crosswalk.json", {"1": {"team": None}})
    git(repo, "add", "data")
    assert hold_tallies(repo, today=TODAY) == []
    assert staged(repo) == {"data/trending/2026/2026-11-22.json", "data/stats/2026/week_11.json", "data/espn/crosswalk.json"}


def test_saved_day_is_the_utc_day():
    assert saved_day({"captured_at": "2026-11-20T21:30:00-05:00"}) == date(2026, 11, 21)
    assert saved_day({"saved_at": "2026-11-21T01:00:00"}) == date(2026, 11, 21)
    assert saved_day({"other": 1}) is None and saved_day([]) is None
