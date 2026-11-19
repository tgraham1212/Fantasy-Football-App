"""Baselines of known findings for the standards checks (accessibility, touch targets,
nomenclature). A baseline lists today's gaps so new problems fail immediately while follow-up
changes fix the listed ones. It may only shrink: a listed finding that no longer occurs also
fails, until it is removed. UPDATE_BASELINES=1 rewrites a baseline on purpose."""

from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def compare(name: str, found: set[str], what: str) -> list[str]:
    """Problems between the findings and the stored baseline, both ways (empty when they match)."""
    path = HERE / f"{name}.json"
    if os.environ.get("UPDATE_BASELINES") == "1":
        path.write_text(json.dumps(sorted(found), indent=1) + "\n", encoding="utf-8", newline="\n")
        return []
    known = set(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else set()
    problems = [f"new {what}: {f}" for f in sorted(found - known)]
    problems += [f"fixed, remove from tests/baselines/{name}.json: {f}" for f in sorted(known - found)]
    return problems
