"""Colour contrast of the site's tokens, in light and dark mode (WCAG 2.2 AA).

axe-core checks the rendered HTML in light and dark mode, but it cannot measure text drawn in the
SVG charts, which reads the same tokens through cssVar(). This test checks the tokens
themselves:
- text at 4.5:1 against every background it sits on, including table rows that are hovered
  (surface mixed with 4% ink) or selected (surface mixed with 12% accent), as styles.css paints them;
- focus rings and chart lines at 3:1 against the page and cards.

Every hex token must be either checked or exempt with a reason, so a new colour has to be
classified. Colours are adjusted in OKLCH by lightness only (see openspec/config.yaml).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from team_palette import contrast  # noqa: E402  (one implementation of the WCAG maths)

CSS = ROOT / "site" / "styles.css"
SURFACES = ("page", "surface")
ROWS = {"hovered row": ("ink", 0.04), "selected row": ("accent", 0.12)}  # color-mix over --surface
TEXT_ON_ROWS = ("ink", "ink-2", "muted")  # the text used inside highlightable table rows (the worked
# example's blue fill mark sits in table.walkthrough, which has no hover highlight)
TEXT_ON_SURFACES = ("ink", "ink-2", "muted", "accent", "good", "bad", "gold")
TEXT_ON_FILLS = (  # (text, fill): text drawn on a coloured background
    ("accent-ink", "accent-fill"),  # selected league button
    ("win-ink", "win-hi"), ("win-ink", "win-mid"), ("win-ink", "win-lo"),  # Games win-probability bar
    ("fill-ink", "fill-hi"), ("chance-ink", "fill-lo"),  # forecast heat cells, both ends of the ramp
    ("#0b0b0b", "pill-good"), ("#0b0b0b", "pill-bad"),  # rating pills: fixed black text in .elo-delta
    # Managers page: slot pills, status badges, PPG chips, banners, rank tags, news thumbnails
    ("pos-qb-i", "pos-qb-f"), ("pos-rb-i", "pos-rb-f"), ("pos-wr-i", "pos-wr-f"), ("pos-te-i", "pos-te-f"),
    ("pos-k-i", "pos-k-f"), ("pos-def-i", "pos-def-f"), ("ink", "pos-rb-f"), ("ink", "pos-wr-f"), ("ink", "pos-te-f"),  # FLEX thirds
    ("pill-ir-i", "pill-ir-f"), ("pill-tx-i", "pill-tx-f"), ("badge-q-i", "badge-q-f"),
    ("tier1-i", "tier1-f"), ("tier2-i", "tier2-f"), ("tier3-i", "tier3-f"), ("tier4-i", "tier4-f"), ("tier5-i", "tier5-f"),
    ("banner-gold-i", "banner-gold"), ("banner-bowl-i", "banner-bowl"),
    ("rank1-i", "rank1-f"), ("rank2-i", "rank2-f"), ("rank3-i", "rank3-f"), ("rival-i", "rival-f"),
    ("ink", "score-f"), ("ink-2", "meter-f"),
    ("th-res-i", "th-res-f"), ("th-up-i", "th-up-f"), ("th-down-i", "th-down-f"), ("th-inj-i", "th-inj-f"),
    ("th-rec-i", "th-rec-f"), ("th-lg-i", "th-lg-f"), ("th-move-i", "th-move-f"),
    ("feat-i", "feat-a"), ("feat-i", "feat-b"),  # the feature picture's gradient, both ends
)
NON_TEXT = ("accent", "form-w", "form-l", "form-d", "rod")  # focus ring, form bars, banner rod; team lines added below
EXEMPT = {
    "grid": "decorative gridlines; the data never depends on them",
    "axis": "decorative axis rules and chip outlines next to text",
    "live": "animated live signal, always shown beside the word 'Live'",
    "banner-gold-edge": "decorative outline on a banner whose year is checked against its fill",
    "banner-bowl-edge": "decorative outline on a banner whose year is checked against its fill",
    "zone-f": "decorative band behind the playoff places on the finishes chart",
}
TEXT_RATIO, NON_TEXT_RATIO = 4.5, 3.0


def token_blocks(css: str) -> dict[str, dict[str, str]]:
    """Hex tokens per mode. Dark inherits anything it doesn't redefine from light."""
    def hexes(block: str) -> dict[str, str]:
        return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\b", block))

    media_at = css.index("@media (prefers-color-scheme: dark)")
    light = hexes(css[css.index(":root {"):media_at])
    media = css[media_at:]
    media = media[:media.index("\n  }")]
    toggle = css[css.index(':root[data-theme="dark"]'):]
    toggle = toggle[:toggle.index("\n}")]
    return {"light": light, "dark": {**light, **hexes(media)}, "dark-toggle": {**light, **hexes(toggle)}}


def mix(base: str, other: str, share: float) -> str:
    """color-mix(in srgb, base, other share), as the row highlights are painted."""
    a = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - share) + y * share):02x}" for x, y in zip(a, b))


def problems(css: str) -> list[str]:
    blocks = token_blocks(css)
    out = []
    if blocks["dark"] != blocks["dark-toggle"]:
        diff = sorted(k for k in blocks["dark"].keys() | blocks["dark-toggle"].keys()
                      if blocks["dark"].get(k) != blocks["dark-toggle"].get(k))
        out.append(f"the two dark token blocks differ: {', '.join('--' + k for k in diff)}")
    for mode in ("light", "dark"):
        t = blocks[mode]

        rows = {name: mix(t["surface"], t[tok], share) for name, (tok, share) in ROWS.items()}

        def value(name: str) -> str:
            return name if name.startswith("#") else rows[name] if name in rows else t[name]

        def label(name: str) -> str:
            return name if name.startswith("#") or name in rows else f"--{name}"

        lines = tuple(k for k in t if re.fullmatch(r"(team|former)-\d+", k))
        pairs = [(fg, bg, TEXT_RATIO) for fg in TEXT_ON_SURFACES for bg in SURFACES]
        pairs += [(fg, bg, TEXT_RATIO) for fg in TEXT_ON_ROWS for bg in rows]
        pairs += [(fg, bg, TEXT_RATIO) for fg, bg in TEXT_ON_FILLS]
        pairs += [(fg, bg, NON_TEXT_RATIO) for fg in NON_TEXT + lines for bg in SURFACES]
        for fg, bg, need in pairs:
            ratio = contrast(value(fg), value(bg))
            if ratio < need:
                out.append(f"{mode}: {label(fg)} on {label(bg)} is {ratio:.2f}:1, needs {need}:1")
        checked = {n for fg, bg, _ in pairs for n in (fg, bg)} - set(rows)
        for name in sorted(set(t) - checked - set(EXEMPT)):
            out.append(f"{mode}: --{name} is neither checked nor exempt; add it to a pair or to EXEMPT")
    return out


def test_colour_tokens_meet_contrast():
    found = problems(CSS.read_text(encoding="utf-8"))
    assert not found, "\n".join(found)


def test_check_names_mode_tokens_and_ratio():
    css = CSS.read_text(encoding="utf-8")
    light_muted = re.search(r"--muted: (#[0-9a-f]{6})", css).group(0)
    found = problems(css.replace(light_muted, "--muted: #898781", 1))
    assert any(p.startswith("light: --muted on --surface is 3.5") for p in found), found


def test_check_catches_dark_only_failure():
    css = CSS.read_text(encoding="utf-8")
    found = problems(css.replace("--accent-fill: #2170cd;", "--accent-fill: #3987e5;").replace(
        "  --accent-fill: #3987e5;  /*", "  --accent-fill: #2170cd;  /*", 1))
    assert any(p.startswith("dark: --accent-ink on --accent-fill") for p in found), found
    assert not any(p.startswith("light: --accent-ink") for p in found), found


def test_unclassified_token_fails():
    css = CSS.read_text(encoding="utf-8").replace("  --grid: #e1e0d9;", "  --grid: #e1e0d9;\n  --new-thing: #123456;", 1)
    assert any("--new-thing is neither checked nor exempt" in p for p in problems(css))
