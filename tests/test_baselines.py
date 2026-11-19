"""The baseline comparison used by the standards checks: new findings fail, fixed ones must be removed."""

from __future__ import annotations

import json

from tests import baselines


def test_compare_both_ways(tmp_path, monkeypatch):
    monkeypatch.setattr(baselines, "HERE", tmp_path)
    monkeypatch.delenv("UPDATE_BASELINES", raising=False)
    (tmp_path / "demo.json").write_text(json.dumps(["a", "b"]), encoding="utf-8")
    assert baselines.compare("demo", {"a", "b"}, "thing") == []
    assert baselines.compare("demo", {"a", "b", "c"}, "thing") == ["new thing: c"]
    assert baselines.compare("demo", {"a"}, "thing") == ["fixed, remove from tests/baselines/demo.json: b"]


def test_update_rewrites(tmp_path, monkeypatch):
    monkeypatch.setattr(baselines, "HERE", tmp_path)
    monkeypatch.setenv("UPDATE_BASELINES", "1")
    assert baselines.compare("demo", {"z", "y"}, "thing") == []
    assert json.loads((tmp_path / "demo.json").read_text(encoding="utf-8")) == ["y", "z"]
