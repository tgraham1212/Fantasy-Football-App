"""The 2013-2021 rookie order from Dynasty League Football (DLF) mock draft ADP, collected by mizelle.net.

``python -m ffapp rookie-adp-fetch`` (run by hand, never by a cold run) downloads each year's page from
``https://mizelle.net/mfl/<year>/`` and DynastyProcess's open player-ID map (``db_playerids.csv``, GPL-3.0)
into the gitignored cache ``.cache/third-party/``, then writes the committed record
``data/pick-values/rookie-order.json``: for each class, slots 1.01-3.12 with each rookie's Sleeper id.
Only that derived ranking is committed; the pages and the ID map stay local. Those classes never change,
so the pages are needed once.

A page embeds ``playerArr`` (``var``, ``const`` or ``let``): each Player with ``status`` ("R" = rookie),
``position``, the MFL ``id`` and ``stats.<month>.picks``, the pick numbers in that month's mock drafts.
A rookie's slot is his rank among the class's QB/RB/WR/TE rookies by mean May-August pick (drafts held
after the NFL draft); ties go to the lower MFL id. A rookie with no Sleeper id keeps his slot, flagged.
"""

from __future__ import annotations

import csv
import io
import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from ffapp.pick_values import HISTORY_SEASONS, SLOTS, rookie_order_path
from ffapp.store import Store, write_json

CACHE = Path(".cache") / "third-party"
PAGE_URL = "https://mizelle.net/mfl/{year}/"
IDS_URL = "https://github.com/dynastyprocess/data/raw/master/files/db_playerids.csv"
POST_DRAFT_MONTHS = ("may", "jun", "jul", "aug")
POSITIONS = ("QB", "RB", "WR", "TE")
SPACING_SECONDS = 2.0
SOURCE = "Dynasty League Football startup mock drafts held May to August on MFL, collected by mizelle.net"


def page_path(cache: Path, year: str) -> Path:
    return cache / "mizelle" / f"{year}.html"


def ids_path(cache: Path) -> Path:
    return cache / "dynastyprocess" / "db_playerids.csv"


def player_arr(html: str) -> list[dict]:
    """The ``playerArr`` JSON array embedded in a mizelle.net page."""
    m = re.search(r"(?:var|const|let)\s+playerArr\s*=\s*\[", html)
    if not m:
        raise ValueError("no playerArr in page")
    start = m.end() - 1
    depth = 0
    in_str = False
    esc = False
    for j in range(start, len(html)):
        c = html[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(html[start:j + 1])
    raise ValueError("unterminated playerArr")


def mfl_to_sleeper(csv_text: str) -> dict[str, str]:
    out = {}
    for row in csv.DictReader(io.StringIO(csv_text)):
        mfl, sid = (row.get("mfl_id") or "").strip(), (row.get("sleeper_id") or "").strip()
        if mfl and sid and mfl != "NA" and sid != "NA":
            out[mfl] = sid
    return out


def display_name(name: str) -> str:
    """MFL's "Last, First" as "First Last"."""
    parts = [p.strip() for p in str(name).split(",", 1)]
    return f"{parts[1]} {parts[0]}" if len(parts) == 2 and parts[1] else str(name)


def dlf_order(players: list[dict], mfl_ids: dict[str, str]) -> list[dict]:
    """Slots 1..36 of one class: rookies by mean May-August pick, ties to the lower MFL id."""
    ranked = []
    for p in players:
        if p.get("status") != "R" or p.get("position") not in POSITIONS:
            continue
        picks = [x for m in POST_DRAFT_MONTHS for x in ((p.get("stats") or {}).get(m) or {}).get("picks") or []]
        if picks:
            ranked.append((statistics.fmean(picks), int(p.get("id") or 0), p))
    ranked.sort(key=lambda r: (r[0], r[1]))
    out = []
    for i, (mean, mfl, p) in enumerate(ranked[:SLOTS]):
        out.append({"slot": i + 1, "sleeper_id": mfl_ids.get(str(mfl)), "name": display_name(p.get("name", "")),
                    "position": p.get("position"), "mean_pick": round(mean, 2), "mfl_id": str(mfl)})
    return out


def fetch_pages(client, cache: Path = CACHE, years=HISTORY_SEASONS, sleep=time.sleep) -> int:
    """Download the missing pages and the ID map into the cache, ``SPACING_SECONDS`` apart; returns how
    many files were fetched."""
    fetched = 0
    targets = [(PAGE_URL.format(year=y), page_path(cache, y)) for y in years] + [(IDS_URL, ids_path(cache))]
    for url, path in targets:
        if path.exists():
            continue
        if fetched:
            sleep(SPACING_SECONDS)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(client.get_text(url), encoding="utf-8")
        fetched += 1
    return fetched


def write_rookie_order(base: Store, cache: Path = CACHE, years=HISTORY_SEASONS) -> dict:
    """Build every cached class's order and write the committed rookie order record."""
    mfl_ids = mfl_to_sleeper(ids_path(cache).read_text(encoding="utf-8"))
    classes = {}
    for year in years:
        classes[str(year)] = dlf_order(player_arr(page_path(cache, year).read_text(encoding="utf-8")), mfl_ids)
    record = {
        "source": SOURCE,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "classes": classes,
        "flagged": [{"class": y, "slot": s["slot"], "name": s["name"]} for y, slots in classes.items() for s in slots if not s["sleeper_id"]],
    }
    write_json(rookie_order_path(base), record)
    return record
