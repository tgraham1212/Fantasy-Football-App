from ffapp.projections import is_projection, to_record
from ffapp.scoring import projected_points, record_points
from tests.fixtures import REDRAFT, load

REDRAFT_SCORING = {k: float(v) for k, v in load(f"league/{REDRAFT['2026']}.json")["scoring_settings"].items()}


def test_kicker_field_goal_yards_and_extra_points():
    scoring = {"fgm_yds": 0.1, "xpm": 1.0, "fgm_0_19": 0.0, "fgm_50p": 0.0}
    assert projected_points({"fgm_yds": 120, "xpm": 3, "fga": 4, "fgm_50p": 1}, scoring) == 15.0


def test_missing_projection_counts_as_zero():
    assert record_points(None, REDRAFT_SCORING) == 0.0
    assert projected_points(None, REDRAFT_SCORING) == 0.0
    assert projected_points({}, REDRAFT_SCORING) == 0.0


def test_precomputed_totals_are_ignored_but_def_buckets_are_not():
    scoring = {"pts_allow_14_20": 1.0, "sack": 1.0, "pts_ppr": 1.0, "pts_half_ppr": 1.0, "pts_std": 1.0}
    stats = {"pts_allow_14_20": 0.4, "sack": 2.5, "pts_ppr": 50, "pts_half_ppr": 50, "pts_std": 50, "pts_allow": 21}
    assert projected_points(stats, scoring) == 2.9


def test_half_ppr_receiver_matches_league_scoring():
    scoring = {"rec": 0.5, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "fum_lost": -2.0}
    stats = {"rec": 6, "rec_yd": 80, "rec_td": 0.5, "rush_yd": 5, "fum_lost": 0.1, "rec_tgt": 8}
    assert projected_points(stats, scoring) == 3 + 8 + 3 + 0.5 - 0.2


def test_fixture_projections_score_close_to_sleeper_half_ppr():
    """Our league-scored projections should land near Sleeper's own half-PPR totals for skill players."""
    rows = [r for r in load("projections/2025/1.json") if is_projection(r)]
    diffs = []
    for row in rows:
        if row["player"]["position"] in ("QB", "RB", "WR", "TE"):
            ours = record_points(to_record(row), REDRAFT_SCORING)
            diffs.append(abs(ours - row["stats"]["pts_half_ppr"]))
    assert diffs
    diffs.sort()
    assert diffs[len(diffs) // 2] < 0.5, f"median diff {diffs[len(diffs) // 2]:.2f}"
