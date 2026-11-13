from ffapp.config import Config, LeagueConfig, ScoringOverride
from ffapp.league import owners, resolve_settings, starter_slots
from tests.fixtures import DYNASTY, REDRAFT, load


def test_owner_mapping_uses_user_ids_and_team_names():
    users = load(f"league/{DYNASTY['2026']}/users.json")
    rosters = load(f"league/{DYNASTY['2026']}/rosters.json")
    mapping = owners(users, rosters)
    assert sorted(mapping) == list(range(1, 13))
    user_ids = {u["user_id"] for u in users}
    for owner in mapping.values():
        assert owner.user_id in user_ids
        assert owner.display_name and owner.team_name


def test_owner_turnover_between_seasons():
    old = owners(load(f"league/{DYNASTY['2022']}/users.json"), load(f"league/{DYNASTY['2022']}/rosters.json"))
    new = owners(load(f"league/{DYNASTY['2026']}/users.json"), load(f"league/{DYNASTY['2026']}/rosters.json"))
    changed = [rid for rid in new if old[rid].user_id != new[rid].user_id]
    assert changed, "the dynasty league has had owner turnover since 2022"
    # 8 of the 12 current owners were in the league in 2022
    assert len({o.user_id for o in old.values()} & {o.user_id for o in new.values()}) == 8


def test_owner_without_metadata_gets_default_team_name():
    users = [{"user_id": "7", "display_name": "sam", "metadata": {}}]
    rosters = [{"roster_id": 1, "owner_id": "7"}]
    assert owners(users, rosters)[1].team_name == "Team sam"


def make_config(overrides=()):
    return Config(
        leagues={"redraft": LeagueConfig(key="redraft", league_id=REDRAFT["2026"], name="Fall Guys")},
        overrides=list(overrides),
    )


def test_resolve_settings_without_override_matches_sleeper():
    league = load(f"league/{REDRAFT['2025']}.json")
    for week in (1, 9, 17):
        assert resolve_settings(make_config(), "redraft", league, week) == {
            k: float(v) for k, v in league["scoring_settings"].items()
        }


def test_resolve_settings_override_applies_from_week():
    league = load(f"league/{REDRAFT['2025']}.json")
    base = float(league["scoring_settings"]["fgm_yds"])
    override = ScoringOverride(league="redraft", season="2025", from_week=6, scoring={"fgm_yds": 0.25, "bonus_rec_te": 0.5})
    config = make_config([override])
    before = resolve_settings(config, "redraft", league, 5)
    after = resolve_settings(config, "redraft", league, 6)
    later = resolve_settings(config, "redraft", league, 17)
    assert before["fgm_yds"] == base and "bonus_rec_te" not in before
    assert after["fgm_yds"] == 0.25 and after["bonus_rec_te"] == 0.5
    assert later == after


def test_resolve_settings_override_other_season_or_league_ignored():
    league = load(f"league/{REDRAFT['2025']}.json")
    base = float(league["scoring_settings"]["fgm_yds"])
    other_season = ScoringOverride(league="redraft", season="2024", from_week=1, scoring={"fgm_yds": 9})
    other_league = ScoringOverride(league="dynasty", season="2025", from_week=1, scoring={"fgm_yds": 9})
    config = Config(
        leagues={
            "redraft": LeagueConfig(key="redraft", league_id="1", name="r"),
            "dynasty": LeagueConfig(key="dynasty", league_id="2", name="d"),
        },
        overrides=[other_season, other_league],
    )
    assert resolve_settings(config, "redraft", league, 10)["fgm_yds"] == base


def test_starter_slots_for_both_leagues():
    assert starter_slots(load(f"league/{DYNASTY['2026']}.json")) == ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "DEF"]
    assert starter_slots(load(f"league/{REDRAFT['2026']}.json")) == ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
