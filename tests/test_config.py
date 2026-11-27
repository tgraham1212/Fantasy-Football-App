from pathlib import Path

import pytest

from ffapp.config import ConfigError, load_config, parse_config

REPO_ROOT = Path(__file__).resolve().parents[1]


def valid_raw():
    return {
        "leagues": {
            "dynasty": {"league_id": "1339662153812025344", "name": "Taco Tuesdays"},
            "redraft": {"league_id": "1389347876550770688", "name": "Fall Guys"},
        },
        "overrides": [
            {"league": "redraft", "season": "2023", "from_week": 6, "scoring": {"fgm_yds": 0.1}},
        ],
    }


def test_repo_config_loads_both_leagues():
    config = load_config(REPO_ROOT / "config" / "leagues.yaml")
    assert set(config.leagues) == {"dynasty", "redraft"}
    assert config.leagues["dynasty"].league_id == "1339662153812025344"
    assert config.leagues["redraft"].league_id == "1389347876550770688"
    assert config.overrides == []
    assert config.simulation.residual_scale == 1.0
    assert config.simulation.replacement_top_n == 5 and config.simulation.prior_weeks == 4.0


def test_valid_config_parses_overrides():
    config = parse_config(valid_raw())
    [override] = config.overrides_for("redraft", "2023")
    assert override.from_week == 6
    assert override.scoring == {"fgm_yds": 0.1}
    assert config.overrides_for("dynasty", "2023") == []


def test_missing_league_id_rejected():
    raw = valid_raw()
    del raw["leagues"]["dynasty"]["league_id"]
    with pytest.raises(ConfigError, match="league_id is required"):
        parse_config(raw)


def test_non_numeric_league_id_rejected():
    raw = valid_raw()
    raw["leagues"]["dynasty"]["league_id"] = "taco-tuesdays"
    with pytest.raises(ConfigError, match="numeric"):
        parse_config(raw)


def test_unknown_top_level_key_rejected():
    raw = valid_raw()
    raw["sleeper_token"] = "abc"
    with pytest.raises(ConfigError, match="unknown keys: sleeper_token"):
        parse_config(raw)


def test_unknown_league_key_rejected():
    raw = valid_raw()
    raw["leagues"]["dynasty"]["colour"] = "red"
    with pytest.raises(ConfigError, match="leagues.dynasty has unknown keys"):
        parse_config(raw)


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda o: o.pop("from_week"), "missing: from_week"),
        (lambda o: o.__setitem__("from_week", 0), "positive integer"),
        (lambda o: o.__setitem__("from_week", "6"), "positive integer"),
        (lambda o: o.__setitem__("league", "keeper"), "not a configured league"),
        (lambda o: o.__setitem__("season", "23"), "4-digit year"),
        (lambda o: o.__setitem__("scoring", {}), "at least one scoring key"),
        (lambda o: o.__setitem__("scoring", {"fgm_yds": "0.1"}), "must be a number"),
        (lambda o: o.__setitem__("note", "x"), "unknown keys: note"),
    ],
)
def test_bad_override_rejected(mutation, message):
    raw = valid_raw()
    mutation(raw["overrides"][0])
    with pytest.raises(ConfigError, match=message):
        parse_config(raw)


def test_overrides_must_be_list():
    raw = valid_raw()
    raw["overrides"] = {"league": "redraft"}
    with pytest.raises(ConfigError, match="overrides must be a list"):
        parse_config(raw)


def test_missing_file_reports_path(tmp_path):
    with pytest.raises(ConfigError, match="cannot read"):
        load_config(tmp_path / "nope.yaml")


def test_residual_scale_defaults_to_one_without_simulation_section():
    assert parse_config(valid_raw()).simulation.residual_scale == 1.0


def test_residual_scale_parsed():
    raw = valid_raw()
    raw["simulation"] = {"residual_scale": 0.9}
    assert parse_config(raw).simulation.residual_scale == 0.9
    raw["simulation"] = {"residual_scale": 2}
    assert parse_config(raw).simulation.residual_scale == 2.0


@pytest.mark.parametrize("bad", [0, -1, "big", True])
def test_invalid_residual_scale_rejected(bad):
    raw = valid_raw()
    raw["simulation"] = {"residual_scale": bad}
    with pytest.raises(ConfigError, match="residual_scale"):
        parse_config(raw)


def test_unknown_simulation_key_rejected():
    raw = valid_raw()
    raw["simulation"] = {"runs": 5}
    with pytest.raises(ConfigError, match="simulation has unknown keys: runs"):
        parse_config(raw)


def test_replacement_settings_default_and_parse():
    cfg = parse_config(valid_raw()).simulation
    assert cfg.replacement_top_n == 3 and cfg.prior_weeks == 4.0
    raw = valid_raw()
    raw["simulation"] = {"replacement_top_n": 5, "prior_weeks": 2}
    cfg = parse_config(raw).simulation
    assert cfg.replacement_top_n == 5 and cfg.prior_weeks == 2.0 and cfg.residual_scale == 1.0


@pytest.mark.parametrize(
    "key, bad",
    [("replacement_top_n", 0), ("replacement_top_n", 2.5), ("replacement_top_n", True), ("prior_weeks", -1), ("prior_weeks", "four")],
)
def test_invalid_replacement_settings_rejected(key, bad):
    raw = valid_raw()
    raw["simulation"] = {key: bad}
    with pytest.raises(ConfigError, match=key):
        parse_config(raw)


def test_ratings_defaults_without_section():
    cfg = parse_config(valid_raw()).ratings
    assert cfg.revert == pytest.approx(1 / 3)
    assert cfg.early_k == (2.0, 1.75, 1.5, 1.25)
    assert cfg.start_mu == 1000.0 and cfg.start_sigma == pytest.approx(1000 / 3)
    assert cfg.ewma_weight == 0.2


def test_ratings_parsed():
    raw = valid_raw()
    raw["ratings"] = {"revert": 0.5, "early_k": [3, 2], "start_mu": 1500, "ewma_weight": 0.1}
    cfg = parse_config(raw).ratings
    assert cfg.revert == 0.5 and cfg.early_k == (3.0, 2.0) and cfg.start_mu == 1500.0
    assert cfg.start_sigma == 500.0, "start_sigma defaults to a third of start_mu"
    assert cfg.ewma_weight == 0.1
    raw["ratings"]["start_sigma"] = 250
    assert parse_config(raw).ratings.start_sigma == 250.0


@pytest.mark.parametrize(
    "key, bad",
    [
        ("revert", 1.5), ("revert", -0.1), ("revert", "third"), ("revert", True),
        ("early_k", []), ("early_k", [2, 0.5]), ("early_k", [1.5, 2]), ("early_k", 2), ("early_k", [True]),
        ("start_mu", 0), ("start_sigma", -1), ("ewma_weight", 0), ("ewma_weight", 1.5),
    ],
)
def test_invalid_ratings_rejected(key, bad):
    raw = valid_raw()
    raw["ratings"] = {key: bad}
    with pytest.raises(ConfigError, match=f"ratings.{key}"):
        parse_config(raw)


def test_unknown_ratings_key_rejected():
    raw = valid_raw()
    raw["ratings"] = {"k_factor": 32}
    with pytest.raises(ConfigError, match="ratings has unknown keys: k_factor"):
        parse_config(raw)


def test_site_refresh_url_is_optional():
    assert parse_config(valid_raw()).site.refresh_url is None
    raw = valid_raw()
    raw["site"] = {"refresh_url": "https://ffapp-refresh.example.workers.dev/"}
    assert parse_config(raw).site.refresh_url == "https://ffapp-refresh.example.workers.dev"
    raw["site"] = {"refresh_url": ""}
    assert parse_config(raw).site.refresh_url is None


@pytest.mark.parametrize("site", [{"refresh_url": "http://plain.example"}, {"refresh_url": 42}, {"refresh_url": "https://a b"}, {"other": 1}, "x"])
def test_site_refresh_url_invalid(site):
    raw = valid_raw()
    raw["site"] = site
    with pytest.raises(ConfigError):
        parse_config(raw)


def test_repo_redraft_rivals_follow_the_team():
    rivals = load_config(REPO_ROOT / "config" / "leagues.yaml").leagues["redraft"].rivals
    assert rivals.rival_of(1) == 9 and rivals.rival_of(9) == 1 and rivals.rival_of(8) == 12
    assert rivals.rivalry_week["2025"] == 7 and rivals.rivalry_week["2026"] is None


def test_league_without_rivals_uses_none():
    assert parse_config(valid_raw()).leagues["dynasty"].rivals is None


@pytest.mark.parametrize("rivals, message", [
    ({"pairs": [[1, 1]]}, "two different"),
    ({"pairs": [[1, 2], [2, 3]]}, "only one rival"),
    ({"pairs": [[0, 2]]}, "positive roster ids"),
    ({"pairs": []}, "non-empty"),
    ({"pairs": [[1, 2]], "rivalry_week": {"2025": 30}}, "week number or null"),
    ({"pairs": [[1, 2]], "colour": "red"}, "unknown keys"),
])
def test_bad_rivals_rejected(rivals, message):
    raw = valid_raw()
    raw["leagues"]["redraft"]["rivals"] = rivals
    with pytest.raises(ConfigError, match=message):
        parse_config(raw)



def test_repo_redraft_keepers():
    """league-draft 4.11.5: the redraft league lists 2026's five keepers by Sleeper id."""
    cfg = load_config()
    assert set(cfg.leagues["redraft"].keepers["2026"]) == {"10229", "7588", "9488", "12514", "12481"}
    assert cfg.leagues["dynasty"].keepers == {}


@pytest.mark.parametrize("keepers, message", [
    ({"26": ["1"]}, "4-digit seasons"),
    ({"2026": "9488"}, "list of Sleeper Player ids"),
    ({"2026": ["A. Name"]}, "list of Sleeper Player ids"),
    ({"2026": ["9488", "9488"]}, "twice"),
])
def test_bad_keepers_rejected(tmp_path, keepers, message):
    import yaml
    path = tmp_path / "leagues.yaml"
    path.write_text(yaml.safe_dump({"leagues": {"redraft": {"league_id": "1", "keepers": keepers}}}), encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(path)
