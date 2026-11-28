"""Draw docs/images/pick-values/diagram.svg: where the rookie pick values come from, where the data is
stored, how the values are calculated and where they show.

Run after changing a source, a stored path, a calculation or what the pick values page shows:
    python -X utf8 tools/pick_values_diagram.py
The wording here must match docs/pick-values.md; "Calc N" is section N of Calculations.txt.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "pick-values" / "diagram.svg"

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
    ("DLF Mock Drafts (mizelle.net)", "", "", ["2013-2021 rookie ADP pages and the", "DynastyProcess ID map, fetched once", "by hand into a local cache"], False),
    ("Sleeper: Stats and Drafts", "Calc 1", "", ["Weekly stats 2013-2021 (slimmed);", "this league's rookie drafts"], False),
    ("ESPN: Start Percentages", "Calc 16", "", ["Season-long start percentages", "2013-2021 for the yearly cut"], False),
]

STORED = [
    ("Rookie Order", "Calc 27", "data/pick-values/rookie-order.json", ["The 2013-2021 classes, slots", "1.01-3.12 with Sleeper ids"], False),
    ("History Records", "Calc 27", "data/history/", ["Stats and ESPN snapshots 2013-2021,", "apart from the league seasons"], False),
    ("Pick Value Model", "Calc 27", "data/pick-values/model.json", ["Rebuilt by hand from committed", "records; cold runs only read it"], False),
]

CALCS = [
    ("History WAR", "Calc 16, 27", "", ["Player WAR with dynasty settings,", "weeks 1-14, yearly cut"], False),
    ("Eight-Season Value", "Calc 27", "", ["Mean WAR of each group's picks in", "seasons 1-8 after the draft, added up"], False),
    ("Groups, Never Rising", "Calc 27", "", ["Early, Middle, Late per round;", "neighbours that break the order", "are averaged"], False),
    ("Unused Picks", "Calc 27", "", ["Group value; next draft: Forecast", "third; later: round average"], False),
]

OUTPUTS = [
    ("Pick Values File", "Calc 27", "site/data/pick-values.json", ["Group values, curves by season,", "values by slot, picks, sources"], True),
]

FEATURES = [
    ("How Pick Values Work", ["Group table with ranges, total WAR", "and season WAR charts, value by", "slot, method and source credits"]),
]

RUNS = [
    ("By hand, once", "history-fetch and rookie-adp-fetch write the history records and the rookie order"),
    ("By hand, yearly", "pick-values rebuilds the model from committed records; python -m ffapp build exports it"),
]

COLS = [
    ("1. WHERE IT COMES FROM", "Fetched once, by hand", "g1", 250),
    ("2. WHERE IT IS STORED", "Records in git", "g2", 270),
    ("3. HOW IT IS CALCULATED", "In this order, when the model is rebuilt", "g3", 290),
    ("4. WHAT IT PRODUCES", "Derived data, deployed with the site", "g4", 310),
    ("5. WHERE IT SHOWS", "fantasyfoosball.net", "g5", 300),
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
           f'aria-labelledby="pv-t" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
           f"<style>{STYLE}</style>", f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           '<title id="pv-t">How the rookie pick values are made: their sources, where the data is stored, the calculations in order, '
           'the pick values file and the page that shows it</title>',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" class="ah"/></marker></defs>',
           text(LEFT, 34, "HOW THE ROOKIE PICK VALUES ARE MADE", "gl")]
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
