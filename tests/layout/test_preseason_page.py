"""The League sub-tab's Preseason tab (preseason-page 4.9.8.x), in the browser against the published data:
the tab, Season picker and URL, the table with share bars, sorting and the redraft Draft Strength column,
the grade key and note, and the phone rows. Expectations come from the published preseason file."""

from __future__ import annotations

import pytest

PHONES = (360, 390, 414, 440)
LEAGUE = "dynasty"


def preseason(page, league=LEAGUE):
    return page.evaluate("async (k) => (await fetch(`data/${k}/preseason.json`)).json()", league)


def open_ps(open_page, width=1280, rest="", league=LEAGUE):
    page, _ = open_page(f"index.html#{league}/league/preseason{rest}", width)
    page.wait_for_function("document.querySelector('#ps-page:not([hidden]) .ps-list li')")
    page.wait_for_timeout(250)
    return page


def heads(page):
    return page.eval_on_selector_all("#ps-card .ps-wide thead th", "ths => ths.map(t => t.textContent.trim())")


def test_preseason_tab_opens(open_page):
    """4.9.8: Preseason is the fourth League tab and opens on the latest season."""
    page, _ = open_page(f"index.html#{LEAGUE}/league/records", 1280)
    page.wait_for_function("document.querySelector('#lg-champions .lg-body').children.length > 0")
    tabs = page.eval_on_selector_all("#lg-tabs button", "bs => bs.map(b => b.textContent.trim())")
    assert tabs == ["Records", "Strength of Schedule", "Draft", "Preseason"]
    page.click("#lg-tabs [data-lg-tab=preseason]")
    page.wait_for_function("document.querySelector('#ps-card table')")
    data = preseason(page)
    assert page.is_visible("#ps-card") and not page.is_visible("#dr-page") and page.is_visible("#ps-season")
    assert page.text_content("#ps-h") == f"{data['latest']} Preseason Forecast"
    assert page.evaluate("location.hash") == f"#{LEAGUE}/league/preseason/{data['latest']}"


def test_season_picker(open_page):
    """4.9.8.1: every season with a Forecast, latest first and selected."""
    page = open_ps(open_page, league="redraft")
    data = preseason(page, "redraft")
    options = page.eval_on_selector_all("#ps-season option", "os => os.map(o => o.value)")
    assert options == sorted(data["seasons"], reverse=True) and options[0] == data["latest"] and "2021" in options


def test_url_names_the_season(open_page):
    """4.9.8.2: a link names the season and opens it."""
    page = open_ps(open_page, rest="/2023")
    assert page.input_value("#ps-season") == "2023" and page.text_content("#ps-h") == "2023 Preseason Forecast"


def test_table_columns_and_order(open_page):
    """4.9.8.3: the columns, ordered by title share; a finished season shows each final place."""
    page = open_ps(open_page, rest="/2025")
    assert heads(page) == ["Grade", "Manager", "Title", "Playoffs", "Last", "Forecast", "Pts/Wk", "Wins Saved", "Finished"]
    data = preseason(page)["seasons"]["2025"]
    top = max(data["teams"], key=lambda t: t["title"])
    first = page.locator("#ps-card .ps-wide tbody tr").first
    assert top["grade"] in first.locator("td").first.inner_text()
    finishes = page.eval_on_selector_all("#ps-card .ps-wide tbody td.ps-finish b", "bs => bs.map(b => b.textContent)")
    assert len(finishes) == len(data["teams"]) and "1st" in finishes


def test_share_bars(open_page):
    """4.9.8.3.1: each share's bar is that share of its track, within 1 px."""
    page = open_ps(open_page, rest="/2025")
    ratios = page.evaluate("""() => [...document.querySelectorAll('#ps-card .ps-wide .ps-share')].map(s => {
        const pct = parseFloat(s.querySelector('.ps-num').textContent) || 0;
        const track = s.querySelector('.ps-track').getBoundingClientRect().width;
        const fill = s.querySelector('.ps-fill').getBoundingClientRect().width;
        return [pct, track, fill];
    })""")
    for pct, track, fill in ratios:
        assert abs(fill - track * pct / 100) <= 1 + track * 0.005, (pct, track, fill)


def test_table_sorting(open_page):
    """4.9.8.3.2: headers sort; Wins Saved highest first."""
    page = open_ps(open_page, rest="/2025")
    page.click("#ps-card thead [data-col=saved] button.sort")
    page.wait_for_timeout(200)
    saved = page.eval_on_selector_all("#ps-card .ps-wide tbody td.ps-saved", "tds => tds.map(t => parseFloat(t.textContent.replace('−', '-')))")
    assert saved == sorted(saved, reverse=True)


def test_draft_strength_column(open_page):
    """4.9.8.3.4: redraft adds Draft Strength (1st to 12th) after Pts/Wk; dynasty has none."""
    page = open_ps(open_page, rest="/2025", league="redraft")
    h = heads(page)
    assert h[h.index("Pts/Wk") + 1] == "Draft Strength" and page.is_visible("#ps-redraft-note")
    page.click("#ps-card thead [data-col=strength] button.sort")
    page.wait_for_timeout(200)
    col = h.index("Draft Strength") + 1
    ranks = page.eval_on_selector_all(f"#ps-card .ps-wide tbody td:nth-child({col})", "tds => tds.map(t => parseInt(t.textContent))")
    assert ranks[0] == 1 and sorted(ranks) == ranks and max(ranks) <= 12
    page = open_ps(open_page, rest="/2025")
    assert "Draft Strength" not in heads(page) and not page.is_visible("#ps-redraft-note")


def test_key_and_note(open_page):
    """4.9.8.5: the grade key with each letter's band, and the method note."""
    page = open_ps(open_page)
    key = page.inner_text("#ps-key")
    for label in ("Title Contender", "Playoff Team", "Playoff Bubble", "Unlikely Playoffs", "Last Place"):
        assert label in key
    assert "10,000" in page.inner_text("#ps-card")


@pytest.mark.parametrize("width", PHONES)
def test_phone_rows(open_page, width):
    """4.9.8.3.3: on phones one list row per team, nothing cut off, no sideways scroll."""
    page = open_ps(open_page, width, rest="/2025")
    data = preseason(page)["seasons"]["2025"]
    assert not page.is_visible("#ps-card .ps-wide") and page.locator("#ps-card .ps-list li").count() == len(data["teams"])
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("[...document.querySelectorAll('#ps-card .ps-list li')].filter(li => li.scrollWidth > li.clientWidth + 1).length") == 0
