"""Calculations.txt documents every calculation: each calculation module is named on a section's
Code: line, and every section carries all the required headings.

Adding a calculation module means adding it to CALCULATION_MODULES and giving it a section."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "Calculations.txt"

CALCULATION_MODULES = (
    "scoring.py", "stats.py", "projections.py", "injuries.py", "noise.py", "lineup.py", "drift.py",
    "simulate.py", "odds.py", "standings.py", "bracket.py", "forecast.py", "games.py", "views.py",
    "live.py", "replacement.py", "ratings.py", "war.py", "espn.py", "positions.py", "calibrate.py", "managers.py", "news.py", "moves.py", "card_states.py",
    "league_records.py", "schedule_strength.py", "draft.py", "injury_reports.py", "preseason.py",
)
HEADINGS = ("Code:", "Data sources:", "Depends on:", "Formula:", "In plain English:", "Assumptions and decisions:")


def sections() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    parts = re.split(r"^=+\n(\d+\. [^\n]+)\n=+\n", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def test_every_calculation_module_has_a_section():
    named = set()
    for body in sections().values():
        m = re.search(r"^Code:\s+(.+(?:\n\s{15}.+)*)", body, flags=re.M)
        if m:
            named.update(re.findall(r"src/ffapp/(\w+\.py)", m.group(1)))
    missing = [mod for mod in CALCULATION_MODULES if mod not in named]
    assert not missing, f"calculation modules without a Calculations.txt section naming them: {missing}"
    for mod in CALCULATION_MODULES:
        assert (ROOT / "src" / "ffapp" / mod).exists(), f"{mod} is listed but does not exist"


def test_every_section_has_all_headings():
    found = sections()
    assert len(found) >= 20, f"expected at least 20 sections, found {len(found)}"
    problems = [f"{name}: missing {h}" for name, body in found.items() for h in HEADINGS if not re.search(rf"^{re.escape(h)}", body, flags=re.M)]
    assert not problems, "\n".join(problems)


def test_readme_points_to_the_calculations_file():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Calculations.txt" in readme
