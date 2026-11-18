# Tasks

## 1. Copy IDs in the code

- [x] 1.1 Add `data-copy="ID"` to every descriptive element in `site/index.html` and `site/calibration.html`, using the IDs from the current `site-copy.txt` (HDR, PRED, GAME, POS, WAR, CAL, MSG). Verify: `tests/test_site_files.py` and the layout check still pass (attributes only).
- [x] 1.2 Add `/*copy:ID*/` markers before every generated descriptive string in `site/app.js`, `games.js`, `positions.js`, `war.js`, `calibration.js`, `refresh.js` and `updates.js`, splitting a sentence out of a larger HTML template where needed, with no change to the output. Verify: the site renders identically (screenshot comparison of each tab at 1280 px before and after) and the layout check passes.

## 2. The site-copy command

- [x] 2.1 Add `src/ffapp/site_copy.py`:
  - extraction of `[data-copy]` HTML, keeping inline markup with whitespace collapsed
  - extraction of marked script literals: `"`, `'` and template literals, multi-line, with nested `${}`
  - rendering and parsing of `site-copy.txt` in the current format, keeping owner `NOTE:` lines and labels
  - the sync record `site-copy.lock.json` (ID to SHA-256), and the status of each entry (in sync, stale, pending, conflict, new, removed)

  Verify: unit tests on a temporary site for extraction, round trip and every status.
- [x] 2.2 Add the CLI `python -m ffapp site-copy [--check | --apply]`, handled before config loading:
  - regeneration updates stale, new and removed entries, never overwrites pending edits, and leaves conflicts alone
  - `--check` prints the statuses and exits non-zero on anything other than in sync
  - `--apply` writes pending edits into the code, refuses entries whose `${...}` placeholders changed, and reports deletion requests

  Verify: unit tests for apply, placeholder refusal and edits preserved through regeneration.
- [x] 2.3 Generate the real `site-copy.txt` and `site-copy.lock.json` with the command. Verify: every one of the current 97 entries is present with the same ID and text, and `--check` reports in sync.

## 3. Tests and the rule

- [x] 3.1 Add `tests/test_site_copy.py`:
  - coverage: unmarked HTML blocks, and unmarked sentence-like script strings minus an allowlist, fail with their location
  - in sync: stale, new or removed entries fail with the fix command
  - pending edits: pending or conflicting entries fail, listing their IDs and saying to confirm with the owner before `--apply`

  Verify: each test fails on a deliberately broken temporary copy (an unmarked paragraph, a changed script string, an edited file entry), then passes on the real site.
- [x] 3.2 Record the rule:
  - `openspec/config.yaml` context: new descriptive text gets a copy ID and is regenerated into `site-copy.txt` in the same change, and pending copy edits are confirmed with the owner before `--apply`
  - a README "Site copy" section covering how to edit, the commands, the statuses and the confirmation step
  - a Claude memory feedback entry to ask before applying

  Verify: the config parses (`openspec validate site-copy --strict`) and the README commands run as written.

## 4. Verify

- [x] 4.1 Run `pytest`, `node --test relay/worker.test.mjs` and `LAYOUT_REQUIRED=1 pytest tests/layout`. Then edit one entry in `site-copy.txt` on a scratch copy and show the pending-edits test failing with the confirmation message, and passing after `--apply` on the scratch copy. Verify: all pass, and the demonstration output is shown to the user.

## Workflow follow-up

- Commit, push and archive with spec sync when the user asks. When the owner sends an edited `site-copy.txt`, the tests flag the pending edits and Claude confirms with the owner before running `--apply`.
