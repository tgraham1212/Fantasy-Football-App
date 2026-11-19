"""Browser layout check: every page at phone, tablet and desktop widths, every control through its
states. See controls.py for the registry and what a control's declared effect allows."""

from __future__ import annotations

import pytest

from tests.layout.conftest import OTHER_ENGINE_WIDTHS, PHONE_WIDTHS, WIDTHS, engine_cases
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


CASES = [(e, c, w) for c in CONTROLS if c.states for e, w in engine_cases()]


@pytest.mark.parametrize("engine,control,width", CASES, ids=[f"{e}-{c.name}-{w}" for e, c, w in CASES], indirect=["engine"])
def test_control_keeps_the_layout(open_page, engine, control: Control, width: int):
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


COVERAGE_VIEWS = ("predictions", "games", "games-final", "positions", "positions-past", "war", "war-all", "war-dialog", "calibration")


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
    page, relay, ctx = open_view(open_page, "games-final", 360)
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


WIDE_FONT = "* { font-family: Verdana, 'DejaVu Sans', sans-serif !important; }"


@pytest.mark.parametrize("engine", ["chromium", "webkit", "firefox"], indirect=True)
@pytest.mark.parametrize("view", COVERAGE_VIEWS)
def test_wide_fonts_do_not_scroll_sideways(open_page, engine, view):
    """Fonts differ between machines (Linux draws wider text than Windows), so a phone layout
    that only just fits on one machine scrolls sideways on another. Check with a wide font."""
    page, relay, ctx = open_view(open_page, view, 360)
    page.add_style_tag(content=WIDE_FONT)
    page.wait_for_timeout(300)
    problems = page.evaluate(OVERFLOW_JS, list(INSIDE))
    assert not problems, f"{view} at 360px with a wide font:\n  " + "\n  ".join(problems)



def test_subtab_strip_swipes_on_a_phone(open_page):
    page, relay, ctx = open_view(open_page, "war", 360)
    strip = page.evaluate("""() => { const m = document.getElementById('subtabs'), t = m.querySelector('[data-page=war]');
        const mr = m.getBoundingClientRect(), tr = t.getBoundingClientRect();
        return { scroll: m.scrollWidth, client: m.clientWidth, tabLeft: tr.left, tabRight: tr.right, left: mr.left, right: mr.right,
                 pressed: t.getAttribute('aria-pressed') }; }""")
    assert strip["scroll"] > strip["client"], f"the sub-tabs should overflow their strip on a phone: {strip}"
    assert strip["left"] - 0.5 <= strip["tabLeft"] and strip["tabRight"] <= strip["right"] + 0.5 and strip["pressed"] == "true", strip
    y = page.evaluate("scrollY")
    page.evaluate("document.getElementById('subtabs').scrollLeft = 0")
    page.wait_for_timeout(200)
    assert page.evaluate("scrollY") == y, "scrolling the sub-tab strip moved the page"
    assert page.evaluate("document.documentElement.scrollWidth") <= 360


def test_subtab_strip_does_not_scroll_on_desktop(open_page):
    page, relay, ctx = open_view(open_page, "predictions", 1280)
    m = page.evaluate("(() => { const m = document.getElementById('subtabs'); return [m.scrollWidth, m.clientWidth, m.className]; })()")
    assert m[0] <= m[1] and "fade" not in m[2], m


@pytest.mark.parametrize("view", ["positions", "positions-past"])
def test_positions_charts_fit_a_phone(open_page, view):
    page, relay, ctx = open_view(open_page, view, 360)
    problems = page.evaluate("""() => {
      const out = [];
      for (const card of document.querySelectorAll('.pos-card')) {
        const c = card.getBoundingClientRect();
        if (c.left < -0.5 || c.right > innerWidth + 0.5) out.push(`${card.dataset.pos} card spans ${c.left}..${c.right}`);
        for (const el of card.querySelectorAll('.pos-top-name, .pos-dot, .pos-rep-label')) {
          const r = el.getBoundingClientRect();
          if (r.left < c.left - 0.5 || r.right > c.right + 0.5) out.push(`${card.dataset.pos}: ${el.getAttribute('class')} ${el.textContent || el.dataset.name} leaves its chart`);
        }
      }
      return out;
    }""")
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("width", [360, 1280])
def test_position_dots_do_not_hide_each_other(open_page, width):
    page, relay, ctx = open_view(open_page, "positions", width)
    overlaps = page.evaluate("""() => {
      const out = [];
      for (const card of document.querySelectorAll('.pos-card')) {
        const dots = [...card.querySelectorAll('.pos-dot')].map((d) => ({ x: +d.getAttribute('cx'), y: +d.getAttribute('cy'), r: +d.getAttribute('r'), n: d.dataset.name }));
        for (let i = 0; i < dots.length; i += 1) for (let j = i + 1; j < dots.length; j += 1) {
          const a = dots[i], b = dots[j];
          if (Math.hypot(a.x - b.x, a.y - b.y) < a.r + b.r - 2) out.push(`${card.dataset.pos}: ${a.n} and ${b.n}`);
        }
      }
      return out;
    }""")
    assert not overlaps, f"{len(overlaps)} overlapping dots at {width}px: " + ", ".join(overlaps[:8])


def test_positions_data_swap_keeps_the_season(open_page):
    from tests.layout.controls import PAST_SEASON, new_data
    page, relay, ctx = open_view(open_page, "positions-past", 1280)
    new_data(page, relay, ctx)
    assert page.eval_on_selector("#positions-season", "s => s.value") == PAST_SEASON
    assert page.locator(".pos-card").count() >= 5 and page.url.endswith("/positions")



def test_paired_charts_share_row_height_and_fill_their_cards(open_page):
    page, relay, ctx = open_view(open_page, "positions", 1280)
    cards = page.evaluate("""() => [...document.querySelectorAll('.pos-card')].map((c) => ({
        pos: c.dataset.pos, top: Math.round(c.getBoundingClientRect().top), height: c.getBoundingClientRect().height,
        row: getComputedStyle(c.querySelector('.pos-chart')).getPropertyValue('--pos-row').trim() }))""")
    rows = {}
    for c in cards:
        rows.setdefault(c["top"], []).append(c)
    pairs = [r for r in rows.values() if len(r) == 2]
    assert pairs, cards
    for a, b in pairs:
        assert a["row"] == b["row"], f"{a['pos']} and {b['pos']} row heights differ: {a['row']} vs {b['row']}"
        assert abs(a["height"] - b["height"]) <= 1, f"{a['pos']} and {b['pos']} cards differ in height"


def test_row_labels_show_manager_and_team(open_page):
    page, relay, ctx = open_view(open_page, "positions", 1280)
    label = page.evaluate("""() => { const l = document.querySelector('.pos-label');
        return { manager: l.querySelector('.owner-name')?.textContent, team: l.querySelector('.team')?.textContent }; }""")
    assert label["manager"] and label["team"], label


@pytest.mark.parametrize("which,text_class", [("data-status", "pos-status"), ("data-taxi", "pos-taxi")])
def test_popup_shows_status_and_taxi_lines(open_page, which, text_class):
    page, relay, ctx = open_view(open_page, "positions", 1280)
    if not page.locator(f".pos-dot[{which}]").count():
        pytest.skip(f"no dot with {which} in this league's current data")
    page.locator(f".pos-dot[{which}]").first.evaluate("e => e.focus({ preventScroll: true })")
    page.wait_for_timeout(200)
    line = page.locator(f".pos-pop:not([hidden]) .{text_class}")
    assert line.count() == 1
    expected = page.locator(f".pos-dot[{which}]").first.get_attribute("data-status") if which == "data-status" else "Taxi"
    assert line.inner_text() == expected



def _scroll_and_left(page, container, cell):
    return page.evaluate("""([container, cell]) => {
      const box = document.querySelector(container);
      box.scrollLeft = box.scrollWidth;
      const c = document.querySelector(cell).getBoundingClientRect(), b = box.getBoundingClientRect();
      // the pinned cell sits flush with the scroll box's edge (sticky left = minus the box's padding)
      return { scrolled: box.scrollLeft, cellLeft: c.left, contentLeft: b.left };
    }""", [container, cell])


@pytest.mark.parametrize("engine", ["chromium", "webkit", "firefox"], indirect=True)
def test_forecast_table_pins_the_manager_column_on_phones(open_page, engine):
    page, relay, ctx = open_view(open_page, "predictions", 360)
    r = _scroll_and_left(page, "#page-predictions .table-wrap", "#odds-body td.col-owner")
    assert r["scrolled"] > 0, "the forecast table should scroll sideways at 360 px"
    assert abs(r["cellLeft"] - r["contentLeft"]) <= 1, f"the Manager column did not stay at the left edge: {r}"


@pytest.mark.parametrize("engine", ["chromium", "webkit", "firefox"], indirect=True)
def test_war_full_list_pins_the_name_column_on_phones(open_page, engine):
    page, relay, ctx = open_view(open_page, "war-dialog", 360)
    r = _scroll_and_left(page, "#war-dialog .dialog-table", "#war-full td.name")
    assert r["scrolled"] > 0, "the full list should scroll sideways at 360 px"
    assert abs(r["cellLeft"] - r["contentLeft"]) <= 1, f"the name column did not stay at the left edge: {r}"


@pytest.mark.parametrize("engine", ["chromium", "webkit", "firefox"], indirect=True)
@pytest.mark.parametrize("view", ["games", "games-final"])
def test_games_cards_stack_and_team_rows_do_not_overlap_on_large_phones(open_page, engine, view):
    page, relay, ctx = open_view(open_page, view, 440)
    problems = page.evaluate("""() => {
      const out = [];
      document.querySelectorAll('.game-body').forEach((b, i) => {
        if (getComputedStyle(b).gridTemplateColumns.trim().split(/\\s+/).length !== 1) out.push(`card ${i} is not stacked`);
      });
      document.querySelectorAll('.game-team').forEach((row, i) => {
        const parts = [...row.querySelectorAll('.owner-name, .team, .mean .num, .mean .unit, .mean .choices, .win')]
          .map((e) => [e.className, e.getBoundingClientRect()]).filter(([, r]) => r.width && r.height);
        for (let a = 0; a < parts.length; a++) for (let b = a + 1; b < parts.length; b++) {
          const [na, ra] = parts[a], [nb, rb] = parts[b];
          const overlap = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left) > 1 && Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top) > 1;
          if (overlap) out.push(`row ${i}: ${na} overlaps ${nb}`);
        }
      });
      return out;
    }""")
    assert not problems, "\n".join(problems[:12])


def test_finished_cards_show_the_actual_score_first(open_page):
    page, relay, ctx = open_view(open_page, "games-final", 1280)
    blocks = page.evaluate("""() => [...document.querySelectorAll('.game-card .game-team .mean')].slice(0, 4).map((m) => m.innerText.split('\\n'))""")
    assert blocks, "no score blocks found"
    for lines in blocks:
        assert lines[1].endswith("forecasted"), lines


def test_charts_reach_the_card_edge_on_phones(open_page):
    page, relay, ctx = open_view(open_page, "predictions", 360)
    gaps = page.evaluate("""() => ['odds-chart', 'rating-chart'].map((id) => {
      const chart = Chart.getChart(id), canvas = document.getElementById(id);
      return canvas.getBoundingClientRect().width - chart.chartArea.right;
    })""")
    # Chart.js keeps half of the last x-axis label inside the canvas (about 10 px); the old reserved
    # label strip was 104 px, so 24 px still catches it
    assert all(g <= 24 for g in gaps), f"empty space right of the chart plots: {gaps}"


def test_metric_buttons_form_one_swipe_strip_on_phones(open_page):
    page, relay, ctx = open_view(open_page, "predictions", 360)
    tops = page.evaluate("""() => [...document.querySelectorAll('#metric-switcher button')].map((b) => Math.round(b.getBoundingClientRect().top))""")
    assert len(set(tops)) == 1, f"metric buttons wrap onto more than one line: {tops}"
    y = page.evaluate("scrollY")
    page.evaluate("document.getElementById('metric-switcher').scrollLeft = 200")
    page.wait_for_timeout(150)
    assert page.evaluate("scrollY") == y and page.evaluate("document.documentElement.scrollWidth") <= 360


PINNED_NEIGHBOURS = (
    ("predictions", "#odds-body tr", "td.col-elo-change"),  # left of the pinned Manager column
    ("war-dialog", "#war-full tbody tr", "td:first-child"),  # the # column, left of the pinned name column
)


@pytest.mark.parametrize("engine", ["chromium", "webkit", "firefox"], indirect=True)
@pytest.mark.parametrize("view,rows,cell", PINNED_NEIGHBOURS, ids=["forecast-table", "war-full-list"])
@pytest.mark.parametrize("width", PHONE_WIDTHS)
def test_pinned_columns_cover_nothing_before_scrolling(open_page, engine, view, rows, cell, width):
    """At the start position the column beside a pinned one must be fully visible (the full
    list's # column was half covered by the pinned name cell's padding cover)."""
    page, relay, ctx = open_view(open_page, view, width)
    covered = page.evaluate("""([rows, cell]) => {
      const out = [];
      for (const tr of [...document.querySelectorAll(rows)].slice(0, 6)) {
        const c = tr.querySelector(cell);
        const pinned = c && c.nextElementSibling;
        if (!c || !pinned) continue;
        const r = c.getBoundingClientRect(), p = pinned.getBoundingClientRect();
        // painted cover: a box-shadow reaching left of the pinned cell over its neighbour
        const reach = Math.min(0, ...[...getComputedStyle(pinned).boxShadow.matchAll(/(-?\d+(?:\.\d+)?)px\s+-?\d/g)].map((m) => parseFloat(m[1])));
        if (p.left + reach < r.right - 0.5) out.push(`${c.textContent.trim()} painted over by a ${-reach}px cover`);
        // stacking: the neighbour's right edge must be on top where it is on screen
        const y = r.top + r.height / 2;
        if (y > 0 && y < innerHeight) {
          const hit = document.elementFromPoint(r.right - 2, y);
          if (!(hit && (hit === c || c.contains(hit)))) out.push(`${c.textContent.trim()} covered by ${hit ? hit.className || hit.tagName : '?'}`);
        }
      }
      return out;
    }""", [rows, cell])
    assert not covered, f"{view} at {width}px: " + "; ".join(covered)


@pytest.mark.parametrize("width", WIDTHS)
def test_lineup_columns_never_overlap(open_page, width):
    """Kickoff times, points and win probability added must never be drawn over each other (the
    kickoff column collapsed to nothing beside long names and its text spilled over the points)."""
    page, relay, ctx = open_view(open_page, "games", width)
    page.evaluate("document.querySelectorAll('.team-players details').forEach((d) => { d.open = true; })")
    found = page.evaluate("""() => {
      const out = []; let kicks = 0;
      // painted text extent: a Range covers text that overflows its box; the name keeps its clipped box
      const box = (e) => { if (e.matches('.pname')) return e.getBoundingClientRect();
        const r = document.createRange(); r.selectNodeContents(e); return r.getBoundingClientRect(); };
      for (const li of document.querySelectorAll('.team-players ul:not(.out) li')) {
        const parts = [...li.children].filter((e) => e.matches('.pos, .pname, .pts, .wpa, .kick') && e.textContent.trim())
          .map((e) => [e.className, box(e)]).filter(([, r]) => r.width && r.height);
        kicks += parts.some(([n]) => n.includes('kick'));
        for (let a = 0; a < parts.length; a++) for (let b = a + 1; b < parts.length; b++) {
          const [na, ra] = parts[a], [nb, rb] = parts[b];
          if (Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left) > 0.5) out.push(`${li.textContent.trim().slice(0, 30)}: ${na} overlaps ${nb}`);
        }
      }
      return { out, kicks };
    }""")
    assert found["kicks"], "the Games view shows no kickoff times, so the check proves nothing"
    assert not found["out"], f"{width}px:\n" + "\n".join(found["out"][:12])
