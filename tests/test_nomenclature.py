"""Nomenclature: text people read uses Managers, Team Names, Players and Forecasts (for simulation
output); "owner", "odds", "chances" and "predictions" are retired. Checked over site-copy.txt
against a baseline of today's entries (tests/baselines/nomenclature.json) that may only shrink.

"projection" is allowed where the entry is about Sleeper's or players' projections (inputs). An
entry can carry "NOTE: nomenclature-ok <reason>" for a justified exception."""

from __future__ import annotations

import re
from pathlib import Path

from ffapp.site_copy import parse_file
from tests.baselines import compare

ROOT = Path(__file__).resolve().parents[1]
RETIRED = {
    "owner": r"\bowners?\b",
    "odds": r"\bodds\b",
    "chances": r"\bchances?\b",
    "prediction": r"\bpredict(?:ion|ions|ed)\b",
}
PROJECTION = r"\bproject(?:ion|ions|ed)\b"
INPUT_CONTEXT = r"\b(sleeper|player|players|rotowire)\b"


def flagged_terms(text: str) -> list[str]:
    terms = [name for name, pattern in RETIRED.items() if re.search(pattern, text, flags=re.I)]
    # placeholders (${...}) are code, not words people read
    plain = re.sub(r"\$\{[^}]*\}", " ", text)
    if re.search(PROJECTION, plain, flags=re.I) and not re.search(INPUT_CONTEXT, plain, flags=re.I):
        terms.append("projection (not about Sleeper's inputs)")
    return terms


def findings() -> set[str]:
    out = set()
    for cid, entry in parse_file(ROOT / "site-copy.txt").items():
        if any(n.lower().startswith("nomenclature-ok") for n in entry.notes):
            continue
        plain = re.sub(r"\$\{[^}]*\}", " ", entry.text)
        for term in flagged_terms(plain):
            out.add(f"{cid} | {term}")
    return out


def test_site_copy_uses_project_nomenclature():
    problems = compare("nomenclature", findings(), "retired term in site copy")
    assert not problems, "\n".join(problems)


def test_flagged_terms():
    assert flagged_terms("the owner's odds of winning") == ["owner", "odds"]
    assert flagged_terms("Sleeper's player projections") == []
    assert "projection (not about Sleeper's inputs)" in flagged_terms("the projected final")
    assert flagged_terms("Forecast for each Manager") == []
