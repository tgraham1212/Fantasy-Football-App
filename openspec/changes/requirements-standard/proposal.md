# Proposal

## Why

The project's 30 specs hold 258 requirements, and none of them can be traced to a stated need or to the test that verifies it. A review of `playoff-odds-simulation` against the NASA Systems Engineering Handbook, Appendix C ("How to Write a Good Requirement") found:
- a requirement that contradicts the code;
- a hidden assumption that would produce wrong Forecasts without warning;
- requirements that state several things at once;
- values with no tolerance;
- retired terms;
- no rationale, no verification method and no parent.

The same gaps run through every spec. Now that features have living docs, the requirements should meet the same bar: each one traceable up to a need and down to its verification.

## What Changes

- **Requirements standard.** Every requirement states one thing, stated positively, with one SHALL. It uses no ambiguous or unverifiable terms, and gives tolerances wherever it has numbers. It carries a rationale where the reason is not obvious, plus two reference lines:
  - **Traces to:** the IDs of its parent requirements or top-level need;
  - **Verified by:** Test, Analysis, Inspection or Demonstration, with the reference.
- **Requirement tree.** A requirement traces to one or more parents (requirements in any spec, or needs). A trace is an association: it shows what a change to the requirement may affect. Every requirement reaches a need through at least one chain. An orphan reveals a missing need, which gets defined, or a requirement no one needs, which gets cut. More than three parents is flagged for review, as a sign of a compound requirement or overlapping parents. An impact report lists everything above and below a requirement.
- **Hierarchical IDs.** Every requirement heading starts with an ID showing its lineage: needs are numbered 1 to 12 (level 0), a requirement derived from need 1 is 1.1, the next level 1.1.1, and so on. A requirement with several parents takes its ID from its primary parent, listed first. IDs are never reused; retired IDs are listed in `openspec/retired-requirements.md`.
- **Top-level needs.** A new `needs` capability states what the app is for, as twelve numbered needs that every requirement ultimately traces to. The owner reviews the needs before any other spec is touched.
- **Requirements diagrams.** SysML-style diagrams drawn from the specs by `tools/requirements_diagram.py`: an overview of the twelve needs with their verification coverage, and one requirement tree per need. A spec edited without a redraw fails the feature-docs check, so the diagrams stay current. They live in a new feature doc, `docs/requirements.md`.
- **Glossary.** `openspec/glossary.md` defines the project's terms (Forecast, as-of week, slate, FLEX, replacement level and others) and takes over the nomenclature rules.
- **Inspection checklist.** `openspec/inspection-checklist.md` records each Inspection-verified requirement's criteria, and each spec's standard review, with the date and result. Editing a spec after its review date fails the check until it is re-inspected.
- **TBR tracking.** A value or behavior that cannot be settled yet is marked To Be Resolved, with its rationale, what closes it and a target.
- **Enforcement.** A new `tests/test_requirements.py` parses every spec. It fails on:
  - a broken or circular trace, or an orphan;
  - a need with no children;
  - a missing verification method, or a test reference that does not exist;
  - banned terms, `SHALL NOT`, or more than one SHALL.

  Today's gaps sit in baselines that may only shrink. A tasks rule makes new changes write compliant requirements.
- **Every spec brought to the standard, one at a time.** Each spec is reviewed by the owner and then committed, starting with `playoff-odds-simulation` as the worked example and then going top-down (pages, model, refresh, data, project), since a requirement is numbered under its parent. The review covers all 13 findings: correctness, nomenclature, one thought per requirement, tolerances, error handling, performance, positive statements, rationale, traceability, verification method, cross-spec overlap and clarity.
- **Playoff size fails loudly.** A league whose Sleeper settings give a playoff size other than six makes the simulation stop with a clear error, instead of forecasting a six-team bracket.
- **Archive of the specs before the change.** A frozen copy at `openspec/specs-archive/pre-requirements-standard/` and a git tag, `specs-before-requirements-standard`.
- **Feature docs requirement.** The feature-docs standard adopted earlier is recorded in `project-standards`, where it was missing.

## Capabilities

### New Capabilities
- `needs`: the app's top-level needs, which every requirement ultimately traces to.

### Modified Capabilities
- `project-standards`: adds the requirements standard (form, traceability, verification, glossary, TBR tracking, the requirements check and the spec archive) and the feature-docs requirement.
- `playoff-odds-simulation`: a league with a playoff size other than six fails the simulation with a clear error.

The other specs are rewritten to the standard without changing the behavior they describe. Where the review finds behavior that is unspecified or wrong, the owner decides at that spec's review: a small fix in this change, or a TBR.

## Impact

- **Specs:** all of `openspec/specs/`, including the two capabilities `refresh-modes` adds when it archives. This change is applied after `refresh-modes` archives.
- **New files:** `openspec/glossary.md`, `openspec/inspection-checklist.md`, `openspec/retired-requirements.md`, `tools/requirements_impact.py`, `tools/requirements_diagram.py`, `docs/requirements.md` and its diagrams, `openspec/specs/needs/`, `openspec/specs-archive/pre-requirements-standard/`, `tests/test_requirements.py`, and baselines in `tests/baselines/`.
- **Code:** `src/ffapp/simulate.py` or `src/ffapp/bracket.py` (the playoff-size check), plus any small fixes the owner approves at a spec's review.
- **Standards:** `openspec/config.yaml` (context and rules) and `CLAUDE.md`.
- **Tests:** new tests where a requirement's verification needs one and the owner approves adding it. Otherwise the requirement is recorded as a verification gap.
