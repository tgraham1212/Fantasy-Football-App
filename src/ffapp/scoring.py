"""Turn a projected (or actual) stat line into fantasy points under league scoring."""

from __future__ import annotations

# Sleeper's own precomputed totals for standard formats. They are ignored when
# scoring so that each league's actual settings decide the points. Note that
# DEF bucket keys such as ``pts_allow_14_20`` also start with ``pts_`` and ARE
# real scoring categories, so only these exact keys are excluded.
PRECOMPUTED_KEYS = frozenset({"pts_ppr", "pts_half_ppr", "pts_std"})


def projected_points(stats: dict | None, scoring: dict[str, float]) -> float:
    """Dot product of a stat line with the league's scoring settings.

    Keys present in only one side contribute nothing; precomputed totals are skipped.
    """
    if not stats:
        return 0.0
    total = 0.0
    for key, value in stats.items():
        if key in PRECOMPUTED_KEYS or value is None:
            continue
        weight = scoring.get(key)
        if weight:
            total += float(value) * float(weight)
    return total


def record_points(record: dict | None, scoring: dict[str, float]) -> float:
    """Projected points for a stored projection record; a missing record counts as 0."""
    if record is None:
        return 0.0
    return projected_points(record.get("stats"), scoring)
