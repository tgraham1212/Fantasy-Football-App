"""Every local script the site loads carries the build placeholder the deploy replaces."""

import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parent.parent / "site"
PLACEHOLDER = "?v=__BUILD__"
SCRIPT_SRC = re.compile(r'<script[^>]*\ssrc="([^"]+)"')
IMPORT_FROM = re.compile(r'^\s*import\b[^;]*?\bfrom\s+"([^"]+)"', re.M)


def local_references(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    pattern = SCRIPT_SRC if path.suffix == ".html" else IMPORT_FROM
    return [ref for ref in pattern.findall(text) if not re.match(r"^[a-z]+://", ref)]


def unstamped(site: Path) -> list[str]:
    missing = []
    for path in sorted([*site.glob("*.html"), *site.glob("*.js")]):
        for ref in local_references(path):
            if not ref.endswith(PLACEHOLDER):
                missing.append(f"{path.name}: {ref}")
    return missing


def test_every_script_reference_carries_the_build_placeholder():
    assert unstamped(SITE) == []


def test_both_pages_and_their_imports_are_covered():
    refs = {p.name: local_references(p) for p in [*SITE.glob("*.html"), *SITE.glob("*.js")]}
    assert f"app.js{PLACEHOLDER}" in refs["index.html"]
    assert f"calibration.js{PLACEHOLDER}" in refs["calibration.html"]
    assert f"./war.js{PLACEHOLDER}" in refs["app.js"]
    assert f"./sorting.js{PLACEHOLDER}" in refs["war.js"]


@pytest.mark.parametrize("name,old,new", [
    ("index.html", 'src="app.js?v=__BUILD__"', 'src="app.js"'),
    ("app.js", '"./war.js?v=__BUILD__"', '"./war.js"'),
])
def test_a_stripped_reference_is_reported(tmp_path, name, old, new):
    for path in [*SITE.glob("*.html"), *SITE.glob("*.js")]:
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / name
    target.write_text(target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    assert [m for m in unstamped(tmp_path) if m.startswith(name)] != []
