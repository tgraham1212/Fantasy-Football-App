"""Draw docs/images/league-records/diagram.svg: where the League page's league records come from, where
the data is stored, how they are calculated and where they show.

Run after changing a source, a stored path, a calculation or what the Records page shows:
    python -X utf8 tools/league_records_diagram.py
The wording here must match docs/league-records.md; "Calc N" is section N of Calculations.txt.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "league-records" / "diagram.svg"

STYLE = """
.grp { stroke-width: 1.5; } .g1 { fill: #efeeeb; stroke: #8c8a84; } .g2 { fill: #eef1f6; stroke: #93a0b8; }
.g3 { fill: #fbf2e1; stroke: #c08a2c; } .g4 { fill: #e8f0fb; stroke: #4f7cc0; } .g5 { fill: #e8f5ea; stroke: #4f9a5c; }
.gl { font-weight: 700; font-size: 13px; letter-spacing: 0.06em; fill: #4c5058; }
.gs { font-size: 11.5px; fill: #4c5058; }
.st { fill: #ffffff; stroke: #2b2f36; stroke-width: 1.4; } .st.rebuilt { stroke-dasharray: 5 3; }
.stt { font-weight: 700; font-size: 12.5px; fill: #14161a; } .sd { font-size: 11.5px; fill: #4c5058; }
.ref { font-size: 10.5px; font-weight: 700; fill: #b4530b; font-family: ui-monospace, Consolas, monospace; }
.path { font-size: 11px; fill: #2b2f36; font-family: ui-monospace, Consolas, monospace; }
.e { fill: none; stroke: #2b2f36; stroke-width: 1.5; } .ah { fill: #2b2f36; }
.lg { font-size: 12.5px; fill: #2b2f36; } .lgn { font-weight: 800; }
"""

# Each box: (title, Calculations.txt reference or "", stored path or "", lines, rebuilt?).
SOURCES = [
    ("Sleeper: League Data", "", "", ["Matchups (points, starters, rosters),", "playoff brackets, rosters with IR", "and taxi, users and Team Names"], False),
    ("Sleeper: Stats", "", "", ["Each Player's NFL team that week"], False),
    ("Sleeper: Projections", "", "", ["Each Player's expected stat line,", "for past-season lineup choices"], False),
]

STORED = [
    ("League Data", "", "data/leagues/", ["One folder per league and season"], False),
    ("Player WAR", "Calc 16", "data/war/", ["Weekly league-scored points and", "WAR per Player and season"], False),
    ("Stats", "", "data/stats/", ["Played weeks, kept forever"], False),
    ("Projections", "", "data/projections/", ["Current and earlier weeks"], False),
    ("Game Views", "Calc 11", "data/games-derived/", ["Lineup choices from 2026 on"], True),
]

CALCS = [
    ("Games That Matter", "Calc 23", "", ["Regular season, the winners bracket's", "path, final and 3rd place game, the", "toilet bowl's path and final"], False),
    ("Manager History", "Calc 19", "", ["Identity, final places, all-play", "luck and Player windows, reused"], False),
    ("Past Lineup Choices", "Calc 11, 23", "", ["Model lineup from stored Projections", "against the starters used, 2021-2025"], False),
    ("League Records", "Calc 23", "", ["Champions, all-time standings, weekly", "and season records, Player records;", "top 25, ties share a rank, oldest first"], False),
]

OUTPUTS = [
    ("League Records File", "Calc 23", "site/data/<league>/records.json", ["Everything the Records page draws,", "one file per league"], True),
]

FEATURES = [
    ("League Page: Records", ["Managers view: Champions, All-Time", "Standings, Weekly and Season Records", "Players view: Best Games, Best Bench", "Games, Career Scoring, Championships", "Each record: a top-25 pop-up"]),
]

RUNS = [
    ("Build", "python -m ffapp build (and every cold run's export) writes the records file from the stored data"),
    ("Records", "the stored league data, WAR files, stats and Projections are records; the records file is derived data"),
]

COLS = [
    ("1. WHERE IT COMES FROM", "Fetched by each cold run", "g1", 250),
    ("2. WHERE IT IS STORED", "Records in git; rebuilt files in the build cache", "g2", 270),
    ("3. HOW IT IS CALCULATED", "In this order, every build", "g3", 290),
    ("4. WHAT IT PRODUCES", "Derived data, deployed with the site", "g4", 300),
    ("5. WHERE IT SHOWS", "fantasyfoosball.net", "g5", 280),
]
GAP, LEFT, TOP, LINE = 34, 24, 64, 15.5


def text(x, y, s, cls, anchor="start"):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>'


def arrow(d):
    return f'<path d="{d}" class="e" marker-end="url(#a)"/>'


def box_height(item):
    title, ref, path, lines, _ = item
    return 30 + (LINE if path else 0) + LINE * len(lines)


def box(x, y, w, item):
    title, ref, path, lines, rebuilt = item
    h = box_height(item)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="st{" rebuilt" if rebuilt else ""}"/>',
           text(x + 12, y + 20, title, "stt")]
    if ref:
        out.append(text(x + w - 10, y + 20, ref, "ref", "end"))
    cy = y + 20 + LINE + 2
    if path:
        out.append(text(x + 12, cy, path, "path"))
        cy += LINE
    out += [text(x + 12, cy + i * LINE, line, "sd") for i, line in enumerate(lines)]
    return out, h


def column(x, w, items, gap=12, chain=False):
    out, y, mids = [], TOP + 58, []
    for i, item in enumerate(items):
        parts, h = box(x + 12, y, w - 24, item)
        out += parts
        if chain and i:
            out.append(arrow(f"M{x + w / 2} {y - gap + 1} V{y - 3}"))
        mids.append(y + h / 2)
        y += h + gap
    return out, y, mids


def build():
    xs, x = [], LEFT
    for _, _, _, w in COLS:
        xs.append(x)
        x += w + GAP
    width = x - GAP + LEFT

    bodies = []
    feature_items = [(t, "", "", lines, False) for t, lines in FEATURES]
    for (title, sub, cls, w), x, items, chain in zip(COLS, xs, (SOURCES, STORED, CALCS, OUTPUTS, feature_items),
                                                    (False, False, True, False, False)):
        parts, bottom, _ = column(x, w, items, gap=18 if chain else 12, chain=chain)
        bodies.append((x, w, cls, title, sub, parts, bottom))
    bottom = max(b[6] for b in bodies) + 6
    height = bottom + 36 + 24 * (len(RUNS) + 1) + 20

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
           f'aria-labelledby="lr-t" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
           f"<style>{STYLE}</style>", f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           '<title id="lr-t">How league records are made: their sources, where the data is stored, the calculations in order, '
           'the records file and the page that shows it</title>',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" class="ah"/></marker></defs>',
           text(LEFT, 34, "HOW LEAGUE RECORDS ARE MADE", "gl")]
    for x, w, cls, title, sub, parts, _ in bodies:
        out.append(f'<rect x="{x}" y="{TOP}" width="{w}" height="{bottom - TOP}" rx="10" class="grp {cls}"/>')
        out.append(text(x + 14, TOP + 24, title, "gl"))
        out.append(text(x + 14, TOP + 42, sub, "gs"))
        out += parts
    mid = TOP + (bottom - TOP) / 2
    for x, w, *_ in bodies[:-1]:
        out.append(arrow(f"M{x + w + 3} {mid} H{x + w + GAP - 4}"))

    ly = bottom + 30
    out.append(f'<rect x="{LEFT + 2}" y="{ly - 11}" width="22" height="13" rx="3" class="st"/>')
    out.append(text(LEFT + 32, ly, "Record: committed to git, kept forever", "lg"))
    out.append(f'<rect x="{LEFT + 342}" y="{ly - 11}" width="22" height="13" rx="3" class="st rebuilt"/>')
    out.append(text(LEFT + 372, ly, "Rebuilt by each run (build cache, deployed site or relay), never committed", "lg"))
    out.append(text(width - LEFT, ly, "Calc N = section N of Calculations.txt", "ref", "end"))
    for i, (name, what) in enumerate(RUNS):
        y = ly + 26 + i * 24
        out.append(f'<text x="{LEFT}" y="{y}" class="lg"><tspan class="lgn">{escape(name)}:</tspan> {escape(what)}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
