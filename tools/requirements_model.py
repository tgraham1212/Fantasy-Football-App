"""The requirement tree, read from the specs (the requirements standard: project-standards 10.x).

Parses every main spec (openspec/specs/*/spec.md) and the ADDED and MODIFIED requirements of every
active change (openspec/changes/<change>/specs/*/spec.md), and checks them against the standard.
Used by tests/test_requirements.py (the check), tools/requirements_impact.py (what a change to one
requirement may affect) and tools/requirements_diagram.py (the diagrams).

Each requirement looks like:

    ### Requirement: 1.1.2 Real schedule
    The simulation SHALL use ...

    **Rationale:** ...            (optional)
    **Traces to:** 1.1; 2.3       (primary parent first)
    **Verified by:** Test: `tests/test_simulate.py::test_uses_real_pairings`
    **TBR:** ...                  (optional)

Needs (the `needs` spec) are numbered 1, 2, ... and verified by "Children".
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ID_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")
HEADING_RE = re.compile(r"^### Requirement:\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^\*\*(Rationale|Traces to|Verified by|TBR):\*\*\s*(.*)$")
TEST_REF_RE = re.compile(r"`?(tests/[\w/.-]+\.py)::([\w:]+)`?")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
METHODS = ("Test", "Analysis", "Inspection", "Demonstration", "Gap")
MAX_PARENTS = 3


@dataclass
class Req:
    spec: str          # capability, e.g. "playoff-odds-simulation"
    source: str        # "main" or the change name
    heading: str       # the text after "### Requirement:"
    rid: str | None    # "1.1.2", or None when the heading has no ID yet
    title: str         # heading without the ID
    statement: str     # text between the heading and the first field or scenario
    fields: dict = field(default_factory=dict)
    scenarios: int = 0

    @property
    def is_need(self) -> bool:
        return self.spec == "needs"

    @property
    def parents(self) -> list[str]:
        raw = self.fields.get("Traces to", "")
        return [p.strip() for p in raw.split(";") if p.strip()]

    @property
    def label(self) -> str:
        return f"{self.spec} | {self.heading}"

    @property
    def verified(self) -> str:
        return self.fields.get("Verified by", "")

    def verifications(self) -> list[tuple[str, str]]:
        """[(method, evidence)] from the Verified by line."""
        out = []
        for item in re.split(r";\s*(?=(?:%s):)" % "|".join(METHODS), self.verified):
            method, _, evidence = item.partition(":")
            if item.strip():
                out.append((method.strip(), evidence.strip()))
        return out


# ---------- parsing ----------

def _sections(text: str) -> dict[str, str]:
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def parse_requirements(text: str, spec: str, source: str) -> list[Req]:
    reqs, cur, in_body = [], None, False
    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h:
            heading = h.group(1)
            m = ID_RE.match(heading)
            cur = Req(spec, source, heading, m.group(1) if m else None, m.group(2) if m else heading, "")
            reqs.append(cur)
            in_body = True
            continue
        if cur is None:
            continue
        if line.startswith("#### Scenario"):
            cur.scenarios += 1
            in_body = False
            continue
        if line.startswith("#"):
            in_body = False
            continue
        f = FIELD_RE.match(line)
        if f:
            cur.fields[f.group(1)] = f.group(2).strip()
            in_body = False
            continue
        if in_body:
            cur.statement = (cur.statement + "\n" + line).strip()
    return reqs


def load(root: Path) -> list[Req]:
    """Every requirement: main specs, overridden by active changes' ADDED and MODIFIED versions."""
    root = Path(root)
    by_key: dict[tuple[str, str], Req] = {}
    for path in sorted((root / "openspec" / "specs").glob("*/spec.md")):
        for r in parse_requirements(path.read_text(encoding="utf-8"), path.parent.name, "main"):
            by_key[(r.spec, r.heading)] = r
    changes = root / "openspec" / "changes"
    for path in sorted(changes.glob("*/specs/*/spec.md")):
        change = path.parents[2].name
        if change == "archive":
            continue
        secs = _sections(path.read_text(encoding="utf-8"))
        for name in ("ADDED Requirements", "MODIFIED Requirements"):
            for r in parse_requirements(secs.get(name, ""), path.parent.name, change):
                old = by_key.get((r.spec, r.heading))
                if old and old.source == "main" and (old.statement, old.fields) == (r.statement, r.fields):
                    continue  # already synced to the main spec
                by_key[(r.spec, r.heading)] = r
    return list(by_key.values())


def main_specs(root: Path) -> list[str]:
    return sorted(p.parent.name for p in (Path(root) / "openspec" / "specs").glob("*/spec.md"))


def index(reqs: list[Req]) -> dict[str, Req]:
    return {r.rid: r for r in reqs if r.rid}


def children(reqs: list[Req]) -> dict[str, list[Req]]:
    out: dict[str, list[Req]] = {}
    for r in reqs:
        for p in r.parents:
            out.setdefault(p, []).append(r)
    return out


def _table_rows(text: str, heading: str) -> list[list[str]]:
    """Body rows of the first markdown table under a '## heading'."""
    body = _sections(text).get(heading, "")
    rows = []
    for line in body.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:]  # drop the header row


def glossary(root: Path) -> tuple[list[str], list[str]]:
    """(terms, banned terms) from openspec/glossary.md."""
    path = Path(root) / "openspec" / "glossary.md"
    if not path.exists():
        return [], []
    secs = _sections(path.read_text(encoding="utf-8"))
    terms = re.findall(r"^- \*\*(.+?):\*\*", secs.get("Terms", ""), re.M)
    banned = [b.strip() for b in re.findall(r"^- (.+)$", secs.get("Banned Terms", ""), re.M)]
    return terms, banned


def retired_ids(root: Path) -> set[str]:
    path = Path(root) / "openspec" / "retired-requirements.md"
    if not path.exists():
        return set()
    return {row[0] for row in _table_rows(path.read_text(encoding="utf-8"), "Retired IDs") if row and ID_RE.match(row[0] + " x")}


def checklist(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """(requirement inspections by ID or heading, spec reviews by spec) from the inspection checklist."""
    path = Path(root) / "openspec" / "inspection-checklist.md"
    if not path.exists():
        return {}, {}
    text = path.read_text(encoding="utf-8")
    insp = {row[0]: row for row in _table_rows(text, "Requirement Inspections") if row and row[0]}
    reviews = {row[0].strip("`"): row for row in _table_rows(text, "Spec Standard Reviews") if row and row[0]}
    return insp, reviews


def git_last_change(root: Path, rel: str) -> str | None:
    """Date (YYYY-MM-DD) of the last commit that touched a path, or None. None in a shallow clone
    (CI checks out one commit, which would date every file today); the rule runs on full clones."""
    try:
        shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=root,
                                 capture_output=True, text=True, check=True).stdout.strip()
        if shallow == "true":
            return None
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=root,
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except (OSError, subprocess.CalledProcessError):
        return None


# ---------- the check ----------

def _plain(statement: str) -> str:
    return re.sub(r"`[^`]*`", " ", statement)


def _test_exists(root: Path, file: str, name: str) -> bool:
    path = Path(root) / file
    if not path.exists():
        return False
    func = name.split("::")[-1]
    return re.search(rf"^\s*def {re.escape(func)}\(", path.read_text(encoding="utf-8"), re.M) is not None


def check(root: Path, accepted: dict | None = None, last_change=None) -> set[str]:
    """Every finding against the standard, as 'spec | requirement | finding' strings."""
    root = Path(root)
    accepted = accepted or {}
    last_change = last_change or (lambda rel: git_last_change(root, rel))
    reqs = load(root)
    ids = index(reqs)
    kids = children(reqs)
    terms, banned = glossary(root)
    retired = retired_ids(root)
    insp, reviews = checklist(root)
    out: set[str] = set()

    # IDs: present, unique, not retired, numbered under the primary parent
    seen: dict[str, Req] = {}
    for r in reqs:
        if not r.rid:
            out.add(f"{r.label} | no ID")
            continue
        if r.rid in seen:
            out.add(f"{r.label} | duplicate ID {r.rid} (also {seen[r.rid].label})")
        seen[r.rid] = r
        if r.rid in retired:
            out.add(f"{r.label} | reuses retired ID {r.rid}")
        if r.is_need:
            if "." in r.rid:
                out.add(f"{r.label} | need ID {r.rid} is not a single number")
        elif "." not in r.rid:
            out.add(f"{r.label} | ID {r.rid} has no parent part")
        elif r.parents and r.rid.rsplit(".", 1)[0] != r.parents[0]:
            out.add(f"{r.label} | ID {r.rid} does not follow primary parent {r.parents[0]}")

    for r in reqs:
        # one positive SHALL
        shalls = len(re.findall(r"\bSHALL\b", _plain(r.statement)))
        if shalls != 1:
            out.add(f"{r.label} | {shalls} SHALLs")
        if re.search(r"\bSHALL NOT\b", _plain(r.statement)):
            out.add(f"{r.label} | SHALL NOT")
        if r.fields.get("TBR") and not re.search(r"\b\d{4}-\d{2}\b", r.fields["TBR"]):
            out.add(f"{r.label} | TBR without a target date")
        # banned terms
        plain = _plain(r.statement).lower()
        for term in banned:
            if re.search(r"(?<![\w-])" + re.escape(term.lower()) + r"(?![\w-])", plain):
                out.add(f"{r.label} | banned term '{term}'")
        # traces
        if not r.is_need:
            if not r.parents:
                out.add(f"{r.label} | orphan: no Traces to")
            for p in r.parents:
                if p not in ids:
                    out.add(f"{r.label} | orphan: parent '{p}' does not exist")
            if len(r.parents) > MAX_PARENTS and r.rid not in accepted:
                out.add(f"{r.label} | {len(r.parents)} parents: split it or review its parents")
        # verification
        if r.is_need:
            if r.verified != "Children":
                out.add(f"{r.label} | need not verified by Children")
            if r.rid and not kids.get(r.rid):
                out.add(f"{r.label} | need with no children")
            continue
        if not r.verified:
            out.add(f"{r.label} | no Verified by")
            continue
        for method, evidence in r.verifications():
            if method not in METHODS:
                out.add(f"{r.label} | unknown verification method '{method}'")
            elif method == "Test":
                refs = TEST_REF_RE.findall(evidence)
                if not refs:
                    out.add(f"{r.label} | Test without a tests/<file>.py::<function> reference")
                for file, name in refs:
                    if not _test_exists(root, file, name):
                        out.add(f"{r.label} | missing test {file}::{name}")
            elif method == "Inspection":
                if (r.rid or r.heading) not in insp:
                    out.add(f"{r.label} | inspection without a checklist row")
        if r.verified and not r.verifications():
            out.add(f"{r.label} | no verification method")

    # cycles and chains that miss a need
    reaches: dict[str, bool] = {}

    def reach(rid: str, path: tuple) -> bool:
        if rid in path:
            out.add(f"{ids[rid].label} | cycle: {' -> '.join(path[path.index(rid):] + (rid,))}")
            return False
        if rid in reaches:
            return reaches[rid]
        r = ids[rid]
        ok = r.is_need or any(reach(p, path + (rid,)) for p in r.parents if p in ids)
        reaches[rid] = ok
        return ok

    for r in reqs:
        if r.rid and not r.is_need and r.parents and all(p in ids for p in r.parents[:1]) and not reach(r.rid, ()):
            out.add(f"{r.label} | no chain reaches a need")

    # glossary entries no spec uses
    corpus = "\n".join(r.heading + "\n" + r.statement + "\n" + "\n".join(r.fields.values()) for r in reqs)
    for p in (root / "openspec" / "specs").glob("*/spec.md"):
        corpus += "\n" + p.read_text(encoding="utf-8")
    corpus = corpus.lower()
    for term in terms:
        name = re.sub(r"\s*\(.*?\)", "", term).lower()
        pattern = r"(?<![\w-])" + re.escape(name).replace(r"\ ", "[ -]") + r"s?(?![\w-])"
        if not re.search(pattern, corpus):
            out.add(f"glossary | {term} | used in no spec")

    # dated standard review for every main spec, redone after the spec changes
    for spec in main_specs(root):
        row = reviews.get(spec)
        if not row:
            out.add(f"{spec} | (spec) | no standard review")
            continue
        date = next((d for c in row[1:] for d in DATE_RE.findall(c)), None)
        if not date:
            out.add(f"{spec} | (spec) | standard review has no date")
            continue
        changed = last_change(f"openspec/specs/{spec}/spec.md")
        if changed and changed > date:
            out.add(f"{spec} | (spec) | changed on {changed}, after its standard review on {date}")
    return out


def open_items(root: Path) -> set[str]:
    """Every TBR and verification gap, as 'spec | requirement | TBR/Gap: text' strings."""
    out = set()
    for r in load(root):
        if r.fields.get("TBR"):
            out.add(f"{r.label} | TBR: {r.fields['TBR']}")
        for method, evidence in r.verifications():
            if method == "Gap":
                out.add(f"{r.label} | Gap: {evidence}")
    return out


def ancestors(rid: str, ids: dict[str, Req]) -> list[tuple[int, Req]]:
    """(depth, requirement) for every chain above rid, primary parent first."""
    out, seen = [], set()

    def up(r: Req, depth: int):
        for p in r.parents:
            if p in ids and (p, depth) not in seen:
                seen.add((p, depth))
                out.append((depth, ids[p]))
                up(ids[p], depth + 1)

    up(ids[rid], 1)
    return out


def descendants(rid: str, kids: dict[str, list[Req]]) -> list[tuple[int, Req]]:
    out = []

    def down(i: str, depth: int, path: tuple):
        for c in sorted(kids.get(i, []), key=lambda r: [int(x) for x in (r.rid or "0").split(".")]):
            out.append((depth, c))
            if c.rid and c.rid not in path:
                down(c.rid, depth + 1, path + (c.rid,))

    down(rid, 1, (rid,))
    return out
