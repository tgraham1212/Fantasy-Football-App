"""Accessibility (WCAG 2.2 AA, axe-core) and Material Design 3 touch targets, in Chromium.

Both compare against baselines in tests/baselines/ that may only shrink: a new finding fails,
and a listed finding that is gone fails until it is removed (UPDATE_BASELINES=1 rewrites)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.baselines import compare
from tests.layout.controls import CONTROL_QUERY, VIEWS

AXE = Path(__file__).resolve().parent / "vendor" / "axe.min.js"
VIEWS_CHECKED = ("predictions", "games", "games-final", "positions", "positions-past", "war", "war-all", "war-dialog", "calibration")
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
TARGET = 48  # px, Material Design 3 touch target


def _open(open_page, view, width):
    v = VIEWS[view]
    page, relay = open_page(v.path, width)
    if v.setup:
        v.setup(page)
    return page


def _axe_findings(page, view, width):
    page.add_script_tag(path=str(AXE))
    result = page.evaluate("""(tags) => axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations'] })
        .then((r) => r.violations.flatMap((v) => v.nodes.map((n) => `${v.id} | ${n.target.join(' ')}`)))""", AXE_TAGS)
    # positional selectors (row and column indexes) change with the data, so drop them: a
    # recurring problem then counts once per view and width, and daily data refreshes stay stable
    return {f"{view} | {width} | {_generic(f)}" for f in result}


def _generic(finding: str) -> str:
    import re
    finding = re.sub(r":nth-(child|of-type)\(\d+\)", "", finding)
    # attribute selectors name data (a manager in a title, a card number, a position); keep only
    # the stable copy IDs
    return re.sub(r"\[(?!data-copy)[^\]]*\]", "", finding)


def test_accessibility_wcag_22_aa(open_page):
    found = set()
    for view in VIEWS_CHECKED:
        for width in (390, 1280):
            page = _open(open_page, view, width)
            found |= _axe_findings(page, view, width)
            page.close()
    problems = compare("axe", found, "accessibility violation")
    assert not problems, "\n".join(problems[:40]) + (f"\n... {len(problems) - 40} more" if len(problems) > 40 else "")


DESCRIBE_JS = """(e) => {
  const attrs = ['id', 'data-page', 'data-view', 'data-col', 'data-mode', 'aria-label'];
  const key = attrs.map((a) => e.getAttribute(a) ? `[${a}=${e.getAttribute(a)}]` : '').join('');
  const text = (e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 30);
  return `${e.tagName.toLowerCase()}${key}${text ? ` "${text}"` : ''}`;
}"""


def _small_controls(page, view):
    return page.evaluate("""([query, target, describe]) => {
      const describeFn = eval(describe);
      const out = [];
      for (const e of document.querySelectorAll(query)) {
        if (!e.getClientRects().length || getComputedStyle(e).visibility === 'hidden') continue;
        if (e.closest('canvas') || e.matches('.pos-dot')) continue;                 // charts: keyboard alternative instead
        if (e.matches('a') && e.closest('p, li') && !e.matches('.nav-link')) continue;  // inline links in sentences (WCAG exception)
        const r = e.getBoundingClientRect();
        if (r.width < target - 0.5 || r.height < target - 0.5) out.push(describeFn(e));
      }
      return [...new Set(out)];
    }""", [CONTROL_QUERY, TARGET, DESCRIBE_JS])


def test_touch_targets_on_phones(open_page):
    found = set()
    for view in VIEWS_CHECKED:
        for width in (360, 440):
            page = _open(open_page, view, width)
            found |= {f"{view} | {c}" for c in _small_controls(page, view)}
            page.close()
    problems = compare("touch", found, "control under 48 x 48 px")
    assert not problems, "\n".join(problems[:40]) + (f"\n... {len(problems) - 40} more" if len(problems) > 40 else "")
