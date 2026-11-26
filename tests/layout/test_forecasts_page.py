"""Behaviour of the league pages and the Forecasts sub-tab (league-odds-site 9.1.1.x, 1.3.x, 1.4.x, 4.2.x),
checked in the browser against the published data: the URL, the table's order, formats and sorting,
highlighting, the chart axis and the rating chart's ranges."""

from __future__ import annotations

import json
import math

import pytest

PAGES = ("predictions", "games", "positions", "managers", "war", "league")


def league_data(page, key: str) -> dict:
    return page.evaluate("async (k) => (await fetch(`data/${k}.json`)).json()", key)


def row_ids(page) -> list[int]:
    return page.eval_on_selector_all("#odds-body tr", "rows => rows.map(r => Number(r.dataset.roster))")


def standings_order(teams: list[dict]) -> list[int]:
    return [t["roster_id"] for t in sorted(teams, key=lambda t: (-(t["wins"] + 0.5 * t["ties"]), -t["points_for"], t["roster_id"]))]


def one_decimal(v: float) -> str:
    """As the page's toFixed(1) does: round the float's exact binary value, halves up (4.25 is
    exact and gives 4.3; 4.35 is stored as 4.3499... and gives 4.3)."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(v).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def pct_text(v) -> str:
    """The rule in league-odds-site 1.3.8."""
    if v is None:
        return "–"
    if v >= 0.9995:
        return "100%"
    if v >= 0.995:
        return ">99%"
    if 0 < v < 0.005:
        return "<1%"
    return f"{round(v * 100)}%"


def click_header(page, col: str):
    page.click(f"#odds-table thead th[data-col={col}] button.sort")
    page.wait_for_timeout(100)


def chart_state(page, canvas: str) -> dict:
    return page.evaluate("""(id) => { const c = Chart.getChart(id);
        return { max: c.options.scales.y.max, labels: c.data.labels.length,
                 sets: c.data.datasets.map(d => ({ id: d.rosterId ?? d.managerId, manager: d.managerId ?? null, color: d.borderColor, team: d.teamColor,
                                                    selected: d.isSelected, data: d.data })) }; }""", canvas)


@pytest.mark.parametrize("subtab", PAGES)
def test_url_opens_the_named_league_and_subtab(open_page, subtab):
    """9.1.1.1: the URL names the league and sub-tab, and opening it shows them."""
    page, _ = open_page("index.html#redraft" + ("" if subtab == "predictions" else f"/{subtab}"), 1280)
    assert page.get_attribute(f"#subtabs [data-page={subtab}]", "aria-pressed") == "true"
    assert page.is_visible(f"#page-{subtab}"), f"#page-{subtab} should be shown"
    pressed = page.eval_on_selector("#league-switcher", "n => [...n.querySelectorAll('button')].find(b => b.getAttribute('aria-pressed') === 'true')?.textContent")
    assert pressed == "Chris Carter's Fall Guys"
    assert page.evaluate("location.hash").startswith("#redraft")


def test_switching_league_keeps_the_subtab(open_page):
    """9.1.1.2"""
    page, _ = open_page("index.html#dynasty/positions", 1280)
    page.click("#league-switcher button:has-text(\"Chris Carter's Fall Guys\")")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    assert page.evaluate("location.hash").startswith("#redraft/positions")
    assert page.get_attribute("#subtabs [data-page=positions]", "aria-pressed") == "true"
    assert page.is_visible("#page-positions")


@pytest.mark.parametrize("league", ["dynasty", "redraft"])
def test_unsorted_table_follows_the_standings(open_page, league):
    """1.3.1: wins (a tie counts half), then points scored."""
    page, _ = open_page(f"index.html#{league}", 1280)
    assert row_ids(page) == standings_order(league_data(page, league)["teams"])


@pytest.mark.parametrize("league", ["dynasty", "redraft"])
def test_projected_record_and_probabilities_are_formatted(open_page, league):
    """1.3.5 and 1.3.8"""
    page, _ = open_page(f"index.html#{league}", 1280)
    data = league_data(page, league)
    teams = {t["roster_id"]: t for t in data["teams"]}
    bottom = data["bottom_column"]["key"]
    rows = page.eval_on_selector_all("#odds-body tr", """rows => rows.map(r => ({ id: Number(r.dataset.roster),
        proj: r.querySelector('td.col-proj').textContent.trim(),
        chances: [...r.querySelectorAll('td.chance')].map(td => td.textContent.trim()) }))""")
    assert len(rows) == len(teams)
    for r in rows:
        t = teams[r["id"]]
        assert r["proj"] == f"{one_decimal(t['proj_wins'])} - {one_decimal(t['proj_losses'])}", r
        assert r["chances"] == [pct_text(t[k]) for k in (bottom, "playoffs", "bye", "title")], r


def test_header_clicks_sort_descending_then_ascending(open_page):
    """1.3.10 and 1.3.10.1"""
    page, _ = open_page("index.html#redraft", 1280)
    teams = {t["roster_id"]: t for t in league_data(page, "redraft")["teams"]}
    assert page.eval_on_selector_all("#odds-table thead th[aria-sort]", "e => e.length") == 0, "no sort state before a click"
    click_header(page, "title")
    first = [teams[i]["title"] for i in row_ids(page)]
    assert first == sorted(first, reverse=True)
    assert page.get_attribute("#odds-table thead th[data-col=title]", "aria-sort") == "descending"
    click_header(page, "title")
    second = [teams[i]["title"] for i in row_ids(page)]
    assert second == sorted(second)
    assert page.get_attribute("#odds-table thead th[data-col=title]", "aria-sort") == "ascending"
    assert page.eval_on_selector_all("#odds-table thead th[aria-sort]", "e => e.length") == 1


@pytest.mark.parametrize("col,key", [("proj", "proj_wins"), ("elo", "elo"), ("elo_change", "elo_change"), ("bye", "bye")])
def test_each_column_sorts_by_its_key(open_page, col, key):
    """1.3.10.2: highest first on the first click, unrated teams last."""
    page, _ = open_page("index.html#dynasty", 1280)
    teams = {t["roster_id"]: t for t in league_data(page, "dynasty")["teams"]}
    click_header(page, col)
    values = [teams[i][key] for i in row_ids(page)]
    rated = [v for v in values if v is not None]
    assert values[: len(rated)] == rated, f"unrated teams sort last: {values}"
    assert rated == sorted(rated, reverse=True), values


def test_manager_column_sorts_a_to_z(open_page):
    """1.3.10: the Manager column's first click is A to Z."""
    page, _ = open_page("index.html#dynasty", 1280)
    click_header(page, "owner")
    names = page.eval_on_selector_all("#odds-body td.col-owner .owner-name a, #odds-body td.col-owner .owner-name",
                                      "els => els.filter(e => e.matches('.owner-name')).map(e => e.childNodes[1]?.textContent ?? e.textContent)")
    ordered = page.evaluate("(n) => [...n].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()))", names)
    assert names == ordered


def test_picking_a_team_dims_the_other_lines(open_page):
    """1.4.4"""
    page, _ = open_page("index.html#redraft", 1280)
    first = row_ids(page)[0]
    page.click(f"#odds-body tr[data-roster='{first}']")
    page.wait_for_timeout(200)
    sets = chart_state(page, "odds-chart")["sets"]
    for s in sets:
        if s["id"] == first:
            assert s["selected"] and s["color"] == s["team"], s
        else:
            assert not s["selected"] and s["color"] != s["team"], f"line {s['id']} should be dimmed"


def test_picking_a_team_highlights_its_manager_in_both_charts(open_page):
    """4.2.4"""
    page, _ = open_page("index.html#dynasty", 1280)
    data = league_data(page, "dynasty")
    first = row_ids(page)[0]
    user = next(t["user_id"] for t in data["teams"] if t["roster_id"] == first)
    page.click(f"#odds-body tr[data-roster='{first}']")
    page.wait_for_timeout(200)
    rating = chart_state(page, "rating-chart")["sets"]
    chosen = [s for s in rating if s["selected"]]
    assert [s["manager"] for s in chosen] == [user], "the picked team's Manager is highlighted in the rating chart"
    assert all(s["color"] != s["team"] for s in rating if not s["selected"] and s["team"]), "the other Managers are dimmed"
    assert any(s["selected"] for s in chart_state(page, "odds-chart")["sets"])


def test_chart_axis_follows_the_highest_value(open_page):
    """1.4.5: 0 to the next multiple of 10 at least 5 points above the highest value, at least 10, at most 100."""
    page, _ = open_page("index.html#redraft", 1280)
    buttons = page.eval_on_selector_all("#metric-switcher button", "b => b.length")
    seen = set()
    for i in range(max(buttons, 1)):
        if buttons:
            page.locator("#metric-switcher button").nth(i).click()
            page.wait_for_timeout(150)
        state = chart_state(page, "odds-chart")
        high = max((v for s in state["sets"] for v in s["data"] if v is not None), default=0)
        assert state["max"] == min(100, max(10, math.ceil((high + 5) / 10) * 10)), (high, state["max"])
        seen.add(state["max"])
    assert len(seen) >= 2, "the metrics should give different axis tops"


def test_last_three_seasons_equals_all_time_with_a_short_history(open_page, base_url):
    """4.2.2.1: a league with two stored seasons shows the same weeks for both ranges."""
    page, _ = open_page("index.html#redraft", 1280)
    data = league_data(page, "dynasty")
    r = data["ratings"]
    keep = r["seasons"][-2:]
    idx = [i for i, w in enumerate(r["weeks"]) if w["season"] in keep]
    r["seasons"], r["weeks"] = keep, [r["weeks"][i] for i in idx]
    for m in r["managers"].values():
        for k in ("mu", "career_z"):
            m[k] = [m[k][i] for i in idx]
    page.route(f"{base_url}/data/dynasty.json*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(data)))
    page.goto("about:blank")
    page.goto(f"{base_url}/index.html#dynasty")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    counts = {}
    for label in ("All time", "Last 3 seasons"):
        page.click(f"#rating-range button:has-text('{label}')")
        page.wait_for_timeout(150)
        counts[label] = chart_state(page, "rating-chart")["labels"]
    assert counts["All time"] == counts["Last 3 seasons"], counts
