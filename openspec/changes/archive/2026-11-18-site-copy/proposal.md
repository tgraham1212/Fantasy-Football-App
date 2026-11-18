# Proposal

## Why

The site's descriptive text is spread across two HTML pages and seven scripts: page descriptions, chart titles and notes, explanations and messages. To copy-edit it, the owner needs one file holding all of it, and the file has to stay current as features add text. A one-off export (`site-copy.txt`, 97 entries) exists today, but nothing keeps it in sync. Editing it changes nothing on the site, and new text would silently be missing from it.

## What Changes

- **`site-copy.txt` becomes a committed, living file.** It holds every piece of descriptive text on the site, each with:
  - a stable ID (for example `POS-02`)
  - a label and its location
  - the text, with page-filled placeholders shown as `${...}` and inline markup (`<em>`, `<strong>`, `<code>`, links) kept visible
- **Stable markers in the code.** Each piece of text gets an ID in the code itself:
  - HTML elements carry `data-copy="ID"`.
  - Generated strings in scripts carry a `/*copy:ID*/` marker just before the string.
  - IDs survive code moves. They let edits be written back exactly.
- **A new command, `python -m ffapp site-copy`:**
  - with no option, it regenerates the file from the code, keeping each entry's ID and label;
  - `--check` reports what is out of sync;
  - `--apply` writes edited text from the file back into the HTML and scripts.
- **A sync record, `site-copy.lock.json`.** It holds each entry's text as last synced, so the command can tell the two directions apart:
  - **code changed** (the file is stale): regenerate;
  - **the file was edited** (pending copy edits): apply them, but only after the owner confirms.
- **Tests:**
  - **Coverage:** every descriptive element in the HTML, and every sentence-like string in the scripts, must carry an ID. Unlisted text fails, like the layout check's rule for unlisted controls.
  - **Code and file in sync:** the code's text and the file must agree. Code changed without regenerating fails, with a fix hint.
  - **Pending copy edits:** when the file has edits not yet in the code, the test fails and lists the IDs. Its message says to check with the owner before running `--apply`.
- **The rule is recorded where future work sees it:**
  - in the `openspec/config.yaml` project context: new descriptive text gets an ID and goes into `site-copy.txt` in the same commit, and pending copy edits are confirmed with the owner before they are applied;
  - in the README;
  - as a working preference in Claude's memory.

## Capabilities

### New Capabilities
- `site-copy`: the copy file of all descriptive site text, covering its stable IDs, coverage of new text, keeping file and code in sync, detecting edits made in the file, and applying them only after the owner confirms.

### Modified Capabilities
<!-- none: the site's text itself does not change in this change -->

## Impact

- **Code:**
  - New `src/ffapp/site_copy.py` and a `site-copy` CLI command.
  - `site/index.html`, `site/calibration.html`: `data-copy` attributes.
  - `site/*.js`: `/*copy:ID*/` markers. These change no behaviour, and the stamping and layout tests are unaffected.
- **Files:** `site-copy.txt` and `site-copy.lock.json`, both committed.
- **Tests:** a new `tests/test_site_copy.py`. Because it runs in the code-push workflow, an out-of-sync file blocks the deploy.
- **Docs and config:** README, `openspec/config.yaml` context, and Claude's project memory.
- No new dependencies. The data refresh workflow is unaffected, because it does not run the tests.
