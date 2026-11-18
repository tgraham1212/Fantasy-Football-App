"""Browser layout check: every page at phone, tablet and desktop widths, every control through its
states. See controls.py for the registry and what a control's declared effect allows."""

from __future__ import annotations

import pytest

from tests.layout.conftest import WIDTHS
from tests.layout.controls import CONTROL_QUERY, CONTROLS, INSIDE, LANDMARKS, VIEWS, Control

TOLERANCE = 0.5

BOXES_JS = """(sels) => {
  const out = {};
  for (const s of sels) {
    document.querySelectorAll(s).forEach((e, i) => {
      const r = e.getBoundingClientRect();
      if (!r.width && !r.height) return;
      out[`${s} #${i}`] = [r.left + scrollX, r.top + scrollY, r.width, r.height];
    });
  }
  return out;
}"""

FLAGS_JS = """([sels, regions, grow]) => {
  const out = {};
  for (const s of sels) {
    document.querySelectorAll(s).forEach((e, i) => {
      out[`${s} #${i}`] = {
        region: regions.some((r) => e.closest(r)),
        grow: grow.some((g) => e.matches(g)),
      };
    });
  }
  return out;
}"""

OVERFLOW_JS = """(inside) => {
  const problems = [];
  const sw = document.documentElement.scrollWidth;
  if (sw > innerWidth + 0.5) problems.push(`page scrolls sideways (${sw}px wide in ${innerWidth}px)`);
  for (const s of inside) {
    for (const e of document.querySelectorAll(s)) {
      const r = e.getBoundingClientRect();
      if (!r.width) continue;
      if (r.left < -0.5 || r.right > innerWidth + 0.5) problems.push(`${s} spans ${Math.round(r.left)}..${Math.round(r.right)} outside 0..${innerWidth}`);
    }
  }
  return problems;
}"""


def open_view(open_page, view_name: str, width: int):
    view = VIEWS[view_name]
    page, relay = open_page(view.path, width)
    if view.setup:
        view.setup(page)
    return page, relay, {"setup": view.setup or (lambda p: None)}


def control_box(page, control: Control):
    """The control's box in page coordinates (independent of scrolling), or None when hidden."""
    return page.evaluate("""(sel) => {
      const e = document.querySelector(sel);
      if (!e || !e.getClientRects().length) return null;
      const r = e.getBoundingClientRect();
      return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
    }""", control.selector)


def threshold(page, control: Control):
    """Document y at or under which elements may move (the declared `below`)."""
    if not control.below:
        return None
    sel = control.selector if control.below == "self" else control.below
    return page.eval_on_selector(sel, "e => e.getBoundingClientRect().bottom + scrollY")


def moved(control: Control, before: dict, after: dict, flags: dict, limit) -> list[str]:
    problems = []
    for key, (x, y, w, h) in before.items():
        if key not in after or flags.get(key, {}).get("region"):
            continue
        if limit is not None and y >= limit - TOLERANCE:
            continue
        ax, ay, aw, ah = after[key]
        deltas = {"x": ax - x, "y": ay - y, "width": aw - w, "height": ah - h}
        if flags.get(key, {}).get("grow"):
            deltas.pop("height")
        bad = {k: round(v, 1) for k, v in deltas.items() if abs(v) > TOLERANCE}
        if bad:
            problems.append(f"{key} changed {bad}")
    return problems


CASES = [(c, w) for c in CONTROLS if c.states for w in WIDTHS]


@pytest.mark.parametrize("control,width", CASES, ids=[f"{c.name}-{w}" for c, w in CASES])
def test_control_keeps_the_layout(open_page, control: Control, width: int):
    page, relay, ctx = open_view(open_page, control.view, width)
    problems = [f"on load: {p}" for p in page.evaluate(OVERFLOW_JS, list(INSIDE))]
    for state in control.states:
        before = page.evaluate(BOXES_JS, list(LANDMARKS))
        own = control_box(page, control)
        limit = threshold(page, control)
        state.act(page, relay, ctx)
        after = page.evaluate(BOXES_JS, list(LANDMARKS))
        flags = page.evaluate(FLAGS_JS, [list(LANDMARKS), list(control.regions), list(control.grow)])
        found = moved(control, before, after, flags, limit)
        new_own = control_box(page, control)
        if own and new_own and not control.self_moves:
            d = {k: round(new_own[k] - own[k], 1) for k in ("x", "y", "width", "height") if abs(new_own[k] - own[k]) > TOLERANCE}
            if d:
                found.append(f"the control itself changed {d}")
        found += page.evaluate(OVERFLOW_JS, list(INSIDE))
        problems += [f"{state.name}: {p}" for p in found]
    assert not problems, f"{control.name} at {width}px:\n  " + "\n  ".join(problems)


COVERAGE_VIEWS = ("predictions", "games", "games-final", "war", "war-all", "war-dialog", "calibration")


@pytest.mark.parametrize("view", COVERAGE_VIEWS)
def test_every_control_is_listed(open_page, view):
    page, relay, ctx = open_view(open_page, view, 1280)
    if view == "predictions":  # bring up the version note so its button is checked too
        from tests.layout.controls import new_version
        new_version(page, relay, ctx)
        assert page.locator("#version-note").is_visible(), "the new version note did not appear"
    selectors = [c.selector for c in CONTROLS]
    unlisted = page.evaluate(
        """([query, selectors, inDialog]) => [...document.querySelectorAll(query)]
             .filter((e) => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
             .filter((e) => !inDialog || e.closest('#war-dialog'))
             .filter((e) => !selectors.some((s) => e.matches(s)))
             .map((e) => e.outerHTML.slice(0, 120))""",
        [CONTROL_QUERY, selectors, view == "war-dialog"],
    )
    assert not unlisted, f"controls on {view} missing from tests/layout/controls.py:\n  " + "\n  ".join(unlisted)


@pytest.mark.parametrize("width", WIDTHS)
def test_full_list_scrolls_only_its_table(open_page, width):
    page, relay, ctx = open_view(open_page, "war-dialog", width)
    sizes = page.evaluate("""() => {
      const d = document.getElementById('war-dialog'), t = d.querySelector('.dialog-table');
      return { dialog: [d.scrollHeight, d.clientHeight], table: [t.scrollHeight, t.clientHeight] };
    }""")
    assert sizes["dialog"][0] <= sizes["dialog"][1] + 1, f"the overlay itself scrolls: {sizes}"
    assert sizes["table"][0] > sizes["table"][1], f"the table should be the scroll area: {sizes}"


def test_phone_lineups_show_full_names(open_page):
    page, relay, ctx = open_view(open_page, "games-final", 375)
    page.click("details.lineup summary")
    page.wait_for_timeout(300)
    clipped = page.evaluate("""() => [...document.querySelectorAll('.team-players ul:not(.out) li .nm')]
        .filter((n) => n.getClientRects().length && n.scrollWidth > n.clientWidth + 1)
        .map((n) => `${n.textContent} (${n.clientWidth} of ${n.scrollWidth}px)`)""")
    assert not clipped, "names cut off on a phone: " + ", ".join(clipped)
    fills = page.evaluate("""() => [...document.querySelectorAll('li.fill .nm')].filter((n) => n.getClientRects().length).map((n) => n.innerText.trim())""")
    assert all(f == "Free agent" for f in fills), fills


def test_data_swap_keeps_the_visitors_place(open_page):
    from tests.layout.controls import new_data
    page, relay, ctx = open_view(open_page, "games-final", 1280)
    page.click(".game-card[data-card='0'] .view-toggle button[data-view='model']")
    page.click(".game-card[data-card='0'] details.lineup summary")
    page.wait_for_timeout(300)
    new_data(page, relay, ctx)
    assert page.locator("#refresh-note").inner_text() == "Updated just now" or not page.locator("#refresh-btn").is_visible()
    assert page.eval_on_selector("#games-week", "s => s.value") == "10"
    assert page.get_attribute(".game-card[data-card='0'] .view-toggle button[data-view='model']", "aria-pressed") == "true"
    assert page.eval_on_selector(".game-card[data-card='0'] details.lineup", "d => d.open")
    assert page.url.endswith("/games/10")
