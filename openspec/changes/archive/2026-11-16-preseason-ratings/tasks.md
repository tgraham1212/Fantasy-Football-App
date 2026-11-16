# Tasks

## 1. Engine

- [x] 1.1 Record each season's post-draft status and members in `weekly_results`, emit week-0 entries in `run_ratings` (reverted or start rating, sigma unchanged, z null, career z carried) and put week-0 items in the file's week list; verify tests cover a returning manager (1300 → 1200), a newcomer (1000), a pre_draft season (no entries) and the week-list order

## 2. Export and site

- [x] 2.1 Make `elo_change` null when the latest entry is week 0 and measure the week-1 change from the preseason entry; verify `tests/test_export.py` covers both
- [x] 2.2 Label week-0 points "Pre" in the rating chart's axis and tooltip; verify by rendering the dynasty page and reading the first label
- [x] 2.3 Update the README's ratings section for the preseason entry and verify the full suite passes
