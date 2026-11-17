"""Generate the 12 per-team chart colours for site/styles.css.

Walks the OKLCH hue wheel starting from the brand blue, alternating lightness
between neighbouring steps so that adjacent hues stay apart for colour-blind
readers (red/green neighbours otherwise collapse under protan/deutan vision).
Light and dark themes get separate sets tuned to their own surfaces.

Dependency-free: the OKLab maths is from Björn Ottosson's reference
implementation. Out-of-gamut colours have their chroma reduced until they fit sRGB.

Former members on the rating chart get neutral greys instead of hues: the 12 hues
are spoken for by current members, and no set of 17 hues separates. Greys differ in
lightness only, so they are spaced by at least 0.15 in OKLCH L (the validator's
normal-vision floor), which leaves three steps that also keep 3:1 contrast against
each surface; the chart pairs them with line dashes to tell six apart.

Run:  python tools/team_palette.py            -> prints both sets as CSS tokens
      python tools/team_palette.py --hexes    -> comma-separated hexes per mode,
                                                 for the dataviz validate_palette.js
      python tools/team_palette.py --greys    -> the former-member greys as CSS tokens
      python tools/team_palette.py --greys --hexes
      python tools/team_palette.py --diverging  -> the Games page win-probability ramp as CSS
                                                   tokens, with text contrast at 11 steps
      python tools/team_palette.py --diverging --hexes

Win-probability ramp (Games page): grey at 50%, green toward 100%, red toward 0%, mixed
in OKLab between the midpoint and each pole. Green/red is the league's ask; it is the
pair colour-blind readers confuse most, so the two arms also differ in lightness (green
lighter, red darker) and every cell prints its percentage, so colour is never the only
cue. Validated with the dataviz validate_palette.py on the poles (2026-11-17), see
DIVERGING_CHECK below for the measured values.
"""

from __future__ import annotations

import math
import sys

BRAND_HUE = 258.0  # OKLCH hue of the light-theme accent #2a78d6

# Slots strictly alternate dark/light so that list neighbours differ in lightness
# as well as hue. Hues that only hold chroma when light (orange, teal, cyan, pink,
# gold, lime) take the light slots; hues that stay vivid when dark (blue, magenta,
# red, green, violet, brown) take the dark slots. The order interleaves the wheel
# so that neighbours are also far apart in hue; it starts at the brand blue.
HUES = [BRAND_HUE, 50, 325, 175, 75, 215, 155, 345, 290, 95, 20, 125]
# (dark-slot L, light-slot L, chroma) per theme. Light surfaces want darker,
# more saturated marks; dark surfaces want lighter, slightly softer ones.
THEMES = {
    "light": {"L": (0.48, 0.62), "C": 0.165},
    "dark": {"L": (0.54, 0.66), "C": 0.140},
}
STEPS = len(HUES)
# Former-member greys: OKLCH lightness steps per theme, chroma 0. Validated with the
# dataviz validate_palette.js (2026-11-15): adjacent-pair ΔE 16 (normal and CVD) and
# every grey >= 3:1 against its surface. The validator's lightness-band and chroma-floor
# checks are for hue palettes and fail for any neutral; they are expected here.
GREYS = {
    "light": (0.28, 0.44, 0.60),
    "dark": (0.84, 0.68, 0.52),
}


# Win-probability poles and midpoint (OKLCH) per theme, and the text colour used on every step.
DIVERGING = {
    "light": {"hi": (0.80, 0.17, 145.0), "mid": (0.93, 0.0, 0.0), "lo": (0.70, 0.17, 25.0), "ink": "#0b0b0b"},
    "dark": {"hi": (0.52, 0.13, 145.0), "mid": (0.31, 0.0, 0.0), "lo": (0.40, 0.15, 25.0), "ink": "#f0efec"},
}
# dataviz validate_palette.py on the two poles (2026-11-17), plus text contrast from diverging_steps():
#   light #f66d67 / #6fda75: CVD dE 9.0 deutan PASS, normal dE 31.1 PASS, text >= 6.84:1 at every step
#   dark  #861118 / #2e7c35: CVD dE 11.1 deutan PASS, normal dE 25.7 PASS, text >= 4.51:1 at every step
# Expected non-passes: the lightness band (a rule for chart marks, not text-carrying cell fills) and
# pole contrast against the page (< 3:1 needs printed values, which every cell has).
DIVERGING_CHECK = "see comment above"


def oklch_to_srgb(L: float, C: float, h_deg: float) -> tuple[float, float, float]:
    h = math.radians(h_deg)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return tuple(_gamma(c) for c in (r, g, bl))


def _gamma(c: float) -> float:
    return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c


def in_gamut(rgb: tuple[float, float, float]) -> bool:
    return all(-0.0005 <= c <= 1.0005 for c in rgb)


def to_hex(L: float, C: float, h: float) -> str:
    """Hex for the OKLCH colour, reducing chroma until it fits sRGB."""
    while C > 0:
        rgb = oklch_to_srgb(L, C, h)
        if in_gamut(rgb):
            break
        C -= 0.002
    rgb = oklch_to_srgb(L, max(C, 0), h)
    return "#" + "".join(f"{round(min(max(c, 0), 1) * 255):02x}" for c in rgb)


def palette(mode: str) -> list[str]:
    cfg = THEMES[mode]
    return [to_hex(cfg["L"][i % 2], cfg["C"], hue % 360) for i, hue in enumerate(HUES)]


def greys(mode: str) -> list[str]:
    return [to_hex(L, 0.0, 0.0) for L in GREYS[mode]]


def _linear(c: float) -> float:
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def hex_to_oklab(hx: str) -> tuple[float, float, float]:
    r, g, b = (_linear(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363329395 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s_,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s_,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s_,
    )


def oklab_to_hex(L: float, a: float, b: float) -> str:
    C, h = math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360
    return to_hex(L, C, h)


def luminance(hx: str) -> float:
    r, g, b = (_linear(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def diverging(mode: str) -> dict[str, str]:
    cfg = DIVERGING[mode]
    return {k: to_hex(*cfg[k]) for k in ("hi", "mid", "lo")} | {"ink": cfg["ink"]}


def diverging_steps(mode: str, steps: int = 11) -> list[tuple[int, str, float]]:
    """(percent, fill, text contrast) at evenly spaced win probabilities, mixed in OKLab like the CSS."""
    ramp = diverging(mode)
    mid = hex_to_oklab(ramp["mid"])
    out = []
    for i in range(steps):
        p = i / (steps - 1)
        pole = hex_to_oklab(ramp["hi"] if p >= 0.5 else ramp["lo"])
        t = abs(p - 0.5) * 2
        fill = oklab_to_hex(*(m + (q - m) * t for m, q in zip(mid, pole)))
        out.append((round(p * 100), fill, round(contrast(fill, ramp["ink"]), 2)))
    return out


def main(argv: list[str]) -> None:
    if "--diverging" in argv:
        for mode in DIVERGING:
            ramp = diverging(mode)
            if "--hexes" in argv:
                print(f"{mode}: {ramp['lo']},{ramp['mid']},{ramp['hi']}")
                continue
            print(f"/* {mode} win-probability ramp: generated by tools/team_palette.py --diverging */")
            print(f"  --win-hi: {ramp['hi']};\n  --win-mid: {ramp['mid']};\n  --win-lo: {ramp['lo']};\n  --win-ink: {ramp['ink']};")
            worst = min(c for _, _, c in diverging_steps(mode))
            print(f"  /* text contrast at 0,10..100%: worst {worst}:1 */")
        return
    if "--greys" in argv:
        for mode in THEMES:
            if "--hexes" in argv:
                print(f"{mode}: {','.join(greys(mode))}")
            else:
                print(f"/* {mode} former-member greys: generated by tools/team_palette.py --greys */")
                for i, hx in enumerate(greys(mode), 1):
                    print(f"  --former-{i}: {hx};")
        return
    if "--hexes" in argv:
        for mode in THEMES:
            print(f"{mode}: {','.join(palette(mode))}")
        return
    for mode in THEMES:
        print(f"/* {mode}: generated by tools/team_palette.py */")
        for i, hx in enumerate(palette(mode), 1):
            print(f"  --team-{i}: {hx};")


if __name__ == "__main__":
    main(sys.argv[1:])
