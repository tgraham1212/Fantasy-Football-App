"""Behaviour of the Managers sub-tab (manager-pages 4.4.x), checked in the browser against the published
managers data: the picker's order and league switching, the PPG chip tiers, the head-to-head order, the
Moves filter, season picker and list headers, and the phone's Show More button for Team News."""

from __future__ import annotations

from urllib.parse import quote


def open_managers(open_page, league="dynasty", name=None, width=1280):
    page, _ = open_page(f"index.html#{league}/managers" + (f"/{quote(name)}" if name else ""), width)
    page.wait_for_selector(".mgr-card")
    return page


def managers(page, league="dynasty") -> list[dict]:
    return page.evaluate("async (k) => (await fetch(`data/${k}/managers.json`)).json()", league)["managers"]


def ordered(ms: list[dict]) -> list[dict]:
    key = lambda m: m["name"].casefold()
    return sorted((m for m in ms if m["current"]), key=key) + sorted((m for m in ms if not m["current"]), key=key)


def shown(page) -> str:
    return page.eval_on_selector("#mgr-select", "s => s.value")


def tier(ppg, repl) -> str:
    """The rule in 4.4.6.1."""
    if ppg is None or not repl:
        return "r3"
    x = ppg / repl
    return "r5" if x >= 1.5 else "r4" if x >= 1.2 else "r3" if x >= 0.9 else "r2" if x >= 0.7 else "r1"


def test_picker_lists_current_managers_then_retired(open_page):
    """4.4.1"""
    page = open_managers(open_page)
    ms = managers(page)
    groups = page.eval_on_selector_all("#mgr-select optgroup", "gs => gs.map(g => [g.label, [...g.children].map(o => o.value)])")
    want = [["Managers", [m["user_id"] for m in ordered(ms) if m["current"]]]]
    if any(not m["current"] for m in ms):
        want.append(["Retired", [m["user_id"] for m in ordered(ms) if not m["current"]]])
    assert groups == want


def test_switching_league_keeps_a_shared_manager_or_shows_the_first(open_page):
    """4.4.1.2"""
    page = open_managers(open_page)
    dyn, red = managers(page, "dynasty"), managers(page, "redraft")
    red_names = {m["name"]: m for m in red}
    shared = next(m for m in ordered(dyn) if m["name"] in red_names)
    only = next(m for m in ordered(dyn) if m["name"] not in red_names)
    for who, expect in ((shared, red_names[shared["name"]]["user_id"]), (only, ordered(red)[0]["user_id"])):
        page.goto("about:blank")
        page = open_managers(open_page, "dynasty", who["name"])
        page.click("#league-switcher button:has-text(\"Chris Carter's Fall Guys\")")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(400)
        assert shown(page) == expect, who["name"]


def test_ppg_chips_follow_the_replacement_tiers(open_page):
    """4.4.6.1"""
    page = open_managers(open_page)
    m = next(x for x in managers(page) if x["user_id"] == shown(page))
    rows = page.locator(".mgr-roster tbody tr").evaluate_all("""rs => rs.map(r => ({ chip: r.querySelector('.mgr-chip')?.className || null,
        pos: r.querySelector('.c-pos').textContent }))""")
    with_ppg = [r for r in m["roster"] if r["ppg"] is not None]
    chips = [r for r in rows if r["chip"]]
    assert len(chips) == len(with_ppg)
    for got, r in zip(chips, with_ppg):
        assert got["chip"].split()[-1] == tier(r["ppg"], m["replacement"].get(r["position"])), r


def test_head_to_head_lists_the_rival_first_then_by_games(open_page):
    """4.4.7.2"""
    page = open_managers(open_page)
    m = next(x for x in managers(page) if x["user_id"] == shown(page))
    page.click("[data-htab='h2h']")
    page.wait_for_timeout(200)
    names = page.locator(".mgr-h2h tbody td.c-m a").all_text_contents()
    rows = m["head_to_head"]
    assert names == [r["name"] for r in rows]
    rest = rows[1:] if rows and rows[0].get("rival") else rows
    assert [r["games"] for r in rest] == sorted((r["games"] for r in rest), reverse=True)
    if m.get("rival"):
        assert rows[0]["rival"] and page.locator(".mgr-h2h tbody tr").first.locator(".riv").count() == 1


def test_moves_filter_season_picker_and_headers(open_page):
    """4.4.9.1, 4.4.9.2 and 4.4.10.1"""
    page = open_managers(open_page)
    m = next(x for x in managers(page) if x["user_id"] == shown(page))
    seasons = sorted(m["faab"], reverse=True)
    assert page.eval_on_selector_all("#mgr-moves-season option", "o => o.map(x => x.value)") == seasons + ["all"]
    filters = page.eval_on_selector_all("#mgr-moves-filter option", "o => o.map(x => x.textContent)")
    assert filters == ["All moves", "Waivers", "Free agents", "Trades"]
    heads = page.locator("#mgr-moves h4.ih").all_text_contents()
    added = len(m["moves"].get(seasons[0], {}).get("added", []))
    assert heads[0].startswith(f"Added ({added})"), heads
    page.select_option("#mgr-moves-filter", "trade")
    page.wait_for_timeout(200)
    heads = page.locator("#mgr-moves h4.ih").all_text_contents()
    assert len(heads) == 1 and heads[0].startswith("Trades ("), heads


def test_phone_news_shows_seven_stories_then_show_more(open_page):
    """4.4.8.2"""
    page = open_managers(open_page, width=360)
    m = next(x for x in managers(page) if x["user_id"] == shown(page))
    assert len(m["news"]) > 8, "the fixture manager needs more than eight stories"
    page.click(".mgr-cardtabs button:has-text('News')")
    page.wait_for_timeout(200)
    visible = lambda: page.locator(".mgr-news .mgr-story").evaluate_all("s => s.filter(x => x.offsetParent !== null).length")
    assert visible() == 7
    page.click(".mgr-showmore")
    page.wait_for_timeout(200)
    assert visible() == len(m["news"]) - 1, "every story under the feature shows"
