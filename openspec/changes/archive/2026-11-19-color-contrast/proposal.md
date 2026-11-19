# Proposal

## Why

The accessibility check lists 146 colour-contrast failures, all in light mode. They come from three colours: the grey for secondary text (`--muted`), the accent blue used as link text, and the white label on the selected league button. Dark mode is never checked, and its league button fails too (3.64:1). Text in the SVG charts is outside axe's reach, so failures there go unrecorded. The project also has no rule for how colours are chosen, although the team palette is already built in OKLCH.

## What Changes

- Light `--muted` changes from #898781 to #716f6a. That is the same hue and chroma in OKLCH, with lightness lowered from 0.623 to 0.543. The contrast is 4.76:1 on the page and 4.89:1 on cards. Dark `--muted` stays #898781, which already passes.
- Light `--accent` changes from #2a78d6 to #2170cd, lowering only L from 0.575 to 0.549. As text it reaches 4.67:1; with white text on it, 4.93:1.
- A new `--accent-fill` token is the background of the selected league button. It is #2170cd in both modes, so the button looks the same in light and dark mode. Dark `--accent` stays #3987e5 for text and focus rings, where it measures 4.79:1.
- A new token contrast test reads the colour tokens from `site/styles.css` for both modes. It checks every text-and-background pair the site uses against 4.5:1, and every focus ring and chart line against 3:1. It covers the SVG chart text that axe cannot see.
- The axe check also runs in dark mode.
- The colour-contrast entries are removed from `tests/baselines/axe.json`, which leaves that baseline at zero entries.
- A colour standard is added to `openspec/config.yaml` and, in brief, to `CLAUDE.md`. It says:
  - colours are defined and adjusted in OKLCH (https://oklch.fyi/);
  - contrast is fixed by changing lightness, keeping hue and chroma;
  - new colours are derived from existing hues;
  - contrast is checked in both modes by the token test.
- The `BRAND_HUE` comment in `tools/team_palette.py` is corrected. The accent's measured hue is 255.5, not 258. The value 258 stays, so the team colours do not change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `project-standards`: two new requirements, "Colour standard" (OKLCH, recorded in the config and `CLAUDE.md`) and "Colour contrast check" (the token test).
- `layout-checks`: "Accessibility check" runs in light and dark mode.

## Impact

- **Site:** `site/styles.css` (tokens and the league button rule). Every page's grey text and links become slightly darker in light mode. Nothing else moves.
- **Tests:**
  - a new `tests/test_colour_contrast.py`;
  - `tests/layout/test_accessibility.py` gains the dark-mode pass, which adds about a minute;
  - the axe baseline drops from 146 entries to 0.
- **Docs:** `openspec/config.yaml`, `CLAUDE.md`, and the `tools/team_palette.py` docstring and comment.
- **Calculations:** none. `Calculations.txt` documents no colour calculations, so it is unchanged.
