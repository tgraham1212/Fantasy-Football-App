"""The League sub-tab's Strength of Schedule tab (strength-of-schedule-page 4.9.6.x), in the browser against
the published data: the tab, its views, Season selector and URL, both tables, their colours and sorting,
the notes and the phone layout with the Manager column pinned. Expectations come from the published
schedule file, so the checks hold as the season moves on."""

from __future__ import annotations

import pytest

PHONES = (360, 390, 414, 440)
LEAGUE = "dynasty"


def schedule(page, league=LEAGUE):
    return page.evaluate("async (k) => (await fetch(`data/${k}/schedule.json`)).json()", league)


def open_sos(open_page, width=1280, rest="", league=LEAGUE):
    page, _ = open_page(f"index.html#{league}/league/schedule{rest}", width)
    page.wait_for_function("document.querySelector('#sos-page table')")
    page.wait_for_timeout(200)
    return page


def finished_season(data):
    """A season with every week played (no upcoming weeks)."""
    return next(s for s, e in sorted(data["seasons"].items(), reverse=True)
                if not any(c["upcoming"] for c in e["ranks"][0]["cells"]))


def heads(page, table):
    return page.eval_on_selector_all(f"{table} thead tr:last-child th", "ths => ths.map(t => t.textContent.trim())")


def quarter(rank, teams):
    return min(4, (rank - 1) * 4 // teams + 1)


def bucket(d):
    if abs(d) < 0.05:
        return "s0"
    if d <= -2:
        return "s1"
    return "s2" if d < 0 else "s3" if d < 2 else "s4"


def test_schedule_tab_opens(open_page):
    """4.9.6: Strength of Schedule is the second League tab and opens on Weekly Ranks for the current season."""
    page, _ = open_page(f"index.html#{LEAGUE}/league/records", 1280)
    page.wait_for_function("document.querySelector('#lg-champions .lg-body').children.length > 0")
    tabs = page.eval_on_selector_all("#lg-tabs button", "bs => bs.map(b => b.textContent.trim())")
    assert tabs[:2] == ["Records", "Strength of Schedule"]
    page.click("#lg-tabs [data-lg-tab=schedule]")
    page.wait_for_timeout(300)
    data = schedule(page)
    assert page.is_visible("#sos-ranks") and not page.is_visible("#sos-swap") and not page.is_visible("#lg-managers")
    assert not page.is_visible("#lg-views") and page.is_visible("#sos-views")
    assert page.input_value("#sos-season") == data["current_season"]
    assert page.evaluate("location.hash") == f"#{LEAGUE}/league/schedule/{data['current_season']}"


def test_view_switch(open_page):
    """4.9.6.1: two buttons switch Weekly Ranks and Schedule Swap and show which is pressed."""
    page = open_sos(open_page)
    page.click("#sos-views [data-sos-view=swap]")
    assert page.is_visible("#sos-swap") and not page.is_visible("#sos-ranks")
    assert page.get_attribute("#sos-views [data-sos-view=swap]", "aria-pressed") == "true"
    assert page.get_attribute("#sos-views [data-sos-view=ranks]", "aria-pressed") == "false"


def test_season_selector(open_page):
    """4.9.6.2: every stored season, current first; a finished season has no Upcoming column."""
    page = open_sos(open_page)
    data = schedule(page)
    options = page.eval_on_selector_all("#sos-season option", "os => os.map(o => o.value)")
    assert options == sorted(data["seasons"], reverse=True) and options[0] == data["current_season"]
    past = finished_season(data)
    page.select_option("#sos-season", past)
    page.wait_for_timeout(300)
    assert "Upcoming" not in heads(page, "#sos-ranks") and page.locator("#sos-ranks td.sos-up").count() == 0
    assert page.evaluate("location.hash") == f"#{LEAGUE}/league/schedule/{past}"


def test_url_names_view_and_season(open_page):
    """4.9.6.3: the URL names the view and season, and a link opens them."""
    page = open_sos(open_page)
    past = finished_season(schedule(page))
    page = open_sos(open_page, rest=f"/swap/{past}")
    assert page.is_visible("#sos-swap") and page.input_value("#sos-season") == past
    page.click("#sos-views [data-sos-view=ranks]")
    assert page.evaluate("location.hash") == f"#{LEAGUE}/league/schedule/{past}"


def test_weekly_ranks_table(open_page):
    """4.9.6.4: a row per Manager in Weekly Ranks order with rank, Season, Played, Upcoming and a cell per week."""
    page = open_sos(open_page)
    season = schedule(page)["seasons"][page.input_value("#sos-season")]
    labels = heads(page, "#sos-ranks")
    upcoming = any(c["upcoming"] for c in season["ranks"][0]["cells"])
    assert labels[:5] == ["Manager", "Rank", "Season", "Played"] + (["Upcoming"] if upcoming else labels[4:5])
    rows = page.locator("#sos-ranks tbody tr")
    assert rows.count() == len(season["ranks"])
    assert rows.first.locator("td.sos-c").count() == len(season["weeks"])
    first = rows.first.locator("td.sos-rank").inner_text().split()
    assert first == ["1st", "Hardest"]
    assert page.locator("#sos-ranks tbody tr").first.locator("td.num").first.inner_text() == f"{season['ranks'][0]['season']:.2f}"


def test_week_cell(open_page):
    """4.9.6.4.1: points at the top, the weekly rank large, the opponent's picture, the full name on hover."""
    page = open_sos(open_page)
    data = schedule(page)
    season = data["seasons"][page.input_value("#sos-season")]
    cell = season["ranks"][0]["cells"][0]
    td = page.locator("#sos-ranks tbody tr").first.locator("td.sos-c").first
    assert td.locator(".sos-pts").inner_text() == f"{cell['points']:.1f}"
    assert td.locator(".sos-rk").inner_text() == str(cell["opp_rank"])
    assert td.locator(".mgr-crest").count() == 1
    name = data["managers"][cell["opp"]]["name"]
    assert name in td.get_attribute("title") and f"ranked {cell['opp_rank']} of" in td.get_attribute("title")
    big, small = (float(td.locator(s).evaluate("e => parseFloat(getComputedStyle(e).fontSize)")) for s in (".sos-rk", ".sos-pts"))
    assert big > small * 1.5


def test_weekly_ranks_colours(open_page):
    """4.9.6.4.2: cells coloured by quarter of the league's teams (1-3, 4-6, 7-9, 10-12 in a 12-team league)."""
    page = open_sos(open_page)
    season = schedule(page)["seasons"][page.input_value("#sos-season")]
    teams = len(season["ranks"])
    classes = page.eval_on_selector_all("#sos-ranks tbody tr", "trs => trs.map(tr => [...tr.querySelectorAll('td.sos-c')].map(td => td.className))")
    for row, cls in zip(season["ranks"], classes):
        for cell, c in zip(row["cells"], cls):
            assert f"r{quarter(cell['opp_rank'], teams)}" in c.split(), (cell, c)
    fills = page.evaluate("""() => ['r1', 'r2', 'r3', 'r4'].map((r) => {
        const td = document.querySelector(`#sos-ranks td.sos-c.${r}:not(.sos-up)`);
        return td ? getComputedStyle(td).backgroundColor : null; })""")
    present = [f for f in fills if f]
    assert len(set(present)) == len(present), f"each quarter has its own colour: {fills}"


def test_projected_weeks_marked(open_page):
    """4.9.6.4.3: upcoming weeks solid, played faded, a line before the first upcoming week under "Forecast"."""
    page = open_sos(open_page)
    season = schedule(page)["seasons"][page.input_value("#sos-season")]
    cells = season["ranks"][0]["cells"]
    if not any(c["upcoming"] for c in cells):
        pytest.skip("the current season has no upcoming weeks")
    first_up = next(i for i, c in enumerate(cells) if c["upcoming"])
    row = page.locator("#sos-ranks tbody tr").first.locator("td.sos-c")
    assert all(("sos-up" in row.nth(i).get_attribute("class")) == c["upcoming"] for i, c in enumerate(cells))
    assert row.nth(first_up).evaluate("e => getComputedStyle(e).borderLeftWidth") == "2px"
    groups = page.eval_on_selector_all("#sos-ranks thead tr.sos-group th", "ths => ths.map(t => t.textContent.trim())")
    assert "Forecast" in groups and "Played" in groups
    faded, solid = row.nth(first_up - 1), row.nth(first_up)
    lum = "e => { const [r, g, b] = getComputedStyle(e).backgroundColor.match(/\\d+/g).map(Number); return 0.2126 * r + 0.7152 * g + 0.0722 * b; }"
    if faded.get_attribute("class").split()[1] == solid.get_attribute("class").split()[1]:
        assert faded.evaluate(lum) > solid.evaluate(lum), "the projected shade is the solid, darker one"


def test_schedule_swap_table(open_page):
    """4.9.6.5: a row and column per Manager in Swap order, own schedule outlined, Own, Avg, Index and Range."""
    page = open_sos(open_page, rest="/swap")
    swap = schedule(page)["seasons"][page.input_value("#sos-season")]["swap"]
    n = len(swap["order"])
    labels = heads(page, "#sos-swap")
    assert labels[:2] == ["Manager", "Rank"] and labels[-4:] == ["Own", "Avg", "Index", "Range"]
    assert page.locator("#sos-swap thead th.sos-sched").count() == n
    rows = page.locator("#sos-swap tbody tr")
    assert rows.count() == n
    for i, r in enumerate(swap["rows"][:3]):
        cells = rows.nth(i).locator("td.sos-w")
        own = swap["order"].index(r["user"])
        assert "own" in cells.nth(own).get_attribute("class")
        assert cells.nth(own).evaluate("e => getComputedStyle(e).outlineStyle") == "solid"
        assert cells.nth(own).inner_text() == f"{r['own']:.1f}"
    assert swap["order"] == [r["user"] for r in swap["rows"]], "the default order puts own schedules on the diagonal"
    assert rows.first.locator("td.sos-range").inner_text() == f"{swap['rows'][0]['lo']:.1f} – {swap['rows'][0]['hi']:.1f}"


def test_schedule_swap_colours(open_page):
    """4.9.6.5.1: cells coloured by wins against own-schedule wins, at -2, 0 and +2, grey within 0.05."""
    page = open_sos(open_page, rest="/swap")
    swap = schedule(page)["seasons"][page.input_value("#sos-season")]["swap"]
    classes = page.eval_on_selector_all("#sos-swap tbody tr", "trs => trs.map(tr => [...tr.querySelectorAll('td.sos-w')].map(td => td.className))")
    for r, cls in zip(swap["rows"], classes):
        for user, v, c in zip(swap["order"], r["wins"], cls):
            want = "own" if user == r["user"] else bucket(v - r["own"])
            assert want in c.split(), (r["user"], user, v, c)


def test_sortable_columns(open_page):
    """4.9.6.7: Weekly Ranks sorts by Season, Played and Upcoming (hardest first, then flipped); Swap by Index."""
    page = open_sos(open_page)
    col = "upcoming" if page.locator("#sos-ranks thead [data-col='upcoming']").count() else "played"
    page.click(f"#sos-ranks thead [data-col='{col}'] button.sort")
    season = schedule(page)["seasons"][page.input_value("#sos-season")]
    by = {r["user"]: r[col] for r in season["ranks"]}
    names = {u: m["name"] for u, m in schedule(page)["managers"].items()}
    order = page.eval_on_selector_all("#sos-ranks tbody .sos-mgr a.manager-link", "as => as.map(a => a.textContent)")
    values = [by[next(u for u, n in names.items() if n == name)] for name in order]
    assert values == sorted(values), "first pick: lowest (hardest) first"
    assert page.get_attribute(f"#sos-ranks thead [data-col='{col}']", "aria-sort") == "ascending"
    page.click(f"#sos-ranks thead [data-col='{col}'] button.sort")
    order = page.eval_on_selector_all("#sos-ranks tbody .sos-mgr a.manager-link", "as => as.map(a => a.textContent)")
    values = [by[next(u for u, n in names.items() if n == name)] for name in order]
    assert values == sorted(values, reverse=True)
    page.click("#sos-views [data-sos-view=swap]")
    page.click("#sos-swap thead [data-col='own'] button.sort")
    own = page.eval_on_selector_all("#sos-swap tbody td.sos-edge", "tds => tds.map(t => parseFloat(t.textContent))")
    assert own == sorted(own, reverse=True)


def test_notes_shown(open_page):
    """4.9.6.8: a note under each table says what the cells hold and which end is the hardest."""
    page = open_sos(open_page)
    assert "lowest average is the hardest" in page.inner_text("#sos-ranks .sos-note")
    page.click("#sos-views [data-sos-view=swap]")
    note = page.inner_text("#sos-swap .sos-note")
    assert "minus wins on your own" in note and "highest index is the hardest" in note


@pytest.mark.parametrize("view", ["", "/swap"])
@pytest.mark.parametrize("width", PHONES)
def test_manager_column_pinned_on_phones(open_page, width, view):
    """4.9.6.9: below 600 px each table scrolls in its card, the Manager column pinned, names on one line."""
    page = open_sos(open_page, width, view)
    card = "#sos-swap" if view else "#sos-ranks"
    assert not page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
    before = page.eval_on_selector(f"{card} tbody .sos-mgr", "e => e.getBoundingClientRect().left")
    page.eval_on_selector(f"{card} .sos-wrap", "w => { w.scrollLeft = w.scrollWidth; }")
    page.wait_for_timeout(100)
    pinned = page.evaluate(f"""() => {{
        const wrap = document.querySelector('{card} .sos-wrap').getBoundingClientRect();
        const cells = [...document.querySelectorAll('{card} .sos-mgr')].map((c) => c.getBoundingClientRect().left);
        const lines = [...document.querySelectorAll('{card} .sos-mgr a.manager-link')].map((a) => a.getClientRects().length);
        return {{ wrap: wrap.left, cells, lines, scrolled: document.querySelector('{card} .sos-wrap').scrollLeft }};
    }}""")
    assert pinned["scrolled"] > 0, "the table is wider than the phone"
    assert all(abs(x - pinned["wrap"]) <= 1 for x in pinned["cells"]), pinned
    assert all(n == 1 for n in pinned["lines"]), "every Manager name on one line"
    assert before >= pinned["wrap"] - 1


@pytest.mark.parametrize("width", PHONES)
def test_summary_columns_first_on_phones(open_page, width):
    """4.9.6.9.1: on phones only Rank and Season (Weekly Ranks) or Rank and Index (Swap) precede the cells,
    all on screen before scrolling."""
    page = open_sos(open_page, width)
    labels = heads(page, "#sos-ranks")
    assert labels[:3] == ["Manager", "Rank", "Season"] and "Played" not in labels and "Upcoming" not in labels
    page.click("#sos-views [data-sos-view=swap]")
    page.wait_for_timeout(200)
    assert heads(page, "#sos-swap")[:3] == ["Manager", "Rank", "Index"]
    right = page.evaluate("""() => {
        const wrap = document.querySelector('#sos-swap .sos-wrap').getBoundingClientRect().right;
        const index = document.querySelector("#sos-swap thead [data-col='index']").getBoundingClientRect().right;
        return [index, wrap]; }""")
    assert right[0] <= right[1] + 1, f"Index is on screen before scrolling: {right}"
