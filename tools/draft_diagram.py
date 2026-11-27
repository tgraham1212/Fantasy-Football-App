"""Draw docs/images/draft/diagram.svg: where the League page's Draft tab comes from, where the data is
stored, how the draft grades are calculated and where they show.

Run after changing a source, a stored path, a calculation or what the Draft tab shows:
    python -X utf8 tools/draft_diagram.py
The wording here must match docs/draft.md; "Calc N" is section N of Calculations.txt.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "draft" / "diagram.svg"

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
    ("Sleeper: Drafts", "", "", ["The draft named in each season's", "league settings: picks, keepers and", "traded picks (until complete)"], False),
    ("Sleeper: ADP", "", "", ["Preseason half-PPR and dynasty", "half-PPR ADP, once a season's", "drafts are complete"], False),
    ("Player WAR and Stats", "Calc 2, 16", "", ["Each Player's WAR per season; weekly", "stats for games played and each", "NFL team's games"], False),
    ("nflverse: Injury Reports", "", "", ["Weekly IR, PUP and Out statuses by", "Sleeper id (completed seasons once,", "the current one daily at most)"], False),
    ("League Configuration", "", "", ["The redraft league's keepers from", "2025 on, by Sleeper id"], False),
]

STORED = [
    ("Drafts", "", "data/leagues/<league>/<season>/", ["draft.json: the draft, picks and", "traded picks as fetched"], False),
    ("ADP", "", "data/adp/<season>.json", ["Position and the two ADP figures"], False),
    ("WAR and Stats", "Calc 16", "data/war/, data/stats/", ["WAR rebuilt each run; stats are records"], False),
    ("Injury Reports", "", "data/injury-reports/", ["One file per season, by week"], False),
]

CALCS = [
    ("Steal/Reach", "Calc 25", "", ["Pick minus ADP (redraft) or ADP rank", "(rookie draft); +/-12 or +/-6 picks;", "best RB/WR left is never a reach"], False),
    ("Slot WAR", "Calc 25", "", ["Mean window WAR of picks within 6", "(redraft) or 3 slots (rookie draft);", "scaled while the window is in progress"], False),
    ("Hit/Bust and Unlucky", "Calc 25", "", ["WAR minus slot WAR: +/-0.75 or +/-1.0;", "over half his team's games missed", "injured (IR, PUP, Out): Unlucky"], False),
    ("Keepers (Redraft)", "Calc 25", "", ["Kept all season by the drafting", "Manager: eligible at one round higher;", "kept this year: a 1st; never a third"], False),
    ("Managers Summary", "Calc 25", "", ["Per draft and all drafts: picks, mean", "ADP difference and WAR above slot,", "total WAR, best pick, unlucky picks"], False),
]

OUTPUTS = [
    ("Draft File", "Calc 25", "site/data/<league>/draft.json", ["Every stored draft's graded picks", "and both Managers summaries"], True),
]

FEATURES = [
    ("League Page: Draft", ["Board: rounds by slots, position", "colours, Draft Day | Results badges", "Table: every pick, ranks, WAR,", "Slot WAR, Hit/Bust, Games Played", "Managers card; Keeper Eligible matrix"]),
    ("Managers Page: Roster Card", ["Gold KE badge on keeper-eligible", "Players (redraft)"]),
]

RUNS = [
    ("Sync", "every cold run fetches a draft until it is complete, and each season's ADP once its drafts are complete"),
    ("Build", "python -m ffapp build (and every cold run's export) writes the draft file from the stored data"),
]

COLS = [
    ("1. WHERE IT COMES FROM", "Fetched by each cold run", "g1", 250),
    ("2. WHERE IT IS STORED", "Records in git; rebuilt files in the build cache", "g2", 270),
    ("3. HOW IT IS CALCULATED", "In this order, every build", "g3", 290),
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
           f'aria-labelledby="draft-t" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
           f"<style>{STYLE}</style>", f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           '<title id="draft-t">How the draft grades are made: their sources, where the data is stored, the calculations in order, '
           'the draft file and the page that shows it</title>',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" class="ah"/></marker></defs>',
           text(LEFT, 34, "HOW THE DRAFT GRADES ARE MADE", "gl")]
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
