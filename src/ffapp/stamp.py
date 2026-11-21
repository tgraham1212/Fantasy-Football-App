"""Stamp the site for a deploy: fingerprint its code, put the fingerprint in every script
and stylesheet URL, and publish it in ``version.json``.

Every deploy runs this (``python -m ffapp stamp-site``). The fingerprint depends only on the
content of the site's code files - everything under ``site/`` except ``site/data/`` - so a
deploy that only brings new data keeps the same script URLs and browsers keep their cache,
while any code change gives every reference a new URL. The page compares its own stamped
fingerprint (``site/version.js``) with ``version.json`` to know when new code is live.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PLACEHOLDER = "__BUILD__"
VERSION_FILE = "version.json"
FINGERPRINT_LENGTH = 10


def code_files(site: Path) -> list[Path]:
    """Every file under ``site`` that is site code: not data, not the published version file."""
    files = []
    for path in site.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(site)
        if rel.parts[0] == "data" or rel.as_posix() == VERSION_FILE or "__pycache__" in rel.parts:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(site).as_posix())


def fingerprint(site: Path) -> str:
    """Hash of the code files' paths and contents, line endings normalised to LF."""
    digest = hashlib.sha256()
    for path in code_files(site):
        digest.update(path.relative_to(site).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()[:FINGERPRINT_LENGTH]


def stamp_site(site: Path) -> str:
    """Fingerprint the unstamped site, replace the placeholder in its pages and scripts, and
    write ``version.json``. Returns the fingerprint."""
    fp = fingerprint(site)
    for path in sorted([*site.glob("*.html"), *site.glob("*.js")]):
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER in text:
            path.write_text(text.replace(PLACEHOLDER, fp), encoding="utf-8", newline="")
    (site / VERSION_FILE).write_text(json.dumps({"code": fp}) + "\n", encoding="utf-8")
    return fp


# Keys that change on every run without changing what the site shows.
TIME_KEYS = frozenset({"generated_at", "last_refresh", "fetched_at", "at"})


def _strip_times(value):
    if isinstance(value, dict):
        return {k: _strip_times(v) for k, v in value.items() if k not in TIME_KEYS}
    if isinstance(value, list):
        return [_strip_times(v) for v in value]
    return value


def site_hash(site: Path) -> str:
    """Hash of the whole unstamped site (code and data) ignoring refresh times, so the cold run
    deploys only when what visitors see would change (docs/refresh-modes.md)."""
    digest = hashlib.sha256()
    for path in sorted((p for p in site.rglob("*") if p.is_file()), key=lambda p: p.relative_to(site).as_posix()):
        rel = path.relative_to(site).as_posix()
        if rel == VERSION_FILE or "__pycache__" in rel:
            continue
        data = path.read_bytes().replace(b"\r\n", b"\n")
        if path.suffix == ".json":
            try:
                data = json.dumps(_strip_times(json.loads(data)), sort_keys=True).encode("utf-8")
            except ValueError:
                pass
        digest.update(rel.encode("utf-8") + b"\0" + data + b"\0")
    return digest.hexdigest()[:16]
