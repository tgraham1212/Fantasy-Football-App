"""site-copy.txt: every piece of descriptive site text, kept in step with the code.

The last three tests run against the real site and are the guard rails: unmarked text, a stale
file, and copy edits not yet applied (which must be confirmed with the owner first) all fail.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ffapp import site_copy as sc

ROOT = Path(__file__).resolve().parents[1]

INDEX = """<!doctype html>
<html><head><title data-copy="HDR-01">Odds</title></head>
<body>
  <p data-copy="POS-01" class="explain">Each dot is a player.
     Hover a <em>dot</em> for details.</p>
  <ul><li data-copy="WAR-01"><strong>Step one.</strong> Count the starts.</li></ul>
  <p id="filled-by-js"></p>
</body></html>
"""
CAL = """<!doctype html><html><head><title data-copy="CAL-01">How good</title></head><body></body></html>
"""
SCRIPT = """const NOTE = /*copy:POS-02*/`Points through week ${payload.final_through} plus ${x ? `projected` : "none"} weeks.`;
const MSG = /*copy:MSG-01*/"Could not start a refresh. Try again later.";
const LABEL = "Rush yds";
function render(n) {
  return `<p class="hint">${/*copy:POS-03*/`Showing ${n} players
    from the final rosters.`}</p>`;
}
"""


@pytest.fixture
def project(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(INDEX, encoding="utf-8")
    (site / "calibration.html").write_text(CAL, encoding="utf-8")
    (site / "page.js").write_text(SCRIPT, encoding="utf-8")
    sc.regenerate(tmp_path, accept={"HDR-01", "POS-01", "WAR-01", "CAL-01", "POS-02", "MSG-01", "POS-03"})
    return tmp_path


def edit_entry(root: Path, cid: str, new_text: str):
    path = root / sc.COPY_FILE
    lines = path.read_text(encoding="utf-8").split("\n")
    i = lines.index(next(line for line in lines if line.startswith(f"[{cid}]")))
    t = lines.index("TEXT:", i)
    lines[t + 1] = new_text
    path.write_text("\n".join(lines), encoding="utf-8")


# -- extraction -------------------------------------------------------------------------------


def test_extracts_html_and_marked_script_strings(project):
    code = sc.code_entries(project / "site")
    assert set(code) == {"HDR-01", "POS-01", "WAR-01", "CAL-01", "POS-02", "MSG-01", "POS-03"}
    assert code["POS-01"].text == "Each dot is a player. Hover a <em>dot</em> for details."  # markup kept, whitespace collapsed
    assert code["WAR-01"].text == "<strong>Step one.</strong> Count the starts."
    assert code["POS-02"].text == 'Points through week ${payload.final_through} plus ${x ? `projected` : "none"} weeks.'  # nested template
    assert code["POS-03"].text == "Showing ${n} players from the final rosters."  # multi-line, nested inside a template
    assert code["MSG-01"].kind == '"'


def test_file_round_trip_keeps_labels_and_notes(project):
    path = project / sc.COPY_FILE
    text = path.read_text(encoding="utf-8").replace("[POS-01] paragraph", "[POS-01] Positions key")
    text = text.replace("[MSG-01] generated text\nWHERE: site/page.js line 2 (generated)\nTEXT:\nCould not start a refresh. Try again later.\n",
                        "[MSG-01] generated text\nWHERE: site/page.js line 2 (generated)\nTEXT:\nCould not start a refresh. Try again later.\nNOTE: keep this short\n")
    path.write_text(text, encoding="utf-8")
    sc.regenerate(project)
    entries = sc.parse_file(path)
    assert entries["POS-01"].label == "Positions key" and entries["MSG-01"].notes == ["keep this short"]
    assert sc.check(project).clean


def test_coverage_finds_unmarked_text(project):
    assert sc.coverage_problems(project / "site") == []
    index = project / "site" / "index.html"
    index.write_text(index.read_text(encoding="utf-8").replace('<p id="filled-by-js"></p>', "<p>A brand new paragraph here.</p>"), encoding="utf-8")
    script = project / "site" / "page.js"
    script.write_text(script.read_text(encoding="utf-8") + 'const N = "A brand new sentence for the page.";\n', encoding="utf-8")
    problems = sc.coverage_problems(project / "site")
    assert any("index.html" in p and "A brand new paragraph" in p for p in problems)
    assert any("page.js line 8" in p and "A brand new sentence" in p for p in problems)
    assert not any("Rush yds" in p for p in problems)  # short labels are not copy


# -- statuses -----------------------------------------------------------------------------------


def test_code_change_is_stale_and_regeneration_fixes_it(project):
    script = project / "site" / "page.js"
    script.write_text(script.read_text(encoding="utf-8").replace("Try again later.", "Please try again later."), encoding="utf-8")
    report = sc.check(project)
    assert report.ids("stale") == ["MSG-01"] and not report.ids("pending")
    sc.regenerate(project)
    assert sc.check(project).clean
    assert sc.parse_file(project / sc.COPY_FILE)["MSG-01"].text == "Could not start a refresh. Please try again later."


def test_owner_edit_is_pending_and_survives_regeneration(project):
    edit_entry(project, "POS-01", "Every dot is one rostered player. Hover a <em>dot</em> for details.")
    assert sc.check(project).ids("pending") == ["POS-01"]
    sc.regenerate(project)  # never applies or discards an owner edit
    assert sc.check(project).ids("pending") == ["POS-01"]
    assert sc.parse_file(project / sc.COPY_FILE)["POS-01"].text.startswith("Every dot is one rostered player.")
    assert "Each dot is a player." in (project / "site" / "index.html").read_text(encoding="utf-8")


def test_both_sides_changed_is_a_conflict(project):
    edit_entry(project, "MSG-01", "Refresh failed. Try again soon.")
    script = project / "site" / "page.js"
    script.write_text(script.read_text(encoding="utf-8").replace("Try again later.", "Please try again later."), encoding="utf-8")
    assert sc.check(project).ids("conflict") == ["MSG-01"]
    sc.regenerate(project)
    assert sc.parse_file(project / sc.COPY_FILE)["MSG-01"].text == "Refresh failed. Try again soon."  # nothing overwritten


def test_new_and_removed_ids(project):
    script = project / "site" / "page.js"
    src = script.read_text(encoding="utf-8").replace('const LABEL = "Rush yds";', 'const LABEL = /*copy:POS-04*/"Rush yards this season, all games";')
    src = src.replace("/*copy:MSG-01*/", "")
    script.write_text(src, encoding="utf-8")
    report = sc.check(project)
    assert report.ids("new") == ["POS-04"] and report.ids("removed") == ["MSG-01"]
    sc.regenerate(project)
    entries = sc.parse_file(project / sc.COPY_FILE)
    assert "POS-04" in entries and "MSG-01" not in entries and sc.check(project).clean


# -- applying -----------------------------------------------------------------------------------


def test_apply_writes_edits_back(project):
    edit_entry(project, "POS-01", "Every dot is one rostered player. Hover a <em>dot</em> for more.")
    edit_entry(project, "POS-02", 'Through week ${payload.final_through}, plus ${x ? `projected` : "none"} weeks to come.')
    edit_entry(project, "MSG-01", 'The refresh didn\'t start. Say "retry" later.')
    result = sc.apply_edits(project)
    assert sorted(result.applied) == ["MSG-01", "POS-01", "POS-02"] and not result.refused
    assert "Every dot is one rostered player. Hover a <em>dot</em> for more." in (project / "site" / "index.html").read_text(encoding="utf-8")
    js = (project / "site" / "page.js").read_text(encoding="utf-8")
    assert '/*copy:MSG-01*/"The refresh didn\'t start. Say \\"retry\\" later."' in js  # quotes escaped for its literal
    assert "Through week ${payload.final_through}, plus" in js
    assert sc.check(project).clean


def test_apply_refuses_changed_placeholders_and_reports_deletions(project):
    edit_entry(project, "POS-02", "Points through the latest week plus the weeks to come.")
    edit_entry(project, "POS-03", "")
    result = sc.apply_edits(project)
    assert result.refused and result.refused[0][0] == "POS-02" and result.deletions == ["POS-03"]
    assert sc.check(project).ids("pending") == ["POS-02", "POS-03"]  # still waiting for the owner


# -- the real site ------------------------------------------------------------------------------


def test_real_site_text_is_all_covered():
    problems = sc.coverage_problems(ROOT / "site")
    assert not problems, (
        "descriptive text without a copy ID; give it data-copy=\"ID\" or a /*copy:ID*/ marker, then run "
        "python -m ffapp site-copy:\n  " + "\n  ".join(problems))


def test_real_copy_file_is_in_sync_with_the_code():
    report = sc.check(ROOT)
    behind = report.ids("stale", "new", "removed")
    assert not behind, f"site-copy.txt is behind the code for {', '.join(behind)}; run python -m ffapp site-copy"


def test_real_copy_file_has_no_unapplied_edits():
    report = sc.check(ROOT)
    pending, conflict = report.ids("pending"), report.ids("conflict")
    assert not pending and not conflict, (
        f"site-copy.txt has copy edits not yet applied (pending: {', '.join(pending) or 'none'}; "
        f"conflict: {', '.join(conflict) or 'none'}). Confirm with the owner, then run "
        "python -m ffapp site-copy --apply")
