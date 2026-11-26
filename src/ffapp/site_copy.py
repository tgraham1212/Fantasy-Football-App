"""The site copy file: every piece of descriptive text on the site in one editable file.

``site-copy.txt`` mirrors the text in the site code so the owner can copy-edit it in one place.
Each entry is identified in the code itself: an HTML element carries ``data-copy="ID"`` (its inner
HTML is the entry), a script string is preceded by ``/*copy:ID*/`` (the literal's content is the
entry). ``site-copy.lock.json`` records a hash of each entry's text as last synced, so the two
directions can be told apart:

    code changed, file not   -> stale: regenerating the file updates it (no confirmation needed)
    file changed, code not   -> pending copy edit: confirm with the owner, then ``--apply``
    both changed             -> conflict: the owner resolves it

Regenerating never applies or discards pending edits; only ``--apply`` writes them into the code.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

COPY_FILE = "site-copy.txt"
LOCK_FILE = "site-copy.lock.json"
HTML_FILES = ("index.html", "calibration.html")
SECTIONS = {  # ID prefix -> section heading, in file order
    "HDR": "Header and footer (every page)",
    "PRED": "Predictions tab",
    "GAME": "Games tab",
    "POS": "Positions tab",
    "WAR": "Player WAR tab",
    "LG": "League tab",
    "CAL": "Calibration page",
    "MSG": "Messages",
}
BLOCK_TAGS = ("p", "li", "h1", "h2", "h3", "title")
MARKER = re.compile(r"/\*copy:([A-Z]+-\d+)\*/")
ID_RE = re.compile(r"^\[([A-Z]+-\d+)\] (.*)$")
MIN_WORDS = 4
# Sentence-like script strings that are not site copy: developer and error text, ARIA-only labels.
EXEMPT = (
    ("app.js", "Could not load the odds data"),  # developer error text
    ("calibration.js", "Could not load the calibration data"),
    ("positions.js", "points per game${extra"),  # screen-reader label built from the entries
    ("positions.js", "fill: color-mix("),  # inline CSS
    ("games.js", "background: color-mix("),
    ("war.js", "also held by"),  # screen-reader only
    ("war.js", "Pts allowed / game"),  # table column label (labels are not site copy)
    ("calibration.js", "points left on the bench"),  # table column labels
    ("calibration.js", "Season value (actual, shrunk)"),  # table row labels around CAL-26
    ("war.js", "Kittle: score, win chance"),  # worked-example table labels around WAR-19..21
)

HEADER = """SITE COPY FOR EDITING
=====================

Edit the text under each TEXT: line, save, and tell Claude; the tests flag the edits and Claude
checks with you before applying them to the site (python -m ffapp site-copy --apply).
- Leave the [ID] and WHERE lines alone; they tell the tool where each piece goes.
- Anything inside ${...} is filled in by the page (a week number, a name, a date). Keep it, move it
  within the sentence if you like, but do not change what is inside the braces.
- Inline tags such as <em>, <strong>, <code> or <a ...> are written back as you leave them.
- To ask for a piece to be deleted, leave its TEXT empty and say so in a NOTE: line.
- Add a NOTE: line under any entry to explain an edit or ask a question; notes are kept.
- Entries marked (generated) are built by the page; some are sentences that join others
  ("add-on"), so read them together.
"""


def collapse(text: str) -> str:
    return " ".join(text.split())


def digest(text: str) -> str:
    return hashlib.sha256(collapse(text).encode("utf-8")).hexdigest()[:16]


@dataclass
class CodeEntry:
    id: str
    file: str  # path relative to the site directory
    line: int
    start: int  # offsets of the editable span in the file's source
    end: int
    raw: str  # the source between start and end
    kind: str  # "html" or the JS quote character
    tag: str = ""

    @property
    def text(self) -> str:
        return collapse(self.raw)

    @property
    def where(self) -> str:
        return f"site/{self.file} line {self.line}" + (" (generated)" if self.kind != "html" else "")


@dataclass
class FileEntry:
    id: str
    label: str
    where: str
    text: str
    notes: list[str] = field(default_factory=list)


# -- extraction: HTML -------------------------------------------------------------------------


class _Spans(HTMLParser):
    """Inner-HTML spans of [data-copy] elements, and descriptive blocks lacking an ID."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        for m in re.finditer("\n", source):
            self.line_starts.append(m.end())
        self.stack: list[dict] = []
        self.spans: list[tuple[str, str, int, int, int]] = []  # id, tag, line, start, end
        self.unmarked: list[tuple[int, str]] = []
        self.svg = 0

    def _pos(self) -> int:
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        start = self._pos()
        inner = start + len(self.get_starttag_text() or "")
        if tag == "svg":
            self.svg += 1
        self.stack.append({"tag": tag, "id": a.get("data-copy"), "inner": inner, "line": self.getpos()[0], "text": []})

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        end = self._pos()
        while self.stack:
            node = self.stack.pop()
            if node["tag"] == tag:
                break
        else:
            return
        if tag == "svg":
            self.svg -= 1
        if node["id"]:
            self.spans.append((node["id"], tag, node["line"], node["inner"], end))
        elif tag in BLOCK_TAGS and not self.svg and not any(n["id"] for n in self.stack):
            text = collapse(re.sub(r"<[^>]+>", " ", self.source[node["inner"]:end]))
            if text:
                self.unmarked.append((node["line"], text))

    def handle_data(self, data):
        pass


def html_entries(site: Path, rel: str) -> tuple[list[CodeEntry], list[tuple[int, str]]]:
    source = (site / rel).read_text(encoding="utf-8")
    parser = _Spans(source)
    parser.feed(source)
    entries = [CodeEntry(cid, rel, line, start, end, source[start:end], "html", tag) for cid, tag, line, start, end in parser.spans]
    return entries, parser.unmarked


# -- extraction: scripts --------------------------------------------------------------------


def scan_string(src: str, i: int) -> int:
    """End index (exclusive) of the string literal starting at src[i]; handles template nesting."""
    quote = src[i]
    j = i + 1
    while j < len(src):
        c = src[j]
        if c == "\\":
            j += 2
            continue
        if c == quote:
            return j + 1
        if quote == "`" and src.startswith("${", j):
            j = scan_expression(src, j + 2)
            continue
        if quote != "`" and c == "\n":
            raise ValueError(f"unterminated string at offset {i}")
        j += 1
    raise ValueError(f"unterminated string at offset {i}")


def scan_expression(src: str, j: int) -> int:
    """Index just past the ``}`` closing a template ``${`` expression that starts at src[j]."""
    depth = 1
    while j < len(src):
        c = src[j]
        if c in "\"'`":
            j = scan_string(src, j)
            continue
        if src.startswith("/*", j):
            j = src.index("*/", j) + 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError("unterminated template expression")


def _line_of(src: str, offset: int) -> int:
    return src.count("\n", 0, offset) + 1


def script_entries(site: Path, rel: str) -> list[CodeEntry]:
    src = (site / rel).read_text(encoding="utf-8")
    out = []
    for m in MARKER.finditer(src):
        i = m.end()
        while i < len(src) and src[i] in " \t\r\n":
            i += 1
        if i >= len(src) or src[i] not in "\"'`":
            raise ValueError(f"{rel}: marker {m.group(1)} is not followed by a string literal")
        end = scan_string(src, i)
        out.append(CodeEntry(m.group(1), rel, _line_of(src, i), i + 1, end - 1, src[i + 1:end - 1], src[i]))
    return out


def string_literals(src: str):
    """(start, end) of every top-level and nested string literal outside comments and regexes."""
    i = 0
    prev = ""
    while i < len(src):
        c = src[i]
        if src.startswith("//", i):
            i = src.find("\n", i)
            i = len(src) if i < 0 else i
            continue
        if src.startswith("/*", i):
            i = src.index("*/", i) + 2
            continue
        if c == "/" and prev in "(,=:[!&|?{};\n" + "":
            j = i + 1
            while j < len(src) and src[j] != "/" and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            i = j + 1
            continue
        if c in "\"'`":
            end = scan_string(src, i)
            yield i, end
            # nested literals inside template expressions
            if c == "`":
                body = src[i + 1:end - 1]
                for s, e in string_literals_in_template(body):
                    yield i + 1 + s, i + 1 + e
            i = end
            prev = c
            continue
        if not c.isspace():
            prev = c
        elif c == "\n":
            prev = prev if prev else "\n"
        i += 1


def string_literals_in_template(body: str):
    j = 0
    while j < len(body):
        if body[j] == "\\":
            j += 2
            continue
        if body.startswith("${", j):
            end = scan_expression(body, j + 2)
            yield from ((j + 2 + s, j + 2 + e) for s, e in string_literals(body[j + 2:end - 1]))
            j = end
            continue
        j += 1


def placeholders(text: str) -> list[str]:
    out, j = [], 0
    while j < len(text):
        if text.startswith("${", j):
            end = scan_expression(text, j + 2)
            out.append(collapse(text[j:end]))
            j = end
            continue
        j += 1
    return out


def _without_placeholders(text: str) -> str:
    out, j = [], 0
    while j < len(text):
        if text.startswith("${", j):
            j = scan_expression(text, j + 2)
            out.append(" | ")
            continue
        out.append(text[j])
        j += 1
    return "".join(out)


def sentence_like(content: str) -> bool:
    """A run of at least MIN_WORDS words between tags/placeholders, with a lowercase word."""
    for run in re.split(r"<[^>]*>|\|", _without_placeholders(content)):
        words = run.split()
        if len(words) >= MIN_WORDS and any(re.fullmatch(r"[a-z][a-z'’]{2,}[.,;:]?", w) for w in words):
            return True
    return False


def unmarked_script_strings(site: Path, rel: str) -> list[tuple[int, str]]:
    src = (site / rel).read_text(encoding="utf-8")
    marked = {e.start - 1 for e in script_entries(site, rel)}
    out = []
    for start, end in string_literals(src):
        if start in marked:
            continue
        content = src[start + 1:end - 1]
        if not sentence_like(content):
            continue
        if any(rel == f and needle in content for f, needle in EXEMPT):
            continue
        out.append((_line_of(src, start), collapse(content)[:120]))
    return out


def script_files(site: Path) -> list[str]:
    return sorted(p.name for p in site.glob("*.js"))


def code_entries(site: Path) -> dict[str, CodeEntry]:
    entries: dict[str, CodeEntry] = {}
    for rel in HTML_FILES:
        if (site / rel).exists():
            for e in html_entries(site, rel)[0]:
                entries[e.id] = e
    for rel in script_files(site):
        for e in script_entries(site, rel):
            if e.id in entries:
                raise ValueError(f"copy ID {e.id} is used twice ({entries[e.id].where} and {e.where})")
            entries[e.id] = e
    return entries


def coverage_problems(site: Path) -> list[str]:
    problems = []
    for rel in HTML_FILES:
        if (site / rel).exists():
            for line, text in html_entries(site, rel)[1]:
                problems.append(f"site/{rel} line {line}: text without data-copy: {text[:100]}")
    for rel in script_files(site):
        for line, text in unmarked_script_strings(site, rel):
            problems.append(f"site/{rel} line {line}: sentence without a /*copy:ID*/ marker: {text}")
    return problems


# -- the copy file and the sync record ------------------------------------------------------


def parse_file(path: Path) -> dict[str, FileEntry]:
    if not path.exists():
        return {}
    entries: dict[str, FileEntry] = {}
    current: FileEntry | None = None
    mode = None
    for raw in path.read_text(encoding="utf-8").split("\n"):
        m = ID_RE.match(raw)
        if m:
            current = FileEntry(m.group(1), m.group(2).strip(), "", "")
            entries[current.id] = current
            mode = None
            continue
        if current is None:
            continue
        if raw.startswith("#"):
            current, mode = None, None
            continue
        if raw.startswith("WHERE:"):
            current.where = raw[6:].strip()
        elif raw.startswith("NOTE:"):
            current.notes.append(raw[5:].strip())
            mode = "note"
        elif raw.startswith("TEXT:"):
            mode = "text"
            rest = raw[5:].strip()
            if rest:
                current.text = rest
        elif mode == "text" and raw.strip():
            current.text = f"{current.text} {raw.strip()}".strip()
        elif mode == "note" and raw.strip():
            current.notes[-1] = f"{current.notes[-1]} {raw.strip()}"
    for e in entries.values():
        e.text = collapse(e.text)
    return entries


def default_label(entry: CodeEntry) -> str:
    if entry.kind != "html":
        return "generated text"
    return {"p": "paragraph", "li": "list item", "h1": "page title", "h2": "heading", "h3": "heading", "title": "browser tab title"}.get(entry.tag, entry.tag)


def _order(cid: str) -> tuple[int, int]:
    prefix, num = cid.rsplit("-", 1)
    return (list(SECTIONS).index(prefix) if prefix in SECTIONS else len(SECTIONS), int(num))


def render_file(entries: list[FileEntry]) -> str:
    out = [HEADER.rstrip(), ""]
    by_section: dict[str, list[FileEntry]] = {}
    for e in sorted(entries, key=lambda e: _order(e.id)):
        by_section.setdefault(e.id.rsplit("-", 1)[0], []).append(e)
    for prefix, rows in by_section.items():
        title = SECTIONS.get(prefix, prefix)
        out += ["", "#" * 78, f"# {title.upper()}", "#" * 78, ""]
        for e in rows:
            out += [f"[{e.id}] {e.label}", f"WHERE: {e.where}", "TEXT:", e.text]
            out += [f"NOTE: {n}" for n in e.notes]
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def read_lock(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return dict(json.loads(path.read_text(encoding="utf-8")).get("entries", {}))


def write_lock(path: Path, hashes: dict[str, str]) -> None:
    body = {"note": "Hash of each site-copy.txt entry as last synced with the code; see src/ffapp/site_copy.py.",
            "entries": dict(sorted(hashes.items(), key=lambda kv: _order(kv[0])))}
    path.write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8", newline="\n")


def statuses(code: dict[str, CodeEntry], file: dict[str, FileEntry], lock: dict[str, str]) -> dict[str, str]:
    """ID -> in_sync | stale | pending | conflict | new | removed."""
    out = {}
    for cid in set(code) | set(file):
        if cid not in file:
            out[cid] = "new"
        elif cid not in code:
            out[cid] = "removed"
        else:
            c, f, h = digest(code[cid].text), digest(file[cid].text), lock.get(cid)
            if c == f:
                out[cid] = "in_sync" if c == h else "stale"  # stale here = only the record is behind
            elif f == h:
                out[cid] = "stale"
            elif c == h:
                out[cid] = "pending"
            else:
                out[cid] = "conflict"
    return out


@dataclass
class Report:
    statuses: dict[str, str]

    def ids(self, *kinds: str) -> list[str]:
        return sorted((k for k, v in self.statuses.items() if v in kinds), key=_order)

    @property
    def clean(self) -> bool:
        return all(v == "in_sync" for v in self.statuses.values())


def check(root: Path) -> Report:
    site = root / "site"
    return Report(statuses(code_entries(site), parse_file(root / COPY_FILE), read_lock(root / LOCK_FILE)))


def regenerate(root: Path, accept: set[str] | None = None) -> Report:
    """Bring the file and record up to date with the code, keeping pending edits and conflicts.
    IDs in ``accept`` (just applied) take the code's text whatever their status."""
    accept = accept or set()
    site = root / "site"
    code, file, lock = code_entries(site), parse_file(root / COPY_FILE), read_lock(root / LOCK_FILE)
    st = statuses(code, file, lock)
    out: list[FileEntry] = []
    new_lock: dict[str, str] = {}
    for cid, entry in code.items():
        old = file.get(cid)
        label = old.label if old else default_label(entry)
        notes = old.notes if old else []
        if st[cid] in ("pending", "conflict") and cid not in accept:
            out.append(FileEntry(cid, label, entry.where, old.text, notes))
            if cid in lock:
                new_lock[cid] = lock[cid]
        else:
            out.append(FileEntry(cid, label, entry.where, entry.text, notes))
            new_lock[cid] = digest(entry.text)
    (root / COPY_FILE).write_text(render_file(out), encoding="utf-8", newline="\n")
    write_lock(root / LOCK_FILE, new_lock)
    return Report(statuses(code, {e.id: e for e in out}, new_lock))


@dataclass
class ApplyResult:
    applied: list[str] = field(default_factory=list)
    refused: list[tuple[str, str]] = field(default_factory=list)
    deletions: list[str] = field(default_factory=list)


def _encode(text: str, kind: str) -> str:
    """Escape the literal's own quote character outside ${...} placeholders (left exactly as written)."""
    if kind == "html":
        return text
    out, j = [], 0
    while j < len(text):
        if kind == "`" and text.startswith("${", j):
            end = scan_expression(text, j + 2)
            out.append(text[j:end])
            j = end
            continue
        c = text[j]
        if c == "\\":
            out.append(text[j:j + 2])
            j += 2
            continue
        out.append("\\" + c if c == kind else c)
        j += 1
    return "".join(out)


def apply_edits(root: Path) -> ApplyResult:
    """Write every pending copy edit into the code, then refresh the file and record."""
    site = root / "site"
    code, file, lock = code_entries(site), parse_file(root / COPY_FILE), read_lock(root / LOCK_FILE)
    st = statuses(code, file, lock)
    result = ApplyResult()
    edits: dict[str, list[tuple[CodeEntry, str]]] = {}
    for cid in sorted((k for k, v in st.items() if v == "pending"), key=_order):
        entry, wanted = code[cid], file[cid].text
        if not wanted:
            result.deletions.append(cid)
            continue
        if Counter(placeholders(wanted)) != Counter(placeholders(entry.text)):
            result.refused.append((cid, "its ${...} placeholders changed"))
            continue
        edits.setdefault(entry.file, []).append((entry, _encode(wanted, entry.kind)))
        result.applied.append(cid)
    for rel, changes in edits.items():
        src = (site / rel).read_text(encoding="utf-8")
        for entry, new in sorted(changes, key=lambda c: c[0].start, reverse=True):
            src = src[: entry.start] + new + src[entry.end:]
        (site / rel).write_text(src, encoding="utf-8", newline="\n")
    regenerate(root, accept=set(result.applied))  # applied entries are in the code: file and record follow it
    return result
