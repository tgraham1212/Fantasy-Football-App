## Purpose

The "How Pick Values Work" page: the rookie pick value model shown and explained like the calibration page, with the group values, the WAR curves behind them, the method and the credit to the sources. It serves need 8, Open Methods, for the values in `rookie-pick-values`, and its layout serves need 9, Usable by Every Manager.

## ADDED Requirements

### Requirement: 8.3 Pick values page
The site SHALL have a page titled "How Pick Values Work", linked from every league page.

**Rationale:** Trade values that include picks rest on this model; Managers need to see where it comes from.
**Traces to:** 8; 4.12; 9
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_page_is_titled_and_linked`

#### Scenario: Open the page
- **WHEN** a visitor follows the "How Pick Values Work" link on a league page
- **THEN** the page opens with its title

### Requirement: 8.3.1 Group values table
The page SHALL show a table of the nine pick groups with each group's slots, measured 8-season WAR, 80% range of the mean, pick counts and model value.

**Rationale:** The model value differs from the measured one where values were averaged; both are shown.
**Traces to:** 8.3; 4.12.3.2
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_group_table`

#### Scenario: Round 2
- **WHEN** the page loads
- **THEN** the 2nd Early row shows its measured −1.13 and its model value −0.75

### Requirement: 8.3.2 Pick value charts
The page SHALL chart total WAR by season since the draft for each group, WAR in each season by round, and mean WAR by slot, each with a legend, a hover value and a table view.

**Traces to:** 8.3; 4.12.6
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_charts_and_table_views`

#### Scenario: Hover a season
- **WHEN** a visitor hovers season 3 on the total-WAR chart
- **THEN** each group's total through season 3 and its pick count show

### Requirement: 8.3.3 Method and sources
The page SHALL state how the values are made and credit Dynasty League Football and mizelle.net for the 2013–2021 rookie order.

**Rationale:** The rookie order comes from their pages; crediting it is owed.
**Traces to:** 8.3; 4.12.1
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_method_and_credits`

#### Scenario: Credits
- **WHEN** the page loads
- **THEN** its method section names Dynasty League Football and mizelle.net

### Requirement: 8.3.4 Pick values page on phones
At 360 to 440 px the page SHALL show every table and chart with no sideways page scroll, wide tables scrolling inside their own box.

**Traces to:** 8.3; 9
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_phone_widths`

#### Scenario: 360 px
- **WHEN** the page opens at 360 px
- **THEN** the page body does not scroll sideways

### Requirement: 8.3.5 Pick values not yet built
Without a pick values file the page SHALL say that pick values have not been built.

**Traces to:** 8.3
**Verified by:** Test: `tests/layout/test_pick_values_page.py::test_not_built_message`

#### Scenario: No model
- **WHEN** the site is built without the model record
- **THEN** the page says pick values have not been built and the league pages work as before
