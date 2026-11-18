# Design

## Context

- **The one-off export.** `site-copy.txt` was produced by a scratch script. It holds 97 entries:
  - the HTML blocks of `site/index.html` and `site/calibration.html` (`p`, `li`, `h1`-`h3`, `title`)
  - 51 script strings found by line number and a search phrase, across `app.js`, `games.js`, `positions.js`, `war.js`, `calibration.js`, `refresh.js` and `updates.js`

  Line numbers move with every edit, so that approach cannot be kept.
- **Inline markup.** About 15 HTML blocks contain `<em>`, `<strong>`, `<code>` or links. Several script strings are template literals with `${...}` placeholders. A few are split across lines inside larger HTML templates (`calibration.js`).
- **Existing pattern.** The layout check's coverage test (`tests/layout/test_layout.py`) fails on unlisted controls. The project context in `openspec/config.yaml` records rules every change must follow.
- **The owner's request.** When `site-copy.txt` has edits, check with them before applying.

## Goals / Non-Goals

**Goals:**
- One command regenerates the file, reports drift, and applies edits.
- IDs live in the code, so entries survive refactors and edits land exactly.
- New text cannot slip past, and file edits never reach the site unconfirmed.

**Non-Goals:**
- Moving the site's text into a separate strings file that the page loads. The code stays the source; the file mirrors it.
- Translating or templating text.
- Covering table column labels, button labels and tab names. The file is for descriptive text; labels can be added later by giving them IDs.

## Decisions

**1. IDs in the code.**
- **HTML:** `data-copy="POS-02"` on the element whose text is the entry. Its inner HTML is the entry text, with inline tags kept.
- **Scripts:** a `/*copy:POS-04*/` comment immediately before the string literal. The literal may be `"..."`, `'...'` or a template literal, and may span lines.
- **Prefixes by section:** `HDR`, `PRED`, `GAME`, `POS`, `WAR`, `CAL`, `MSG`.
- **Seeding:** existing entries keep the IDs from the current export. New entries take the next free number in their section.
- **Labels** live in the file. A regeneration keeps an existing entry's label, and gives a new entry a label built from its location.
- Alternatives considered:
  - Line numbers plus a search phrase. Rejected: it breaks on every edit.
  - A central strings module. Rejected: a large refactor of every page, for no gain in what the owner sees.

**2. `src/ffapp/site_copy.py`, three operations.**
- `extract()` reads the HTML with an HTML parser, collecting `[data-copy]` elements and their inner HTML with whitespace collapsed, and reads the scripts with a scanner. The scanner finds `/*copy:ID*/`, then the next string literal, respecting escapes and the nesting of template-literal `${...}` expressions.
- `write_file()` renders the file in the current format. The header explains how to edit, then come sections and entries (`[ID] label`, `WHERE:`, `TEXT:`, and any `NOTE:` lines the owner added, which are kept).
- `parse_file()` reads it back.
- **CLI:**
  - `python -m ffapp site-copy` regenerates. Pending owner edits are never overwritten, and the sync record is updated only for code-side changes.
  - `--check` prints the status and exits non-zero when anything is stale, pending or conflicting.
  - `--apply` writes pending edits into the code.
- **The command needs no config file.** Like `stamp-site`, it is handled before the league config loads.

**3. Sync record `site-copy.lock.json`.**
- It maps each ID to the SHA-256 of its text as last synced, which is also the text the file was last regenerated with. Each entry's status:

  | code vs record | file vs record | status | action |
  |---|---|---|---|
  | same | same | in sync | none |
  | changed | same | stale | regenerate (automatic, no confirmation) |
  | same | changed | pending copy edit | owner confirms, then `--apply` |
  | changed | changed | conflict | owner resolves |
  | in code, not in file | n/a | new | regenerate |
  | in file, not in code | n/a | removed | regenerate drops it |

- Hashes instead of text keep the record small. The file itself shows the text.

**4. Tests (`tests/test_site_copy.py`).**
- **Coverage:**
  - Every `p`, `li`, `h1`-`h3` and `title` with text in the two HTML pages has `data-copy`, or sits inside one that does.
  - Every script string literal of at least four words containing a lowercase letter and a space is marked, except an allowlist. The allowlist covers developer and error text, such as `Could not load the odds data (${err.message}).`, and ARIA-only labels.
- **In sync:** no entry is stale, new or removed. The message gives the fix.
- **Pending edits:** no entry is pending or conflicting. The message lists the IDs and reads: "site-copy.txt has copy edits not yet applied; confirm with the owner, then run `python -m ffapp site-copy --apply`".
- **Unit tests on a temporary site:** extraction of attributes and markers (multi-line literal, nested `${}`), the round trip of parse and write, the status table, `--apply` writing back, placeholder refusal, and edits preserved through regeneration.
- These tests run in the code-push workflow, so a stale file or unapplied edits block a code deploy. The data refresh workflow does not run tests and is unaffected.

**5. Placeholder guard.** On `--apply`, the multiset of `${...}` expressions in the edited text must equal the code text's, in any order. Otherwise the entry is refused and named. Inline tags are written as given, and the layout check afterwards catches any layout effect.

**6. Where the rule lives.**
- **`openspec/config.yaml` context** gains two sentences:
  - every new piece of descriptive site text gets a copy ID (`data-copy` or `/*copy:ID*/`) and its entry is regenerated into `site-copy.txt` in the same change;
  - pending copy edits found by the tests are confirmed with the owner before `--apply`.
- **README:** a "Site copy" section covering editing, the commands, the statuses, and that applying needs the owner's go-ahead.
- **Claude memory:** a feedback entry, so I ask before applying.

## Risks / Trade-offs

- [The heuristic coverage scanner flags non-copy strings, or misses short ones] → an explicit allowlist for false positives. Short labels are a declared non-goal.
- [Owner edits committed without applying would block code deploys] → intended: the tests make the pending state visible. The data refresh keeps running.
- [Template literals with HTML inside (calibration tables) are hard to mark] → mark the literal holding the sentence. Where a sentence is part of a larger template, split it into its own marked literal concatenated in, with no change to the output.
- [Markers add noise to scripts] → short comments, one per sentence.

## Migration Plan

1. Add the IDs from the current export to the code. Generate `site-copy.txt` and the sync record with the command, and check the output matches today's file entry for entry, apart from format tweaks.
2. Land the tests, the rule and the docs together.
3. Rollback: delete the command, the tests, the markers and the files. The site's output never depends on them.

## Open Questions

None.
