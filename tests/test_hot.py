"""The hot run (docs/refresh-modes.md): one bundle, the data folder untouched."""
import base64
import json
from datetime import datetime, timezone

from ffapp.cli import main
from ffapp.config import load_config
from ffapp.hot import bundle_meta, content_hash, run_hot
from tests.test_refresh import client, projections_for_2026, run, stats_for_2026, tree_digest, write_config


def refreshed(tmp_path):
    cfg = write_config(tmp_path)
    assert run(tmp_path, cfg, "refresh", overrides={**projections_for_2026(), **stats_for_2026()}) == 0
    return cfg


def test_hot_run_builds_one_bundle_and_leaves_data_unchanged(tmp_path):
    cfg = refreshed(tmp_path)
    before = tree_digest(tmp_path / "data")
    now = datetime(2026, 11, 16, 20, tzinfo=timezone.utc)
    result = run_hot(client({**projections_for_2026(), **stats_for_2026()}), load_config(cfg), tmp_path / "data", runs=500, now=now)
    assert tree_digest(tmp_path / "data") == before, "the hot run works on a scratch copy"
    bundle = result.bundle
    assert bundle["generated_at"] == "2026-11-16T20:00:00+00:00" and bundle["week"] == 10 and bundle["season"] == "2026"
    assert set(bundle["files"]) == {"dynasty.json", "dynasty/games/index.json", "dynasty/games/week_10.json"}
    assert bundle["files"]["dynasty.json"]["teams"], "the league forecast as the page reads it"
    assert bundle["files"]["dynasty/games/week_10.json"]["games"]
    assert bundle["games"] and all(k.startswith("2026-10-") and "@" in k for k in bundle["games"])
    assert set(bundle["games"].values()) <= {"scheduled", "in_progress", "final"}
    assert bundle["hash"] == content_hash(bundle)


def test_content_hash_ignores_times_and_meta_fits_the_relay():
    bundle = {"generated_at": "a", "games": {"2026-11-NYJ@NE": "final"}, "files": {"x.json": {"generated_at": "a", "teams": [1]}}}
    later = {**bundle, "generated_at": "b", "files": {"x.json": {"generated_at": "b", "teams": [1]}}}
    assert content_hash(bundle) == content_hash(later)
    assert content_hash(bundle) != content_hash({**bundle, "files": {"x.json": {"teams": [2]}}})
    many = {"hash": "h", "generated_at": "2026-11-22T18:00:00+00:00",
            "games": {f"2026-11-T{i:02d}X@T{i:02d}Y": "in_progress" for i in range(16)}}
    meta = bundle_meta(many)
    decoded = json.loads(base64.b64decode(meta))
    assert decoded["g"]["2026-11-T00X@T00Y"] == "i" and len(json.dumps(decoded)) < 1024


def test_hot_command_writes_the_bundle_and_its_meta(tmp_path, capsys):
    cfg = refreshed(tmp_path)
    out = tmp_path / "live.json"
    argv = ["--config", str(cfg), "--data", str(tmp_path / "data"), "--site-data", str(tmp_path / "site-data"), "hot", "--out", str(out), "--runs", "300"]
    assert main(argv, client=client({**projections_for_2026(), **stats_for_2026()})) == 0
    bundle = json.loads(out.read_text(encoding="utf-8"))
    meta = json.loads(base64.b64decode((tmp_path / "live.json.meta").read_text(encoding="ascii")))
    assert meta["h"] == bundle["hash"] and meta["t"] == bundle["generated_at"]
