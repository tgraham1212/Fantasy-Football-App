## MODIFIED Requirements

### Requirement: Yearly and weekly cut
A league-season SHALL use one of three cuts, and the stored file SHALL say which was used:

- **weekly**: every scored regular-season week has a weekly snapshot. Each week's consensus lineup and replacement players come from that week's snapshot.
- **yearly**: no scored regular-season week has a weekly snapshot. Every week comes from the season snapshot.
- **merged**: some, but not all, scored regular-season weeks have a weekly snapshot. A scored week with a weekly snapshot uses that snapshot. Every other week ranks players by a merged start percentage, and the season snapshot is not used for ranking.

A player's merged start percentage SHALL be the highest percent started he has in any trusted weekly snapshot. A weekly snapshot of a scored week SHALL be trusted for a player only if he played that week. A weekly snapshot of a week not yet scored SHALL always be trusted.

A player SHALL use the higher of that figure and his percent owned only when both of these hold:
- he played in no scored week that has a weekly snapshot;
- his latest stored injury status for the season is on the shared out-status list (Out, Doubtful, IR, PUP, Sus, NA, DNR).

His percent owned SHALL come from the most recent weekly snapshot holding him, or else from the season snapshot. Ties SHALL break by ESPN id, as in every other ranking.

Rationale, kept with the requirement so it can be referenced later:

- **The in-season season snapshot is one week's view.** While a season is in progress, ESPN's public feed reports its season-level start percentage as the current week's figure. The stored season snapshot is therefore one week's view, rewritten on every run. In 2026 it matched the week 11 snapshot for every player.
- **That week's absences distort every week.** Ranking every week by that one view treats a player who is on a bye or hurt in the snapshot week as a bench player all season (Josh Jacobs in week 11: owned 91.5%, started 8.6%). The consensus starter cut moves deeper and the replacement players become genuine backups. The 2026 RB replacement level came out at 5.0 points against 8 to 11 in every completed season.
- **Why the highest figure, and why the current week counts.** Byes and injuries only ever lower a start percentage, never raise it, so the highest trusted figure is the closest to a player's role while active.
  - A scored week is trusted only if he played, which removes byes and injuries that week.
  - The current, unscored week is always trusted. A low figure from a bye or injury there cannot win the maximum, and a player whose team had a bye in the only scored captured week gets his real figure from it.
- **Why ownership only for injured players.** A player hurt for the season before weekly capture began, such as Jacobs if his absence is an injury, shows near 0% started in every snapshot. Percent owned barely moves during an injured-reserve stint, so it is a fair proxy for how often he was started while healthy.
  - Ownership is limited to players with an injury status that keeps them out.
  - For a healthy backup, ownership far exceeds start rate (owned 50%, started 15%). Using it for every player not seen active wrongly lifted week-10-bye backups into the replacement zone: an earlier version of this rule gave 2026 WR 6.5 and RB 6.4.
- **Measured on 2026.** With these rules, 2026 redraft levels moved from QB 18.0, RB 5.0, WR 8.2 to QB 15.6, RB 9.6, WR 8.8, inside the 2021 to 2025 range at every position. Each captured week adds evidence, so the merged figure improves as the season goes on.
- **Which seasons are affected.** Past seasons were captured after they ended, so their season snapshot is the genuine season-long figure and they keep the yearly cut. Once every week of a season has its own snapshot (2027 onward), that season uses the weekly cut and the merged rule no longer applies.

#### Scenario: Past season
- **WHEN** the WAR command runs for 2023
- **THEN** 2023 uses the yearly cut and the file is marked yearly

#### Scenario: Season with every week captured
- **WHEN** every scored week of a season has a weekly snapshot
- **THEN** that season uses the weekly cut and the file is marked weekly

#### Scenario: Partly captured season
- **WHEN** a season has weekly snapshots for weeks 10 and 11 only, and weeks 1 to 10 are scored
- **THEN** week 10 uses its own snapshot, weeks 1 to 9 use the merged start percentage, and the file is marked merged

#### Scenario: Bye in the captured scored week
- **WHEN** a healthy receiver's team had a bye in week 10, the only scored captured week, and the unscored week 11 snapshot shows him 80% started and 95% owned
- **THEN** his merged start percentage is 80, from week 11, and his ownership is not used

#### Scenario: Bye in the current week
- **WHEN** a running back played in week 10 and was 85% started then, and shows 8% started in the unscored week 11 snapshot because of a week 11 bye
- **THEN** his merged start percentage is 85

#### Scenario: Injured before weekly capture began
- **WHEN** a running back played weeks 1 to 5, missed every week from week 6, is on IR, and is 70% owned and 0% started in every weekly snapshot
- **THEN** his merged start percentage is his 70% ownership, and he is ranked by it for weeks 1 to 5

#### Scenario: Healthy backup not seen active
- **WHEN** a healthy receiver did not play in the only scored captured week, shows 15% started in the unscored week, and is 50% owned
- **THEN** his merged start percentage is 15
