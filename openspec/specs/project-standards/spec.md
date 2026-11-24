# project-standards Specification

## Purpose

Records the standards every change to the project follows (browsers, phone sizes, accessibility, Material Design usability, colour, Player names, nomenclature, writing style, calculation and feature documentation, and requirements) where planned work and everyday work both see them, and checks the ones that can be checked. It serves needs 9, Usable by Every Manager, and 10, Maintainable Project; the terms are in `openspec/glossary.md`.

## Requirements

### Requirement: 10.1 Requirements standard recorded
The requirements standard SHALL be written in the `openspec/config.yaml` project context and summarised in `CLAUDE.md`, with a tasks rule that makes every planned change write requirements to it.

**Rationale:** Planned changes read the context; every session reads `CLAUDE.md`.
**Traces to:** 10
**Verified by:** Inspection: `openspec/config.yaml` (context and `rules.tasks`), `CLAUDE.md`

#### Scenario: Planning a change
- **WHEN** a change is proposed
- **THEN** its tasks instructions include the rule to write requirements to the standard

### Requirement: 10.2 One statement per requirement
Each requirement SHALL state one thing, positively, in a single sentence or a sentence with a list, using `SHALL` once and never `SHALL NOT`.

**Rationale:** NASA SEH Appendix C, Clarity and General Goodness: one subject and one predicate per requirement, stated positively, makes each one verifiable on its own.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_one_shall_per_requirement`

#### Scenario: Two behaviors in one requirement
- **WHEN** a requirement reads "the page SHALL swap the data and SHALL keep the scroll position"
- **THEN** the requirements check reports it until it is split into two requirements

#### Scenario: Negative statement
- **WHEN** a requirement reads "players on injured reserve SHALL NOT start"
- **THEN** the requirements check reports it until it is restated positively

### Requirement: 10.3 Verifiable wording
Requirement statements SHALL use only verifiable terms, excluding the unverifiable and ambiguous terms and the retired nomenclature terms listed in the glossary (among them `adequate`, `fast`, `robust`, `etc.`, `and/or`).

**Rationale:** NASA SEH Appendix C, Verifiability: a term that cannot be measured cannot be tested.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_no_banned_terms`

#### Scenario: Vague speed
- **WHEN** a requirement says the page loads "quickly"
- **THEN** the requirements check names the term and the requirement

### Requirement: 10.4 Tolerances on values
A requirement that states a quantity SHALL state its unit and its tolerance or bound (for example "within 2 minutes", "at least 10,000 runs", "±0.1 percentage point").

**Rationale:** NASA SEH Appendix C, Product Requirement and Performance: a value without a bound has no pass or fail.
**Traces to:** 10
**Verified by:** Inspection: `openspec/inspection-checklist.md`, the spec's standard review

#### Scenario: Sum with rounding
- **WHEN** a requirement says outcome probabilities sum to 100% "allowing for rounding"
- **THEN** it is restated as "100% ±0.1 percentage point"

### Requirement: 10.4.1 Spec standard review record
`openspec/inspection-checklist.md` SHALL record, for every spec, the date its standard review (tolerances, rationale, glossary terms) was last done and the result.

**Rationale:** These judgment checks cannot be parsed, so each review is dated instead.
**Traces to:** 10.4; 10.5; 10.10
**Verified by:** Test: `tests/test_requirements.py::test_every_spec_has_a_dated_review`

#### Scenario: Re-inspection after a change
- **WHEN** a change edits a spec
- **THEN** that spec's standard review is redone and its checklist date updated in the same change

### Requirement: 10.5 Rationale where not obvious
A requirement whose reason is not evident from its statement SHALL carry a one-line `**Rationale:**` giving the reason and any assumption, or a pointer to the `Calculations.txt` section that records it.

**Rationale:** NASA SEH Appendix C, General Goodness: an intelligible rationale lets a later reader judge whether the requirement still holds.
**Traces to:** 10
**Verified by:** Inspection: `openspec/inspection-checklist.md`, the spec's standard review

#### Scenario: A modelling choice
- **WHEN** a requirement fixes the noise pool minimum at 200 residuals
- **THEN** its rationale says why, or points to `Calculations.txt` section 4

### Requirement: 10.6 Requirement tree
Every requirement other than a need SHALL carry a `**Traces to:**` line listing one or more parent IDs separated by semicolons, primary parent first, so that every parent chain reaches a need without a cycle.

**Rationale:** A trace associates a requirement with the higher-level ones a change to it may affect.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_every_requirement_reaches_a_need`

#### Scenario: Two levels
- **WHEN** requirement 1.2.1 traces to 1.2, which traces to need 1
- **THEN** the requirements check accepts both

#### Scenario: Two parents
- **WHEN** a requirement traces to `2.3; 1.4`
- **THEN** the requirements check accepts it, and both parents list it as a child

#### Scenario: Orphan
- **WHEN** a requirement has no Traces to line, or names a parent ID that does not exist
- **THEN** the requirements check reports it as an orphan

#### Scenario: Cycle
- **WHEN** two requirements trace to each other
- **THEN** the requirements check reports the cycle

### Requirement: 10.6.1 Requirement IDs
Every requirement heading SHALL begin with a unique ID: a need's ID is its sequence number, and a derived requirement's ID is its primary parent's ID followed by a dot and the next unused number at that level.

**Rationale:** The ID shows a requirement's level and lineage at a glance, as in NASA practice.
**Traces to:** 10.6
**Verified by:** Test: `tests/test_requirements.py::test_ids_follow_the_primary_parent`

#### Scenario: Third level
- **WHEN** a requirement's primary parent is 1.2
- **THEN** its ID is 1.2.N, where N is the next unused number under 1.2

#### Scenario: ID that does not match its parent
- **WHEN** requirement 3.1.2 lists 1.4 as its primary parent
- **THEN** the requirements check reports the mismatch

#### Scenario: Primary parent changes
- **WHEN** a requirement's primary parent is changed to another requirement
- **THEN** it and its descendants take new IDs under the new parent, and the old IDs are retired

### Requirement: 10.6.1.1 Retired IDs
An ID SHALL never be reused: when a requirement is cut or renumbered, its old ID is listed in `openspec/retired-requirements.md` with the requirement's name, the date and the reason.

**Rationale:** A reused ID would make old commits, reviews and checklist entries point to the wrong requirement.
**Traces to:** 10.6.1
**Verified by:** Test: `tests/test_requirements.py::test_retired_ids_are_not_reused`

#### Scenario: Cut requirement
- **WHEN** requirement 4.2.3 is cut
- **THEN** 4.2.3 is listed as retired, and the next requirement under 4.2 takes a new number

### Requirement: 10.6.2 Parent count review
The requirements check SHALL report every requirement with more than three parents, unless the maintainer has accepted it with a reason in `tests/baselines/requirements_accepted.json`.

**Rationale:** Many parents signal a compound requirement or overlapping higher-level ones.
**Traces to:** 10.6
**Verified by:** Test: `tests/test_requirements.py::test_parent_count_is_reviewed`

#### Scenario: Four parents
- **WHEN** a requirement traces to four parents and is not accepted
- **THEN** the requirements check names it, to be split or have its parents reviewed

#### Scenario: Accepted exception
- **WHEN** the owner accepts a four-parent requirement with a reason
- **THEN** the requirements check passes and the reason stays on record

### Requirement: 10.6.3 Impact report
`python -X utf8 tools/requirements_impact.py <ID>` SHALL list every requirement and need above and below the given requirement in the tree, with the verification reference of each.

**Rationale:** The point of tracing is to see what a change to one requirement may affect.
**Traces to:** 10.6
**Verified by:** Test: `tests/test_requirements.py::test_impact_report_lists_ancestors_and_descendants`

#### Scenario: Changing a simulation requirement
- **WHEN** the report runs for a simulation requirement with two parents and children
- **THEN** it lists both parent chains up to the needs, the requirements below it, and how each is verified

### Requirement: 10.6.4 Requirements diagrams
The requirements diagrams, an overview of the needs and one tree per need in SysML requirement-diagram notation, SHALL be drawn from the specs by `tools/requirements_diagram.py` and match what it draws from the committed specs.

**Rationale:** Model-based systems engineering practice; a diagram drawn from the specs cannot drift from them.
**Traces to:** 10.6; 10.13
**Verified by:** Test: `tests/test_feature_docs.py::test_diagrams_are_generated_and_current`

#### Scenario: Spec edited without a redraw
- **WHEN** a commit adds requirement 1.1.4 without rerunning the generator
- **THEN** the feature-docs check fails naming the out-of-date diagram

#### Scenario: Reading a need's tree
- **WHEN** someone opens need 1's diagram
- **THEN** it shows every requirement under need 1 by level, its spec, its «deriveReqt» link to its primary parent, «trace» links to other parents, and its «verify» test, inspection or gap

### Requirement: 10.7 Every need delivered
Every need SHALL have at least one requirement tracing to it.

**Rationale:** A need with no children is a need nothing delivers.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_every_need_has_children`

#### Scenario: Childless need
- **WHEN** no requirement traces to a need
- **THEN** the requirements check names the need

### Requirement: 10.8 Verification reference
Every requirement other than a need SHALL carry a `**Verified by:**` line giving its method and evidence:
- Test: `tests/<file>.py::<function>`, which exists;
- Analysis: a report and its section;
- Inspection: a file and what to look for;
- Demonstration: a named procedure in `docs/`.

**Rationale:** NASA SEH Appendix C, Verifiability.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_every_requirement_has_a_verification`

#### Scenario: Test renamed
- **WHEN** a referenced test function is renamed or deleted
- **THEN** the requirements check names the requirement and the missing test

#### Scenario: No test yet
- **WHEN** no test verifies a requirement yet
- **THEN** its line reads `**Verified by:** Gap: <what would verify it>`, and the gap is listed in a baseline

### Requirement: 10.8.1 Inspection record
`openspec/inspection-checklist.md` SHALL list every requirement verified by Inspection with its pass criteria, the date it was last inspected and the result.

**Rationale:** An inspection counts only when its criteria and date are written down.
**Traces to:** 10.8
**Verified by:** Test: `tests/test_requirements.py::test_inspection_checklist_covers_every_inspection`

#### Scenario: New inspection requirement
- **WHEN** a change adds a requirement verified by Inspection without a checklist entry
- **THEN** the requirements check names the requirement

#### Scenario: Linked requirement changes after an inspection
- **WHEN** an inspected requirement, or a requirement directly linked to it (a parent or a child, primary or association), is added or changed in a commit after the inspection was recorded
- **THEN** the requirements check fails until the requirement is inspected again and its date updated

#### Scenario: Distant change
- **WHEN** a requirement two or more links away from an inspected requirement changes
- **THEN** that inspection stands, since its direct links were re-inspected

### Requirement: 10.9 Open items marked
A value or behavior that cannot be settled yet SHALL be marked `**TBR:**` with its rationale, what closes it and a target date (`YYYY-MM` or `YYYY-MM-DD`).

**Rationale:** NASA SEH Appendix C, Completeness: open items are stated openly rather than hidden in vague wording.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_tbr_has_a_target_date`

#### Scenario: TBR without a date
- **WHEN** a TBR line gives no target date
- **THEN** the requirements check names the requirement

### Requirement: 10.9.1 Open items listed
Every TBR and verification gap SHALL be listed in `tests/baselines/requirements_open.json`, which may only shrink.

**Rationale:** One list shows every open item and keeps new ones from slipping in unseen.
**Traces to:** 10.9; 10.8
**Verified by:** Test: `tests/test_requirements.py::test_open_items_match_the_baseline`

#### Scenario: New TBR
- **WHEN** a change adds a TBR without adding it to the baseline
- **THEN** the requirements check fails naming it

### Requirement: 10.10 Glossary
`openspec/glossary.md` SHALL define every project term that specs use with a specific meaning, the nomenclature rules and the banned-terms list.

**Rationale:** NASA SEH Appendix C, Consistency: terminology is used consistently and key terms are defined in one glossary.
**Traces to:** 10
**Verified by:** Inspection: `openspec/inspection-checklist.md`; Test: `tests/test_requirements.py::test_glossary_entries_are_used`

#### Scenario: Undefined term
- **WHEN** a spec's standard review finds "Slate Forecast" used as a term the glossary does not define
- **THEN** the term is added to the glossary in the same change

#### Scenario: Dead entry
- **WHEN** a glossary term is used in no spec
- **THEN** the requirements check names the entry

### Requirement: 10.11 Requirements check
`tests/test_requirements.py` SHALL check every main spec and every active change's delta specs against the requirements standard, reporting each finding with its spec and requirement ID.

**Rationale:** What is checked automatically stays true across sessions.
**Traces to:** 10
**Verified by:** Test: `tests/test_requirements.py::test_findings_match_the_baseline`

#### Scenario: Findings baselined
- **WHEN** a spec not yet brought to the standard has findings
- **THEN** they are listed in `tests/baselines/requirements.json`, and fixing one without removing it from the baseline fails the check

### Requirement: 10.12 Specs archived before the standard
The specs as they stood before the requirements standard SHALL be kept unchanged at `openspec/specs-archive/pre-requirements-standard/` and under the git tag `specs-before-requirements-standard`.

**Rationale:** The owner asked for a way back to the original wording if a rewrite loses meaning.
**Traces to:** 10
**Verified by:** Inspection: the folder and `git tag --list specs-before-requirements-standard`

#### Scenario: Recovering a requirement
- **WHEN** a rewritten requirement is found to have lost meaning
- **THEN** its original text is read from the archive folder or the tag

### Requirement: 10.13 Feature docs
Each feature whose flow is worth explaining SHALL have a living `docs/<feature>.md` with a diagram drawn by `tools/<feature>_diagram.py`, registered in `tests/test_feature_docs.py` with the code files whose changes must update it.

**Rationale:** The standard was adopted with the simulation doc and recorded in the project context; this records it in the spec.
**Traces to:** 10
**Verified by:** Test: `tests/test_feature_docs.py::test_diagrams_are_generated_and_current`

#### Scenario: Stale diagram
- **WHEN** a diagram's generator changes and the SVG is not redrawn
- **THEN** the feature-docs check fails naming the generator

### Requirement: 10.14 Standards recorded
The project standards SHALL be written in the `openspec/config.yaml` context and summarised in `CLAUDE.md`, covering browsers, phone widths, accessibility, Material Design, colour, Player names, nomenclature, style, and calculation and feature documentation.

**Rationale:** Planned changes read the context; every session reads `CLAUDE.md`.
**Traces to:** 10
**Verified by:** Inspection: `openspec/config.yaml` (context) and `CLAUDE.md`, each listed standard is present

#### Scenario: Quick fix outside a change
- **WHEN** a small fix is made without a planned change
- **THEN** the standards in `CLAUDE.md` apply to it

### Requirement: 9.5 Supported browsers
Every change SHALL work in Chrome, Safari, Edge and Firefox on desktop, and in Chrome and Safari on phones, at the tested phone widths.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_layout.py::test_control_keeps_the_layout`; Test: `tests/layout/test_layout.py::test_wide_fonts_do_not_scroll_sideways`

#### Scenario: Safari on a phone
- **WHEN** a change ships a new page
- **THEN** the page works in Safari's engine at the tested phone widths

### Requirement: 9.5.1 Phone widths from statistics
The tested phone widths SHALL cover StatCounter's top six US mobile screen widths, reviewed at least once a year and whenever a new width enters the top six.

**Rationale:** October 2026 statistics: 414, 390, 384, 360, 402 and 393 px; tested at 360, 390, 414 and 440 px.
**Traces to:** 9.5
**Verified by:** Inspection: `openspec/config.yaml`, the dated StatCounter figures, next due 2027-10

#### Scenario: Width list from statistics
- **WHEN** the yearly review finds a new width in the top six
- **THEN** the tested widths are updated to cover it

### Requirement: 9.6 Material Design 3 usability
Interactive controls SHALL follow Material Design 3's usability rules, touch targets of at least 48 × 48 px on phones, visible focus and pressed states, and a consistent type scale, while the site keeps its own visual style.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_accessibility.py::test_touch_targets_on_phones`; Inspection: the live site, focus and pressed states and the type scale

#### Scenario: New control
- **WHEN** a change adds a button
- **THEN** it has a visible focus state and, on phones, a touch target of at least 48 × 48 px

### Requirement: 9.7 Colour standard
Site colours SHALL be chosen and adjusted in OKLCH, a contrast fix changing only lightness and keeping hue and chroma, and a new colour derived from an existing hue where one fits.

**Rationale:** Tokens are stored as hex, each adjusted one noting its OKLCH lightness (`tools/team_palette.py` has the helpers).
**Traces to:** 9
**Verified by:** Inspection: `site/styles.css`, adjusted tokens carry their OKLCH note

#### Scenario: Grey text too light
- **WHEN** a grey text colour fails its contrast ratio
- **THEN** the fix lowers its OKLCH lightness and keeps its hue and chroma

### Requirement: 9.7.1 Colour contrast check
For light and dark mode, a test SHALL check each text colour token against its backgrounds at 4.5:1, and focus rings and chart lines against the page and card backgrounds at 3:1, naming the mode, both tokens and the ratio on failure.

**Traces to:** 9.7; 9
**Verified by:** Test: `tests/test_colour_contrast.py::test_colour_tokens_meet_contrast`; Test: `tests/test_colour_contrast.py::test_check_catches_dark_only_failure`

#### Scenario: Chart text too light
- **WHEN** a change sets chart axis text to a grey of 3.5:1 on cards in light mode
- **THEN** the check fails naming light mode, the two tokens and 3.5:1

### Requirement: 9.7.1.1 Every colour token classified
Every colour token SHALL be checked as a text, line or background colour, or exempted with a reason.

**Traces to:** 9.7.1
**Verified by:** Test: `tests/test_colour_contrast.py::test_unclassified_token_fails`

#### Scenario: New token
- **WHEN** a change adds a colour token without classifying it
- **THEN** the contrast test fails naming the token

### Requirement: 9.8 Player name standard
Wherever the site shows a Player's name in a limited space, it SHALL show the full name, switching to first initial and last name ("A. St. Brown") only when the full name does not fit, a defence by its team nickname, with the full name in a tooltip and never cut off.

**Traces to:** 9
**Verified by:** Test: `tests/layout/test_layout.py::test_phone_lineups_show_full_names`; Test: `tests/layout/test_managers_page.py::test_cards_cut_nothing_and_never_scroll_sideways`

#### Scenario: Name does not fit
- **WHEN** "Amon-Ra St. Brown" is wider than its space
- **THEN** "A. St. Brown" shows, with the full name on hover

### Requirement: 10.10.1 Nomenclature
Everything people read, site text, documentation and specs, SHALL use the glossary's terms: Managers, Team Names, Players, Forecasts for the simulation's output, and Projections only for Sleeper's inputs.

**Traces to:** 10.10
**Verified by:** Test: `tests/test_nomenclature.py::test_site_copy_uses_project_nomenclature`; Test: `tests/test_requirements.py::test_no_banned_terms`

#### Scenario: Forecast wording
- **WHEN** a change adds a note describing the simulation's playoff numbers
- **THEN** the note calls them Forecasts

### Requirement: 10.10.1.1 Nomenclature check
A test SHALL flag each `site-copy.txt` entry using a retired term (`owner`, `odds`, `chances`, or `prediction` for a Forecast) that is not in a committed baseline, code and data identifiers exempt.

**Traces to:** 10.10.1; 10.16
**Verified by:** Test: `tests/test_nomenclature.py::test_site_copy_uses_project_nomenclature`; Test: `tests/test_nomenclature.py::test_flagged_terms`

#### Scenario: Retired term in new copy
- **WHEN** a change adds site text reading "the owner's odds"
- **THEN** the check fails naming the entry and the terms

### Requirement: 10.15 Writing style
Writing SHALL follow APA style, with titles and headings in title case.

**Traces to:** 10
**Verified by:** Inspection: `openspec/inspection-checklist.md`, each spec's standard review

#### Scenario: New heading
- **WHEN** a change adds a section titled "how it works"
- **THEN** the review corrects it to "How It Works"
