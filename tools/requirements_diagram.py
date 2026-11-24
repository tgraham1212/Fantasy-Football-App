"""Draw the requirements diagrams (docs/requirements.md) from the specs, in SysML requirement-diagram
notation:
- docs/images/requirements/diagram.svg: the needs, each with its requirement count, depth,
  verification mix, gaps and TBRs;
- docs/images/requirements/need-N.svg: one tree per need, a column per level.

Run after any spec change (the feature-docs check fails until the diagrams match the specs):
    python -X utf8 tools/requirements_diagram.py
The parser is tools/requirements_model.py, shared with the requirements check.
"""
from __future__ import annotations

import sys
import textwrap
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requirements_model as model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "docs" / "images" / "requirements"
OUT = DIR / "diagram.svg"

STYLE = """
text { font-family: 'Segoe UI', system-ui, sans-serif; }
.bg { fill: #ffffff; }
.title { font-size: 20px; font-weight: 700; fill: #14161a; }
.sub { font-size: 12.5px; fill: #4c5058; }
.col { font-size: 11.5px; font-weight: 700; fill: #6b6f78; letter-spacing: 0.08em; }
.req { fill: #ffffff; stroke: #2b2f36; stroke-width: 1.4; }
.need { fill: #fbf2e1; stroke: #c08a2c; stroke-width: 1.6; }
.ext { fill: #f4f4f2; stroke: #9a9890; stroke-width: 1.2; stroke-dasharray: 4 3; }
.hdr { fill: #eef1f6; } .needhdr { fill: #f5e2bd; } .exthdr { fill: #e9e8e4; }
.ster { font-size: 10.5px; fill: #4c5058; font-style: italic; }
.rid { font-size: 12.5px; font-weight: 800; fill: #14161a; font-family: ui-monospace, Consolas, monospace; }
.rname { font-size: 12.5px; font-weight: 700; fill: #14161a; }
.rtext { font-size: 11px; fill: #2b2f36; }
.spec { font-size: 10.5px; fill: #3c67a8; font-family: ui-monospace, Consolas, monospace; }
.tc { fill: #e8f5ea; stroke: #4f9a5c; stroke-width: 1.3; }
.insp { fill: #e8f0fb; stroke: #4f7cc0; stroke-width: 1.3; }
.anal { fill: #f1ecfa; stroke: #8a6fc0; stroke-width: 1.3; }
.gap { fill: #fdecec; stroke: #c0392b; stroke-width: 1.3; stroke-dasharray: 5 3; }
.none { fill: #fdecec; stroke: #c0392b; stroke-width: 1.3; }
.tctext { font-size: 10.5px; fill: #14161a; font-family: ui-monospace, Consolas, monospace; }
.tbr { fill: #b4530b; } .tbrt { font-size: 10px; font-weight: 800; fill: #ffffff; }
.derive { fill: none; stroke: #2b2f36; stroke-width: 1.4; stroke-dasharray: 6 3; }
.trace { fill: none; stroke: #8a8880; stroke-width: 1.4; stroke-dasharray: 2 3; }
.verify { fill: none; stroke: #4f9a5c; stroke-width: 1.3; stroke-dasharray: 6 3; }
.vgap { fill: none; stroke: #c0392b; stroke-width: 1.3; stroke-dasharray: 6 3; }
.elab { font-size: 10px; fill: #4c5058; font-style: italic; }
.lg { font-size: 11.5px; fill: #2b2f36; }
.nnum { font-size: 22px; font-weight: 800; fill: #b4530b; font-family: ui-monospace, Consolas, monospace; }
.nname { font-size: 14px; font-weight: 700; fill: #14161a; }
.stat { font-size: 11.5px; fill: #2b2f36; } .statn { font-weight: 800; } .gapn { font-weight: 800; fill: #c0392b; }
.bt { fill: #4f9a5c; } .bi { fill: #4f7cc0; } .ba { fill: #8a6fc0; } .bd { fill: #2fa3a3; } .bgp { fill: #c0392b; } .bempty { fill: #e4e2dc; }
"""

MARKERS = "".join(
    f'<marker id="{mid}" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="11" markerHeight="11" orient="auto">'
    f'<path d="M1,1 L11,6 L1,11" fill="none" stroke="{col}" stroke-width="1.4"/></marker>'
    for mid, col in (("open", "#2b2f36"), ("openg", "#8a8880"), ("openv", "#4f9a5c"), ("openr", "#c0392b")))

W, H, CW, ROWH, TCW = 260, 118, 310, 134, 320


def key(rid: str) -> list[int]:
    return [int(x) for x in rid.split(".")]


def spec_label(r: model.Req) -> str:
    return r.spec if r.source == "main" else f"{r.spec} · proposed"


def plain(text: str) -> str:
    return " ".join(text.replace("`", "").replace("**", "").split())


def svg_open(width: int, height: int) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
            f"<style>{STYLE}</style>", f"<defs>{MARKERS}</defs>", f'<rect class="bg" width="{width}" height="{height}"/>']


def req_box(x: float, y: float, r: model.Req, kind: str) -> str:
    cls, hdr = {"req": ("req", "hdr"), "need": ("need", "needhdr"), "ext": ("ext", "exthdr")}[kind]
    s = [f'<rect class="{cls}" x="{x}" y="{y}" width="{W}" height="{H}" rx="3"/>',
         f'<rect class="{hdr}" x="{x + 0.7}" y="{y + 0.7}" width="{W - 1.4}" height="34" rx="2.5"/>',
         f'<text class="ster" x="{x + W / 2}" y="{y + 13}" text-anchor="middle">{"«need»" if r.is_need else "«requirement»"}</text>']
    title = r.title if len(r.title) <= 30 else r.title[:29] + "…"
    s.append(f'<text x="{x + W / 2}" y="{y + 28}" text-anchor="middle"><tspan class="rid">{escape(r.rid or "")}</tspan>'
             f'<tspan class="rname" dx="6">{escape(title)}</tspan></text>')
    lines = textwrap.wrap(plain(r.statement), 46)
    if len(lines) > 4:
        lines = lines[:4]
        lines[3] = lines[3][:43] + "…"
    for i, line in enumerate(lines):
        s.append(f'<text class="rtext" x="{x + 8}" y="{y + 50 + i * 14}">{escape(line)}</text>')
    s.append(f'<text class="spec" x="{x + 8}" y="{y + H - 7}">{escape(spec_label(r))}</text>')
    if r.fields.get("TBR"):
        s.append(f'<rect class="tbr" x="{x + W - 38}" y="{y + H - 19}" width="32" height="14" rx="7"/>'
                 f'<text class="tbrt" x="{x + W - 22}" y="{y + H - 8.5}" text-anchor="middle">TBR</text>')
    return "\n".join(s)


def verify_box(x: float, y: float, r: model.Req) -> tuple[str, str, str]:
    """(svg, edge class, marker) for a requirement's verification."""
    items = r.verifications()
    if not items:
        return (f'<rect class="none" x="{x}" y="{y}" width="{TCW}" height="60" rx="3"/>'
                f'<text class="ster" x="{x + 8}" y="{y + 15}">no verification</text>'
                f'<text class="tctext" x="{x + 8}" y="{y + 32}">Verified by line missing</text>', "vgap", "openr")
    first = items[0][0]
    cls, ster = {"Test": ("tc", "«testCase»"), "Inspection": ("insp", "«inspection»"), "Analysis": ("anal", "«analysis»"),
                 "Demonstration": ("anal", "«demonstration»"), "Gap": ("gap", "«gap»")}.get(first, ("none", "«unknown»"))
    s = [f'<rect class="{cls}" x="{x}" y="{y}" width="{TCW}" height="60" rx="3"/>',
         f'<text class="ster" x="{x + 8}" y="{y + 15}">{ster}</text>']
    text = []
    for method, evidence in items:
        evidence = plain(evidence).replace("tests/", "")
        text.append(evidence if method == first else f"{method}: {evidence}")
    for i, line in enumerate(textwrap.wrap("; ".join(text), 46)[:2]):
        s.append(f'<text class="tctext" x="{x + 8}" y="{y + 32 + i * 14}">{escape(line)}</text>')
    return "\n".join(s), ("vgap" if first == "Gap" else "verify"), ("openr" if first == "Gap" else "openv")


def tree_svg(need: model.Req, reqs: list[model.Req], ids: dict) -> str:
    # the tree follows primary parents; other parents are drawn as «trace» to boxes outside it
    prim: dict[str, list[model.Req]] = {}
    for r in reqs:
        if r.rid and r.parents and r.parents[0] in ids:
            prim.setdefault(r.parents[0], []).append(r)
    order: list[model.Req] = []

    def walk(r: model.Req):
        order.append(r)
        for c in sorted(prim.get(r.rid, []), key=lambda c: key(c.rid)):
            walk(c)

    walk(need)
    placed = {r.rid for r in order}
    level = {r.rid: r.rid.count(".") for r in order}
    maxlvl = max(level.values())
    x0, y0 = 40, 150
    pos = {r.rid: (x0 + level[r.rid] * CW, y0 + i * ROWH) for i, r in enumerate(order)}
    tcx = x0 + (maxlvl + 1) * CW + 20

    ext: list[tuple[model.Req, str, str]] = []  # (outside requirement, requirement in tree, "in"/"out")
    for r in order:
        for p in r.parents[1:]:
            if p in ids and p not in placed:
                ext.append((ids[p], r.rid, "out"))
    for r in reqs:
        if r.rid and r.rid not in placed:
            for p in r.parents[1:]:
                if p in placed:
                    ext.append((r, p, "in"))
    ext_y = y0 + len(order) * ROWH + 50
    width = max(tcx + TCW + 40, x0 + CW + max(len({o.rid for o, _, _ in ext}), 1) * (W + 50) + 40)
    height = ext_y + (H + 70 if ext else 0) + 70
    count = len(order) - 1
    s = svg_open(width, height)
    s.append(f'<text class="title" x="40" y="44">Requirements Diagram: Need {need.rid}, {escape(need.title)}</text>')
    s.append(f'<text class="sub" x="40" y="66">{count} requirement{"s" if count != 1 else ""} derived from need {need.rid} · '
             'drawn from the specs by tools/requirements_diagram.py · level = number of dots in the ID</text>')
    for lvl in range(maxlvl + 1):
        s.append(f'<text class="col" x="{x0 + lvl * CW}" y="{y0 - 18}">{"NEED · LEVEL 0" if lvl == 0 else f"LEVEL {lvl}"}</text>')
    if count:
        s.append(f'<text class="col" x="{tcx}" y="{y0 - 18}">VERIFIED BY</text>')
    else:
        s.append(f'<text class="sub" x="{x0 + CW}" y="{y0 + 60}">No requirement traces to this need yet.</text>')
    # «deriveReqt» to the primary parent
    for r in order[1:]:
        cx, cy = pos[r.rid]
        px, py = pos[r.parents[0]]
        s.append(f'<path class="derive" d="M{cx},{cy + H / 2} H{cx - 25} V{py + H / 2} H{px + W}" marker-end="url(#open)"/>')
    if len(order) > 1:
        cx, cy = pos[order[1].rid]
        s.append(f'<text class="elab" x="{cx - 28}" y="{cy + H / 2 - 6}" text-anchor="end">«deriveReqt»</text>')
    # «verify»
    for i, r in enumerate(order[1:]):
        x, y = pos[r.rid]
        box, ecls, mk = verify_box(tcx, y + 28, r)
        s.append(box)
        s.append(f'<path class="{ecls}" d="M{tcx},{y + 58} H{x + W}" marker-end="url(#{mk})"/>')
        if i == 0:
            s.append(f'<text class="elab" x="{tcx - 8}" y="{y + 52}" text-anchor="end">«verify»</text>')
    for r in order:
        x, y = pos[r.rid]
        s.append(req_box(x, y, r, "need" if r.is_need else "req"))
    # «trace» to and from other branches
    if ext:
        s.append(f'<text class="col" x="{x0}" y="{ext_y - 16}">OTHER BRANCHES · «trace» (extra parents)</text>')
    slot: dict[str, int] = {}  # one box per outside requirement, however many links it has
    for i, (o, inner, direction) in enumerate(ext):
        first = o.rid not in slot
        slot.setdefault(o.rid, len(slot))
        ex = x0 + CW + slot[o.rid] * (W + 50)
        if first:
            s.append(req_box(ex, ext_y, o, "ext"))
        ix, iy = pos[inner]
        lane = iy + H + 8 + (i % 3) * 5
        if direction == "out":   # the tree requirement lists the outside one as an extra parent
            s.append(f'<path class="trace" d="M{ix + W / 2 + 20},{iy + H} V{lane} H{ex + W / 2} V{ext_y}" marker-end="url(#openg)"/>')
        else:                    # the outside requirement lists the tree one as an extra parent
            s.append(f'<path class="trace" d="M{ex + W / 2},{ext_y} V{lane} H{ix + W / 2 - 20} V{iy + H}" marker-end="url(#openg)"/>')
    ly = height - 40
    for i, (cls, mk, lab) in enumerate((("derive", "open", "«deriveReqt»: primary parent (sets the ID)"),
                                        ("trace", "openg", "«trace»: extra parent"),
                                        ("verify", "openv", "«verify»: test, inspection or analysis"),
                                        ("vgap", "openr", "verification gap"))):
        lx = x0 + i * 320
        s.append(f'<path class="{cls}" d="M{lx},{ly} H{lx + 46}" marker-end="url(#{mk})"/>'
                 f'<text class="lg" x="{lx + 56}" y="{ly + 4}">{escape(lab)}</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


def need_stats(need: model.Req, reqs: list[model.Req], ids: dict) -> dict:
    kids = model.children(reqs)
    below = {r.rid: r for _, r in model.descendants(need.rid, kids) if r.rid}
    mix = {"Test": 0, "Inspection": 0, "Analysis": 0, "Demonstration": 0, "Gap": 0}
    for r in below.values():
        items = r.verifications()
        mix[items[0][0] if items and items[0][0] in mix else "Gap"] += 1
    depth = max((r.rid.count(".") for r in below.values()), default=0)
    tbr = sum(1 for r in below.values() if r.fields.get("TBR"))
    return {"count": len(below), "depth": depth, "mix": mix, "tbr": tbr}


def overview_svg(needs: list[model.Req], reqs: list[model.Req], ids: dict) -> str:
    cols, bw, bh, gx, gy = 4, 300, 172, 24, 24
    rows = -(-len(needs) // cols)
    x0, y0 = 40, 110
    width = x0 * 2 + cols * bw + (cols - 1) * gx
    height = y0 + rows * (bh + gy) + 100
    s = svg_open(width, height)
    s.append('<text class="title" x="40" y="44">Requirements Overview: The Needs</text>')
    s.append('<text class="sub" x="40" y="66">Each need with the requirements derived from it and how they are verified · '
             'one tree per need in need-N.svg</text>')
    for i, n in enumerate(needs):
        st = need_stats(n, reqs, ids)
        x = x0 + (i % cols) * (bw + gx)
        y = y0 + (i // cols) * (bh + gy)
        s.append(f'<rect class="need" x="{x}" y="{y}" width="{bw}" height="{bh}" rx="4"/>')
        s.append(f'<text class="ster" x="{x + 12}" y="{y + 18}">«need»</text>')
        s.append(f'<text class="nnum" x="{x + 12}" y="{y + 46}">{n.rid}</text>'
                 f'<text class="nname" x="{x + 18 + 14 * len(n.rid)}" y="{y + 44}">{escape(n.title)}</text>')
        s.append(f'<text class="stat" x="{x + 12}" y="{y + 70}"><tspan class="statn">{st["count"]}</tspan> requirements · '
                 f'<tspan class="statn">{st["depth"]}</tspan> levels deep</text>')
        bx, by, bwid = x + 12, y + 82, bw - 24
        if st["count"]:
            cx = bx
            for name, cls in (("Test", "bt"), ("Inspection", "bi"), ("Analysis", "ba"), ("Demonstration", "bd"), ("Gap", "bgp")):
                v = st["mix"][name]
                if v:
                    w = bwid * v / st["count"]
                    s.append(f'<rect class="{cls}" x="{cx:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="12" rx="2"/>')
                    cx += w
        else:
            s.append(f'<rect class="bempty" x="{bx}" y="{by}" width="{bwid}" height="12" rx="2"/>')
        m = st["mix"]
        s.append(f'<text class="stat" x="{x + 12}" y="{y + 114}">Test {m["Test"]} · Inspection {m["Inspection"]} · '
                 f'Analysis {m["Analysis"]} · Demo {m["Demonstration"]}</text>')
        gap = f'<tspan class="gapn">{m["Gap"]} gap{"s" if m["Gap"] != 1 else ""}</tspan>' if m["Gap"] else "0 gaps"
        s.append(f'<text class="stat" x="{x + 12}" y="{y + 134}">{gap} · {st["tbr"]} TBR</text>')
        s.append(f'<text class="spec" x="{x + 12}" y="{y + 158}">need-{n.rid}.svg</text>')
    ly = y0 + rows * (bh + gy) + 24
    for i, (cls, lab) in enumerate((("bt", "Test"), ("bi", "Inspection"), ("ba", "Analysis"), ("bd", "Demonstration"), ("bgp", "Gap"))):
        lx = x0 + i * 170
        s.append(f'<rect class="{cls}" x="{lx}" y="{ly - 10}" width="22" height="12" rx="2"/><text class="lg" x="{lx + 30}" y="{ly}">{lab}</text>')
    total = len([r for r in reqs if not r.is_need])
    numbered = len([r for r in reqs if not r.is_need and r.rid])
    s.append(f'<text class="sub" x="40" y="{ly + 32}">{numbered} of {total} requirements numbered and placed in the tree; '
             f'{total - numbered} not yet brought to the standard.</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"


def build_all() -> dict[Path, str]:
    reqs = model.load(ROOT)
    ids = model.index(reqs)
    needs = sorted((r for r in reqs if r.is_need and r.rid), key=lambda r: key(r.rid))
    out = {OUT: overview_svg(needs, reqs, ids)}
    for n in needs:
        out[DIR / f"need-{n.rid}.svg"] = tree_svg(n, reqs, ids)
    return out


def build() -> str:
    return build_all()[OUT]


if __name__ == "__main__":
    DIR.mkdir(parents=True, exist_ok=True)
    files = build_all()
    for stale in DIR.glob("need-*.svg"):
        if stale not in files:
            stale.unlink()
    for path, svg in files.items():
        path.write_text(svg, encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} diagrams to {DIR.relative_to(ROOT)}")
