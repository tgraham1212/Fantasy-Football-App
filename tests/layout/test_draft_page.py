"""The League sub-tab's Draft tab (league-draft-page 4.9.7.x), in the browser against the published data:
the tab, its views, Season picker and URL, the board (cells, traded and keeper marks, grade switch), the
table (columns, badges, position ranks, via, sorting), the Managers card, the notes and both phone
layouts. Expectations come from the published draft file, so the checks hold as the data changes."""

from __future__ import annotations

import pytest

PHONES = (360, 390, 414, 440)
LEAGUE = "dynasty"


def draft(page, league=LEAGUE):
    return page.evaluate("async (k) => (await fetch(`data/${k}/draft.json`)).json()", league)


def open_draft(open_page, width=1280, rest="", league=LEAGUE):
    page, _ = open_page(f"index.html#{league}/league/draft{rest}", width)
    page.wait_for_function("document.querySelector('#dr-page:not([hidden]) table')")
    page.wait_for_timeout(250)
    return page


def heads(page, table):
    return page.eval_on_selector_all(f"{table} thead tr:last-child th", "ths => ths.map(t => t.textContent.trim())")


def test_draft_tab_opens(open_page):
    """4.9.7: Draft is the third League tab and opens on the board of the latest stored draft."""
    page, _ = open_page(f"index.html#{LEAGUE}/league/records", 1280)
    page.wait_for_function("document.querySelector('#lg-champions .lg-body').children.length > 0")
    tabs = page.eval_on_selector_all("#lg-tabs button", "bs => bs.map(b => b.textContent.trim())")
    assert tabs[:3] == ["Records", "Strength of Schedule", "Draft"]
    page.click("#lg-tabs [data-lg-tab=draft]")
    page.wait_for_function("document.querySelector('#dr-board table')")
    data = draft(page)
    assert page.is_visible("#dr-board") and not page.is_visible("#dr-table") and not page.is_visible("#lg-managers")
    assert page.is_visible("#dr-views") and not page.is_visible("#sos-views")
    assert page.input_value("#dr-season") == data["latest"]
    assert page.evaluate("location.hash") == f"#{LEAGUE}/league/draft/{data['latest']}"


def test_view_switch(open_page):
    """4.9.7.1: two buttons switch the board and the table and show which is pressed."""
    page = open_draft(open_page)
    page.click("#dr-views [data-dr-view=table]")
    assert page.is_visible("#dr-table") and not page.is_visible("#dr-board")
    assert page.get_attribute("#dr-views [data-dr-view=table]", "aria-pressed") == "true"
    assert page.get_attribute("#dr-views [data-dr-view=board]", "aria-pressed") == "false"
    assert not page.is_visible("#dr-grades"), "the grade switch belongs to the board (its space is kept)"


def test_season_picker(open_page):
    """4.9.7.2: every season with a stored draft, latest first and selected."""
    page = open_draft(open_page)
    data = draft(page)
    options = page.eval_on_selector_all("#dr-season option", "os => os.map(o => o.value)")
    assert options == sorted(data["seasons"], reverse=True) and options[0] == data["latest"]
    assert "2022" in options, "the dynasty rookie drafts start in 2022"
    page.select_option("#dr-season", "2023")
    page.wait_for_timeout(300)
    assert page.text_content("#dr-draft-h") == "2023 Rookie Draft"


def test_url_names_view_and_season(open_page):
    """4.9.7.3: the URL names the view and season, and a link opens them."""
    page = open_draft(open_page, rest="/table/2023", league="redraft")
    assert page.is_visible("#dr-table") and page.input_value("#dr-season") == "2023"
    assert page.text_content("#dr-draft-h") == "2023 Draft"
    page.click("#dr-views [data-dr-view=board]")
    assert page.evaluate("location.hash") == "#redraft/league/draft/2023"


def test_board_layout(open_page):
    """4.9.7.4: one row per round, one column per slot headed by its Manager; cells give pick, Player,
    position and team in the position's colours."""
    page = open_draft(open_page, rest="/2025")
    data = draft(page)
    season = data["seasons"]["2025"]
    rows = page.locator("#dr-board tbody tr").count()
    cols = page.locator("#dr-board thead th.dr-slot").count()
    assert (rows, cols) == (season["rounds"], len(season["slots"]))
    first = next(p for p in season["picks"] if p["no"] == 1)
    cell = page.locator("#dr-board .dr-cell[data-pick='1']")
    text = cell.inner_text()
    assert first["label"] in text and first["player"]["pos"] in text and first["player"]["team"] in text
    assert first["player"]["last"] in cell.get_attribute("title")
    assert first["player"]["pos"].lower() in cell.get_attribute("class")
    header = page.locator("#dr-board thead th.dr-slot").nth(first["slot"] - 1).inner_text()
    assert data["managers"][season["slots"][first["slot"] - 1]["user"]]["name"] in header
    # nothing in a cell is cut off
    clipped = page.evaluate("""() => [...document.querySelectorAll('#dr-board .dr-cell *')]
        .filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible').length""")
    assert clipped == 0


def test_board_traded_and_keeper_marks(open_page):
    """4.9.7.4.1: a traded pick names the Manager who made it; a keeper reads Keeper."""
    page = open_draft(open_page, rest="/2025")
    data = draft(page)
    traded = next(p for p in data["seasons"]["2025"]["picks"] if p["user"] != p["slot_user"])
    by = page.locator(f"#dr-board .dr-cell[data-pick='{traded['no']}'] .dr-by")
    assert by.count() == 1 and data["managers"][traded["user"]]["name"] in by.inner_text()
    page = open_draft(open_page, rest="/2022", league="redraft")
    keeper = next(p for p in draft(page, "redraft")["seasons"]["2022"]["picks"] if p["keeper"])
    assert "Keeper" in page.locator(f"#dr-board .dr-cell[data-pick='{keeper['no']}']").inner_text()


def test_grade_switch(open_page):
    """4.9.7.4.2: Draft Day shows Steal/Reach badges, Results shows Hit, Bust and Unlucky badges."""
    page = open_draft(open_page, rest="/2025")
    picks = draft(page)["seasons"]["2025"]["picks"]
    day = page.locator("#dr-board .dr-badge.steal, #dr-board .dr-badge.reach").count()
    assert day == sum(1 for p in picks if p["steal_reach"]) and page.locator("#dr-board .dr-badge.hit").count() == 0
    page.click("#dr-grades [data-dr-grade=results]")
    page.wait_for_timeout(300)
    assert page.locator("#dr-board .dr-badge.steal, #dr-board .dr-badge.reach").count() == 0
    for kind in ("hit", "bust", "unlucky"):
        assert page.locator(f"#dr-board .dr-badge.{kind}").count() == sum(1 for p in picks if p["hit_bust"] == kind)
    assert page.get_attribute("#dr-grades [data-dr-grade=results]", "aria-pressed") == "true"


def test_table_columns(open_page):
    """4.9.7.5: the table's columns, and the Pick cell with the overall number."""
    page = open_draft(open_page, rest="/table/2025")
    assert heads(page, "#dr-table .dr-wide") == ["Pick", "Manager", "Player", "ADP", "ADP Rank", "WAR", "WAR Rank", "Slot WAR", "Hit/Bust", "Games Played"]
    first_cells = page.eval_on_selector_all("#dr-table .dr-wide tbody tr:nth-child(13) td", "tds => tds.map(t => t.innerText.trim())")
    assert first_cells[0].replace("\n", " ") == "2.01 (13)"


def test_player_column_badge(open_page):
    """4.9.7.5.1: the Player column ends with the Steal or Reach badge."""
    page = open_draft(open_page, rest="/table/2025")
    picks = draft(page)["seasons"]["2025"]["picks"]
    graded = [p for p in picks if p["steal_reach"]]
    assert graded, "the 2025 draft has steals or reaches"
    p = graded[0]
    last = page.locator(f"#dr-table .dr-wide tbody tr:nth-child({p['no']}) td:nth-child(3) .dr-player > :last-child")
    assert ("Steal" if p["steal_reach"] == "steal" else "Reach") in last.inner_text()


def test_position_rank_badges(open_page):
    """4.9.7.5.2: ADP Rank and WAR Rank give the position rank as a badge after the overall rank."""
    page = open_draft(open_page, rest="/table/2025")
    p = next(p for p in draft(page)["seasons"]["2025"]["picks"] if p["adp_rank"])
    row = page.locator(f"#dr-table .dr-wide tbody tr:nth-child({p['no']})")
    adp = row.locator("td:nth-child(5)")
    assert adp.inner_text().split() == [str(p["adp_rank"]), f"{p['player']['pos']}{p['adp_pos_rank']}"]
    assert p["player"]["pos"].lower() in adp.locator(".mgr-pill").get_attribute("class")
    assert row.locator("td:nth-child(7)").inner_text().split() == [str(p["war_rank"]), f"{p['player']['pos']}{p['war_pos_rank']}"]


def test_table_via(open_page):
    """4.9.7.5.3: a traded pick shows 'via' and the slot's original Manager."""
    page = open_draft(open_page, rest="/table/2025")
    data = draft(page)
    p = next(p for p in data["seasons"]["2025"]["picks"] if p["user"] != p["slot_user"])
    cell = page.locator(f"#dr-table .dr-wide tbody tr:nth-child({p['no']}) td:nth-child(2)").inner_text()
    assert data["managers"][p["user"]]["name"] in cell and f"via {data['managers'][p['slot_user']]['name']}" in cell


def test_table_sorting(open_page):
    """4.9.7.5.4: headers sort the table; Pick ascending on opening, WAR highest first."""
    page = open_draft(open_page, rest="/table/2025")
    assert page.get_attribute("#dr-table thead th[data-col=no]", "aria-sort") == "ascending"
    page.click("#dr-table thead [data-col=war] button.sort")
    page.wait_for_timeout(200)
    wars = page.eval_on_selector_all("#dr-table .dr-wide tbody tr td:nth-child(6)", "tds => tds.map(t => parseFloat(t.innerText.replace('−', '-')))")
    assert wars == sorted(wars, reverse=True)


def test_managers_card(open_page):
    """4.9.7.7: the Managers summary, sorted by mean WAR above slot WAR, for this draft or all drafts."""
    page = open_draft(open_page, rest="/2025")
    data = draft(page)
    names = page.eval_on_selector_all("#dr-managers .dr-mgr-table tbody tr td:first-child a.manager-link", "as => as.map(a => a.textContent.trim())")
    assert names == [data["managers"][r["user"]]["name"] for r in data["seasons"]["2025"]["summary"]]
    page.click("#dr-span [data-dr-span=all]")
    page.wait_for_timeout(300)
    names = page.eval_on_selector_all("#dr-managers .dr-mgr-table tbody tr td:first-child a.manager-link", "as => as.map(a => a.textContent.trim())")
    assert names == [data["managers"][r["user"]]["name"] for r in data["all_drafts"]]


def test_measures_note(open_page):
    """4.9.7.8: the note explains the grades with the league's thresholds."""
    page = open_draft(open_page, rest="/2025", league="redraft")
    note = page.text_content("#dr-note-redraft")
    assert page.is_visible("#dr-note-redraft") and not page.is_visible("#dr-note-rookie")
    assert "a full round (12 picks)" in note and "0.75 WAR" in note and "Unlucky" in note
    page = open_draft(open_page, rest="/2025")
    assert page.is_visible("#dr-note-rookie") and "half a round (6 picks)" in page.text_content("#dr-note-rookie")


@pytest.mark.parametrize("width", PHONES)
def test_phone_board_pinned_round_column(open_page, width):
    """4.9.7.4.3: on phones the board scrolls inside its card with the round column pinned."""
    page = open_draft(open_page, width, rest="/2025")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    before = page.eval_on_selector("#dr-board tbody tr th.dr-rd", "e => e.getBoundingClientRect().left")
    page.eval_on_selector("#dr-board", "e => { e.scrollLeft = 400; }")
    page.wait_for_timeout(150)
    after = page.eval_on_selector("#dr-board tbody tr th.dr-rd", "e => e.getBoundingClientRect().left")
    assert abs(after - before) <= 18, "the round labels stay in view"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


@pytest.mark.parametrize("width", PHONES)
def test_phone_table_rows(open_page, width):
    """4.9.7.5.5: on phones the table is one list row per pick, nothing cut off."""
    page = open_draft(open_page, width, rest="/table/2025")
    picks = draft(page)["seasons"]["2025"]["picks"]
    assert not page.is_visible("#dr-table .dr-wide") and page.is_visible("#dr-table .dr-list")
    assert page.locator("#dr-table .dr-list li").count() == len(picks)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    wide = page.evaluate("""() => [...document.querySelectorAll('#dr-table .dr-list li')]
        .filter(li => li.scrollWidth > li.clientWidth + 1).length""")
    assert wide == 0


def keepers_of(data):
    season = data["latest"]
    return season, data["seasons"][season]["keepers"]


def test_keeper_matrix(open_page):
    """4.9.7.9: below the latest redraft draft, Managers by price round with each eligible Player."""
    page = open_draft(open_page, league="redraft")
    data = draft(page, "redraft")
    season, ke = keepers_of(data)
    assert page.is_visible("#dr-keepers") and page.text_content("#dr-keepers-h") == f"Keeper Eligible for {ke['for_season']}"
    assert page.is_visible("#dr-keepers-provisional") == (not ke["final"])
    rows = page.locator("#dr-keepers .dr-ke-matrix tbody tr")
    assert rows.count() == len(ke["rows"])
    row = next(r for r in ke["rows"] if r["players"])
    i = ke["rows"].index(row)
    pl = row["players"][0]
    cell = rows.nth(i).locator("td").nth(pl["price_round"] - 1)
    assert pl["player"]["last"] in cell.inner_text() or pl["player"]["last"] in (cell.locator(".dr-ke-chip").first.get_attribute("title") or "")
    # an older season has no matrix, nor does the dynasty league
    page.select_option("#dr-season", sorted(data["seasons"])[0])
    page.wait_for_timeout(300)
    assert not page.is_visible("#dr-keepers")
    page = open_draft(open_page)
    assert not page.is_visible("#dr-keepers")


@pytest.mark.parametrize("width", PHONES)
def test_keeper_matrix_on_phones(open_page, width):
    """4.9.7.9.1: on phones, one list per Manager with price rounds; no sideways page scroll."""
    page = open_draft(open_page, width, league="redraft")
    _, ke = keepers_of(draft(page, "redraft"))
    assert not page.is_visible("#dr-keepers .dr-ke-table") and page.is_visible("#dr-keepers .dr-ke-list")
    assert page.locator("#dr-keepers .dr-ke-list li").count() == len(ke["rows"])
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
