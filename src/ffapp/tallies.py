"""Running tallies are committed once a day (docs/refresh-modes.md, "Committed").

Trending adds (``data/trending/<season>/<day>.json``) and the ESPN rostered and started percentages
(``data/espn/<season>/season.json`` and ``week_NN.json``) change on every fetch. Each cold run still
writes them, so the export and the site carry the latest values, but after ``git add data`` the run
calls :func:`hold_tallies`: a changed tally file whose committed copy was saved on the same UTC day is
unstaged and restored. New files (the day's first trending file) are kept. So git holds one copy a
day, from the first cold run after midnight UTC.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

TALLY_PATTERNS = ("data/trending/*/*.json", "data/espn/*/season.json", "data/espn/*/week_*.json")
TIME_KEYS = ("saved_at", "captured_at")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def saved_day(payload: object) -> date | None:
    """The UTC day a tally was saved, from its ``saved_at`` or ``captured_at`` time."""
    if not isinstance(payload, dict):
        return None
    for key in TIME_KEYS:
        value = payload.get(key)
        if isinstance(value, str):
            try:
                when = datetime.fromisoformat(value)
            except ValueError:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return when.astimezone(timezone.utc).date()
    return None


def hold_tallies(repo: Path, today: date | None = None) -> list[str]:
    """Unstage and restore staged changes to tally files whose committed copy is from ``today`` (UTC);
    returns the paths held back."""
    today = today or datetime.now(timezone.utc).date()
    changed = _git(repo, "diff", "--cached", "--name-only", "--diff-filter=M", "--", "data/trending", "data/espn").split()
    held = []
    for path in changed:
        if not any(fnmatch.fnmatch(path, pattern) for pattern in TALLY_PATTERNS):
            continue
        try:
            committed = json.loads(_git(repo, "show", f"HEAD:{path}"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        if saved_day(committed) == today:
            _git(repo, "restore", "--staged", "--worktree", "--", path)
            held.append(path)
    return held
