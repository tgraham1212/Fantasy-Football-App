"""Draw docs/images/refresh-modes/diagram.svg: the three refresh modes and what one hot and one cold run do.

Run after changing a mode, a trigger or a run's steps:  python -X utf8 tools/refresh_modes_diagram.py
The wording here must match docs/refresh-modes.md.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "refresh-modes" / "diagram.svg"
W, H = 1392, 856

STYLE = """
.grp-off { fill: #efeeeb; stroke: #8c8a84; } .grp-quiet { fill: #eef1f6; stroke: #93a0b8; }
.grp-live { fill: #e8f5ea; stroke: #4f9a5c; } .grp-hot { fill: #fbf2e1; stroke: #c08a2c; }
.grp-cold { fill: #e8f0fb; stroke: #4f7cc0; } .grp { stroke-width: 1.5; }
.gl { font-weight: 700; font-size: 13px; letter-spacing: 0.06em; fill: #4c5058; }
.st { fill: #ffffff; stroke: #2b2f36; stroke-width: 1.4; }
.mt { font-weight: 800; font-size: 15px; fill: #14161a; } .mc { font-size: 12px; fill: #4c5058; font-family: ui-monospace, Consolas, monospace; }
.k { font-weight: 700; font-size: 12.5px; fill: #14161a; } .v { font-size: 12.5px; fill: #2b2f36; }
.stt { font-weight: 700; font-size: 12.5px; fill: #14161a; } .sd { font-size: 11.5px; fill: #4c5058; }
.e { fill: none; stroke: #2b2f36; stroke-width: 1.5; } .e.dash { stroke: #b4530b; stroke-dasharray: 6 4; stroke-width: 1.6; }
.bd { fill: #ffffff; stroke: #2b2f36; stroke-width: 1.2; }
.bt { font-size: 10.5px; font-weight: 800; fill: #14161a; text-anchor: middle; dominant-baseline: central; }
.lg { font-size: 12.5px; fill: #2b2f36; } .lgn { font-weight: 800; }
.note { font-size: 12px; fill: #4c5058; font-style: italic; } .dl { font-size: 11.5px; fill: #b4530b; font-weight: 700; }
.ah { fill: #2b2f36; } .ah-s { fill: #b4530b; }
"""

# Mode boxes: (css group, title, code, rows of (label, value lines)).
MODES = [
    ("grp-off", "Off-season", "offseason", [
        ("When", ["Both leagues' seasons are over, until the", "next NFL season's week 1"]),
        ("Hot", ["Off"]),
        ("Cold", ["Daily at 11:00 UTC"]),
        ("Button", ["Starts a cold run"]),
        ("Page", ["Static files only"]),
    ]),
    ("grp-quiet", "Quiet", "quiet", [
        ("When", ["In season, no NFL game in progress"]),
        ("Hot", ["Every 15 min: current-week forecast", "and game cards"]),
        ("Cold", ["Every 15 min; commits and deploys", "only when something changed"]),
        ("Button", ["Starts a hot run and a cold run"]),
        ("Page", ["Newer of the live bundle and static files"]),
    ]),
    ("grp-live", "Live", "live", [
        ("When", ["An NFL game has kicked off and is not final"]),
        ("Hot", ["Back to back: the clock starts one each", "minute when none is running (1-1.5 min)"]),
        ("Cold", ["Every 15 min, no simulation; commits", "only when a record changed"]),
        ("Button", ["Held: live updates are already on"]),
        ("Page", ["Live bundle, checked every 30 s"]),
    ]),
]

TRANSITIONS = [
    ("1", "Off-season to Quiet", "the NFL season's week 1 begins (Sleeper's NFL state)"),
    ("2", "Quiet to Live", "a game's kickoff time passes"),
    ("3", "Live to Quiet", "every game that kicked off is final (the last slate goes final)"),
    ("4", "Quiet to Off-season", "both leagues' championship weeks are scored"),
    ("5", "Live to Live", "a slate goes final: a cold run saves that slate's forecast to history"),
]

HOT = [
    ("Clock", ["Each minute the Worker", "works out the mode; is", "a hot run due?"]),
    ("Already running?", ["Yes: skip this minute.", "No: start one."]),
    ("Restore inputs", ["The latest cold run's", "build cache (ratings,", "projections, WAR...)"]),
    ("Live data", ["Current-week matchups", "and the NFL scoreboard"]),
    ("Simulate + cards", ["Live week, 10,000 runs;", "this week's game cards"]),
    ("One KV write", ["Bundle: forecasts, cards,", "game status, time"]),
]
COLD = [
    ("Trigger", ["15 min, button, slate", "final, or daily"]),
    ("Full sync", ["Rosters, moves, stats,", "projections, schedule"]),
    ("Records", ["Game log, slate forecasts,", "scored weeks, frozen", "projections"]),
    ("Rebuild derived", ["Ratings, replacement,", "WAR, site export"]),
    ("Save build cache", ["The newest one is what", "hot runs restore"]),
    ("Changed?", ["No: end.", "Yes: commit records,", "deploy Pages"]),
]


def text(x, y, s, cls, anchor="start"):
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>'


def badge(x, y, n):
    return f'<circle cx="{x}" cy="{y}" r="11" class="bd"/><text x="{x}" y="{y}" class="bt">{n}</text>'


def arrow(d, dash=False):
    return f'<path d="{d}" class="e{" dash" if dash else ""}" marker-end="url(#{"s" if dash else "a"})"/>'


def mode_box(x, y, w, h, mode):
    grp, title, code, rows = mode
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" class="grp {grp}"/>',
           text(x + 16, y + 28, title, "mt"), text(x + w - 16, y + 28, code, "mc", "end")]
    cy = y + 56
    for label, lines in rows:
        out.append(text(x + 16, cy, label, "k"))
        for i, line in enumerate(lines):
            out.append(text(x + 84, cy + i * 17, line, "v"))
        cy += 17 * len(lines) + 9
    return out


def step(x, y, w, h, title, lines):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" class="st"/>', text(x + 12, y + 22, title, "stt")]
    out += [text(x + 12, y + 41 + i * 16, line, "sd") for i, line in enumerate(lines)]
    return out


def lane(y, label, cls, steps):
    sx, sw, sh, gap = 40, 190, 92, 30
    out = [f'<rect x="24" y="{y}" width="{W - 48}" height="150" rx="10" class="grp {cls}"/>', text(40, y + 24, label, "gl")]
    top = y + 40
    for i, (title, lines) in enumerate(steps):
        x = sx + i * (sw + gap)
        out += step(x, top, sw, sh, title, lines)
        if i:
            out.append(arrow(f"M{x - gap + 2} {top + sh / 2} H{x - 3}"))
    return out


def build():
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
             f'aria-labelledby="rm-t" font-family="Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">',
             f"<style>{STYLE}</style>", f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
             '<title id="rm-t">Refresh modes: off-season, quiet and live, with their transitions, and the steps of one hot run and one cold run</title>',
             '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0 0 L10 5 L0 10 z" class="ah"/></marker>'
             '<marker id="s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0 0 L10 5 L0 10 z" class="ah-s"/></marker></defs>']

    # Panel A: modes.
    parts.append(text(24, 32, "REFRESH MODES", "gl"))
    bw, bh, by, gap = 400, 262, 84, 72
    xs = [24, 24 + bw + gap, 24 + 2 * (bw + gap)]
    for x, mode in zip(xs, MODES):
        parts += mode_box(x, by, bw, bh, mode)
    for i, (fwd, back) in enumerate((("1", "4"), ("2", "3"))):
        x0, x1 = xs[i] + bw, xs[i + 1]
        parts.append(arrow(f"M{x0 + 2} {by + 70} H{x1 - 3}"))
        parts.append(badge((x0 + x1) / 2, by + 52, fwd))
        parts.append(arrow(f"M{x1 - 2} {by + 200} H{x0 + 3}"))
        parts.append(badge((x0 + x1) / 2, by + 182, back))
    lx = xs[2]
    parts.append(arrow(f"M{lx + 150} {by - 2} C{lx + 170} {by - 46} {lx + 250} {by - 46} {lx + 270} {by - 3}"))
    parts.append(badge(lx + 210, by - 36, "5"))

    ly = by + bh + 34
    for i, (n, name, trigger) in enumerate(TRANSITIONS):
        col, row = divmod(i, 3)
        x, y = 24 + col * 680, ly + row * 24
        parts.append(badge(x + 11, y - 4, n))
        parts.append(f'<text x="{x + 30}" y="{y}" class="lg"><tspan class="lgn">{escape(name)}:</tspan> {escape(trigger)}</text>')

    # Panel B: the runs.
    hy = ly + 96
    parts += lane(hy, "ONE HOT RUN  (Cloudflare Worker clock, GitHub Actions job, writes Cloudflare KV; never commits)", "grp-hot", HOT)
    cy = hy + 196
    parts += lane(cy, "ONE COLD RUN  (GitHub Actions, writes git and GitHub Pages; never reads the live bundle)", "grp-cold", COLD)
    # Cold build cache feeds the hot run's inputs.
    cache_x = 40 + 4 * 220 + 95
    restore_x = 40 + 2 * 220 + 95
    parts.append(arrow(f"M{cache_x} {cy + 40} V{cy - 16} H{restore_x} V{hy + 136}", dash=True))
    parts.append(text(restore_x + 110, cy - 22, "build cache: the inputs every hot run starts from", "dl"))
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
