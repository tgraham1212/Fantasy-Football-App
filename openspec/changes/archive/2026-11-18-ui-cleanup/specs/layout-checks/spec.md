## MODIFIED Requirements

### Requirement: Layout check
A browser test SHALL load each page of the site at widths of 375, 440, 768, 1000 and 1280 px (440 standing for current large phones) and SHALL fail when the page scrolls sideways at any width, naming the page and width.

#### Scenario: Overflowing note
- **WHEN** a message under a button runs past the right edge at 1000 px
- **THEN** the layout check fails naming the page and the width

#### Scenario: Large phone width
- **WHEN** a Games card is cramped side by side at 440 px
- **THEN** the layout check fails at 440 px
