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


def _blocks(text: str) -> dict[str, str]:
    """Requirement ID -> its whole block (heading, statement, reference lines, scenarios), blank lines
    and surrounding spaces dropped, so only a real edit changes it."""
    out, rid, buf = {}, None, []

    def close():
        if rid:
            out[rid] = "\n".join(buf)

    for line in text.splitlines():
        h = HEADING_RE.match(line)
        if h or re.match(r"^## ", line):
            close()
            m = ID_RE.match(h.group(1)) if h else None
            rid, buf = (m.group(1) if m else None), []
        if rid and line.strip():
            buf.append(line.strip())
    close()
    return out


SPEC_FILE_RE = re.compile(r"^openspec/(?:specs/[^/]+|changes/(?!archive/)[^/]+/specs/[^/]+)/spec\.md$")


class GitHistory:
    """Commit order, for the re-inspection rules. A spec's standard review is stale when a commit
    touching the spec is newer than the commit that last recorded its checklist row. An inspection
    is stale when its requirement, or a requirement directly linked to it (a parent or a child,
    primary or association), was added or changed in a commit newer than the one that last recorded
    its row.

    Commit order, not dates: a rebase (fetch and rebase before every push) re-dates commits but keeps
    their order. In a shallow clone (CI checks out one commit) the history is missing, so nothing is
    stale; the rule runs on full clones. Uncommitted edits count once they are committed."""

    CHECKLIST = "openspec/inspection-checklist.md"

    def __init__(self, root: Path):
        self.root = Path(root)
        self._order: dict[str, int] | None = None
        self._rows: dict[str, str] | None = None
        self._paths: dict[str, str | None] = {}
        self._reqs: dict[str, str] | None = None

    def _git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True,
                              encoding="utf-8", check=True).stdout

    def _ready(self) -> bool:
        if self._order is None:
            try:
                if self._git("rev-parse", "--is-shallow-repository").strip() == "true":
                    self._order = {}
                else:  # newest first: a lower index is a newer commit
                    self._order = {sha: i for i, sha in enumerate(self._git("rev-list", "HEAD").split())}
            except (OSError, subprocess.CalledProcessError):
                self._order = {}
        return bool(self._order)

    def _row_commits(self) -> dict[str, str]:
        """Checklist row key (ID or spec name) -> the newest commit that added or changed that row."""
        if self._rows is None:
            self._rows, sha = {}, None
            for line in self._git("log", "--format=COMMIT %H", "-p", "-U0", "--", self.CHECKLIST).splitlines():
                if line.startswith("COMMIT "):
                    sha = line.split()[1]
                elif line.startswith("+|") and sha:
                    key = line[1:].strip().strip("|").split("|")[0].strip().strip("`")
                    self._rows.setdefault(key, sha)
            # a row re-recorded but not yet committed is newer than every commit
            def rows(text: str) -> dict[str, str]:
                return {ln.strip().strip("|").split("|")[0].strip().strip("`"): ln.strip()
                        for ln in text.splitlines() if ln.startswith("|") and not ln.startswith("|---")}
            path = self.root / self.CHECKLIST
            try:
                committed = rows(self._git("show", f"HEAD:{self.CHECKLIST}"))
            except subprocess.CalledProcessError:
                committed = {}
            if path.exists() and self._order is not None:
                self._order["WORKTREE"] = -1
                for key, line in rows(path.read_text(encoding="utf-8")).items():
                    if committed.get(key) != line:
                        self._rows[key] = "WORKTREE"
        return self._rows

    def _path_commit(self, rel: str) -> str | None:
        if rel not in self._paths:
            self._paths[rel] = self._git("log", "-1", "--format=%H", "--", rel).strip() or None
        return self._paths[rel]

    def _req_commits(self) -> dict[str, str]:
        """Requirement ID -> the newest commit that added or changed its block. Walks every commit to
        the main specs and active changes' delta specs, oldest first; an active change's ADDED or
        MODIFIED version stands in for the main one, as in load()."""
        if self._reqs is None:
            self._reqs = {}
            log = self._git("log", "--reverse", "--first-parent", "--no-renames", "--format=COMMIT %H",
                            "--name-status", "--", "openspec/specs", "openspec/changes")
            commits: list[tuple[str, list[tuple[str, str]]]] = []
            for line in log.splitlines():
                if line.startswith("COMMIT "):
                    commits.append((line.split()[1], []))
                elif "\t" in line and commits:
                    status, path = line.split("\t", 1)
                    if SPEC_FILE_RE.match(path):
                        commits[-1][1].append((status[0], path))
            wanted = [f"{sha}:{path}" for sha, files in commits for st, path in files if st != "D"]
            blobs = self._cat(wanted)
            parsed: dict[str, dict[str, str]] = {}
            before: dict[str, str] = {}
            for sha, files in commits:
                for st, path in files:
                    if st == "D":
                        parsed.pop(path, None)
                    else:
                        text = blobs.get(f"{sha}:{path}", "")
                        if path.startswith("openspec/specs/"):
                            parsed[path] = _blocks(text)
                        else:
                            secs = _sections(text)
                            parsed[path] = {**_blocks(secs.get("ADDED Requirements", "")),
                                            **_blocks(secs.get("MODIFIED Requirements", ""))}
                now: dict[str, str] = {}
                for path in sorted(parsed, key=lambda p: not p.startswith("openspec/specs/")):
                    now.update(parsed[path])  # main specs first, then active changes over them
                for rid, block in now.items():
                    if before.get(rid) != block:
                        self._reqs[rid] = sha
                before = now
        return self._reqs

    def _cat(self, objects: list[str]) -> dict[str, str]:
        """'sha:path' -> file text, in one git cat-file call."""
        if not objects:
            return {}
        raw = subprocess.run(["git", "cat-file", "--batch"], cwd=self.root, input="\n".join(objects).encode() + b"\n",
                             capture_output=True, check=True).stdout
        out, pos = {}, 0
        for name in objects:
            end = raw.index(b"\n", pos)
            header = raw[pos:end].split()
            pos = end + 1
            if len(header) == 3 and header[1] == b"blob":
                size = int(header[2])
                out[name] = raw[pos:pos + size].decode("utf-8", "replace")
                pos += size + 1
        return out

    def _newer(self, sha: str | None, key: str) -> bool:
        row_sha = self._row_commits().get(key)
        if not sha or not row_sha or sha not in self._order or row_sha not in self._order:
            return False
        return self._order[sha] < self._order[row_sha]

    def changed_after(self, rel: str, key: str) -> bool:
        """True when a commit touching `rel` is newer than the commit that last recorded row `key`."""
        if not self._ready():
            return False
        try:
            return self._newer(self._path_commit(rel), key)
        except (OSError, subprocess.CalledProcessError):
            return False

    def req_changed_after(self, rid: str, key: str) -> bool:
        """True when requirement `rid` was added or changed in a commit newer than the commit that last
        recorded row `key`."""
        if not self._ready():
            return False
        try:
            return self._newer(self._req_commits().get(rid), key)
        except (OSError, subprocess.CalledProcessError):
            return False


# ---------- the check ----------

def _plain(statement: str) -> str:
    return re.sub(r"`[^`]*`", " ", statement)


def _test_exists(root: Path, file: str, name: str) -> bool:
    path = Path(root) / file
    if not path.exists():
        return False
    func = name.split("::")[-1]
    return re.search(rf"^\s*def {re.escape(func)}\(", path.read_text(encoding="utf-8"), re.M) is not None


def check(root: Path, accepted: dict | None = None, history=None) -> set[str]:
    """Every finding against the standard, as 'spec | requirement | finding' strings."""
    root = Path(root)
    accepted = accepted or {}
    history = history or GitHistory(root)  # anything with changed_after(path, row key) -> bool
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

    # an inspection is redone when its requirement, or one directly linked to it (a parent or a
    # child, primary or association), is added or changed; if those links hold, the rest of the tree does
    for rid, row in insp.items():
        if rid not in ids:
            continue
        date = next((d for c in row[1:] for d in DATE_RE.findall(c)), None)
        if not date:
            out.add(f"{ids[rid].label} | inspection row has no date")
            continue
        near = [rid] + [p for p in ids[rid].parents if p in ids] + [k.rid for k in kids.get(rid, []) if k.rid]
        changed = [x for x in dict.fromkeys(near) if history.req_changed_after(x, rid)]
        if changed:
            out.add(f"{ids[rid].label} | re-inspect: {', '.join(changed)} changed in a commit after its inspection on {date}")

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
        if history.changed_after(f"openspec/specs/{spec}/spec.md", spec):
            out.add(f"{spec} | (spec) | changed in a commit after its standard review on {date}")
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
