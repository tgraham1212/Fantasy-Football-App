"""Behaviour of the Player WAR sub-tab (war-leaderboard-page 3.2.x), checked in the browser against the
published WAR files: the season control and cut note, the leaderboards, the All-Time modes, the Manager
cell, the expanded list and its sorting, and the worked example."""

from __future__ import annotations

POSITIONS = ["QB", "RB", "WR", "TE", "DEF", "K"]
LABELS = {"QB": "Quarterbacks", "RB": "Running backs", "WR": "Wide receivers", "TE": "Tight ends", "DEF": "Defenses", "K": "Kickers"}
QB_STATS = ["Pass yds", "Pass TD", "INT", "Rush yds", "Rush TD"]


def open_war(open_page, league: str = "redraft", width: int = 1280):
    page, _ = open_page(f"index.html#{league}/war", width)
    page.wait_for_selector("#war-grid .war-table")
    return page


def fetch(page, path):
    return page.evaluate("async (p) => (await fetch(p)).json()", path)


def season_file(page, league: str, season: str) -> dict:
    index = fetch(page, f"data/{league}/war/index.json")
    entry = next(s for s in index["seasons"] if s["season"] == season)
    return fetch(page, f"data/{league}/war/{entry['file']}")


def by_war(rows):
    return sorted(rows, key=lambda r: (-r["war"], -r["points"], r["name"]))


def test_season_control_and_cut_note(open_page):
    """3.2.1, 3.2.1.1 and 3.2.1.2"""
    page = open_war(open_page)
    index = fetch(page, "data/redraft/war/index.json")
    assert page.eval_on_selector("#war-season", "s => s.value") == index["current"]
    values = page.eval_on_selector_all("#war-season option", "o => o.map(x => x.value)")
    assert values == [s["season"] for s in reversed(index["seasons"])] + ["all"]
    current = next(s for s in index["seasons"] if s["season"] == index["current"])
    label = page.eval_on_selector("#war-season", "s => s.options[s.selectedIndex].textContent")
    if current["through_week"] < 14:
        assert label == f"{current['season']} (through week {current['through_week']})"
    note = page.inner_text("#war-note")
    if current["cut"] == "merged":
        assert "merged replacement cut" in note
    yearly = next(s for s in index["seasons"] if s["cut"] == "yearly")
    page.select_option("#war-season", yearly["season"])
    page.wait_for_timeout(300)
    assert "yearly replacement cut" in page.inner_text("#war-note")


def test_leaderboards_show_the_top_ten_per_position(open_page):
    """3.2.2"""
    page = open_war(open_page)
    data = season_file(page, "redraft", page.eval_on_selector("#war-season", "s => s.value"))
    heads = page.eval_on_selector_all("#war-grid .war-table h3", "h => h.map(x => x.textContent)")
    present = [p for p in POSITIONS if any(pl["position"] == p for pl in data["players"])]
    assert heads == [LABELS[p] for p in present]
    for pos, table in zip(present, page.locator("#war-grid .war-table").all()):
        names = table.locator("tbody td.name").all_text_contents()
        assert names == [r["name"] for r in by_war([p for p in data["players"] if p["position"] == pos])][:10], pos
        assert table.locator("thead th").all_text_contents() == ["#", "Name", "NFL", "Manager", "WAR"]


def test_all_time_modes(open_page):
    """3.2.3 and 3.2.3.1: Seasons (with a year column) by default, Career (one row per player, seasons played)."""
    page = open_war(open_page)
    page.select_option("#war-season", "all")
    page.wait_for_timeout(500)
    assert page.is_visible("#war-mode")
    assert page.get_attribute("#war-mode button[data-mode='seasons']", "aria-pressed") == "true"
    assert "Year" in page.locator("#war-grid .war-table").first.locator("thead th").all_text_contents()
    page.click("#war-mode button[data-mode='career']")
    page.wait_for_timeout(300)
    first = page.locator("#war-grid .war-table").first
    assert "Szns" in first.locator("thead th").all_text_contents()
    page.click("#war-grid .war-table .expand")
    page.wait_for_timeout(300)
    names = page.locator("#war-full tbody td.name").all_text_contents()
    assert len(names) == len(set(names)), "Career lists each player once"


def test_manager_cell_lists_other_holders_and_dashes_the_unrostered(open_page):
    """3.2.4.1 and 3.2.4.2"""
    page = open_war(open_page)
    data = season_file(page, "redraft", page.eval_on_selector("#war-season", "s => s.value"))
    page.click("#war-grid .war-table .expand")  # the quarterback list
    page.wait_for_timeout(300)
    qbs = {r["name"]: r for r in data["players"] if r["position"] == "QB"}
    rows = page.locator("#war-full tbody tr").evaluate_all("""rs => rs.map(r => ({ name: r.querySelector('td.name').textContent,
        owner: r.querySelector('td.war-owner').textContent.trim(), title: r.querySelector('td.war-owner span[title]')?.title || '' }))""")
    checked = 0
    for r in rows:
        p = qbs[r["name"]]
        if not p["owner"]:
            assert r["owner"] == "—", r
        elif p.get("others"):
            assert r["title"] == "Also held by: " + ", ".join(p["others"]), r
            checked += 1
    assert any(not p["owner"] for p in qbs.values()) or checked, "the list should show a dash or another holder"


def test_expanded_list_lists_every_player_with_the_position_columns(open_page):
    """3.2.5 and 3.2.6: every player at the position, most WAR first, with the stat columns; closing keeps the season."""
    page = open_war(open_page)
    season = page.eval_on_selector("#war-season", "s => s.value")
    data = season_file(page, "redraft", season)
    page.click("#war-grid .war-table .expand")
    page.wait_for_timeout(300)
    names = page.locator("#war-full tbody td.name").all_text_contents()
    assert names == [r["name"] for r in by_war([p for p in data["players"] if p["position"] == "QB"])]
    heads = page.locator("#war-full thead th").all_text_contents()
    assert heads == ["#", "Name", "NFL", "Manager", "GP", "PS", *QB_STATS, "WAR"]
    page.click("#war-dialog-close")
    page.wait_for_timeout(200)
    assert not page.evaluate("document.getElementById('war-dialog').open")
    assert page.eval_on_selector("#war-season", "s => s.value") == season


def test_expanded_list_sorts_from_its_headers(open_page):
    """3.2.7"""
    page = open_war(open_page)
    page.click("#war-grid .war-table .expand")
    page.wait_for_timeout(300)
    assert page.locator("#war-full thead th[aria-sort]").count() == 0
    ps = page.locator("#war-full thead th[data-col='points']")
    points = lambda: [float(x) for x in page.locator("#war-full tbody tr td:nth-child(6)").all_text_contents()]
    ps.locator("button").click()
    page.wait_for_timeout(150)
    assert points() == sorted(points(), reverse=True) and ps.get_attribute("aria-sort") == "descending"
    ps.locator("button").click()
    page.wait_for_timeout(150)
    assert points() == sorted(points()) and ps.get_attribute("aria-sort") == "ascending"


def test_worked_example_uses_the_leagues_2024_weeks(open_page):
    """3.2.8.1: Kittle and Bowers in 2024, Bye or Out for missed weeks, totals from the league's file."""
    page = open_war(open_page)
    wt = season_file(page, "redraft", "2024")["walkthrough"]
    page.wait_for_selector("#war-walkthrough table")
    rows = page.locator("#war-walkthrough tbody tr")
    assert rows.count() == len(wt["4217"]["weekly"])
    for i, w in enumerate(wt["4217"]["weekly"]):
        cells = rows.nth(i).locator("td").all_text_contents()
        if w["played"]:
            assert cells[0] == f"{w['score']:.1f}", (i, cells)
        else:
            assert cells[0] in ("Bye", "Out"), (i, cells)
    total = page.locator("#war-walkthrough tfoot tr.total td").all_text_contents()
    fmt = lambda v: ("+" if v >= 0 else "") + f"{v:.2f}"
    assert total == [fmt(wt["4217"]["war"]), fmt(wt["11604"]["war"])]
