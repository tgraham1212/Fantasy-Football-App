"""The schedule summary the relay's clock decides the refresh mode from, and the stored run time."""
from datetime import datetime, timezone

from ffapp.schedule import read_last_run, refresh_schedule, schedule_summary, write_last_run, write_summary
from ffapp.sleeper import SleeperClient
from ffapp.store import Store
from tests.fixtures import FixtureSession

# Fixture schedule: week 10 all final; week 11 scheduled. The state fixture says week 10.


def client():
    return SleeperClient(FixtureSession(), min_interval=0, sleep=lambda s: None)


def test_summary_lists_this_and_next_weeks_games(seeded_store):
    refresh_schedule(client(), seeded_store)
    summary = schedule_summary(seeded_store, ["dynasty"], client().state())
    assert summary["offseason"] is False and summary["season"] == "2026" and summary["week"] == 10
    weeks = {g["week"] for g in summary["games"]}
    assert weeks == {10, 11}
    week10 = [g for g in summary["games"] if g["week"] == 10]
    assert week10 and all(g["state"] == "final" for g in week10)
    first = summary["games"][0]
    assert first["id"].startswith("2026-10-") and "@" in first["id"]
    assert first["kickoff"] == int(datetime.fromisoformat(first["slate"]).timestamp() * 1000)
    assert summary["games"] == sorted(summary["games"], key=lambda g: (g["kickoff"], g["id"]))


def test_offseason_when_no_league_is_in_season(seeded_store):
    league = seeded_store.read_league("dynasty", "2026")
    seeded_store.write_season("dynasty", seeded_store.read_season("dynasty", "2026"))
    path = seeded_store.season_dir("dynasty", "2026") / "league.json"
    from ffapp.store import write_json

    write_json(path, {**league, "status": "complete"})
    summary = schedule_summary(seeded_store, ["dynasty"], client().state())
    assert summary["offseason"] is True and summary["games"] == []


def test_summary_written_only_reports_a_change_once(seeded_store):
    refresh_schedule(client(), seeded_store)
    summary = schedule_summary(seeded_store, ["dynasty"], client().state())
    assert write_summary(seeded_store, summary) is True
    assert write_summary(seeded_store, summary) is False


def test_last_run_round_trip(tmp_path):
    store = Store(tmp_path / "data")
    assert read_last_run(store) is None
    at = datetime(2026, 11, 22, 17, 20, tzinfo=timezone.utc)
    write_last_run(store, at)
    assert read_last_run(store) == at
