"""The requirements standard (project-standards 10.x; NASA Systems Engineering Handbook, Appendix C).

tools/requirements_model.py parses every main spec and every active change's delta specs and checks
each requirement: one positive SHALL, no banned terms (openspec/glossary.md), a hierarchical ID that
follows its primary parent and was never retired, Traces to parents that exist and reach a need
without a cycle, at most three parents unless accepted, a Verified by method with evidence that
exists, an inspection checklist row for Inspection, a target date on every TBR, children for every
need, glossary entries in use, and a dated standard review for every spec, redone after it changes.

The fixture tests below prove each rule on small sample specs. The last two run the check on the
real specs: today's findings are listed in tests/baselines/requirements.json and the open items
(TBRs and verification gaps) in tests/baselines/requirements_open.json. Both may only shrink.
Exceptions to the three-parent rule are accepted, with a reason, in
tests/baselines/requirements_accepted.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tests import baselines

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import requirements_impact as impact  # noqa: E402
import requirements_model as model  # noqa: E402

PURPOSE = "Fixture spec for the requirements check, long enough to pass validation."


def req(heading, statement="The site SHALL show it.", traces=None, verified="Analysis: report, section 1",
        tbr=None, need=False):
    lines = [f"### Requirement: {heading}", statement, ""]
    if traces is not None:
        lines.append(f"**Traces to:** {traces}")
    if need:
        lines.append("**Verified by:** Children")
    elif verified is not None:
        lines.append(f"**Verified by:** {verified}")
    if tbr is not None:
        lines.append(f"**TBR:** {tbr}")
    lines += ["", "#### Scenario: A case", "- **WHEN** something happens", "- **THEN** it is shown", ""]
    return "\n".join(lines)


NEEDS = [req("1 Need One", need=True), req("2 Need Two", need=True)]


def make_root(tmp_path, specs, glossary="", checklist="", retired=""):
    """A project tree with openspec/specs/<name>/spec.md for each entry, plus the optional files."""
    root = tmp_path
    for name, reqs in {"needs": NEEDS, **specs}.items():
        path = root / "openspec" / "specs" / name / "spec.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {name} Specification\n\n## Purpose\n\n{PURPOSE}\n\n## Requirements\n\n" + "\n".join(reqs),
                        encoding="utf-8")
    for rel, text in (("glossary.md", glossary), ("inspection-checklist.md", checklist),
                      ("retired-requirements.md", retired)):
        if text:
            (root / "openspec" / rel).write_text(text, encoding="utf-8")
    return root


def findings(root, **kw):
    kw.setdefault("last_change", lambda rel: None)
    return model.check(root, **kw)


def about(found, label):
    """Findings for one requirement (by 'spec | heading')."""
    return {f.split(" | ", 2)[2] for f in found if f.startswith(label + " | ")}


# ---------- fixture tests: one per rule ----------

def test_one_shall_per_requirement(tmp_path):
    root = make_root(tmp_path, {"a": [
        req("1.1 Two", "The page SHALL swap the data and SHALL keep the scroll position.", "1"),
        req("1.2 Negative", "Players on injured reserve SHALL NOT start.", "1"),
        req("1.3 Quoted", "Each requirement SHALL use `SHALL` once.", "1"),
        req("1.4 None", "The page shows the data.", "1"),
    ]})
    f = findings(root)
    assert "2 SHALLs" in about(f, "a | 1.1 Two")
    assert "SHALL NOT" in about(f, "a | 1.2 Negative")
    assert about(f, "a | 1.3 Quoted") == set()
    assert "0 SHALLs" in about(f, "a | 1.4 None")


def test_no_banned_terms(tmp_path):
    glossary = "# Glossary\n\n## Terms\n\n## Banned Terms\n\n- quickly\n- etc.\n- and/or\n"
    root = make_root(tmp_path, {"a": [
        req("1.1 Vague", "The page SHALL load quickly, show scores, etc.", "1"),
        req("1.2 Code", "The check SHALL name the term `quickly` when it finds it.", "1"),
        req("1.3 Either", "The page SHALL show wins and/or losses.", "1"),
    ]}, glossary=glossary)
    f = findings(root)
    assert about(f, "a | 1.1 Vague") == {"banned term 'quickly'", "banned term 'etc.'"}
    assert about(f, "a | 1.2 Code") == set()
    assert about(f, "a | 1.3 Either") == {"banned term 'and/or'"}


def test_every_requirement_reaches_a_need(tmp_path):
    root = make_root(tmp_path, {"a": [
        req("1.1 Middle", traces="1"),
        req("1.1.1 Lower", traces="1.1"),
        req("1.2 Two parents", traces="1; 2"),
        req("1.3 No trace"),
        req("1.4 Missing parent", traces="1.9"),
        req("1.5 Old style", traces="needs: Need One"),
    ], "b": [
        req("3.1 Loop A", traces="3.2"),
        req("3.2 Loop B", traces="3.1"),
    ]})
    f = findings(root)
    assert about(f, "a | 1.1 Middle") == set()
    assert about(f, "a | 1.1.1 Lower") == set()
    assert about(f, "a | 1.2 Two parents") == set()
    reqs = model.load(root)
    kids = model.children(reqs)
    assert "1.2" in {r.rid for r in kids["1"]} and "1.2" in {r.rid for r in kids["2"]}
    assert about(f, "a | 1.3 No trace") == {"orphan: no Traces to"}
    assert "orphan: parent '1.9' does not exist" in about(f, "a | 1.4 Missing parent")
    assert "orphan: parent 'needs: Need One' does not exist" in about(f, "a | 1.5 Old style")
    loop = about(f, "b | 3.1 Loop A") | about(f, "b | 3.2 Loop B")
    assert any(x.startswith("cycle:") for x in loop)
    assert "no chain reaches a need" in loop


def test_ids_follow_the_primary_parent(tmp_path):
    root = make_root(tmp_path, {"a": [
        req("1.1 Right", traces="1"),
        req("1.1.1 Third level", traces="1.1; 2"),
        req("3.1.2 Wrong parent", traces="1.1"),
        req("1.1 Duplicate", traces="1"),
        req("No ID", traces="1"),
        req("5 Not a need", traces="1"),
    ], "needs2": [req("2.1 Dotted need", need=True)]})
    f = findings(root)
    assert about(f, "a | 1.1.1 Third level") == set()
    assert "ID 3.1.2 does not follow primary parent 1.1" in about(f, "a | 3.1.2 Wrong parent")
    assert any(x.startswith("duplicate ID 1.1") for x in about(f, "a | 1.1 Duplicate") | about(f, "a | 1.1 Right"))
    assert "no ID" in about(f, "a | No ID")
    assert "ID 5 has no parent part" in about(f, "a | 5 Not a need")


def test_retired_ids_are_not_reused(tmp_path):
    retired = ("# Retired Requirements\n\n## Retired IDs\n\n| ID | Requirement | Date | Reason |\n|---|---|---|---|\n"
               "| 1.2 | Old rule | 2026-11-23 | Cut at review |\n")
    root = make_root(tmp_path, {"a": [req("1.1 Kept", traces="1"), req("1.2 Reused", traces="1")]}, retired=retired)
    f = findings(root)
    assert model.retired_ids(root) == {"1.2"}
    assert about(f, "a | 1.1 Kept") == set()
    assert "reuses retired ID 1.2" in about(f, "a | 1.2 Reused")


def test_parent_count_is_reviewed(tmp_path):
    parents = [req("3 Need Three", need=True), req("4 Need Four", need=True)]
    root = make_root(tmp_path, {"needs34": parents, "a": [req("1.1 Four", traces="1; 2; 3; 4"), req("1.2 Three", traces="1; 2; 3")]})
    f = findings(root)
    assert "4 parents: split it or review its parents" in about(f, "a | 1.1 Four")
    assert about(f, "a | 1.2 Three") == set()
    assert about(findings(root, accepted={"1.1": "a reason"}), "a | 1.1 Four") == set()


def test_impact_report_lists_ancestors_and_descendants(tmp_path):
    root = make_root(tmp_path, {"a": [
        req("1.1 Simulation", traces="1"),
        req("2.1 Game page", traces="2"),
        req("1.1.1 Lineups", traces="1.1; 2.1", verified="Test: `tests/test_x.py::test_lineups`"),
        req("1.1.1.1 Lineup data", traces="1.1.1"),
    ]})
    text = impact.report(root, "1.1.1")
    above = text.split("Above")[1].split("Below")[0]
    below = text.split("Below")[1]
    assert text.splitlines()[0].startswith("1.1.1 Lineups  [a]  Verified by: Test:")
    for rid in ("1.1 Simulation", "1 Need One", "2.1 Game page", "2 Need Two"):
        assert rid in above
    assert above.index("1.1 Simulation") < above.index("2.1 Game page")  # primary parent first
    assert "1.1.1.1 Lineup data" in below and "Analysis: report, section 1" in below


def test_every_need_has_children(tmp_path):
    root = make_root(tmp_path, {"a": [req("1.1 Child", traces="1")]})
    f = findings(root)
    assert about(f, "needs | 1 Need One") == set()
    assert about(f, "needs | 2 Need Two") == {"need with no children"}


def test_every_requirement_has_a_verification(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_real():\n    pass\n", encoding="utf-8")
    root = make_root(tmp_path, {"a": [
        req("1.1 Tested", traces="1", verified="Test: `tests/test_x.py::test_real`"),
        req("1.2 Renamed", traces="1", verified="Test: `tests/test_x.py::test_gone`"),
        req("1.3 None", traces="1", verified=None),
        req("1.4 Odd method", traces="1", verified="Hope: it works"),
        req("1.5 Gap", traces="1", verified="Gap: a test that the page shows it"),
    ]})
    f = findings(root)
    assert about(f, "a | 1.1 Tested") == set()
    assert about(f, "a | 1.2 Renamed") == {"missing test tests/test_x.py::test_gone"}
    assert about(f, "a | 1.3 None") == {"no Verified by"}
    assert "unknown verification method 'Hope'" in about(f, "a | 1.4 Odd method")
    assert about(f, "a | 1.5 Gap") == set()
    assert "a | 1.5 Gap | Gap: a test that the page shows it" in model.open_items(root)


def test_inspection_checklist_covers_every_inspection(tmp_path):
    checklist = ("# Inspection Checklist\n\n## Requirement Inspections\n\n"
                 "| ID | Requirement | Spec | Pass criteria | Last inspected | Result |\n|---|---|---|---|---|---|\n"
                 "| 1.1 | Listed | a | The value has a bound | 2026-11-23 | Pass |\n\n## Spec Standard Reviews\n\n"
                 "| Spec | Last reviewed | Result | Notes |\n|---|---|---|---|\n")
    root = make_root(tmp_path, {"a": [
        req("1.1 Listed", traces="1", verified="Inspection: the checklist"),
        req("1.2 Unlisted", traces="1", verified="Inspection: the checklist"),
    ]}, checklist=checklist)
    f = findings(root)
    assert about(f, "a | 1.1 Listed") == set()
    assert about(f, "a | 1.2 Unlisted") == {"inspection without a checklist row"}


def test_inspection_is_redone_when_its_tree_changes(tmp_path):
    checklist = ("# Inspection Checklist\n\n## Requirement Inspections\n\n"
                 "| ID | Requirement | Spec | Pass criteria | Last inspected | Result |\n|---|---|---|---|---|---|\n"
                 "| 1.1 | Page | a | The page shows it | 2026-11-20 | Pass |\n"
                 "| 2.1 | Other | a | It shows | 2026-11-20 | Pass |\n\n## Spec Standard Reviews\n\n"
                 "| Spec | Last reviewed | Result | Notes |\n|---|---|---|---|\n")
    root = make_root(tmp_path, {
        "a": [req("1.1 Page", traces="1", verified="Inspection: the page"), req("2.1 Other", traces="2", verified="Inspection: it")],
        "b": [req("1.1.1 Child elsewhere", traces="1.1")],
    }, checklist=checklist)
    dates = {"openspec/specs/a/spec.md": "2026-11-20", "openspec/specs/b/spec.md": "2026-11-22"}
    f = findings(root, last_change=dates.get)
    assert about(f, "a | 1.1 Page") == {"re-inspect: openspec/specs/b/spec.md changed on 2026-11-22, after its inspection on 2026-11-20"}
    assert about(f, "a | 2.1 Other") == set(), "nothing beneath 2.1 changed"


def test_every_spec_has_a_dated_review(tmp_path):
    checklist = ("# Inspection Checklist\n\n## Requirement Inspections\n\n"
                 "| ID | Requirement | Spec | Pass criteria | Last inspected | Result |\n|---|---|---|---|---|---|\n\n"
                 "## Spec Standard Reviews\n\n| Spec | Last reviewed | Result | Notes |\n|---|---|---|---|\n"
                 "| `needs` | 2026-11-23 | Pass | |\n| `a` | 2026-11-20 | Pass | |\n")
    root = make_root(tmp_path, {"a": [req("1.1 X", traces="1")], "b": [req("2.1 Y", traces="2")]}, checklist=checklist)
    dates = {"openspec/specs/needs/spec.md": "2026-11-23", "openspec/specs/a/spec.md": "2026-11-22"}
    f = findings(root, last_change=dates.get)
    assert about(f, "needs | (spec)") == set()  # changed the day it was reviewed
    assert about(f, "a | (spec)") == {"changed on 2026-11-22, after its standard review on 2026-11-20"}
    assert about(f, "b | (spec)") == {"no standard review"}


def test_tbr_has_a_target_date(tmp_path):
    root = make_root(tmp_path, {"a": [
        req("1.1 Dated", traces="1", tbr="Set after the worked example, 2026-12."),
        req("1.2 Undated", traces="1", tbr="Set later."),
    ]})
    f = findings(root)
    assert about(f, "a | 1.1 Dated") == set()
    assert about(f, "a | 1.2 Undated") == {"TBR without a target date"}
    assert "a | 1.1 Dated | TBR: Set after the worked example, 2026-12." in model.open_items(root)


def test_glossary_entries_are_used(tmp_path):
    glossary = ("# Glossary\n\n## Terms\n\n- **Slate:** games with one kickoff time.\n"
                "- **Hot run (HR):** the quick refresh.\n- **Dead term:** used nowhere.\n\n## Banned Terms\n\n- etc.\n")
    root = make_root(tmp_path, {"a": [req("1.1 Uses", "Each slate SHALL be shown after a hot run.", "1")]}, glossary=glossary)
    f = findings(root)
    assert {x for x in f if x.startswith("glossary")} == {"glossary | Dead term | used in no spec"}


# ---------- the real specs ----------

def accepted() -> dict:
    path = ROOT / "tests" / "baselines" / "requirements_accepted.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def test_findings_match_the_baseline():
    found = model.check(ROOT, accepted=accepted())
    stale = sorted(f for f in found if "after its standard review" in f or "after its inspection" in f)
    assert not stale, "re-inspect these specs and update their review dates in openspec/inspection-checklist.md:\n" + "\n".join(stale)
    problems = baselines.compare("requirements", found, "requirements finding")
    assert not problems, "\n".join(problems)


def test_open_items_match_the_baseline():
    problems = baselines.compare("requirements_open", model.open_items(ROOT), "open item (TBR or verification gap)")
    assert not problems, "\n".join(problems)
