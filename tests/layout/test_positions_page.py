"""Behaviour of the Positions sub-tab (positional-rankings-page 3.1.x), checked in the browser against the
published positions data: the season control, which charts show, row order, the replacement line, the
top player's label, out-of-range values and the taxi and injury markers."""

from __future__ import annotations

import functools
import json

import pytest

ORDER = ["QB", "RB", "WR", "TE", "K", "DEF"]


def open_positions(open_page, league: str, width: int = 1280):
    page, relay = open_page(f"index.html#{league}/positions", width)
    page.wait_for_selector(".pos-card")
    return page


def fetch(page, path: str):
    return page.evaluate("async (p) => (await fetch(p)).json()", path)


def season_payload(page, league: str) -> dict:
    index = fetch(page, f"data/{league}/positions/index.json")
    entry = next(s for s in index["seasons"] if s["season"] == index["current"])
    return fetch(page, f"data/{league}/positions/{entry['file']}")


def expected_rows(payload: dict, pos: str) -> list[str]:
    """The rule in 3.1.3: best player's points per game, then the next best, then Team Name; empty rows last."""
    rows = [(t, sorted((p["ppg"] for p in t["players"] if p["position"] == pos), reverse=True)) for t in payload["teams"]]

    def cmp(a, b):
        (ta, pa), (tb, pb) = a, b
        if not pa or not pb:
            return (1 if pb else 0) - (1 if pa else 0) or ((ta["team_name"] > tb["team_name"]) - (ta["team_name"] < tb["team_name"]))
        for i in range(max(len(pa), len(pb))):
            d = (pb[i] if i < len(pb) else float("-inf")) - (pa[i] if i < len(pa) else float("-inf"))
            if d:
                return 1 if d > 0 else -1
        return (ta["team_name"] > tb["team_name"]) - (ta["team_name"] < tb["team_name"])

    return [t["display_name"] for t, _ in sorted(rows, key=functools.cmp_to_key(cmp))]


def test_season_control_defaults_to_the_current_season(open_page):
    """3.1.1 and 3.1.1.1"""
    page = open_positions(open_page, "dynasty")
    index = fetch(page, "data/dynasty/positions/index.json")
    assert page.eval_on_selector("#positions-season", "s => s.value") == index["current"]
    options = page.eval_on_selector_all("#positions-season option", "o => o.map(x => x.value)")
    assert options == [s["season"] for s in reversed(index["seasons"])], "every season with a file, newest first"
    current = next(s for s in index["seasons"] if s["season"] == index["current"])
    if current["status"] == "in_progress":
        assert f"through week {current['final_through']}" in page.inner_text("#page-positions")


@pytest.mark.parametrize("league", ["dynasty", "redraft"])
def test_one_chart_per_started_position_in_order(open_page, league):
    """3.1.2"""
    page = open_positions(open_page, league)
    shown = page.eval_on_selector_all(".pos-card", "cards => cards.map(c => c.dataset.pos)")
    assert shown == [p for p in ORDER if p in season_payload(page, league)["positions"]]


@pytest.mark.parametrize("league", ["dynasty", "redraft"])
def test_rows_follow_each_managers_best_player(open_page, league):
    """3.1.3"""
    page = open_positions(open_page, league)
    payload = season_payload(page, league)
    for pos in payload["positions"]:
        labels = page.eval_on_selector_all(f".pos-card[data-pos='{pos}'] .pos-label",
                                           "ls => ls.map(l => l.title.replace(/ \\(.*\\)$/, ''))")
        assert labels == expected_rows(payload, pos), pos


def test_replacement_line_sits_at_the_replacement_level(open_page):
    """3.1.4"""
    page = open_positions(open_page, "redraft")
    payload = season_payload(page, "redraft")
    for pos, info in payload["positions"].items():
        card = f".pos-card[data-pos='{pos}']"
        lines = page.locator(f"{card} line.pos-rep")
        if info.get("replacement") is None:
            assert lines.count() == 0, pos
            continue
        ticks = page.eval_on_selector_all(f"{card} text.pos-tick", "ts => ts.map(t => [Number(t.textContent), Number(t.getAttribute('x'))])")
        (v0, x0), (v1, x1) = ticks[0], ticks[-1]
        want = x0 + (info["replacement"] - v0) * (x1 - x0) / (v1 - v0)
        assert abs(float(lines.first.get_attribute("x1")) - want) <= 1, (pos, want)
        assert page.locator(f"{card} text.pos-rep-label").text_content() == "Replacement Level"


def test_top_player_is_labelled_over_his_dot(open_page):
    """3.1.7"""
    page = open_positions(open_page, "dynasty")
    for card in page.locator(".pos-card").all():
        dots = card.locator(".pos-dot").evaluate_all("ds => ds.map(d => ({ ppg: Number(d.dataset.ppg), x: Number(d.getAttribute('cx')), name: d.dataset.name }))")
        if not dots:
            continue
        top = max(dots, key=lambda d: d["ppg"])
        label = card.locator("text.pos-top-name")
        assert label.count() == 1
        assert abs(float(label.get_attribute("x")) - top["x"]) <= 0.5 or label.evaluate("t => t.getAttribute('transform') !== null")
        assert label.text_content() in top["name"], (label.text_content(), top["name"])


def test_out_of_range_value_sits_at_the_edge_with_an_arrow(open_page, base_url):
    """3.1.8: a value past the axis is drawn at the edge with an arrow, and its popup shows the true value."""
    page = open_positions(open_page, "dynasty")
    index = fetch(page, "data/dynasty/positions/index.json")
    entry = next(s for s in index["seasons"] if s["season"] == index["current"])
    payload = fetch(page, f"data/dynasty/positions/{entry['file']}")
    player = next(p for p in payload["teams"][0]["players"] if p["position"] == "QB")
    player["ppg"] = 99.0
    page.route(f"{base_url}/data/dynasty/positions/{entry['file']}*",
               lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(payload)))
    page.goto("about:blank")
    page.goto(f"{base_url}/index.html#dynasty/positions")
    page.wait_for_selector(".pos-card[data-pos='QB'] .pos-dot")
    card = page.locator(".pos-card[data-pos='QB']")
    dot = card.locator(f".pos-dot[data-name=\"{player['name']}\"]")
    xs = card.locator(".pos-dot").evaluate_all("ds => ds.map(d => Number(d.getAttribute('cx')))")
    assert float(dot.get_attribute("cx")) == max(xs), "drawn at the right edge"
    assert card.locator(".pos-arrow").count() >= 1
    dot.evaluate("e => e.focus({ preventScroll: true })")
    page.wait_for_timeout(200)
    assert "99.0" in page.inner_text(".pos-pop:not([hidden])")


def test_taxi_and_injury_markers_follow_the_flags(open_page):
    """3.1.6"""
    page = open_positions(open_page, "dynasty")
    payload = season_payload(page, "dynasty")
    players = [p for t in payload["teams"] for p in t["players"] if p["position"] in payload["positions"]]
    assert page.locator(".pos-dot.taxi").count() == sum(1 for p in players if p["taxi"])
    assert page.locator(".pos-hurt").count() == sum(1 for p in players if p["injured"])
