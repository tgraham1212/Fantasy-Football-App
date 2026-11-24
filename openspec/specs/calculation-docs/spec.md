# calculation-docs Specification

## Purpose

Keeps every calculation the project performs documented in one plain-text file, `Calculations.txt`, so anyone can see how each number on the site is produced: its formula and inputs, and in plain English what it does, what it assumes and the decisions behind it. It delivers need 8, Open Methods.

## Requirements

### Requirement: 8.2 Calculations file
`Calculations.txt` at the project root SHALL hold one section per calculation, each with its name, the code that performs it, its formulas in plain-text notation, its data sources and where they are stored, its dependencies, a plain-English description, and its assumptions and decisions with their reasons.

**Traces to:** 8
**Verified by:** Test: `tests/test_calculations_doc.py::test_every_section_has_all_headings`

#### Scenario: Reading a section
- **WHEN** someone opens the Player WAR section
- **THEN** it shows the win-probability and WAR formulas, the start-percentage and stat inputs, its dependencies, a plain-English walk-through, and the decisions behind the merged cut

### Requirement: 8.2.1 Every calculation covered
Every module that performs a calculation SHALL be named by a section of `Calculations.txt`, the list of calculation modules kept in the test.

**Traces to:** 8.2
**Verified by:** Test: `tests/test_calculations_doc.py::test_every_calculation_module_has_a_section`

#### Scenario: New calculation module
- **WHEN** a change adds `src/ffapp/trades.py` to the calculation modules without a section naming it
- **THEN** the test fails naming `trades.py`

### Requirement: 8.2.2 Kept current
A change that alters a calculation's formula, inputs, assumptions or settings SHALL update its section in `Calculations.txt` in the same change.

**Traces to:** 8.2; 10
**Verified by:** Inspection: each change's review, the changed calculations' sections

#### Scenario: Changed setting
- **WHEN** a change alters the replacement-level shrinkage weight
- **THEN** the same change updates that section's formula and decision note

### Requirement: 8.2.3 README points to the file
The README SHALL point to `Calculations.txt` in place of repeating the formulas.

**Traces to:** 8.2
**Verified by:** Test: `tests/test_calculations_doc.py::test_readme_points_to_the_calculations_file`

#### Scenario: Reading the README
- **WHEN** someone looks for how the Forecasts are calculated in the README
- **THEN** it points them to `Calculations.txt`
