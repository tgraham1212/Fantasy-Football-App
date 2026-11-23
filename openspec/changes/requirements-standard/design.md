# Design

## Context

See proposal.md (Why). Today each spec is a Purpose plus requirements, each with a statement and scenarios. Nothing links a requirement to a need or to its verification. `openspec validate --strict` limits a requirement's text (everything between its heading and its first scenario) to 500 characters. The reference lines this change adds count toward that limit.

Measured against `playoff-odds-simulation`, the 13 review findings are:
1. correctness;
2. nomenclature;
3. one thought per requirement;
4. tolerances;
5. error handling;
6. performance;
7. positive statements;
8. rationale;
9. traceability;
10. verification method;
11. overlap between specs;
12. clarity;
13. the method-versus-outcome question, settled below.

Feature docs affected: `docs/simulation.md`. Its "How It Is Calculated" step 5 gains the six-team constraint. No other feature doc changes, because the rest of this change edits specs, not features.

## Goals / Non-Goals

**Goals:**
- Every requirement traceable up to a need and down to its evidence, checked by a test.
- Each spec reviewed by the owner on its own, so a review is one spec, not 260 requirements.
- The original wording kept and recoverable.

**Non-Goals:**
- Changing behavior beyond the playoff-size check and the small fixes the owner approves at a spec's review.
- Writing every missing test. A requirement without one is marked as a verification gap, and gaps are listed and may only shrink.

## Decisions

### 1. Reference lines inside the requirement
Each requirement keeps its statement, then up to four bold lines before its scenarios:

```
### Requirement: 1.1.2 Real schedule
The simulation SHALL use each league's Sleeper matchup pairings for every remaining regular-season week.

**Rationale:** (only where the reason is not evident)
**Traces to:** 1.1
**Verified by:** Test: `tests/test_simulate.py::test_uses_real_pairings`
**TBR:** (only for an open item: rationale, what closes it, target date)
```

`openspec validate --strict` accepts this format (tested on this change's deltas). Because the lines count toward the 500-character limit, statements stay near 250 characters, and longer ones are split. That is the NASA conciseness rule anyway.

- **Alternative: a separate traceability matrix** (a CSV or table per spec). The matrix drifts from the text, and a reviewer has to read two files.
- **Alternative: front matter per requirement.** OpenSpec's parser does not support it.

### 2. Traces are associations, and the tree is many-to-many
`**Traces to:**` lists one or more parent IDs, separated by semicolons, primary parent first (decision 12). A trace is an association. It says which higher-level requirements a change to this one may affect, so a requirement may serve several parents.

The check resolves every parent and follows every chain upward. It reports:
- an orphan: no line, or a parent that does not exist;
- a cycle;
- a requirement none of whose chains reaches a need.

More than three parents is reported for review, because it usually means a compound lower-level requirement or overlapping higher-level ones. The owner may accept an exception, with a reason, in `tests/baselines/requirements_accepted.json`. Three is a starting threshold, revisited after the worked example.

Renaming a requirement breaks its children's links, which the check reports.

### 3. Needs are a spec, synced early
The needs are requirements in `openspec/specs/needs/spec.md`, with `**Verified by:** Children`. They are a goal level: a need is verified when its children are. The owner reviews them first.

The needs delta is then synced to the main specs right away, with `openspec-sync-specs` narrowed to this one delta, so that the rewritten specs can trace to needs during apply. The `project-standards` and `playoff-odds-simulation` deltas sync at archive as usual.

### 4. Main specs are edited directly
The rewrite of the existing specs is done in `openspec/specs/` as the implementation work. It is not written as MODIFIED deltas.

Writing about 260 MODIFIED blocks would copy every spec into this change. It would also make each spec's review a diff between two copies. The deltas here carry only new behavior: the needs, the standard's requirements and the playoff-size check. Every rewrite is checked by the requirements test and recoverable from the archive.

- **Alternative: MODIFIED deltas for everything.** This is the conventional route, but it doubles review effort for a change whose point is the review.

### 5. The requirements check
`tests/test_requirements.py` parses every main spec and the delta specs of every active change. For each requirement it reports:
- more than one SHALL, or SHALL NOT;
- a banned term;
- a missing or unresolvable Traces to, a cycle, or a chain that misses a need;
- a missing Verified by, a method outside Test, Analysis, Inspection and Demonstration (or Children for needs), or a Test reference whose file or function does not exist;
- a need with no children.

Findings go to `tests/baselines/requirements.json`, and open items (`TBR` lines and `Gap:` verifications) go to `tests/baselines/requirements_open.json`. Both use the existing shrink-only `tests/baselines.compare`. Each spec's commit shrinks the findings baseline. At the end of the change it is empty, and only open items remain.

The banned terms are read from a "Banned Terms" list in `openspec/glossary.md`, so the standard and the check share one list. That list is NASA's unverifiable terms plus "etc.", "and/or", "as needed", "as appropriate", "but not limited to", "TBD", and the retired nomenclature terms.

Tolerances, rationale and undefined terms are judgment calls a parser cannot make. They are verified by Inspection, recorded in the checklist (decision 10).

### 6. Method versus outcome (finding 13)
For the forecasting model, the method *is* the product. The empirical noise pools and the least-squares drift fit are what make it this model and not another. So requirements may name the method at the level a Manager would care about, for example "errors drawn from past misses of Players at the same position and projection level". The formulas stay in `Calculations.txt`, which the rationale points to. Requirements stay free of code-level detail: module, function and file names.

### 7. Playoff-size check
The check lives where the simulation starts for a league, in the code that builds the inputs for `simulate()`. It raises an error when `BracketRules.from_league(...).playoff_teams != 6`. The error fails the cold run's simulate step, so the run stops before committing or deploying, and the site keeps its last good Forecasts.

It is placed at the simulation and not inside `BracketRules`, because the export and the game Forecasts also read `BracketRules`. Failing there would hide which step cared. A test runs the simulation on a fixture league whose settings say 8.

### 8. Spec order and review gate
After the needs, the glossary and the worked example (`playoff-odds-simulation`), the specs go top-down, because a requirement is numbered under its primary parent (decision 12): the site pages first (closest to the needs), then the model and calculations, the refresh specs, the data specs, and the project specs.

A requirement whose primary parent sits in a spec not yet rewritten keeps its heading unnumbered and its finding in the baseline. It is numbered when it is next reached, or at the close-out sweep.

Each spec ends with a summary for the owner:
- requirements split, rewritten, added or cut;
- orphans, with a proposed new need or a cut;
- TBRs and verification gaps;
- any behavior fix needed.

Work stops until the owner approves. The spec is then committed (and pushed when the owner asks). A parent that is not rewritten yet leaves its children's chains incomplete. Those findings stay in the baseline until the parent's spec is done.

### 9. The archive
After `refresh-modes` archives, so its synced specs are included, `openspec/specs/` is copied to `openspec/specs-archive/pre-requirements-standard/` and the commit is tagged `specs-before-requirements-standard`. The folder sits outside `openspec/specs/`, so `openspec list`, validation and the requirements check never read it.

### 10. Inspection checklist
`openspec/inspection-checklist.md` has two tables:
- **Requirement inspections:** each requirement verified by Inspection, with its pass criteria, the date last inspected and the result.
- **Spec standard reviews:** each spec, with the date its judgment items (tolerances, rationale, glossary terms, compound statements the parser cannot see) were last reviewed and the result.

The check fails when:
- a requirement verified by Inspection has no row;
- a spec has no review row;
- a spec's file changed in a commit later than its review date (from `git log`).

So editing a spec without re-inspecting it fails once the edit is committed. The owner's approval at each spec's gate is the inspection, and its date goes in the table.

- **Alternative: a date on each requirement's Verified by line.** It spends the 500-character budget and scatters the record.

### 11. Impact report
`tools/requirements_impact.py <ID>` uses the check's parser to print the requirement's ancestors up to the needs and its descendants, with each one's verification reference. It is what a change author runs before editing a requirement, and the tasks rule tells them to.

### 12. Hierarchical IDs
Every requirement heading starts with an ID that shows its place in the tree, the owner's NASA practice:
- a need (level 0) is numbered in sequence: `1` to `12`;
- a requirement derived from it (level 1) is `1.1`, `1.2`;
- the next level is `1.2.1`, and so on.

```
1   Season Forecasts                    (needs)
1.1   Season simulation                 (playoff-odds-simulation)
1.1.2   Real schedule                   (playoff-odds-simulation)
1.1.2.1   Matchup pairings stored       (sleeper-league-sync)
```

IDs are global across specs, so a spec holds requirements from several branches, and the ID, not the file, says where each sits. The ID goes in the heading (`### Requirement: 1.1.2 Real schedule`), which OpenSpec accepts and which does not count toward the 500-character limit. Traces then cite bare IDs, which are shorter than spec-and-name references and survive a rename of the requirement's words.

**Several parents.** The ID follows the primary parent, listed first in `**Traces to:**`. Other parents are associations: they appear in the impact report and list the requirement as a child, but do not shape its ID.

**Numbering.** A new requirement takes the next unused number under its primary parent. Gaps are allowed. An ID is never reused: a cut or renumbered requirement's old ID goes in `openspec/retired-requirements.md` with its name, date and reason, so old commits and checklist entries never point at the wrong requirement.

**Renumbering.** Changing a requirement's primary parent gives it, and its whole subtree, new IDs, and retires the old ones. The impact report lists the subtree first. This is the price of IDs that carry lineage, and it is meant to be rare: adding a second parent does not renumber anything.

**Numbering goes top-down.** A requirement can be numbered only once its primary parent has an ID. So spec rewrites go from the needs downward (decision 8).

- **Alternative: flat IDs per spec** (`SIM-014`). Stable under re-parenting, but the ID says nothing about lineage, which is what the owner reads it for.

### 13. Requirements diagrams
`tools/requirements_diagram.py` draws the requirement tree from the same parser as the check, in SysML requirement-diagram notation:
- **Overview** (`docs/images/requirements/diagram.svg`): the twelve needs, each with its requirement count, depth, verification mix (Test, Inspection, Analysis, Demonstration, Gap), TBRs and requirements not yet numbered.
- **One tree per need** (`docs/images/requirements/need-N.svg`): the need at level 0, then each level in its own column, left to right. Each box is a «requirement» with its ID, name, statement and spec, and a TBR badge if it has one. A dashed «deriveReqt» arrow runs to its primary parent and a dotted «trace» arrow to each extra parent (a box from another need's branch is shown faded). A «verify» arrow comes from its test case, inspection row or gap.

One diagram for about 260 requirements would be unreadable. One per need keeps each one to a scrollable page and matches how the owner reviews.

The diagrams belong to a new feature doc, `docs/requirements.md`, which explains the standard, the IDs and how to read the diagrams. It is registered in `tests/test_feature_docs.py` with the specs folder as its "code", so any spec edit without a redraw fails the existing currency check. The check gets one extension: a generator may expose `OUTPUTS` (path to SVG) for several files instead of one `OUT`.

The drawing is regenerated in every spec's commit during apply, so it grows as specs are numbered. The mock-ups in this change's `mockups/` folder show the layout with dummy data.

- **Alternative: a modelling tool** (Cameo, Capella or SysML v2 text). A real model, but a second source of truth outside the repo and a tool the project does not otherwise need.

## Risks / Trade-offs

- **A rewrite changes a requirement's meaning** → the owner reviews each spec against the archive copy, and the scenarios, which are the acceptance tests, stay unless the review changes them.
- **Test names are brittle, and a refactor breaks references** → the check names each broken reference, and fixing it is part of the refactor.
- **The work is long (about 260 requirements)** → one spec per review. The baseline shows progress, and work can stop between specs without leaving anything half done.
- **The 500-character limit forces splits that read choppy** → rationale is optional and short. A long reason points to `Calculations.txt` or a feature doc instead of restating it.
- **The needs are drafted by the assistant** → they are the first thing the owner reviews, before any spec traces to them. Orphans found later revise them.
- **The playoff-size check stops the whole cold run, including the other league** → accepted for now. A backlog item records the plan to skip only the affected league, or to support other bracket sizes, should a league ever change.
- **Re-parenting renumbers a subtree** → the impact report lists it first, old IDs are retired, not reused, and a second parent never renumbers.
- **Verification gaps look like failures** → they are listed openly, as NASA intends. The list is a test-coverage map, not a defect count.

## Migration Plan

1. Wait for `refresh-modes` to archive with spec sync.
2. Archive the specs folder and tag the commit.
3. Owner reviews the needs, then sync them. Write the glossary, the check and the baselines. Add the standard to the config and `CLAUDE.md`.
4. Worked example, then the remaining specs one at a time, each reviewed and committed.
5. Archive this change, which syncs the `project-standards` and `playoff-odds-simulation` deltas.

**Rollback:** the archive folder or the tag restores any spec. Removing `tests/test_requirements.py` and its baselines removes the check.
