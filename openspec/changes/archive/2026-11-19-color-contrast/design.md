# Design

## Context

The colour tokens are in `site/styles.css`. There are three blocks:

- light, on `:root`;
- dark, under `@media (prefers-color-scheme: dark)`, guarded by `:root:not([data-theme="light"])`;
- dark again, on `:root[data-theme="dark"]` for the toggle.

The two dark blocks must stay identical. The axe check runs light mode only. It scans 9 views at 390 and 1280 px. A scan of both modes on 2026-11-19 found every failure in five colour pairs:

| Mode | Text | Background | Ratio | Findings |
|---|---|---|---|---|
| light | `--muted` #898781 | page #f9f9f7 | 3.41 | 16 |
| light | `--muted` #898781 | surface #fcfcfb | 3.50 | 40+ |
| light | `--accent` #2a78d6 | page or surface | 4.19 to 4.30 | 10 |
| light | white | `--accent` #2a78d6 | 4.42 | 14 |
| dark | white | `--accent` #3987e5 | 3.64 | 14 |

Dark `--muted` (#898781 on #1a1a19, 4.85:1) passes. Axe does not measure SVG text, such as `.pos-tick` on the Positions charts, which uses `--muted`. That text fails at the same ratio as the HTML grey.

## Goals / Non-Goals

**Goals:**
- No text in either mode below 4.5:1.
- A cheap check that covers chart text and dark mode, and stays enforced.
- A written colour rule (OKLCH, change lightness only).

**Non-Goals:**
- Restyling. Hue and chroma stay the same, so the site keeps its look.
- Regenerating the team palette.
- Fixing the touch-target baseline, which is a separate follow-up.

## Decisions

1. **Change lightness only, in OKLCH.** Each new colour keeps the old hue and chroma. Only L is lowered, to the first value that clears the target with some headroom. Light `--muted` goes from L 0.623 to 0.543 (#716f6a): that gives 4.76:1 rather than a bare 4.5:1, so tinted row hovers don't drop it below the line. Light `--accent` goes from L 0.575 to 0.549 (#2170cd). Lowering only lightness is the rule the new colour standard writes down. *Alternative:* the nearest passing hex in sRGB, rejected because it drifts in hue.

2. **Split the accent's two jobs in dark mode.** In dark mode `--accent` is both text on near-black, which needs a light blue, and the fill behind a white label, which needs a dark blue. No single blue does both. A new `--accent-fill` token is the background of `.leagues button[aria-pressed="true"]`. Its value is #2170cd in both modes, the new light accent, so the button looks the same in either mode and no new hue is added. *Alternative:* black text on the bright dark-mode blue (5.41:1), rejected so the button stays consistent with light mode.

3. **Token test in Python, not the browser.** `tests/test_colour_contrast.py` parses the three token blocks with a regular expression for `--name: #hex`. It asserts that the two dark blocks are identical and computes WCAG contrast for a declared list of pairs:
   - **Text (4.5:1):**
     - `--ink`, `--ink-2`, `--muted`, `--accent`, `--good`, `--bad` and `--gold` on `--page` and `--surface`;
     - `--accent-ink` on `--accent-fill`;
     - `--win-ink` on `--win-hi`, `--win-mid` and `--win-lo`;
     - `--fill-ink` on `--fill-hi`;
     - `--chance-ink` on `--fill-lo`.
   - **Non-text (3:1):** `--accent` as the focus ring, and each `--team-*` chart colour, on `--page` and `--surface`.
   - **Exempt, with a comment saying why:**
     - `--grid` and `--axis` (decorative rules);
     - `--live` and `--live-dim` (an animated signal shown next to the "Live" text);
     - the pill and win fills (backgrounds whose text is checked above).

   This runs in milliseconds and needs no browser. It covers SVG text, because chart code reads the same tokens through `cssVar`.

   The pill text is fixed #0b0b0b in `.elo-delta`, not a token. It is checked as a literal against both pill fills in each mode. In dark mode, #0b0b0b on the pills measures 11.2:1 and 9.5:1. The Python helpers `contrast` and `hex_to_oklab` are imported from `tools/team_palette.py`, so there is one implementation of the maths.

4. **Axe in dark mode.** The axe check loops over `("light", "dark")`. For dark it sets `data-theme="dark"` on `<html>`. That attribute wins over the OS preference, so it also tests the toggle path, and the media-query path has identical tokens, which the token test enforces. The mode goes into the fingerprint as `view | width | mode | rule | selector`. The baseline will be empty after the fix, so changing the format rewrites nothing that matters. The extra pass costs about one minute.

5. **The colour standard goes in config and `CLAUDE.md`.** It goes in the project-standards block of `openspec/config.yaml` as a "Colour" bullet, and as one line in the Standards list of `CLAUDE.md`. `tools/team_palette.py` keeps `BRAND_HUE = 258.0`, so the team colours are unchanged, and its comment now says it is the palette's start hue, near the accent's measured 255.5.

## Risks / Trade-offs

- **A darker grey narrows the gap between `--muted` and `--ink-2`** (#52514e, 7.5:1). They remain distinguishable: L 0.543 against 0.44. Mitigation: screenshots at 440 and 1280 for the owner, before and after.
- **Linux fonts in CI render differently.** Contrast doesn't depend on font metrics, but a newly overflowing table could add a finding. The dark pass adds findings only if a colour fails, and the token test already proves none do.
- **The token list can go stale** when a new token is added. Mitigation: the test fails on any token in a block that is neither in a pair nor in the exempt list, so every new colour must be classified.
