import copy
import hashlib
from pathlib import Path

from ffapp.cli import main
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
    code = run(tmp_path, cfg, "refresh", overrides=projections_for_2026())
    assert code == 0
    assert (tmp_path / "data" / "leagues" / "dynasty" / "2026" / "league.json").exists()
    assert (tmp_path / "data" / "projections" / "2026" / "week_17.json").exists()
    assert (tmp_path / "data" / "odds" / "dynasty" / "2026" / "asof_09.json").exists()
    assert (tmp_path / "site-data" / "dynasty.json").exists()
    assert (tmp_path / "site-data" / "index.json").exists()


def test_bad_config_exits_2(tmp_path):
    cfg = tmp_path / "leagues.yaml"
    cfg.write_text("leagues: {}\n", encoding="utf-8")
    assert main(["--config", str(cfg), "--data", str(tmp_path / "data"), "sync"], client=client()) == 2
