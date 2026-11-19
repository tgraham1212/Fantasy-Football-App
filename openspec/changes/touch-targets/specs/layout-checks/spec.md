# Spec Delta

## MODIFIED Requirements

### Requirement: Touch targets
A browser test SHALL check every visible interactive control at the phone widths. It SHALL probe a 48 × 48 px square (Material Design 3's touch target) centred on each control, or the control's own box where that is larger. It SHALL fail when any probe point lands outside the control, counting invisible tap areas as part of it. A control is exempt only if it is listed in a committed baseline, and the baseline SHALL only shrink.

#### Scenario: Small new button
- **WHEN** a change adds a 30 px-tall button on the Games page
- **THEN** the touch-target check fails naming the button and its size

#### Scenario: Compact chip with a tap area
- **WHEN** a 32 px-tall chip has a transparent tap area extending it to 48 px
- **THEN** the touch-target check passes it

#### Scenario: Overlapping tap areas
- **WHEN** two chips' tap areas overlap, so part of one chip's 48 px square responds to its neighbour
- **THEN** the touch-target check fails naming the chip
