"""The Managers page (site/managers.js): URLs, the info bars, the four cards and phone behaviour, on
the exported site data. Worst cases (the longest names, many banners, big scores) are injected by
rewriting managers.json on its way to the page."""

from __future__ import annotations

import json

import pytest

from tests.layout.conftest import PHONE_WIDTHS, WIDE_FONT, WIDTHS
from tests.layout.test_layout import OVERFLOW_JS, open_view

CUT_JS = """(sel) => [...document.querySelectorAll(sel)].filter((e) => e.getClientRects().length && e.scrollWidth > e.clientWidth + 1)
  .map((e) => e.textContent.trim().slice(0, 30))"""
OUTSIDE_JS = """([outer, inner]) => {
  const out = [];
  for (const box of document.querySelectorAll(outer)) {
    if (!box.getClientRects().length) continue;
    const b = box.getBoundingClientRect();
    for (const e of box.querySelectorAll(inner)) {
      const r = e.getBoundingClientRect();
      if (r.width && (r.right > b.right + 0.5 || r.left < b.left - 0.5)) out.push(`${e.className || e.tagName} ${e.textContent.trim().slice(0, 20)}`);
    }
  }
  return out;
}"""


def _worst_case(route):
    """The selected dynasty page with the hardest values: long names, big scores, double-digit WAR, and a
    season-end record and points for."""
    body = json.loads(route.fetch().text())
    for m in body["managers"]:
        t = m["tiles"]
        t["record"] = {**t.get("record", {}), "wins": 10, "losses": 10, "ties": 1}
        t["points_for"] = 2488.88
        if t.get("last_result"):
            t["last_result"]["points"], t["last_result"]["opp_points"] = 188.62, 104.04
        if t.get("top_scorer"):
            t["top_scorer"]["name"] = "Jaxon Smith-Njigba"
        if m["players"].get("best"):
            m["players"]["best"].update(name="Amon-Ra St. Brown", war=12.4, seasons=11)
        m["banners"] = {"champion": ["2021", "2022", "2024", "2025"], "toilet_bowl": ["2023", "2026"]}
    route.fulfill(status=200, json=body)


def test_link_names_the_manager_and_arrows_update_the_url(open_page):
    page, _, _ = open_view(open_page, "managers-retired", 1280)
    assert page.locator("#mgr-select option:checked").inner_text().startswith("TateFM")
    assert "Seasons" in page.locator(".mgr-facts").inner_text()   # a retired manager
    page.click("#mgr-next")
    page.wait_for_timeout(400)
    name = page.locator("#mgr-select option:checked").inner_text().split(" · ")[0]
    assert page.evaluate("location.hash").endswith(f"/managers/{name}")


@pytest.mark.parametrize("wide", [False, True], ids=["font", "wide-font"])
@pytest.mark.parametrize("width", WIDTHS)
def test_tiles_fit_the_worst_case(open_page, width, wide):
    page, _, _ = open_view(open_page, "managers", width)
    page.route("**/managers.json", _worst_case)
    page.reload()
    page.wait_for_load_state("networkidle")
    if wide:
        page.add_style_tag(content=WIDE_FONT)
        page.evaluate("window.dispatchEvent(new Event('resize'))")   # names are fitted again after the font change
    page.wait_for_timeout(500)
    cut = page.evaluate(CUT_JS, ".mgr-tile .main, .mgr-tile .l2, .mgr-tile-k .lbl")
    outside = page.evaluate(OUTSIDE_JS, [".mgr-tile", ".mgr-score > *, .mgr-crest, .mgr-head"])
    problems = page.evaluate(OVERFLOW_JS, ["#mgr-content"])
    assert not cut and not outside and not problems, f"{width}px: cut {cut}, outside {outside}, {problems}"


@pytest.mark.parametrize("width", [360, 1280])
def test_banners_stack_only_when_out_of_room(open_page, width):
    page, _, _ = open_view(open_page, "managers", width)
    page.route("**/managers.json", _worst_case)
    page.reload()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)
    flags = page.evaluate("""() => { const b = document.getElementById('mgr-banners');
      return { stacked: b.classList.contains('stacked'), over: b.scrollWidth > b.clientWidth + 1, champs: b.querySelectorAll('.mgr-flag.champ').length }; }""")
    assert flags["champs"] == 4 and not flags["over"], flags
    assert page.evaluate(OVERFLOW_JS, [".mgr-bar"]) == []


@pytest.mark.parametrize("width", WIDTHS + (1100, 1366))
def test_cards_cut_nothing_and_never_scroll_sideways(open_page, width):
    page, _, _ = open_view(open_page, "managers", width)
    tabs = ["hist", "h2h", "rec"]
    problems = []
    for card in ("roster", "history", "moves", "news"):
        page.evaluate("(c) => document.querySelector(`[data-card-tab='${c}']`).click()", card)
        for tab in (tabs if card == "history" else [None]):
            if tab:
                page.evaluate("(t) => document.querySelector(`[data-htab='${t}']`).click()", tab)
            page.wait_for_timeout(150)
            problems += [f"{card}/{tab}: name cut {n}" for n in page.evaluate(CUT_JS, ".mgr-card.show .pname, .mgr-card:not([hidden]) .mgr-table .pname")]
            problems += [f"{card}: sideways scroll" for s in page.evaluate("() => [...document.querySelectorAll('.mgr-scroll')].filter((e) => e.getClientRects().length && e.scrollWidth > e.clientWidth + 1).map((e) => 1)")]
            problems += [f"{card}/{tab}: outside {o}" for o in page.evaluate(OUTSIDE_JS, [".mgr-card", ".mgr-feat .board > *, .mgr-feat .h, .mgr-story, .mgr-rec, .mgr-key, .mgr-h2h"])]
    lines = page.evaluate("() => [...document.querySelectorAll('.mgr-key')].map((k) => new Set([...k.children].map((c) => Math.round(c.getBoundingClientRect().top))).size)")
    wrapped = page.evaluate("""() => [...document.querySelectorAll('.mgr-h2h td.last')].filter((td) => {
      const r = document.createRange(); r.selectNodeContents(td); return new Set([...r.getClientRects()].map((x) => Math.round(x.top))).size > 1; }).length""")
    assert not problems and all(n == 1 for n in lines) and not wrapped, f"{width}px: {problems} legend lines {lines} wrapped scores {wrapped}"


@pytest.mark.parametrize("width", PHONE_WIDTHS)
def test_phone_cards_never_scroll_inside_and_share_a_height(open_page, width):
    page, _, _ = open_view(open_page, "managers", width)
    heights = []
    for card in ("roster", "history", "moves", "news"):
        page.evaluate("(c) => document.querySelector(`[data-card-tab='${c}']`).click()", card)
        page.wait_for_timeout(150)
        shown = page.evaluate("""() => { const c = document.querySelector('.mgr-card.show');
          const inner = [...c.querySelectorAll('.mgr-scroll')].some((s) => getComputedStyle(s).overflowY !== 'visible');
          return { inner, height: c.getBoundingClientRect().height, count: document.querySelectorAll('.mgr-card.show').length }; }""")
        assert shown["count"] == 1 and not shown["inner"], (card, shown)
        heights.append(shown["height"])
    assert min(heights) >= 600 - 1, heights


@pytest.mark.parametrize("width", [1366, 1280, 1100])
def test_desktop_cards_share_one_height(open_page, width):
    page, _, _ = open_view(open_page, "managers", width)
    heights = page.evaluate("() => [...document.querySelectorAll('.mgr-card')].map((c) => Math.round(c.getBoundingClientRect().height))")
    assert len(set(heights)) == 1, heights


@pytest.mark.parametrize("view", ["predictions", "games", "positions", "war"])
def test_manager_names_open_their_page(open_page, view):
    page, _, _ = open_view(open_page, view, 1280)
    link = page.locator("a.manager-link").first
    name = link.get_attribute("data-manager-link")
    link.evaluate("e => e.click()")
    page.wait_for_timeout(500)
    assert not page.locator("#page-managers").is_hidden(), view
    assert page.locator("#mgr-select option:checked").inner_text().split(" · ")[0] == name
    assert page.evaluate("location.hash").endswith(f"/managers/{name}") or page.evaluate("decodeURIComponent(location.hash)").endswith(f"/managers/{name}")


# text wider than its box to the fraction of a pixel (an ellipsis shows from 0.01 px over)
FRACTION_CUT_JS = """(sel) => [...document.querySelectorAll(sel)].filter((e) => {
  if (!e.getClientRects().length || getComputedStyle(e).whiteSpace === 'normal') return false;
  const r = document.createRange(); r.selectNodeContents(e);
  return r.getBoundingClientRect().width > e.getBoundingClientRect().width + 0.5; }).map((e) => e.textContent.trim().slice(0, 40))"""


@pytest.mark.parametrize("wide", [False, True], ids=["font", "wide-font"])
@pytest.mark.parametrize("width", WIDTHS)
def test_moves_card_cuts_nothing(open_page, width, wide):
    """Moves rows and trade blocks (managers-moves): no player name or "how" line cut, nothing
    outside the card, no sideways scroll, for one season, All seasons and the Trades filter."""
    page, _, _ = open_view(open_page, "managers-moves", width)
    if wide:
        page.add_style_tag(content=WIDE_FONT)
        page.evaluate("window.dispatchEvent(new Event('resize'))")
        page.wait_for_timeout(400)
    problems = []
    for season, filt in ((None, "all"), ("all", "all"), ("all", "trade")):
        if season:
            page.select_option("#mgr-moves-season", season)
        page.select_option("#mgr-moves-filter", filt)
        page.wait_for_timeout(300)
        label = f"{season or 'season'}/{filt}"
        assert page.locator("#mgr-moves .mgr-mv, #mgr-moves .mgr-trade").count(), f"{label}: no moves shown, the check proves nothing"
        problems += [f"{label}: cut {t}" for t in page.evaluate(FRACTION_CUT_JS, "#mgr-moves .fitname, #mgr-moves .mgr-mv .how")]
        problems += [f"{label}: outside {o}" for o in page.evaluate(OUTSIDE_JS, ["#mgr-moves", ".mgr-mv > *, .mgr-trade, .mgr-trade .it, .mgr-meter .ms > *"])]
        problems += [f"{label}: sideways scroll" for _ in page.evaluate("() => [...document.querySelectorAll('#mgr-moves .mgr-scroll')].filter((e) => e.scrollWidth > e.clientWidth + 1).map(() => 1)")]
    assert not problems, f"{width}px: " + "; ".join(problems[:12])
