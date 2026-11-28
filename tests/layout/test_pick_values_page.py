"""The How Pick Values Work page (pick-values-page 8.3.x), in the browser against the published pick values
file: its title and link, the group table, the charts with their table views, the method and credits, the
phone widths and the not-built message."""

from __future__ import annotations

import json

import pytest

PHONES = (360, 390, 414, 440)


def open_pv(open_page, width=1280):
    page, _ = open_page("pick-values.html", width)
    page.wait_for_selector("#main:not([hidden]), #not-run:not([hidden])")
    page.wait_for_timeout(200)
    return page


def fetch(page, path):
    return page.evaluate("async (p) => (await fetch(p)).json()", path)


def test_page_is_titled_and_linked(open_page):
    """8.3: titled "How Pick Values Work" and linked from the league pages."""
    page, _ = open_page("index.html#dynasty", 1280)
    link = page.locator("footer a[href='pick-values.html']")
    assert link.count() == 1 and link.inner_text() == "How Pick Values Work"
    page = open_pv(open_page)
    assert page.title() == "How Pick Values Work" and page.inner_text("h1") == "How Pick Values Work"
    assert page.is_visible("#main") and not page.is_visible("#not-run")


def test_group_table(open_page):
    """8.3.1: nine groups with slots, measured value and range, picks and model value."""
    page = open_pv(open_page)
    model = fetch(page, "data/pick-values.json")
    rows = page.locator("#pv-groups tbody tr")
    assert rows.count() == 9
    second = page.locator("#pv-groups tr[data-group='2-Early']").inner_text()
    g = model["groups"]["2-Early"]
    assert "2.01–2.04" in second
    assert f"{abs(g['measured']):.2f}" in second and f"{abs(g['value']):.2f}" in second
    assert page.locator("#pv-groups thead th").all_text_contents() == ["Pick", "Slots", "Measured, 8 seasons", "Picks (season 1 / 8)", "Model value"]


def test_charts_and_table_views(open_page):
    """8.3.2: three charts with legends and hover values, each with a table view; the round picker swaps groups."""
    page = open_pv(open_page)
    for cid in ("pv-total-chart", "pv-season-chart", "pv-slot-chart"):
        assert page.evaluate(f"!!Chart.getChart(document.getElementById('{cid}'))"), cid
    legend = page.evaluate("Chart.getChart(document.getElementById('pv-total-chart')).data.datasets.map(d => d.label)")
    assert legend == ["1st Early", "1st Middle", "1st Late"]
    page.click("#pv-round-switcher button:nth-child(3)")
    page.wait_for_timeout(200)
    legend = page.evaluate("Chart.getChart(document.getElementById('pv-total-chart')).data.datasets.map(d => d.label)")
    assert legend == ["3rd Early", "3rd Middle", "3rd Late"]
    assert page.locator("#pv-round-switcher button[aria-pressed='true']").inner_text() == "3rd round"
    # hover season 3 on the total chart: the tooltip lists each group's total and picks
    tip = page.evaluate("""(() => {
        const c = Chart.getChart(document.getElementById('pv-total-chart'));
        const els = c.data.datasets.map((_, i) => ({datasetIndex: i, index: 2}));
        c.tooltip.setActiveElements(els, {x: c.scales.x.getPixelForValue(2), y: c.chartArea.top + 20});
        c.update();
        return {title: c.tooltip.title, body: c.tooltip.body.map(b => b.lines.join(' '))};
    })()""")
    assert tip["title"] == ["Through season 3"] and all("picks" in b for b in tip["body"])
    for table in ("#pv-total-table", "#pv-season-table", "#pv-slot-table"):
        assert page.locator(f"{table} tbody tr").count() > 0, table
    assert page.locator("#pv-slot-table tbody tr").count() == 36


def test_method_and_credits(open_page):
    """8.3.3: the method names Dynasty League Football and mizelle.net."""
    page = open_pv(open_page)
    method = page.inner_text("#pv-method")
    assert "Dynasty League Football" in method and "mizelle.net" in method
    assert page.locator("#pv-method a[href='https://mizelle.net/mfl/']").count() == 1


@pytest.mark.parametrize("width", PHONES)
def test_phone_widths(open_page, width):
    """8.3.4: every table and chart shows with no sideways page scroll."""
    page = open_pv(open_page, width)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    for cid in ("pv-total-chart", "pv-season-chart", "pv-slot-chart"):
        assert page.locator(f"#{cid}").bounding_box()["width"] > 200, cid
    assert page.is_visible("#pv-groups")


def test_not_built_message(open_page, base_url):
    """8.3.5: without a pick values file the page says so."""
    page = open_pv(open_page)
    index = fetch(page, "data/index.json")
    index["pick_values"] = None
    page.route(f"{base_url}/data/index.json*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(index)))
    page.goto("about:blank")
    page.goto(f"{base_url}/pick-values.html")
    page.wait_for_selector("#not-run:not([hidden])")
    assert not page.is_visible("#main")
    assert "have not been built" in page.inner_text("#not-run")
