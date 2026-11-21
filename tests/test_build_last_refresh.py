"""The offline build dates the site by the last data commit when no run is on record, so the page can
still tell an older live bundle from a newer one (docs/refresh-modes.md)."""
from __future__ import annotations

import subprocess
from datetime import timezone
from pathlib import Path

from ffapp.cli import last_commit_time


def test_last_commit_time_outside_git_is_none(tmp_path):
    assert last_commit_time(tmp_path) is None


def test_last_commit_time_is_the_commit_in_utc(tmp_path):
    def git(*args, env=None):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, env=env)

    git("init", "-q")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.json").write_text("{}", encoding="utf-8")
    git("add", ".")
    import os
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
           "GIT_COMMITTER_DATE": "2026-11-21T00:09:25-05:00", "GIT_AUTHOR_DATE": "2026-11-21T00:09:25-05:00"}
    git("commit", "-q", "-m", "records", env=env)
    when = last_commit_time(Path(tmp_path / "data"))
    assert when.tzinfo == timezone.utc and when.isoformat() == "2026-11-21T05:09:25+00:00"
