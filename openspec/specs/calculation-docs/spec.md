# calculation-docs Specification

## Purpose

Keeps every calculation the project performs documented in one plain-text file, `Calculations.txt`, so anyone can see how each number on the site is produced: the formula and its inputs, and in plain English what it does, what it assumes, and the decisions behind it.

## Requirements

### Requirement: Calculations file
The project SHALL keep `Calculations.txt` at its root, with one section per calculation. Each section SHALL hold:
- the calculation's name
- the code that performs it
- the formula or formulas, in plain-text notation
- the data sources and inputs, with where they are stored
- its dependencies on other calculations
- a plain-English description of how it works
- the assumptions and decisions made, with their reasons

#### Scenario: Reading a section
- **WHEN** the owner opens the Player WAR section
- **THEN** it shows the win-probability and WAR formulas, the ESPN start-percentage and stat inputs, its dependency on the replacement cut, a plain-English walk-through, and the decisions such as the merged cut and its reasoning

### Requirement: Every calculation covered
A test SHALL fail when a module that performs a calculation has no section in `Calculations.txt` naming it. The test SHALL read the list of calculation modules from the test itself, so adding a calculation module means adding it to that list and documenting it.

#### Scenario: New calculation module
- **WHEN** a change adds `src/ffapp/trades.py` to the calculation modules without a section naming it
- **THEN** the test fails naming `trades.py`

### Requirement: Kept current
A change that alters a calculation (its formula, inputs, assumptions or parameters) SHALL update its section in `Calculations.txt` in the same change. The README SHALL point to `Calculations.txt` instead of repeating the formulas.

#### Scenario: Changed parameter
- **WHEN** a change alters the replacement-level shrinkage weight
- **THEN** the same change updates the replacement-level section's formula and its decision note
