"""Every local script and stylesheet the site loads carries the build placeholder, and every
deploy stamps it through `ffapp stamp-site` (code fingerprint plus version.json)."""

import json
import re
from pathlib import Path

import pytest
import yaml

from ffapp.stamp import PLACEHOLDER as BARE, fingerprint, stamp_site

SITE = Path(__file__).resolve().parent.parent / "site"
WORKFLOWS = SITE.parent / ".github" / "workflows"
PLACEHOLDER = "?v=__BUILD__"
SCRIPT_SRC = re.compile(r'<script[^>]*\ssrc="([^"]+)"')
STYLESHEET = re.compile(r'<link[^>]*\srel="stylesheet"[^>]*\shref="([^"]+)"')
IMPORT_FROM = re.compile(r'^\s*import\b[^;]*?\bfrom\s+"([^"]+)"', re.M)


def local_references(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    refs = [*SCRIPT_SRC.findall(text), *STYLESHEET.findall(text)] if path.suffix == ".html" else IMPORT_FROM.findall(text)
    return [ref for ref in refs if not re.match(r"^[a-z]+://", ref)]


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


def test_stylesheets_carry_the_placeholder():
    for page in ("index.html", "calibration.html"):
        assert f"styles.css{PLACEHOLDER}" in local_references(SITE / page)


@pytest.mark.parametrize("name,old,new", [
    ("index.html", 'src="app.js?v=__BUILD__"', 'src="app.js"'),
    ("index.html", 'href="styles.css?v=__BUILD__"', 'href="styles.css"'),
    ("app.js", '"./war.js?v=__BUILD__"', '"./war.js"'),
])
def test_a_stripped_reference_is_reported(tmp_path, name, old, new):
    for path in [*SITE.glob("*.html"), *SITE.glob("*.js")]:
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    target = tmp_path / name
    target.write_text(target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    assert [m for m in unstamped(tmp_path) if m.startswith(name)] != []


def deploying_workflows() -> dict[str, list[dict]]:
    """Workflow file -> steps of the job that deploys Pages."""
    out = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for job in (yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs") or {}).values():
            steps = job.get("steps") or []
            if any("deploy-pages" in str(step.get("uses", "")) for step in steps):
                out[path.name] = steps
    return out


def test_every_deploy_stamps_through_the_shared_command():
    deploys = deploying_workflows()
    assert {"refresh.yml", "site.yml"} <= set(deploys)
    for name, steps in deploys.items():
        stamp = [i for i, s in enumerate(steps) if "ffapp stamp-site" in str(s.get("run", ""))]
        upload = [i for i, s in enumerate(steps) if "upload-pages-artifact" in str(s.get("uses", ""))]
        assert stamp and upload and stamp[0] < upload[0], f"{name} must run `python -m ffapp stamp-site` before the upload"
        assert not any(BARE in str(s.get("run", "")) for s in steps), f"{name} stamps by hand"


def copy_site(dest: Path) -> Path:
    for path in SITE.rglob("*"):
        rel = path.relative_to(SITE)
        if path.is_file() and rel.parts[0] != "data" and "__pycache__" not in rel.parts and rel.name != "version.json":
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            (dest / rel).write_bytes(path.read_bytes())
    (dest / "data").mkdir(parents=True)
    (dest / "data" / "index.json").write_text("{}", encoding="utf-8")
    return dest


def test_fingerprint_ignores_data_and_line_endings(tmp_path):
    site = copy_site(tmp_path / "site")
    first = fingerprint(site)
    (site / "data" / "index.json").write_text('{"last_refresh": "later"}', encoding="utf-8")
    (site / "data" / "extra.json").write_text("[]", encoding="utf-8")
    assert fingerprint(site) == first
    script = site / "games.js"
    script.write_bytes(script.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert fingerprint(site) == first


def test_fingerprint_changes_with_code(tmp_path):
    site = copy_site(tmp_path / "site")
    first = fingerprint(site)
    (site / "styles.css").write_bytes((site / "styles.css").read_bytes() + b"\n/* changed */\n")
    assert fingerprint(site) != first


def test_stamp_site_writes_the_fingerprint_everywhere(tmp_path):
    site = copy_site(tmp_path / "site")
    expected = fingerprint(copy_site(tmp_path / "copy"))
    fp = stamp_site(site)
    assert fp == expected
    for path in [*site.glob("*.html"), *site.glob("*.js")]:
        assert BARE not in path.read_text(encoding="utf-8"), path.name
    index = (site / "index.html").read_text(encoding="utf-8")
    assert f'src="app.js?v={fp}"' in index and f'href="styles.css?v={fp}"' in index
    assert f'CODE = "{fp}"' in (site / "version.js").read_text(encoding="utf-8")
    assert json.loads((site / "version.json").read_text(encoding="utf-8")) == {"code": fp}
