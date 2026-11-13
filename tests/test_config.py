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
