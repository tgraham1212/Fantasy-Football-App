"""What a change to one requirement may affect: every requirement and need above it (each parent
chain, primary parent first) and below it, with how each is verified.

Run before editing a requirement:
    python -X utf8 tools/requirements_impact.py 1.1.2
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import requirements_model as model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def line(r: model.Req) -> str:
    how = "Children" if r.is_need else (r.verified or "no Verified by")
    return f"{r.rid or '(no ID)'} {r.title}  [{r.spec}]  Verified by: {how}"


def report(root: Path, rid: str) -> str:
    reqs = model.load(root)
    ids = model.index(reqs)
    if rid not in ids:
        raise SystemExit(f"no requirement with ID {rid}")
    r = ids[rid]
    out = [line(r)]
    if r.fields.get("TBR"):
        out.append(f"  TBR: {r.fields['TBR']}")
    out.append("")
    out.append("Above (parent chains up to the needs):")
    above = model.ancestors(rid, ids)
    out += [("  " * depth) + line(a) for depth, a in above] or ["  (none: this is a need)"]
    missing = [p for p in r.parents if p not in ids]
    out += [f"  parent {p} does not exist" for p in missing]
    out.append("")
    out.append("Below (requirements that trace to it):")
    below = model.descendants(rid, model.children(reqs))
    out += [("  " * depth) + line(d) for depth, d in below] or ["  (none)"]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -X utf8 tools/requirements_impact.py <ID>")
    print(report(ROOT, sys.argv[1]))
