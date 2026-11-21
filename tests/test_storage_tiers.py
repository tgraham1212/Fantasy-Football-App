"""The storage tiers hold (docs/refresh-modes.md, "Where Data Lives").

- No rebuilt path is tracked by git.
- Every folder under data/ is listed in the document as committed or rebuilt.
- The site can be built from committed records alone, with no network.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ffapp.cli import main
from ffapp.sleeper import SleeperClient
from ffapp.store import DERIVED_PATHS
from tests.test_refresh import projections_for_2026, run, stats_for_2026, write_config

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "refresh-modes.md"


def tracked(*patterns: str) -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files", "--", *patterns], cwd=ROOT, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    return [line for line in out.stdout.splitlines() if line]


def test_no_rebuilt_path_is_tracked():
    patterns = [f"data/{p}" for p in DERIVED_PATHS] + ["site/data"]
    assert tracked(*patterns) == [], "rebuilt data is tracked by git: git rm -r --cached it"


def test_every_data_folder_is_listed_in_the_document():
    text = DOC.read_text(encoding="utf-8")
    listed = set(re.findall(r"`data/([a-z-]+)/", text))
    folders = {Path(p).parts[1] for p in tracked("data")} | {p.split("/")[0] for p in DERIVED_PATHS}
    missing = sorted(folders - listed)
    assert not missing, f"data folders missing from docs/refresh-modes.md: {missing}"


class NoNetwork:
    def get(self, url, *, timeout, headers):
        raise AssertionError(f"the offline build called {url}")


def test_build_from_committed_records_alone(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    data = tmp_path / "data"
    for pattern in DERIVED_PATHS:  # a fresh clone: no rebuilt data, no site data
        for path in data.glob(pattern):
            shutil.rmtree(path) if path.is_dir() else path.unlink()
    shutil.rmtree(tmp_path / "site-data")
    offline = SleeperClient(NoNetwork(), min_interval=0, sleep=lambda s: None)
    argv = ["--config", str(cfg), "--data", str(data), "--site-data", str(tmp_path / "site-data"), "build"]
    assert main(argv, client=offline) == 0
    assert (tmp_path / "site-data" / "index.json").exists() and (tmp_path / "site-data" / "dynasty.json").exists()
    assert (data / "war").exists() and (data / "ratings").exists() and (data / "games-derived").exists()
