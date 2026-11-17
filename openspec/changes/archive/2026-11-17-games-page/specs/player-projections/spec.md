# Spec Delta

## MODIFIED Requirements

### Requirement: Raw stat lines and source details
Each stored projection SHALL keep the full projected stat line as the source returned it, plus the player ID, NFL team, opponent, game date, source company and the source's last-modified time.

#### Scenario: Stored record contents
- **WHEN** a projection is stored for a running back
- **THEN** the record includes every projected stat field the source gave (e.g., rushing yards, receptions, first downs), not just precomputed point totals

#### Scenario: Game date kept
- **WHEN** the source gives a projection with the game date 2026-11-22
- **THEN** the stored record carries that date
