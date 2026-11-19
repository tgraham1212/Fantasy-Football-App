"""Accessibility (WCAG 2.2 AA, axe-core, light and dark mode) and Material Design 3 touch targets, in Chromium.

Both compare against baselines in tests/baselines/ that may only shrink: a new finding fails,
and a listed finding that is gone fails until it is removed (UPDATE_BASELINES=1 rewrites)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.baselines import compare
from tests.layout.controls import CONTROL_QUERY, VIEWS

AXE = Path(__file__).resolve().parent / "vendor" / "axe.min.js"
WIDE_FONT = "* { font-family: Verdana, 'DejaVu Sans', sans-serif !important; }"  # as in test_layout.py
VIEWS_CHECKED = ("predictions", "games", "games-final", "positions", "positions-past", "war", "war-all", "war-dialog", "calibration")
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
TARGET = 48  # px, Material Design 3 touch target


def _open(open_page, view, width):
    v = VIEWS[view]
    page, relay = open_page(v.path, width)
    if v.setup:
        v.setup(page)
    return page


def _axe_findings(page, view, width, mode):
    # data-theme wins over the OS preference; the media-query dark block has the same tokens
    # (tests/test_colour_contrast.py checks that)
    page.evaluate("(m) => document.documentElement.setAttribute('data-theme', m)", mode)
    page.add_script_tag(path=str(AXE))
    result = page.evaluate("""(tags) => axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations'] })
        .then((r) => r.violations.flatMap((v) => v.nodes.map((n) => `${v.id} | ${n.target.join(' ')}`)))""", AXE_TAGS)
    # positional selectors (row and column indexes) change with the data, so drop them: a
    # recurring problem then counts once per view and width, and daily data refreshes stay stable
    return {f"{view} | {width} | {mode} | {_generic(f)}" for f in result}


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
            for mode in ("light", "dark"):
                page = _open(open_page, view, width)
                found |= _axe_findings(page, view, width, mode)
                page.close()
    problems = compare("axe", found, "accessibility violation")
    assert not problems, "\n".join(problems[:40]) + (f"\n... {len(problems) - 40} more" if len(problems) > 40 else "")


DESCRIBE_JS = """(e) => {
  const attrs = ['id', 'data-page', 'data-view', 'data-col', 'data-mode', 'aria-label'];
  const key = attrs.map((a) => e.getAttribute(a) ? `[${a}=${e.getAttribute(a)}]` : '').join('');
  const text = (e.innerText || e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 30);
  return `${e.tagName.toLowerCase()}${key}${text ? ` "${text}"` : ''}`;
}"""


PROBE_JS = """async ([query, target, describe]) => {
  const describeFn = eval(describe);
  const frame = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const modal = document.querySelector('dialog[open]');
  const out = {};
  // a pinned column: sticky with a left offset (a header row that sticks to the top doesn't count)
  const pinnedOf = (n) => { for (; n; n = n.parentElement) { const cs = getComputedStyle(n); if (cs.position === 'sticky' && cs.left !== 'auto') return n; } return null; };
  const probe = (e, coverRight = -Infinity) => {   // coverRight: right edge of a pinned column over it
    const r = e.getBoundingClientRect();
    // a control larger than the target (a table row, a scroll box) is probed over its visible part;
    // anything smaller gets a full target-sized square, so clipping of its tap area still fails
    let v = { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
    for (let a = e.parentElement; a; a = a.parentElement) {
      if (getComputedStyle(a).overflow === 'visible') continue;
      const c = a.getBoundingClientRect();
      v = { left: Math.max(v.left, c.left), top: Math.max(v.top, c.top), right: Math.min(v.right, c.right), bottom: Math.min(v.bottom, c.bottom) };
    }
    v = { left: Math.max(v.left, 0, coverRight), top: Math.max(v.top, 0), right: Math.min(v.right, innerWidth), bottom: Math.min(v.bottom, innerHeight) };
    // the visible part is probed, but never less than the target: a mostly hidden control still fails
    const span = (own, lo, hi) => own > target ? [(lo + hi) / 2, Math.max(hi - lo, target) - 2] : null;
    const sx = span(r.width, v.left, v.right), sy = span(r.height, v.top, v.bottom);
    const cx = sx ? sx[0] : r.left + r.width / 2, w = sx ? sx[1] : target - 2;   // inset 1 px
    const cy = sy ? sy[0] : r.top + r.height / 2, h = sy ? sy[1] : target - 2;
    for (const [fx, fy] of [[-1,-1],[0,-1],[1,-1],[-1,0],[0,0],[1,0],[-1,1],[0,1],[1,1]]) {
      const corner = fx && fy ? 6 : 0;                                           // corners 7 px in: rounded corners
      const x = cx + fx * (w / 2 - corner), y = cy + fy * (h / 2 - corner);
      const hit = document.elementFromPoint(x, y);
      if (!hit || !(hit === e || e.contains(hit))) {
        return { hit, why: `${Math.round(r.width)} x ${Math.round(r.height)} px, point (${fx}, ${fy}) hits ${hit ? describeFn(hit) : 'nothing'}` };
      }
    }
    return null;
  };
  for (const e of document.querySelectorAll(query)) {
    if (!e.getClientRects().length || getComputedStyle(e).visibility === 'hidden') continue;
    if (e.closest('canvas') || e.matches('.pos-dot')) continue;                 // charts: keyboard alternative instead
    if (e.matches('a') && e.closest('p, li') && !e.matches('.nav-link')) continue;  // inline links in sentences (WCAG exception)
    if (modal && !modal.contains(e)) continue;                                   // inert behind an open dialog
    e.scrollIntoView({ block: 'center', inline: 'center' });
    await frame();                                                               // let snap scrolling settle
    let fail = probe(e);
    if (fail && fail.hit && pinnedOf(fail.hit) && !pinnedOf(e)) {                // under a pinned column: scroll it clear,
      e.scrollIntoView({ block: 'center', inline: 'end' });                      // as a reader would, and try again
      await frame();
      fail = probe(e);
      const pin = fail && fail.hit && pinnedOf(fail.hit);                        // still partly under it (a wide pinned
      if (pin) fail = probe(e, pin.getBoundingClientRect().right);               // column): a reader taps the part beside
    }                                                                            // it, which must be 48 px too
    if (fail) out[describeFn(e)] = fail.why;
  }
  return out;
}"""


def _small_controls(page, view) -> dict[str, str]:
    """Controls whose 48 x 48 px tap area (or own box, if larger) does not all respond to them:
    too small, clipped by a container, or overlapped by a neighbour's tap area."""
    return page.evaluate(PROBE_JS, [CONTROL_QUERY, TARGET, DESCRIBE_JS])


def test_touch_targets_on_phones(open_page):
    found, detail = set(), {}
    # 360 px also with a wide font: Linux draws wider text than Windows, so chips that fit one row
    # here wrap there, and a pinned column grows (both broke tap areas only on the CI runner)
    for view in VIEWS_CHECKED:
        for width, wide in ((360, False), (440, False), (360, True)):
            page = _open(open_page, view, width)
            if wide:
                page.add_style_tag(content=WIDE_FONT)
                page.wait_for_timeout(300)
            for control, why in _small_controls(page, view).items():
                found.add(f"{view} | {control}")
                detail.setdefault(f"{view} | {control}", f"{width} px{' (wide font)' if wide else ''}: {why}")
            page.close()
    problems = compare("touch", found, "control without a 48 x 48 px tap area")
    problems = [f"{p}  [{detail[k]}]" if (k := p.split(": ", 1)[-1]) in detail else p for p in problems]
    assert not problems, "\n".join(problems[:40]) + (f"\n... {len(problems) - 40} more" if len(problems) > 40 else "")
