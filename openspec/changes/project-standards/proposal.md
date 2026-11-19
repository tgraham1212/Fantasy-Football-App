# Proposal

## Why

The project has grown to six pages and two leagues of statistics without written standards. Three recent episodes show the cost:

- A Chrome-only layout check missed a 440 px phone.
- A Linux font wrapped a title.
- Terms drifted: owner and manager, odds, chances, predictions and forecasts for the same idea.

The owner wants standards that every change follows, recorded where future work sees them, and checked automatically where possible. These cover browsers, phone sizes, accessibility, Material Design usability, nomenclature and APA style, and calculation documentation.

## What Changes

- **Standards recorded in two places:**
  - in `openspec/config.yaml` project context, which reaches every OpenSpec change;
  - in a new short `CLAUDE.md` at the project root, which reaches every working session.

  They state:
  - **Browsers:** Chrome, Safari, Edge and Firefox on desktop; Chrome and Safari on mobile.
  - **Phone widths:** the most common US mobile widths, from StatCounter (October 2026: 414, 390, 384, 360, 402 and 393 px wide). They are tested at 360, 390, 414 and 440 px and reviewed yearly.
  - **Accessibility:** WCAG 2.2 AA.
  - **Material Design 3:** its usability rules are adopted: 48 × 48 px touch targets, visible focus and press states, and a consistent type scale. Its visual system is explicitly not adopted (components, colour roles, shapes and elevation); the current look stays.
  - **Nomenclature for anything people read:** Managers, Team Names, Players, and Forecasts for simulation output. Sleeper's inputs stay "projections". Code and data identifiers are exempt.
  - **APA style:** title case for titles and headings, APA conventions in prose.
  - **Calculations:** every calculation is documented in `Calculations.txt`.
- **`Calculations.txt`**, a new file at the project root. Each calculation has a section with:
  - its formula, data sources, inputs and code location
  - a plain-English description with its assumptions and decisions

  It covers the simulation, noise, lineups and the replacement floor, roster drift, game forecasts, win probability added, lineup choices, replacement level, manager ratings, Player WAR (including the merged cut), positional rankings and calibration. The README's calculation sections move into it, and the README points there.
- **Enforcement:**
  - **Browsers:** the layout check runs in Chromium (Chrome and Edge), WebKit (Safari's engine) and Firefox.
  - **Phone widths:** 360, 390, 414 and 440 px replace 375 and 440, alongside 768, 1000 and 1280.
  - **Accessibility check:** an axe-core check against WCAG 2.2 AA on every page.
  - **Touch-target check:** 48 × 48 px for interactive controls on phones.
  - **Nomenclature check:** reviews `site-copy.txt` for retired terms (owner, odds, chances and predictions where they mean the forecast).
  - **Calculations check:** a test that every calculation module has a section in `Calculations.txt`.
  - **Baselines:** the accessibility, touch-target and nomenclature checks start from recorded baselines of today's findings. A baseline may only shrink, so nothing new can slip in, while follow-up changes fix what is listed.
- **Code-push workflow:** installs Playwright's WebKit and Firefox before testing.

Out of scope, as follow-up changes:
- fixing the baselined accessibility, touch-target and nomenclature findings, including renaming the Predictions tab and other "odds" wording to "forecast" through `site-copy.txt` for the owner's approval;
- any Safari or Firefox layout fixes beyond small ones found while bringing the browsers in.

## Capabilities

### New Capabilities
- `project-standards`: the recorded project standards (browsers, phone widths, accessibility, Material Design usability, nomenclature, APA style, calculations), where they live, and the nomenclature check.
- `calculation-docs`: `Calculations.txt`, covering its required contents per calculation, its coverage test, and keeping it current with every calculation change.

### Modified Capabilities
- `layout-checks`:
  - "Layout check" runs in three browser engines at the new phone widths.
  - New requirements for the accessibility check and the touch-target check, with their shrinking baselines.

## Impact

- **Docs and config:**
  - New `Calculations.txt` and `CLAUDE.md`.
  - `openspec/config.yaml`: the context block.
  - `README.md`: the calculation sections move out, links and the standards summary are added.
- **Tests:**
  - `tests/layout/conftest.py`: browsers and widths.
  - New `tests/layout/test_accessibility.py`, `tests/test_nomenclature.py` and `tests/test_calculations_doc.py`, with baseline files under `tests/baselines/`.
- **Dependencies:** dev-only additions. axe-core is loaded in the browser from a pinned CDN copy or a vendored file; the browser extra is unchanged.
- **CI:** `site.yml` installs WebKit and Firefox (`python -m playwright install --with-deps webkit firefox`), adding about a minute or two and a longer test run.
- **No change to the site's behaviour or data.**
