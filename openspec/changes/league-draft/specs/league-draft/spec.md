## Purpose

The draft figures behind the League sub-tab's Draft tab: for every stored draft of a league, each pick's Steal/Reach against ADP, its Hit/Bust against the WAR its draft slot usually produces in this league (slot WAR), whether it was an unlucky pick, and the Managers summaries for one draft and all drafts. It serves need 4, Manager History, through `league-draft-page`; the formulas are in `Calculations.txt`.

## ADDED Requirements

### Requirement: 4.11 Draft export
The export SHALL write one draft file per league, holding every stored draft of that league with its graded picks and Managers summaries.

**Traces to:** 4
**Verified by:** Test: `tests/test_draft.py::test_export_writes_draft_file`

#### Scenario: Build
- **WHEN** `python -m ffapp build` runs
- **THEN** each configured league has a draft file in the site data with an entry for each season that has a stored draft

### Requirement: 4.11.1 ADP difference
For each pick, the export SHALL give its ADP difference to 0.1: in redraft, the pick number minus the Player's ADP; in a rookie draft, the pick number minus the Player's ADP rank among that draft's Players.

**Rationale:** A rookie draft holds a small, separate pool, so its Players are compared by their order of ADP.
**Traces to:** 4.11
**Verified by:** Test: `tests/test_draft.py::test_adp_difference`

#### Scenario: Redraft pick later than ADP
- **WHEN** a redraft Player with an ADP of 55.3 is taken with pick 70
- **THEN** the pick's ADP difference is +14.7

### Requirement: 4.11.1.1 Steal
A pick SHALL be a steal when its ADP difference is at least +12 in redraft or at least +6 in a rookie draft.

**Rationale:** A full round in redraft and half a round in a 3-round rookie draft.
**Traces to:** 4.11.1
**Verified by:** Test: `tests/test_draft.py::test_steal_thresholds`

#### Scenario: Rookie draft
- **WHEN** a rookie-draft Player with ADP rank 24 is taken with pick 34
- **THEN** the pick is a steal (+10)

### Requirement: 4.11.1.2 Reach
A pick SHALL be a reach when its ADP difference is -12 or less in redraft or -6 or less in a rookie draft, unless the Player is a running back or wide receiver with one of the two lowest ADPs at his position among the Players still available.

**Rationale:** Taking the best back or receiver left during a run on the position is not a reach.
**Traces to:** 4.11.1
**Verified by:** Test: `tests/test_draft.py::test_reach_thresholds_and_position_exception`

#### Scenario: Best back left
- **WHEN** a redraft RB with an ADP of 90.0 is taken with pick 75 while he has the second-lowest ADP of the RBs still available
- **THEN** the pick is not a reach

### Requirement: 4.11.1.3 Ungraded picks
The export SHALL mark keepers and Players without an ADP as having no Steal/Reach grade.

**Traces to:** 4.11.1
**Verified by:** Test: `tests/test_draft.py::test_keepers_and_missing_adp_ungraded`

#### Scenario: Keeper
- **WHEN** a redraft keeper occupies the 1.04 pick
- **THEN** the 1.04 pick has no Steal/Reach grade

### Requirement: 4.11.2 Hit and bust
A pick SHALL be a hit when its WAR exceeds its slot WAR by at least 0.75 in redraft or 1.0 in a rookie draft, and a bust when its WAR falls short of its slot WAR by at least as much.

**Rationale:** About 19 of each per redraft draft and 4 to 7 per rookie draft in the stored drafts, spread across all rounds.
**Traces to:** 4.11
**Verified by:** Test: `tests/test_draft.py::test_hit_and_bust_thresholds`

#### Scenario: First-round hit
- **WHEN** a redraft pick 7 has 3.26 WAR against a slot WAR of 1.23
- **THEN** the pick is a hit, +2.03 WAR

### Requirement: 4.11.2.1 Grading window
A pick's WAR SHALL be its Player's WAR on every roster over the draft season in redraft, and over the draft season and the following season in a rookie draft.

**Rationale:** Redraft values only that season; a rookie draft pays off over years, and a fixed two-season window lets drafts of different ages be compared.
**Traces to:** 4.11.2
**Verified by:** Test: `tests/test_draft.py::test_grading_window`

#### Scenario: Traded rookie
- **WHEN** a 2025 rookie produced 0.6 WAR for the drafting roster in 2025 and 0.8 WAR for another roster in 2026
- **THEN** the pick's WAR is 1.4

### Requirement: 4.11.2.2 Slot WAR
For each pick, the export SHALL give its slot WAR to 0.01: the mean WAR of picks within 6 slots of it in redraft, or 3 slots in a rookie draft, across the league's drafts whose grading window is complete.

**Rationale:** What a draft position usually produces in this league, so early and late picks can both be hits or busts.
**Traces to:** 4.11.2; 4.11.2.1
**Verified by:** Test: `tests/test_draft.py::test_slot_war`

#### Scenario: Pick 20
- **WHEN** a redraft league's completed drafts hold picks 14 to 26
- **THEN** pick 20's slot WAR is the mean WAR of those picks, keepers left out

### Requirement: 4.11.2.2.1 Window in progress
While a pick's grading window is in progress, its slot WAR SHALL be scaled by the share of the window's regular-season weeks already played.

**Traces to:** 4.11.2.2
**Verified by:** Test: `tests/test_draft.py::test_slot_war_scaled_in_season`

#### Scenario: Halfway through the season
- **WHEN** 7 of 14 regular-season weeks of the 2026 redraft season are played and pick 20's slot WAR is 0.90
- **THEN** its slot WAR shown is 0.45

### Requirement: 4.11.2.3 Unlucky pick
A pick SHALL be unlucky when its Player missed more than half of his NFL team's regular-season games in the grading window so far while listed Out, on injured reserve or on PUP.

**Rationale:** A Player lost to injury says little about the pick; a healthy Player who is not playing is no excuse.
**Traces to:** 4.11.2; 4.11.2.1; 6.6.5
**Verified by:** Test: `tests/test_draft.py::test_unlucky_pick`

#### Scenario: Injured receiver
- **WHEN** a 2024 redraft receiver's team played 14 regular-season games and he was on injured reserve for 10 of them
- **THEN** the pick is unlucky

#### Scenario: Healthy rookie not playing
- **WHEN** a rookie missed 15 of his team's 23 games with no Out, IR or PUP status
- **THEN** the pick is not unlucky

### Requirement: 4.11.2.3.1 Unlucky in place of bust
The export SHALL give an unlucky pick that is not a hit the grade Unlucky, in place of Bust.

**Traces to:** 4.11.2.3
**Verified by:** Test: `tests/test_draft.py::test_unlucky_replaces_bust`

#### Scenario: Short of the slot
- **WHEN** an unlucky pick's WAR is 1.2 below its slot WAR
- **THEN** its grade is Unlucky and it counts as neither a hit nor a bust

### Requirement: 4.11.3 Position ranks
For each pick, the export SHALL give the Player's rank and position rank among that draft's Players, by ADP and by WAR.

**Traces to:** 4.11
**Verified by:** Test: `tests/test_draft.py::test_position_ranks`

#### Scenario: Second receiver by ADP
- **WHEN** a receiver has the 5th-lowest ADP of the draft's Players and the 2nd-lowest of its receivers
- **THEN** his ADP rank is 5 and his ADP position rank is WR2

### Requirement: 4.11.4 Managers summary
For one draft and for all of a league's drafts, the export SHALL give each Manager's picks, mean ADP difference to 0.1, mean WAR above slot WAR to 0.01, total WAR, best pick and number of unlucky picks.

**Traces to:** 4.11
**Verified by:** Test: `tests/test_draft.py::test_managers_summary`

#### Scenario: Three picks
- **WHEN** a Manager's three picks in a draft are +10, -2 and +4 against ADP
- **THEN** that Manager's mean ADP difference for the draft is +4.0

### Requirement: 4.11.4.1 Picks by the Manager who made them
Each pick SHALL count for the Manager whose roster made it, traded picks included.

**Traces to:** 4.11.4
**Verified by:** Test: `tests/test_draft.py::test_traded_pick_counts_for_its_maker`

#### Scenario: Traded first
- **WHEN** Z28kid86 makes the 1.04 pick that was CheefWiggum's slot
- **THEN** the pick counts in Z28kid86's summary and not in CheefWiggum's

### Requirement: 4.11.5 Recorded keepers
The redraft league's keepers from 2025 on SHALL be read from the league configuration by season and marked as keepers, with no Steal/Reach or Hit/Bust grade.

**Rationale:** The league's keeper rules are tracked outside Sleeper, which flags no keepers after 2024; its 2022 to 2024 flags followed earlier rules and stay as Sleeper has them.
**Traces to:** 4.11; 4.11.1.3
**Verified by:** Test: `tests/test_draft.py::test_configured_keepers_marked`

#### Scenario: 2026 keepers
- **WHEN** the configuration lists Rashee Rice, Javonte Williams, Jaxon Smith-Njigba, Emeka Egbuka and Cam Skattebo for 2026
- **THEN** those 5 picks of the 2026 redraft draft are keepers and have no grade

### Requirement: 4.11.6 Keeper eligible
For the latest redraft draft, the export SHALL list as keeper eligible each Player drafted by a Manager who stayed on that Manager's roster through the championship week.

**Rationale:** The league's rule: a Player is kept by the team that drafted him and held him all season.
**Traces to:** 4.11
**Verified by:** Test: `tests/test_draft.py::test_keeper_eligible_needs_the_whole_season`

#### Scenario: Dropped in week 9
- **WHEN** a Manager drafted a Player in 2026 and dropped him in week 9
- **THEN** the Player is not keeper eligible for 2027

### Requirement: 4.11.6.1 Keeper price
A keeper-eligible Player's price SHALL be the round one higher than the round he was drafted in, with first-round picks not eligible.

**Traces to:** 4.11.6
**Verified by:** Test: `tests/test_draft.py::test_keeper_price`

#### Scenario: Seventh-round pick
- **WHEN** a keeper-eligible Player was drafted in round 7 of 2026
- **THEN** his price for 2027 is a round 6 pick

### Requirement: 4.11.6.2 Second-year keeper
A Player kept in the draft season SHALL cost a first-round pick to keep again, unless he was also kept the season before, which makes him not eligible.

**Traces to:** 4.11.6
**Verified by:** Test: `tests/test_draft.py::test_second_year_keeper`

#### Scenario: Kept in 2026
- **WHEN** Jaxon Smith-Njigba, kept in round 2 of 2026, stays on his roster all season
- **THEN** his price for 2027 is a round 1 pick

### Requirement: 4.11.6.3 Season in progress
While the latest redraft season is in progress, the export SHALL list keeper eligibility through the latest week played and mark the list as not final.

**Traces to:** 4.11.6
**Verified by:** Test: `tests/test_draft.py::test_keeper_eligible_in_progress`

#### Scenario: Week 12 of 2026
- **WHEN** the 2026 redraft season has played week 12
- **THEN** the list holds the drafted Players still on their drafting roster with no move off it, marked not final
