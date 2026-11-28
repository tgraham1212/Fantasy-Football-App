## Purpose

The rookie pick value model: the WAR a dynasty rookie pick has been worth over its Player's first 8 seasons, by round and third of the round, built from thirteen rookie classes and the site's own Player WAR, and the value it gives a pick not used yet. It serves need 4, Manager History, through the Trades tab (`league-trades`) and `pick-values-page`; the formulas are in `Calculations.txt`.

## ADDED Requirements

### Requirement: 4.12 Rookie pick values
The system SHALL keep a pick value model giving each dynasty rookie pick group the WAR its Players have averaged over the 8 seasons from their draft.

**Rationale:** A pick carries no WAR until it is used; trades of picks need a value grounded in history.
**Traces to:** 4
**Verified by:** Test: `tests/test_pick_values.py::test_model_values`

#### Scenario: First-round early pick
- **WHEN** the model is built from the 2013–2025 classes
- **THEN** a 1st-round pick in slots 1 to 4 is worth +3.38 WAR, to 0.01

### Requirement: 4.12.1 Rookie order sources
A rookie class's draft order SHALL be its DLF post-draft mock ADP for 2013–2021 and this league's rookie draft from 2022, the 2022 startup draft's rookies counting in pick order.

**Rationale:** The DLF order agrees with this league's own rookie drafts at 0.79–0.90 (rank correlation) for 2022–2026.
**Traces to:** 4.12
**Verified by:** Test: `tests/test_pick_values.py::test_rookie_order_sources`

#### Scenario: 2022 startup draft
- **WHEN** the 2022 dynasty startup draft took Breece Hall as its first rookie and Drake London as its second
- **THEN** the 2022 class has Hall at slot 1.01 and London at 1.02

### Requirement: 4.12.1.1 DLF rookie order
A 2013–2021 rookie's slot SHALL be his rank among that class's QB, RB, WR and TE rookies by his mean pick in the DLF mock drafts held May to August.

**Rationale:** Drafts before the NFL draft rank rookies without knowing their teams; rookie drafts are held after it.
**Traces to:** 4.12.1
**Verified by:** Test: `tests/test_pick_values.py::test_dlf_rookie_order`

#### Scenario: Two rookies
- **WHEN** one rookie's May to August picks average 18.5 and another's 22.0
- **THEN** the first ranks ahead of the second, whatever their February picks were

### Requirement: 4.12.1.2 Third-party pages kept local
Pages from third-party sites SHALL be fetched only by a command run by hand into a cache kept out of git.

**Rationale:** The pages belong to their sites; only the model built from them is published.
**Traces to:** 4.12.1; 6.1
**Verified by:** Test: `tests/test_pick_values.py::test_third_party_cache_not_committed`

#### Scenario: Cold run
- **WHEN** a cold run starts
- **THEN** it makes no request to mizelle.net

### Requirement: 4.12.1.3 Rookie order record
The 2013–2021 rookie order SHALL be kept as a record listing each class's slots with each rookie's Sleeper id, rookies without one flagged.

**Rationale:** Those classes never change, so the model can be rebuilt from committed records alone.
**Traces to:** 4.12.1; 6.1
**Verified by:** Test: `tests/test_pick_values.py::test_rookie_order_record`

#### Scenario: Rebuild without the cache
- **WHEN** the model is rebuilt on a fresh clone with no local cache
- **THEN** the 2013–2021 classes come from the rookie order record and the values match the committed model

### Requirement: 4.12.2 History WAR
WAR for 2013–2021 SHALL follow the Player WAR method with the dynasty league's scoring and lineup, regular-season weeks 1 to 14 and the season-long ESPN start-percentage cut.

**Rationale:** The same WAR for every season, so old and new classes compare like for like.
**Traces to:** 4.12; 3.3
**Verified by:** Test: `tests/test_pick_values.py::test_history_war_matches_stored_war`

#### Scenario: Method check
- **WHEN** the history method is run on the dynasty 2023 season
- **THEN** every Player's WAR equals the stored 2023 WAR to 0.0001

### Requirement: 4.12.2.1 History records
The 2013–2021 Sleeper weekly stats, slimmed to the fields scoring and WAR read, and the ESPN season start percentages SHALL be kept as records apart from the league seasons.

**Rationale:** History WAR must be reproducible from git, and history seasons must not enter the Forecasts' error pools or replacement levels.
**Traces to:** 4.12.2; 6.1
**Verified by:** Test: `tests/test_pick_values.py::test_history_records_apart`

#### Scenario: Error pools
- **WHEN** the history stats for 2013–2021 are stored
- **THEN** the Forecasts' error pools are built from the same seasons as before

### Requirement: 4.12.3 Eight-season value
A pick group's value SHALL be the sum over seasons 1 to 8 after the draft of the mean WAR of the group's picks that have reached that season, a season without games counting 0.

**Rationale:** A 1st-round career runs about 8 seasons; first-round WAR per season is near zero by season 8.
**Traces to:** 4.12
**Verified by:** Test: `tests/test_pick_values.py::test_eight_season_value`

#### Scenario: Shorter classes
- **WHEN** season 8 has been reached only by the 2013–2018 classes
- **THEN** that season's mean is over those classes' picks alone

### Requirement: 4.12.3.1 Pick groups
Each round's picks SHALL form three groups: Early (picks 1 to 4), Middle (5 to 8) and Late (9 to 12).

**Rationale:** Trades name picks by round and position in it, and single slots are too noisy to value.
**Traces to:** 4.12.3
**Verified by:** Test: `tests/test_pick_values.py::test_pick_groups`

#### Scenario: Pick 2.06
- **WHEN** a pick is the 6th of round 2
- **THEN** it is in the 2nd Middle group

### Requirement: 4.12.3.2 Values never rise
Group values in pick order from 1st Early to 3rd Late SHALL be non-increasing, any group above the one before it being averaged with it, with equal weights, until none is.

**Rationale:** An earlier pick is never worth less than a later one; the measured order in rounds 2 and 3 is chance.
**Traces to:** 4.12.3
**Verified by:** Test: `tests/test_pick_values.py::test_values_never_rise`

#### Scenario: Round 2
- **WHEN** the measured 2nd Early, Middle and Late values are −1.13, −0.46 and −0.66
- **THEN** all three become −0.75

### Requirement: 4.12.4 Unused pick value
A pick not yet used SHALL be worth its group's value when its draft order is known, else the value of its round's group from 4.12.4.1, else its round's average group value.

**Rationale:** The value moves with what is known about where the pick will fall.
**Traces to:** 4.12
**Verified by:** Test: `tests/test_pick_values.py::test_unused_pick_value`

#### Scenario: Two drafts away
- **WHEN** a 2028 1st is valued during the 2026 season
- **THEN** it is worth the mean of the three 1st-round group values, +1.65 today

### Requirement: 4.12.4.1 Next draft from the Forecast
A next-draft pick before its order is known SHALL take the third of the round its original team's place in the current Forecast's projected finish gives it, worst finish first.

**Rationale:** This league's draft order follows the final standings.
**Traces to:** 4.12.4
**Verified by:** Test: `tests/test_pick_values.py::test_next_draft_from_forecast`

#### Scenario: Contender's pick
- **WHEN** the current Forecast gives a team the league's best projected finish
- **THEN** its next 1st is a 1st Late pick, worth +0.11

### Requirement: 4.12.5 Model record
The pick value model SHALL be written from committed records alone by a command and kept as a record that cold runs only read.

**Rationale:** A rebuild needs no third-party page, so it can run anywhere, and later automatically each season.
**Traces to:** 4.12; 6.1
**Verified by:** Test: `tests/test_pick_values.py::test_model_record_not_rewritten`; Test: `tests/test_pick_values.py::test_rookie_order_record`

#### Scenario: Cold run
- **WHEN** a cold run builds the site
- **THEN** the model record is byte for byte as before

### Requirement: 4.12.6 Pick values export
The export SHALL write one pick values file with the group values, each group's WAR by season since the draft, each slot's mean WAR, the sample sizes and the sources.

**Traces to:** 4.12
**Verified by:** Test: `tests/test_pick_values.py::test_export_writes_pick_values_file`

#### Scenario: Build
- **WHEN** `python -m ffapp build` runs with the model record present
- **THEN** `site/data/pick-values.json` holds nine groups with their values and sample sizes
