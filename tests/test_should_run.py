from datetime import datetime, timezone

from ffapp.schedule import read_last_run, should_run, write_last_run
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from tests.fixtures import FixtureSession

# Fixture schedule: week 10 all final, last game Monday 2026-11-17 01:15 UTC; week 11 first kickoff
# Thursday 2026-11-20 01:15 UTC. The state fixture says week 10.


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def decide(tmp_path, now, last=None, mode="check", overrides=None):
    store = Store(tmp_path / "data")
    if last is not None:
        write_last_run(store, last)
    return should_run(client(overrides), store, now, mode)


def test_quiet_wednesday_does_not_run(tmp_path):
    d = decide(tmp_path, utc(2026, 11, 18, 20), last=utc(2026, 11, 18, 11))
    assert d.run is False and "no kickoff" in d.reason


def test_runs_before_a_kickoff(tmp_path):
    d = decide(tmp_path, utc(2026, 11, 20, 0, 20), last=utc(2026, 11, 19, 11))
    assert d.run is True and "kicks off" in d.reason


def test_kickoff_more_than_an_hour_away_waits(tmp_path):
    assert decide(tmp_path, utc(2026, 11, 19, 23, 20), last=utc(2026, 11, 19, 11)).run is False


def test_runs_after_a_game_goes_final(tmp_path):
    # last run Sunday evening before Monday night's game; Monday's game is now final
    d = decide(tmp_path, utc(2026, 11, 17, 6, 20), last=utc(2026, 11, 16, 23, 0))
    assert d.run is True and "final" in d.reason


def test_spacing_blocks_a_run_within_three_hours(tmp_path):
    d = decide(tmp_path, utc(2026, 11, 20, 0, 20), last=utc(2026, 11, 19, 22, 30))
    assert d.run is False and "min ago" in d.reason


def test_daily_and_manual_always_run(tmp_path):
    assert decide(tmp_path, utc(2026, 11, 18, 11), last=utc(2026, 11, 18, 10, 30), mode="daily").run is True
    assert decide(tmp_path, utc(2026, 11, 18, 11), last=utc(2026, 11, 18, 10, 30), mode="manual").run is True


def test_scoreboard_failure_skips_unless_daily(tmp_path):
    broken = {"espn/scoreboard/10.json": 503}
    assert decide(tmp_path, utc(2026, 11, 20, 0, 20), last=utc(2026, 11, 19, 11), overrides=broken).run is False
    d = decide(tmp_path, utc(2026, 11, 20, 11), mode="daily", overrides=broken)
    assert d.run is True and "schedule unavailable" in d.reason


def test_last_run_round_trip(tmp_path):
    store = Store(tmp_path / "data")
    assert read_last_run(store) is None
    write_last_run(store, utc(2026, 11, 22, 17, 20))
    assert read_last_run(store) == utc(2026, 11, 22, 17, 20)
