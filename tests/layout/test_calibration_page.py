"""The calibration page (odds-calibration 7.9.x and 8.1.x), checked in the browser against the published
calibration report and league files: its title and link, the not-run message, the live model numbers
and the switches it states."""

from __future__ import annotations

import json


def open_calibration(open_page, width=1280):
    page, _ = open_page("calibration.html", width)
    page.wait_for_selector("#main:not([hidden]), #not-run:not([hidden])")
    return page


def fetch(page, path):
    return page.evaluate("async (p) => (await fetch(p)).json()", path)


def test_page_is_titled_and_linked_from_the_league_pages(open_page):
    """7.9"""
    page, _ = open_page("index.html#dynasty", 1280)
    assert page.locator("a[href='calibration.html']").count() >= 1
    page = open_calibration(open_page)
    assert page.inner_text("h1") == "How Good Are These Forecasts?"
    assert page.title() == "How Good Are These Forecasts?"
    assert page.is_visible("#main") and not page.is_visible("#not-run")


def test_not_run_message_without_a_report(open_page, base_url):
    """7.9.2"""
    page = open_calibration(open_page)
    index = fetch(page, "data/index.json")
    index.pop("calibration", None)
    page.route(f"{base_url}/data/index.json*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(index)))
    page.goto("about:blank")
    page.goto(f"{base_url}/calibration.html")
    page.wait_for_selector("#not-run:not([hidden])")
    assert not page.is_visible("#main")


def test_explanation_uses_the_published_model(open_page):
    """8.1.1: replacement levels per position for each league, and the 20-point edge two and twelve weeks out."""
    page = open_calibration(open_page)
    index = fetch(page, "data/index.json")
    leagues = [fetch(page, f"data/{l['file']}") for l in index["leagues"]]
    tables = page.inner_text("#how-tables")
    for league in leagues:
        for pos in league["replacement"]["levels"]:
            assert pos in tables, (league["league_key"], pos)
    drift = page.inner_text("#how-drift")
    for league, entry in zip(leagues, index["leagues"]):
        slopes = league["model"]["drift"]["slopes"]
        two, twelve = round(20 * slopes[1]), round(20 * slopes[min(12, len(slopes)) - 1])
        if twelve >= 20:
            assert f"In {entry['name']}" in drift and "full edge" in drift
        else:
            assert f"keep about {two} of those points two weeks out and {twelve} twelve weeks out" in drift


def test_switches_and_n_are_stated(open_page):
    """8.1.2"""
    page = open_calibration(open_page)
    report = fetch(page, "data/calibration.json")
    meta = page.inner_text("#meta")
    floor = "replacement floor off" if report.get("replacement_floor") is False else "replacement floor on"
    assert floor in meta
    if report.get("replacement_floor") is not False and report.get("replacement_top_n"):
        assert f"best {report['replacement_top_n']} free agents" in meta
    assert ("roster drift off" if report.get("roster_drift") is False else "roster drift on") in meta
