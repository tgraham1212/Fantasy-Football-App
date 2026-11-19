"""The progress line printed during long test runs (tests/progress.py)."""

from tests.progress import Progress


class _Config:
    pluginmanager = None


def test_progress_line_reports_count_time_estimate_failures_and_current_test():
    p = Progress(_Config(), every=60)
    p.total, p.done, p.failed, p.start = 800, 200, 1, 0.0
    line = p.line(300.0, "tests/layout/test_layout.py::test_control_keeps_the_layout[webkit-refresh-440]")
    assert line == ("progress: 200/800 tests (25%) · 5:00 elapsed · about 15 min left · 1 failed"
                    " · now test_layout.py::test_control_keeps_the_layout[webkit-refresh-440]")


def test_progress_line_has_no_estimate_before_the_first_test_finishes():
    p = Progress(_Config(), every=60)
    p.total, p.start = 10, 0.0
    assert "left" not in p.line(5.0, "tests/test_x.py::test_a")


def test_progress_line_says_under_a_minute_near_the_end():
    p = Progress(_Config(), every=60)
    p.total, p.done, p.start = 100, 99, 0.0
    assert "under 1 min left" in p.line(99.0, "tests/test_x.py::test_a")
