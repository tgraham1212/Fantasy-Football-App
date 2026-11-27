"""Draw docs/images/simulation/diagram.svg: where the simulation's data comes from, where it is stored,
how the calculations use it and which features show the result.

Run after changing a source, a stored path, a calculation or a feature that shows Forecasts:
    python -X utf8 tools/simulation_diagram.py
The wording here must match docs/simulation.md; "Calc N" is section N of Calculations.txt.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "simulation" / "diagram.svg"

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
    ("Sleeper: League Data", "", "", ["Rosters, lineups, matchups, schedule,", "playoff brackets, scoring settings,", "transactions"], False),
    ("Sleeper: Projections", "", "", ["Each player's expected stat line for a", "week (Rotowire via Sleeper)"], False),
    ("Sleeper: Stats", "", "", ["Every player's actual stat line;", "corrections replace the old line"], False),
    ("ESPN Scoreboard", "", "", ["NFL kickoffs, quarter and clock,", "final scores"], False),
    ("config/leagues.yaml", "", "", ["Runs per Forecast (10,000), scoring", "overrides, replacement settings"], False),
]

STORED = [
    ("League Data", "", "data/leagues/", ["One folder per league and season"], False),
    ("Projections", "", "data/projections/", ["Current and earlier weeks"], False),
    ("Future Projections", "", "data/projections-future/", ["Weeks after the current one"], True),
    ("Stats", "", "data/stats/", ["Played weeks, kept forever"], False),
    ("NFL Schedule", "", "data/nfl/  +  data/nfl-live/", ["Kickoffs and finals; live clocks", "in the rebuilt copy"], False),
    ("Replacement Levels", "Calc 14", "data/replacement/", ["Waiver-level points per position", "and week, from free agents"], True),
    ("Roster Drift Fit", "Calc 6", "data/model/", ["How much of a team's edge", "survives k weeks ahead"], True),
]

CALCS = [
    ("Fantasy Points", "Calc 1", "", ["Each stat x what the league pays", "for it, per league"], False),
    ("Noise Pools", "Calc 4", "", ["Actual minus projected points, by", "position and projection band;", "rebuilt in memory each run"], True),
    ("Best Lineup + Floor", "Calc 5", "", ["Best projected starters; an empty", "slot is worth replacement level"], False),
    ("Roster Drift", "Calc 6", "", ["Shrinks each team's edge and adds", "spread the further ahead a week is"], False),
    ("Season Simulation", "Calc 7, 8", "", ["The rest of the season 10,000 times:", "score = projection + drawn miss;", "standings, playoff and losers brackets"], False),
    ("Live Adjustment", "Calc 12", "", ["In a game: points so far + projection", "for the time left, spread shrinking"], False),
]

OUTPUTS = [
    ("Forecast Outcomes", "Calc 9", "data/odds/<league>/<season>/", ["asof_NN.json: one per completed week", "live.json: the current week (rebuilt)", "slates_NN.json: after each slate;", "upcoming weeks: every pair's win share"], False),
    ("Game Forecasts", "Calc 10", "data/games/  +  data/games-derived/", ["Win probability and scores per game;", "a log frozen at kickoff and a", "Forecast of record per final week"], False),
    ("Lineup Views", "Calc 11", "data/games-derived/", ["Model lineup vs. the starters used;", "lineup choices in points"], True),
    ("Win Probability Added", "Calc 13", "data/games-derived/", ["How far each player's score moved", "the team's win probability"], True),
    ("Live Bundle", "", "Cloudflare KV (relay)", ["The hot run's current-week Forecast", "and game cards, every 15 min or", "back to back during games"], True),
    ("Calibration", "Calc 18", "data/calibration/", ["Every finished season replayed; run", "on demand (python -m ffapp calibrate)"], False),
]

FEATURES = [
    ("Forecasts Page", ["Probability of the playoffs, a bye,", "the final, the title and the losers", "bracket; projected record; weekly", "history chart"]),
    ("Games Page", ["Win probability, projected scores", "and score spread per game; Model |", "Actual lineups, lineup choices and", "WPA tags; live swaps from the bundle"]),
    ("Managers Page", ["Team News: a story when a team's", "playoff probability moves sharply", "between weeks"]),
    ("Calibration Page", ["How often results landed inside", "the Forecast ranges, by season,", "game and score"]),
    ("League Page", ["Strength of Schedule: upcoming", "weeks' projected scores and every", "pair's win share (Calc 24)"]),
]

RUNS = [
    ("Cold run", "every 15 min in season, daily off-season: every calculation, commits changed records, deploys the site"),
    ("Hot run", "current week only: Live Adjustment and Game Forecasts into the live bundle; never commits"),
    ("Calibration", "on demand: replays every finished season through the same simulation"),
]

COLS = [
    ("1. WHERE IT COMES FROM", "Fetched by each cold run", "g1", 250),
    ("2. WHERE IT IS STORED", "Records in git; rebuilt files in the build cache", "g2", 270),
    ("3. HOW IT IS CALCULATED", "In this order, every simulating run", "g3", 290),
    ("4. WHAT IT PRODUCES", "Forecasts and where they are kept", "g4", 300),
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
           f'aria-labelledby="sim-t" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
           f"<style>{STYLE}</style>", f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
           '<title id="sim-t">How the simulation works: its sources, where the data is stored, the calculations in order, '
           'what they produce and the pages that show it</title>',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path d="M0 0 L10 5 L0 10 z" class="ah"/></marker></defs>',
           text(LEFT, 34, "HOW THE SIMULATION WORKS", "gl")]
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
