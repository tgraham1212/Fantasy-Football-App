# site-copy Specification

## Purpose

One committed file, `site-copy.txt`, holds every piece of descriptive text on the site, so the maintainer can copy-edit it in one place. The file stays in step with the code, new text cannot be added without appearing in it, and edits made in the file reach the site only after the maintainer confirms them. It serves need 10, Maintainable Project.

## Requirements

### Requirement: 10.16 Site copy file
`site-copy.txt` SHALL hold every piece of descriptive text on the site, grouped by page or tab, each entry with a stable ID, a short label, its location and its text, with page-filled values as `${...}` placeholders and inline markup as written.

**Traces to:** 10
**Verified by:** Test: `tests/test_site_copy.py::test_file_round_trip_keeps_labels_and_notes`; Test: `tests/test_site_copy.py::test_real_copy_file_is_in_sync_with_the_code`

#### Scenario: Generated note with a placeholder
- **WHEN** the Positions note for a season in progress is listed
- **THEN** its text reads with `${...}` placeholders where the week numbers go

### Requirement: 10.16.1 IDs in the code
Every entry SHALL be identified in the code itself, an HTML element by a `data-copy` attribute and a script string by a `/*copy:ID*/` marker just before it, so that its ID moves with it.

**Traces to:** 10.16
**Verified by:** Test: `tests/test_site_copy.py::test_extracts_html_and_marked_script_strings`

#### Scenario: Code moved
- **WHEN** a function holding a marked string moves to another part of its script
- **THEN** the entry keeps its ID and its edits still apply to that string

### Requirement: 10.16.2 Every piece of text covered
Every heading, paragraph, list item and page title in the HTML, and every script string of four words or more outside a short exempt list, SHALL carry a copy ID.

**Traces to:** 10.16
**Verified by:** Test: `tests/test_site_copy.py::test_coverage_finds_unmarked_text`; Test: `tests/test_site_copy.py::test_real_site_text_is_all_covered`

#### Scenario: New paragraph without an ID
- **WHEN** a change adds a paragraph to a page without `data-copy`
- **THEN** the coverage test fails and names the paragraph

### Requirement: 10.16.3 Code and copy file in step
`python -m ffapp site-copy` SHALL bring the file and its sync record, `site-copy.lock.json`, up to date with every entry whose code text changed while its file text did not.

**Traces to:** 10.16
**Verified by:** Test: `tests/test_site_copy.py::test_code_change_is_stale_and_regeneration_fixes_it`; Test: `tests/test_site_copy.py::test_real_copy_file_is_in_sync_with_the_code`

#### Scenario: Code text changed
- **WHEN** a change rewrites the Positions note in the script but not `site-copy.txt`
- **THEN** the sync test fails with the entry's ID and says to run `python -m ffapp site-copy`

### Requirement: 10.16.3.1 New and removed IDs
Regenerating the file SHALL add every new ID in the code and drop every ID removed from it.

**Traces to:** 10.16.3
**Verified by:** Test: `tests/test_site_copy.py::test_new_and_removed_ids`

#### Scenario: New entry
- **WHEN** a change adds text with a new copy ID
- **THEN** regenerating adds the entry to the file

### Requirement: 10.16.4 Pending copy edits
An entry whose file text differs from the sync record while its code text does not SHALL count as a pending edit, kept through test runs and regeneration and listed by a failing test until the maintainer confirms it.

**Traces to:** 10.16
**Verified by:** Test: `tests/test_site_copy.py::test_owner_edit_is_pending_and_survives_regeneration`; Test: `tests/test_site_copy.py::test_real_copy_file_has_no_unapplied_edits`

#### Scenario: Maintainer edited the file
- **WHEN** the maintainer rewrites entry POS-02 in `site-copy.txt`
- **THEN** the pending-edits test lists POS-02 and says to confirm with the maintainer before running `python -m ffapp site-copy --apply`

### Requirement: 10.16.4.1 Conflicting edits
An entry changed in both the code and the file SHALL be reported as a conflict for the maintainer, with neither side overwritten.

**Traces to:** 10.16.4
**Verified by:** Test: `tests/test_site_copy.py::test_both_sides_changed_is_a_conflict`

#### Scenario: Both sides changed
- **WHEN** POS-02 was edited in the file and its code text also changed
- **THEN** the test reports a conflict on POS-02 and nothing is overwritten

### Requirement: 10.16.5 Applying copy edits
`python -m ffapp site-copy --apply` SHALL write each pending edit into its marked HTML element or script string, with placeholders and markup as given, and update the sync record.

**Traces to:** 10.16; 10.16.4
**Verified by:** Test: `tests/test_site_copy.py::test_apply_writes_edits_back`

#### Scenario: Edit applied
- **WHEN** the maintainer confirms and `--apply` runs with a pending edit to POS-02
- **THEN** the Positions page key carries the new text and the sync record matches

### Requirement: 10.16.5.1 Edits refused
`--apply` SHALL refuse an edit that drops or changes a placeholder, and report an entry left empty with a note asking for deletion, applying the others.

**Traces to:** 10.16.5
**Verified by:** Test: `tests/test_site_copy.py::test_apply_refuses_changed_placeholders_and_reports_deletions`

#### Scenario: Broken placeholder
- **WHEN** an edited note no longer contains `${payload.final_through}`
- **THEN** `--apply` refuses that entry, names it, and applies the others
