"""The refresh workflows keep to docs/refresh-modes.md: the hot run never commits or deploys, the
cold run commits and deploys only on change, and every workflow carries the same rebuilt paths."""
from pathlib import Path

import yaml

from ffapp.store import DERIVED_PATHS

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def steps(name, job):
    return load(name)["jobs"][job]["steps"]


def text(step):
    return str(step.get("run", "")) + str(step.get("uses", "")) + str(step.get("with", ""))


def test_hot_run_never_commits_pushes_or_deploys():
    wf = load("hot.yml")
    assert wf["permissions"] == {"contents": "read"}
    assert wf["concurrency"]["group"] == "hot"
    for step in steps("hot.yml", "hot"):
        body = text(step)
        assert "git commit" not in body and "git push" not in body and "pages" not in body, step


def test_cold_run_has_no_gate_or_test_suite_and_deploys_on_change():
    wf = load("refresh.yml")
    assert list(wf["jobs"]) == ["refresh"], "the gate job is gone: the relay's clock decides"
    run = steps("refresh.yml", "refresh")
    assert not any("pytest" in text(s) or "should-run" in text(s) for s in run)
    deploy = [s for s in run if "deploy-pages" in text(s) or "upload-pages-artifact" in text(s) or "stamp-site" in text(s)]
    assert deploy and all(s.get("if") == "steps.site.outputs.deploy == 'true'" for s in deploy)
    assert run[-1]["uses"].startswith("actions/cache/save"), "the cache is saved last, after a successful deploy"
    assert any("git diff --cached --quiet" in text(s) for s in run), "commit only when a record changed"
    triggers = wf[True] if True in wf else wf["on"]  # PyYAML reads the bare key `on` as True
    assert triggers["schedule"] == [{"cron": "0 11 * * *"}], "only the daily fallback is scheduled on GitHub"


def cache_paths(name, job):
    for step in steps(name, job):
        if "actions/cache/" in str(step.get("uses", "")):
            paths = step["with"]["path"]
            if "env.BUILD_PATHS" in paths:
                paths = load(name)["env"]["BUILD_PATHS"]
            return {line.strip() for line in paths.splitlines() if line.strip()}
    return set()


def test_every_workflow_carries_the_same_rebuilt_paths():
    expected = {f"data/{p}" for p in DERIVED_PATHS} | {"site/data"}
    assert cache_paths("refresh.yml", "refresh") == expected
    assert cache_paths("hot.yml", "hot") == expected
    assert cache_paths("site.yml", "test") == expected and cache_paths("site.yml", "deploy") == expected


def test_gitignore_matches_the_rebuilt_paths():
    ignore = (WORKFLOWS.parent.parent / ".gitignore").read_text(encoding="utf-8").splitlines()
    for path in DERIVED_PATHS:
        assert f"data/{path}" in ignore or f"data/{path}/" in ignore, path
    assert "site/data/" in ignore
