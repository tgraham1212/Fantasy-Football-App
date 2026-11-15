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
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "asof_09.json").exists()
    assert (tmp_path / "site-data" / "dynasty.json").exists()
    assert (tmp_path / "site-data" / "index.json").exists()


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


def test_refresh_runs_six_steps_and_stats_failure_stops_before_replacement(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "sync") == 0
    before = tree_digest(tmp_path / "data")
    overrides = {**projections_for_2026(), **stats_for_2026(), "stats/2026/1.json": 500}
    code = run(tmp_path, cfg, "refresh", overrides=overrides)
    assert code != 0
    assert not (tmp_path / "data" / "replacement").exists() and not (tmp_path / "data" / "odds").exists()
    assert not (tmp_path / "data" / "stats").exists()
    assert {k: v for k, v in tree_digest(tmp_path / "data").items() if not k.startswith("projections")} == {k: v for k, v in before.items() if not k.startswith("projections")}

    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    assert (tmp_path / "data" / "stats" / "2026" / "week_01.json").exists()
    assert (tmp_path / "data" / "replacement" / "dynasty" / "2026.json").exists()
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "asof_09.json").exists()
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
