import copy
import hashlib
import json
from pathlib import Path

from ffapp.cli import main
from ffapp.projections import upsert_week
from ffapp.store import Store
from ffapp.sleeper import SleeperClient
from tests.fixtures import DYNASTY, FixtureSession, load


def tree_digest(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def write_config(tmp_path):
    cfg = tmp_path / "leagues.yaml"
    cfg.write_text(
        f'leagues:\n  dynasty:\n    league_id: "{DYNASTY["2026"]}"\n    name: Taco Tuesdays\noverrides: []\n',
        encoding="utf-8",
    )
    return cfg


def projections_for_2026():
    """FixtureSession overrides serving the 2025 week-1 rows as every 2026 week."""
    rows = load("projections/2025/1.json")
    overrides = {}
    for week in range(1, 18):
        reused = copy.deepcopy(rows)
        for row in reused:
            row["season"] = "2026"
            row["week"] = week
        overrides[f"projections/2026/{week}.json"] = reused
    return overrides


def client(overrides=None):
    return SleeperClient(FixtureSession(overrides), min_interval=0, sleep=lambda s: None)


def run(tmp_path, cfg, *args, overrides=None):
    argv = ["--config", str(cfg), "--data", str(tmp_path / "data"), "--site-data", str(tmp_path / "site-data"), *args]
    return main(argv, client=client(overrides))


def test_refresh_stops_at_projections_failure_and_leaves_data_unchanged(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    before = tree_digest(tmp_path / "data")

    # projections for 2026 week 1 fail on the server; nothing later may run
    code = run(tmp_path, cfg, "refresh", overrides={"projections/2026/1.json": 503})
    assert code != 0
    assert tree_digest(tmp_path / "data") == before, "a failed refresh changes nothing on disk"
    assert not (tmp_path / "data" / "odds").exists()
    assert not (tmp_path / "site-data").exists()


def test_refresh_runs_every_step_when_sources_work(tmp_path):
    cfg = write_config(tmp_path)
    code = run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()})
    assert code == 0
    assert (tmp_path / "data" / "leagues" / "dynasty" / "2026" / "league.json").exists()
    assert (tmp_path / "data" / "projections" / "2026" / "week_17.json").exists()
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "live.json").exists()  # the fixture schedule has week 10 under way
    assert (tmp_path / "site-data" / "dynasty.json").exists()
    assert (tmp_path / "site-data" / "index.json").exists()
    # the site's "Updated" time is this run's start, the same moment last_run.json records
    index = json.loads((tmp_path / "site-data" / "index.json").read_text(encoding="utf-8"))
    last_run = json.loads((tmp_path / "data" / "refresh" / "last_run.json").read_text(encoding="utf-8"))
    assert index["last_refresh"] == last_run["started_at"]


def test_stats_command_writes_current_season(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    rows = load("stats/2025/1.json")
    for row in rows:
        row["season"] = "2026"
    overrides = {f"stats/2026/{w}.json": (rows if w == 1 else []) for w in range(1, 18)}
    assert run(tmp_path, cfg, "stats", overrides=overrides) == 0
    assert (tmp_path / "data" / "stats" / "2026" / "week_01.json").exists()
    assert not (tmp_path / "data" / "stats" / "2026" / "week_02.json").exists()


def stats_for_2026():
    rows = load("stats/2025/1.json")
    for row in rows:
        row["season"] = "2026"
    return {f"stats/2026/{w}.json": (rows if w == 1 else []) for w in range(1, 18)}


def test_refresh_steps_in_order():
    from ffapp.cli import REFRESH_STEPS

    assert [name for name, _ in REFRESH_STEPS] == [
        "sync", "projections", "stats", "schedule", "snapshot", "trending", "ratings", "replacement", "war", "simulate", "games", "export",
    ]


def test_refresh_continues_past_a_snapshot_failure_with_a_warning(tmp_path, capsys, monkeypatch):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    overrides = {**projections_for_2026(), **stats_for_2026(), "espn/players.json": 503}
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert run(tmp_path, cfg, "refresh", overrides=overrides) == 0
    out = capsys.readouterr().out
    assert "WARNING  Refresh skipped a step: snapshot failed" in out and "::warning" not in out
    assert not (tmp_path / "data" / "espn" / "2026").exists() and not (tmp_path / "data" / "espn" / "2022").exists()
    assert (tmp_path / "data" / "espn" / "crosswalk.json").exists()  # the Sleeper-side crosswalk does not need ESPN
    assert not (tmp_path / "data" / "war").exists()  # no snapshots stored, so every season is skipped, which is not a failure
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "live.json").exists()  # the fixture schedule has week 10 under way
    assert (tmp_path / "site-data" / "dynasty.json").exists()

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert run(tmp_path, cfg, "refresh", overrides=overrides) == 0
    assert "::warning title=Refresh skipped a step::snapshot failed" in capsys.readouterr().out


def test_clean_refresh_prints_no_warning_and_writes_snapshots_and_war(tmp_path, capsys):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    out = capsys.readouterr().out
    assert "WARNING" not in out and "::warning" not in out
    assert (tmp_path / "data" / "espn" / "2026" / "season.json").exists()
    assert (tmp_path / "data" / "espn" / "2026" / "week_10.json").exists()
    assert (tmp_path / "data" / "espn" / "crosswalk.json").exists()
    assert (tmp_path / "data" / "war" / "dynasty" / "2026.json").exists()


def test_war_failure_stops_the_refresh(tmp_path, monkeypatch):
    import ffapp.cli as cli

    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    monkeypatch.setattr(cli, "REFRESH_STEPS", tuple((n, (lambda ctx: 1) if n == "war" else h) for n, h in cli.REFRESH_STEPS))
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 1
    assert not (tmp_path / "data" / "odds").exists() and not (tmp_path / "site-data").exists()


def test_ratings_command_writes_every_league(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    assert run(tmp_path, cfg, "ratings") == 0
    payload = json.loads((tmp_path / "data" / "ratings" / "dynasty.json").read_text(encoding="utf-8"))
    assert payload["league_key"] == "dynasty" and len(payload["managers"]) >= 12


def test_refresh_runs_every_step_and_stats_failure_stops_before_ratings(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    before = tree_digest(tmp_path / "data")
    overrides = {**projections_for_2026(), **stats_for_2026(), "stats/2026/1.json": 500}
    code = run(tmp_path, cfg, "refresh", overrides=overrides)
    assert code != 0
    assert not (tmp_path / "data" / "replacement").exists() and not (tmp_path / "data" / "odds").exists()
    assert not (tmp_path / "data" / "stats").exists() and not (tmp_path / "data" / "ratings").exists()
    assert {k: v for k, v in tree_digest(tmp_path / "data").items() if not k.startswith("projections")} == {k: v for k, v in before.items() if not k.startswith("projections")}

    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    assert (tmp_path / "data" / "stats" / "2026" / "week_01.json").exists()
    assert (tmp_path / "data" / "ratings" / "dynasty.json").exists()
    assert (tmp_path / "data" / "replacement" / "dynasty" / "2026.json").exists()
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "live.json").exists()  # the fixture schedule has week 10 under way
    assert (tmp_path / "site-data" / "dynasty.json").exists()


def test_refresh_does_not_calibrate(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    assert not (tmp_path / "data" / "calibration").exists()
    assert not (tmp_path / "data" / "odds" / "dynasty" / "2025").exists()
    assert not (tmp_path / "site-data" / "calibration.json").exists()


def test_calibrate_command_writes_report_and_export_publishes_it(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    # 2025 projections: the week-1 fixture reused for every week of the completed season
    rows = load("projections/2025/1.json")
    for week in range(1, 18):
        reused = copy.deepcopy(rows)
        for row in reused:
            row["week"] = week
        upsert_week(Store(tmp_path / "data"), "2025", week, reused)
    assert run(tmp_path, cfg, "projections", overrides=projections_for_2026()) == 0
    assert run(tmp_path, cfg, "calibrate", "--runs", "200", "--residual-scale", "1.1") == 0
    report = json.loads((tmp_path / "data" / "calibration" / "report.json").read_text(encoding="utf-8"))
    assert report["runs"] == 200 and report["residual_scale"] == 1.1
    assert (tmp_path / "data" / "calibration" / "report.md").exists()
    assert (tmp_path / "data" / "odds" / "dynasty" / "2025" / "asof_16.json").exists()
    assert run(tmp_path, cfg, "calibrate", "--residual-scale", "0") == 2

    assert run(tmp_path, cfg, "simulate", "--runs", "200") == 0
    assert run(tmp_path, cfg, "export") == 0
    index = json.loads((tmp_path / "site-data" / "index.json").read_text(encoding="utf-8"))
    assert index["calibration"] == {"generated_at": report["generated_at"], "file": "calibration.json"}
    published = json.loads((tmp_path / "site-data" / "calibration.json").read_text(encoding="utf-8"))
    assert published == report


def test_bad_config_exits_2(tmp_path):
    cfg = tmp_path / "leagues.yaml"
    cfg.write_text("leagues: {}\n", encoding="utf-8")
    assert main(["--config", str(cfg), "--data", str(tmp_path / "data"), "sync"], client=client()) == 2


def test_schedule_failure_continues_with_a_warning_and_games_failure_stops(tmp_path, capsys, monkeypatch):
    import ffapp.cli as cli

    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    overrides = {**projections_for_2026(), **stats_for_2026(), "espn/scoreboard/10.json": 503}
    assert run(tmp_path, cfg, "refresh", overrides=overrides) == 0
    out = capsys.readouterr().out
    assert "WARNING  Refresh skipped a step: schedule failed" in out
    assert (tmp_path / "data" / "games" / "dynasty" / "2026").exists()  # games still ran without a schedule
    assert (tmp_path / "data" / "refresh" / "last_run.json").exists()

    monkeypatch.setattr(cli, "REFRESH_STEPS", tuple((n, (lambda ctx: 1) if n == "games" else h) for n, h in cli.REFRESH_STEPS))
    before = (tmp_path / "data" / "refresh" / "last_run.json").read_text(encoding="utf-8")
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 1
    assert (tmp_path / "data" / "refresh" / "last_run.json").read_text(encoding="utf-8") == before  # a failed run records nothing


def test_should_run_writes_github_output(tmp_path, monkeypatch):
    cfg = write_config(tmp_path)
    out = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert run(tmp_path, cfg, "should-run", "--mode", "manual") == 0
    assert out.read_text(encoding="utf-8") == "run=true" + chr(10)


def test_refresh_continues_past_a_trending_failure_with_a_warning(tmp_path, capsys):
    cfg = write_config(tmp_path)
    overrides = {**projections_for_2026(), **stats_for_2026(), "players/nfl/trending/add.json": 503}
    assert run(tmp_path, cfg, "refresh", overrides=overrides) == 0
    out = capsys.readouterr().out
    # a plain warning line locally, a GitHub annotation under Actions
    assert "Refresh skipped a step: trending failed" in out or "Refresh skipped a step::trending failed" in out
    assert (tmp_path / "site-data" / "index.json").exists()
