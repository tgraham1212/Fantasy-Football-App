# Tasks

## 1. Fresh scripts after deploy

- [x] 1.1 Add `?v=__BUILD__` to the script URLs in `site/index.html` and `site/calibration.html` and to the module imports in `site/app.js` and `site/war.js`, and verify both pages still load and work from `python -m http.server 8765 -d site` (Predictions, Player WAR, calibration)
- [x] 1.2 Add a workflow step after the data commit and before `upload-pages-artifact` that replaces `__BUILD__` with the short commit SHA in `site/*.html` and `site/*.js`, and verify by running the same `sed` locally on a copy of `site/` that every placeholder is replaced and the copy still serves
- [x] 1.3 Add `tests/test_site_files.py` asserting every local `<script src>` and `import ... from` reference in `site/*.html` and `site/*.js` carries the placeholder, and verify it passes now and fails when a reference is stripped in a temporary copy
- [x] 1.4 Document the stamp and the deploy step in the README's website and scheduled-job sections, and verify the described `sed` command matches the workflow

## 2. Season snapshot refresh

- [x] 2.1 Add an in-progress check to `capture_snapshots` (any configured league stores the season with a status other than `complete`) so such seasons are fetched on every run and replaced after a successful fetch, with completed seasons untouched, and verify tests in `tests/test_espn.py` cover the in-progress refresh, a completed season left alone, and a failed refresh leaving the stored snapshot intact
- [x] 2.2 Update the `snapshot` command's README entry and the Player WAR section to say the current season's snapshot settles at season end, and verify `python -m ffapp snapshot` on the real store re-fetches 2026 only

## 3. Spec hygiene and integration

- [x] 3.1 Run `openspec validate deploy-and-snapshot-cleanup` and `openspec validate --specs --strict` after the archive-time merge is simulated on a scratch copy of `openspec/specs/league-odds-site/spec.md`, and verify the merged spec passes strict validation with no length warnings
- [x] 3.2 Run `pytest` and `python -m ffapp refresh` locally and verify all tests pass, the 2026 season snapshot is re-fetched, and the site files still carry the placeholder after the refresh

## Workflow follow-up

- Commit and push after the user's review, then archive the change with spec sync.
