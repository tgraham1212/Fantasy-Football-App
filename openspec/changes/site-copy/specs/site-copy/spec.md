## Purpose

One committed file, `site-copy.txt`, holds every piece of descriptive text on the site so the owner can copy-edit it in one place. The file stays in step with the code, new text cannot be added without appearing in it, and edits made in the file reach the site only after the owner confirms them.

## ADDED Requirements

### Requirement: Copy file contents
`site-copy.txt` SHALL hold every piece of descriptive text on the site: page and tab descriptions, headings, chart titles and notes, explanations, notes the scripts generate, and on-screen messages. Each entry SHALL have a stable ID, a short label, its location and its text, grouped by page or tab. Values the page fills in SHALL appear as `${...}` placeholders. Inline markup SHALL appear as written.

#### Scenario: Positions page key
- **WHEN** the owner opens `site-copy.txt`
- **THEN** the Positions section lists the dot key with its ID, a label, its location and its full sentence

#### Scenario: Generated note with a placeholder
- **WHEN** the Positions note for a season in progress is listed
- **THEN** its text reads with `${...}` placeholders where the week numbers go

### Requirement: Stable IDs in the code
Every entry SHALL be identified in the code itself: an HTML element by a `data-copy` attribute holding its ID, a script string by a `/*copy:ID*/` marker immediately before it. An entry's ID SHALL NOT change when the code around it moves.

#### Scenario: Code moved
- **WHEN** a function holding a marked string moves to another part of its script
- **THEN** the entry keeps its ID and its edits still apply to that string

### Requirement: Every piece of text covered
A test SHALL fail when the site has descriptive text without an ID:
- a heading, paragraph, list item or page title in the HTML without `data-copy`;
- a sentence-like string (at least four words) in a script without a copy marker, unless it is on a short list of exempt strings, such as developer error text.

#### Scenario: New paragraph without an ID
- **WHEN** a change adds a paragraph to a page without `data-copy`
- **THEN** the coverage test fails and names the paragraph

#### Scenario: New generated note without a marker
- **WHEN** a change adds a note sentence in a script without a copy marker
- **THEN** the coverage test fails and names the script and line

### Requirement: Code and copy file in sync
The system SHALL keep a sync record (`site-copy.lock.json`) of each entry's text as last synced. When an entry's code text differs from the sync record and its file text does not, the code has changed, and regenerating the file SHALL update the entry and the record. A test SHALL fail while the file is stale, naming the entries and the command that fixes it. A new ID in the code SHALL be added to the file on regeneration, and an ID removed from the code SHALL be dropped.

#### Scenario: Code text changed
- **WHEN** a change rewrites the Positions note in the script but not `site-copy.txt`
- **THEN** the sync test fails with the entry's ID and says to run `python -m ffapp site-copy`

#### Scenario: Regenerated
- **WHEN** `python -m ffapp site-copy` runs after that change
- **THEN** the file and the sync record carry the new text and the sync test passes

### Requirement: Pending copy edits confirmed with the owner
When an entry's text in `site-copy.txt` differs from the sync record and its code text does not, the entry SHALL count as a pending copy edit. A test SHALL fail while pending copy edits exist, listing their IDs and saying that the owner must confirm before they are applied. Running the tests or regenerating the file SHALL never apply or discard them. When the same entry has changed in both the code and the file, the test SHALL report a conflict for the owner to resolve.

#### Scenario: Owner edited the file
- **WHEN** the owner rewrites the text of entry POS-02 in `site-copy.txt`
- **THEN** the pending-edits test fails, lists POS-02, and says to confirm with the owner before running `python -m ffapp site-copy --apply`

#### Scenario: Regeneration keeps edits
- **WHEN** the file is regenerated while POS-02 has a pending edit
- **THEN** POS-02 keeps the owner's text

#### Scenario: Both sides changed
- **WHEN** POS-02 was edited in the file and its code text also changed
- **THEN** the test reports a conflict on POS-02 and nothing is overwritten

### Requirement: Applying copy edits
`python -m ffapp site-copy --apply` SHALL write each pending copy edit into its marked HTML element or script string and update the sync record. Placeholders and inline markup SHALL be written back as given. An edit that drops or changes a placeholder SHALL be refused, naming the entry. An entry left empty with a note asking for deletion SHALL be reported, not applied.

#### Scenario: Edit applied
- **WHEN** the owner confirms and `--apply` runs with a pending edit to POS-02
- **THEN** the Positions page key in `site/index.html` carries the new text, the sync record matches, and the sync and pending-edits tests pass

#### Scenario: Broken placeholder
- **WHEN** an edited generated note no longer contains `${payload.final_through}`
- **THEN** `--apply` refuses that entry, names it, and applies the others
