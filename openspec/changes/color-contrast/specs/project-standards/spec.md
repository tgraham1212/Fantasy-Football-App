# Spec Delta

## ADDED Requirements

### Requirement: Colour standard
Site colours SHALL be defined and adjusted in OKLCH (reference: https://oklch.fyi/). A contrast fix SHALL change a colour's lightness and keep its hue and chroma. A new colour SHALL be derived from an existing hue where one fits. The rule SHALL be written in the `openspec/config.yaml` project context and summarised in `CLAUDE.md`.

#### Scenario: Grey text too light
- **WHEN** a grey text colour fails its contrast ratio
- **THEN** the fix lowers its OKLCH lightness and keeps its hue and chroma

#### Scenario: New control colour
- **WHEN** a change needs a new fill colour for a control
- **THEN** it is derived from an existing hue in OKLCH, not picked freely

### Requirement: Colour contrast check
A test SHALL read the colour tokens in `site/styles.css` for light and dark mode, then check each text colour against the backgrounds it is used on at 4.5:1. Focus rings and chart lines SHALL be checked against the page and card backgrounds at 3:1. A failure SHALL name the mode, both tokens and the ratio. Gridlines, axis lines and the animated live signal are exempt, because they are decorative or paired with text.

#### Scenario: Chart text too light
- **WHEN** a change sets chart axis text to a grey of 3.5:1 on cards in light mode
- **THEN** the colour contrast check fails naming light mode, the two tokens and 3.5:1

#### Scenario: Dark mode only
- **WHEN** a colour passes in light mode but fails in dark mode
- **THEN** the colour contrast check fails naming dark mode
