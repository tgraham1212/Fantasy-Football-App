"""The League sub-tab's Records page (league-records-page 4.9.x), in the browser against the published data:
the tab and its URL, the Managers and Players views, each table, the luck explanation, the record pop-up
and phone sheet, game tags, pictures and the phone lists."""

from __future__ import annotations

import re

import pytest

PHONES = (360, 390, 414, 440)
# the page order (the JSON file sorts its keys)
WEEKLY = ("high_team", "low_team", "high_matchup", "low_matchup", "blowout", "closest", "high_loss", "low_win")
SEASON = ("most_points", "fewest_points", "most_against", "best_record", "worst_record", "best_missed", "worst_made",
          "luckiest", "unluckiest", "win_streak", "loss_streak", "bench", "lineup_gained", "lineup_lost")


def records(page, league):
    return page.evaluate("async (k) => (await fetch(`data/${k}/records.json`)).json()", league)


def open_league(open_page, league="redraft", width=1280, view=""):
    page, _ = open_page(f"index.html#{league}/league/records{view}", width)
    page.wait_for_function("document.querySelector('#lg-champions .lg-body').children.length > 0")
    return page


def sideways(page):
    return page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")


def test_league_tab_opens_on_records(open_page):
    """4.9 and league-odds-site 9.1.1: League is the sixth sub-tab and opens on Records, Managers view."""
    page, _ = open_page("index.html#redraft", 1280)
    tabs = page.eval_on_selector_all("#subtabs button", "bs => bs.map(b => b.textContent.trim())")
    assert tabs == ["Forecasts", "Games", "Positions", "Managers", "Player WAR", "League"]
    page.click("#subtabs [data-page=league]")
    page.wait_for_timeout(200)
    assert page.is_visible("#page-league") and page.is_visible("#lg-managers") and not page.is_visible("#lg-players")
    assert page.get_attribute("#lg-tabs [data-lg-tab=records]", "aria-pressed") == "true"
    assert page.get_attribute("#lg-views [data-lg-view=managers]", "aria-pressed") == "true"
    assert page.evaluate("location.hash") == "#redraft/league/records"


def test_url_names_the_tab_and_view(open_page):
    """4.9.1: the URL names the tab and view; a link opens them; switching league keeps them."""
    page = open_league(open_page, view="/players")
    assert page.is_visible("#lg-players") and page.get_attribute("#lg-views [data-lg-view=players]", "aria-pressed") == "true"
    page.click("#league-switcher button:has-text('Taco Tuesdays')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)
    assert page.evaluate("location.hash") == "#dynasty/league/records/players" and page.is_visible("#lg-players")
    page.click("#lg-views [data-lg-view=managers]")
    assert page.evaluate("location.hash") == "#dynasty/league/records"


def test_view_switch(open_page):
    """4.9.2: two buttons switch the views and show which is pressed."""
    page = open_league(open_page)
    page.click("#lg-views [data-lg-view=players]")
    assert page.is_visible("#lg-players") and not page.is_visible("#lg-managers")
    assert page.get_attribute("#lg-views [data-lg-view=players]", "aria-pressed") == "true"
    assert page.get_attribute("#lg-views [data-lg-view=managers]", "aria-pressed") == "false"


def test_managers_view_sections(open_page):
    """4.9.2.1: Champions, All-Time Standings, Weekly Records, Season Records."""
    page = open_league(open_page)
    heads = page.eval_on_selector_all("#lg-managers > section > h2", "hs => hs.map(h => h.textContent.trim())")
    assert heads == ["Champions", "All-Time Standings", "Weekly Records", "Season Records"]


@pytest.mark.parametrize("league,last", [("redraft", "Toilet Bowl Champion"), ("dynasty", "Last Place")])
def test_champions_table(open_page, league, last):
    """4.9.2.1.1: finished seasons newest first, the champion's Team Name, the last column's name, best Player."""
    page = open_league(open_page, league)
    data = records(page, league)
    heads = page.eval_on_selector_all("#lg-champions .lg-wide thead th", "ths => ths.map(t => t.textContent.trim())")
    assert heads == ["Year", "Champion", "Runner-up", last, "Record", "Points Scored", "Best Player"]
    rows = page.eval_on_selector_all("#lg-champions .lg-wide tbody tr", """rs => rs.map(r => ({ year: r.cells[0].textContent.trim(),
        champ: r.cells[1].textContent, best: r.cells[6].textContent }))""")
    assert [r["year"] for r in rows] == [c["season"] for c in data["champions"]] == sorted((c["season"] for c in data["champions"]), reverse=True)
    for r, c in zip(rows, data["champions"]):
        assert data["managers"][c["champion"]]["name"] in r["champ"] and (c["team_name"] or "") in r["champ"]
        if c["best_player"]:
            assert f'{c["best_player"]["war"]:.1f} WAR' in r["best"]


@pytest.mark.parametrize("league", ["redraft", "dynasty"])
def test_standings_table(open_page, league):
    """4.9.2.1.2 and 4.9.2.1.2.1: win % as .700, current Managers ranked, former ones grouped without a rank."""
    page = open_league(open_page, league)
    data = records(page, league)
    rows = page.eval_on_selector_all("#lg-standings .lg-wide tbody tr:not(.lg-group)", """rs => rs.map(r => ({ rank: r.cells[0].textContent.trim(),
        pct: r.cells[3].textContent.trim(), former: r.classList.contains('former') }))""")
    assert len(rows) == len(data["standings"])
    assert all(re.fullmatch(r"\.\d{3}|1\.000", r["pct"]) for r in rows), rows
    former = [r for r in rows if r["former"]]
    assert all(r["rank"] == "" for r in former) and all(r["rank"] for r in rows if not r["former"])
    has_group = page.locator("#lg-standings .lg-wide tr.lg-group").count() == 1
    assert has_group == bool(former), "a Former Managers heading only when there are former Managers"


@pytest.mark.parametrize("league", ["redraft", "dynasty"])
def test_record_rows(open_page, league):
    """4.9.2.1.3, 4.9.2.1.3.2 and 4.9.2.1.3.3: one row per league record with its first entry, tags, results
    and the current-season marker."""
    page = open_league(open_page, league)
    data = records(page, league)
    weekly = page.eval_on_selector_all("#lg-weekly .lg-wide tbody tr", "rs => rs.map(r => ({ value: r.cells[1].querySelector('.lg-value').textContent, when: r.cells[4].textContent }))")
    firsts = [data["weekly"][k][0] for k in WEEKLY if data["weekly"][k]]
    assert len(weekly) == 8 == len(firsts)
    for row, e in zip(weekly, firsts):
        assert row["value"] == f'{e["value"]:,.2f}'
        assert ("This season" in row["when"]) == bool(e["current"])
        if e["kind"] != "regular":
            assert e["kind"] in row["when"]
    season = page.eval_on_selector_all("#lg-season .lg-wide tbody tr", "rs => rs.map(r => ({ year: r.cells[2].textContent.trim(), result: r.cells[4].textContent.trim() }))")
    seasons_first = [data["season"][k][0] for k in SEASON if data["season"][k]]
    assert len(season) == len(seasons_first) == 14
    labels = {"first": "1st", "second": "2nd", "third": "3rd", "playoffs": "Playoffs", "missed": "Missed Playoffs",
              "toilet_bowl": "Toilet Bowl Champ", "last": "Last", "in_progress": "In progress"}
    for row, e in zip(season, seasons_first):
        assert row["result"] == labels[e["result"]] and row["year"] == e["season"] + ("*" if e["current"] else "")
    assert page.is_visible("#lg-season .lg-star") == any(e["current"] for e in seasons_first)


def test_luck_explained(open_page):
    """4.9.2.1.3.1: on hover and focus, and at the top of the luck pop-ups only."""
    page = open_league(open_page)
    note = page.text_content("#lg-dialog-note").strip()
    assert note.startswith("Each week your score plays all 11 other teams")
    tips = page.locator("#lg-season .lg-wide .lg-tip")
    assert tips.count() == 2 and tips.first.get_attribute("title") == note and tips.first.get_attribute("tabindex") == "0"
    page.click("#lg-season .lg-wide [data-record='season:luckiest'] .lg-more")
    assert page.is_visible("#lg-dialog-note")
    page.click("#lg-dialog-close")
    page.click("#lg-season .lg-wide [data-record='season:most_points'] .lg-more")
    assert not page.is_visible("#lg-dialog-note")


@pytest.mark.parametrize("width", [1280, 360])
def test_record_popup(open_page, width):
    """4.9.3 and 4.9.3.1: the top 25 with gold, silver and bronze ranks; a bottom sheet with a 48 px close
    button on phones; focus returns to the record on close."""
    page = open_league(open_page, width=width)
    data = records(page, "redraft")
    opener = "#lg-weekly .lg-wide [data-record='weekly:blowout'] .lg-more" if width > 600 else "#lg-weekly .lg-narrow [data-record='weekly:blowout']"
    page.click(opener)
    page.wait_for_timeout(200)
    assert page.evaluate("document.getElementById('lg-dialog').open")
    part = ".lg-wide tbody tr" if width > 600 else ".lg-narrow .lg-item"
    assert page.locator(f"#lg-dialog-body {part}").count() == len(data["weekly"]["blowout"]) == 25
    ranks = page.eval_on_selector_all(f"#lg-dialog-body {part} .lg-rank", "rs => rs.slice(0, 3).map(r => r.className)")
    assert ranks == ["lg-rank r1", "lg-rank r2", "lg-rank r3"]
    assert page.text_content("#lg-dialog-title") == "Biggest Blowout"
    if width <= 600:
        box = page.locator("#lg-dialog").bounding_box()
        close = page.locator("#lg-dialog-close").bounding_box()
        assert abs(box["y"] + box["height"] - page.viewport_size["height"]) <= 2, "a sheet from the bottom of the screen"
        assert close["width"] >= 48 and close["height"] >= 48
    page.click("#lg-dialog-close")
    assert not page.evaluate("document.getElementById('lg-dialog').open")
    assert page.evaluate("document.activeElement.dataset.record") == "weekly:blowout", "focus returns to the record"


def test_players_view(open_page):
    """4.9.2.2 and 4.9.2.2.1: four cards, top 5 each, position filters in order, styled as badges."""
    page = open_league(open_page, view="/players")
    data = records(page, "redraft")
    cards = page.eval_on_selector_all("#lg-players > section", "ss => ss.map(s => s.dataset.card)")
    assert cards == ["best_games", "bench_games", "career", "championships"]
    order = page.eval_on_selector_all("#lg-players [data-card=best_games] .lg-pos-btn", "bs => bs.map(b => b.textContent.trim())")
    assert order == ["All", "QB", "RB", "WR", "TE", "DEF", "K"]
    for card in cards:
        assert page.locator(f"#lg-players [data-card={card}] .lg-wide tbody tr").count() == min(5, len(data["players"][card]["ALL"]))
    page.click("#lg-players [data-card=best_games] [data-lg-pos=QB]")
    pos = page.eval_on_selector_all("#lg-players [data-card=best_games] .lg-wide tbody .lg-pos", "ps => ps.map(p => p.textContent)")
    assert pos and set(pos) == {"QB"}
    assert page.get_attribute("#lg-players [data-card=best_games] [data-lg-pos=QB]", "aria-pressed") == "true"
    radius = page.eval_on_selector("#lg-players [data-card=best_games] [data-lg-pos=RB]", "b => getComputedStyle(b).borderRadius")
    assert radius == "6px", "rectangular, like the roster position badges"


@pytest.mark.parametrize("league", ("redraft", "dynasty"))
@pytest.mark.parametrize("spacing", (0, 1.5))
@pytest.mark.parametrize("width", (768, 1000, 1100, 1280))
def test_player_tables_cut_nothing(open_page, width, spacing, league):
    """4.9.2.2 and the name standard: every cell's content fits its column (a cut cell drew a stray dot), and a
    name too wide for the full form shows the short form rather than being cut. The wider spacing stands in
    for Linux fonts, which run wider than Windows ones."""
    page = open_league(open_page, league=league, width=width, view="/players")
    if spacing:
        page.add_style_tag(content=f"body {{ letter-spacing: {spacing}px; }}")
        page.evaluate("dispatchEvent(new Event('resize'))")
    page.wait_for_timeout(300)
    cut = page.evaluate("""() => [...document.querySelectorAll('#lg-players .lg-wide tbody td')]
      .filter(td => td.scrollWidth > td.clientWidth + 1).map(td => td.textContent.trim())""")
    assert cut == []
    names = page.evaluate("""() => [...document.querySelectorAll('#lg-players .lg-wide .fitname')].map(el => {
      const r = document.createRange(); r.selectNodeContents(el);
      return r.getBoundingClientRect().width <= el.getBoundingClientRect().width + 0.5 || el.classList.contains('fit-wrap'); })""")
    assert names and all(names)


def test_pictures_with_names(open_page):
    """4.9.4: a Manager's team logo, else Sleeper avatar; a Player's photo and position badge."""
    page = open_league(open_page)
    data = records(page, "redraft")
    champ = data["champions"][0]
    m = data["managers"][champ["champion"]]
    src = page.get_attribute("#lg-champions .lg-wide tbody tr:first-child .lg-champ img", "src")
    assert src == (m["logo"] or f"https://sleepercdn.com/avatars/thumbs/{m['avatar']}")
    if champ["best_player"]:
        head = page.get_attribute("#lg-champions .lg-wide tbody tr:first-child .mgr-head img", "src")
        assert champ["best_player"]["player_id"] in head
        assert page.locator("#lg-champions .lg-wide tbody tr:first-child .lg-pos").count() == 1


@pytest.mark.parametrize("width", PHONES)
def test_phone_lists(open_page, width):
    """4.9.5: lists on phones, no sideways scroll, no score lines."""
    page = open_league(open_page, width=width)
    assert not page.is_visible("#lg-weekly .lg-wide") and page.is_visible("#lg-weekly .lg-narrow")
    assert not sideways(page)
    text = page.text_content("#lg-weekly .lg-narrow")
    assert not re.search(r"\d+\.\d\d–\d+\.\d\d", text), "no score lines on phones"
    page.click("#lg-views [data-lg-view=players]")
    page.wait_for_timeout(200)
    assert not sideways(page)
