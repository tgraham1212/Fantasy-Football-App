"""Vacant rosters read as owned by the last earlier owner, else the first later one."""

from __future__ import annotations

import json

from ffapp.league import owners
from ffapp.store import Store, write_json


def season(store: Store, league: str, year: str, roster_owners: dict[int, str | None], users: list[tuple[str, str, str]]):
    base = store.season_dir(league, year)
    write_json(base / "league.json", {"league_id": f"L{year}", "season": year, "status": "complete", "settings": {}})
    write_json(base / "users.json", [{"user_id": uid, "display_name": name, "metadata": {"team_name": team}} for uid, name, team in users])
    write_json(base / "rosters.json", [{"roster_id": rid, "owner_id": uid, "players": []} for rid, uid in roster_owners.items()])


def make_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    season(store, "dyn", "2022", {1: "a", 11: "deek"}, [("a", "Alice", "Aces"), ("deek", "DeekBurg", "ProjectRestoration")])
    season(store, "dyn", "2023", {1: "a", 11: None, 12: None}, [("a", "Alice", "Aces")])
    season(store, "dyn", "2024", {1: "a", 11: "z", 12: None, 13: "b"}, [("a", "Alice", "Aces"), ("z", "Z28kid86", "Zeds"), ("b", "Bob", "Bees")])
    season(store, "dyn", "2021", {1: "a", 13: None}, [("a", "Alice", "Aces")])
    return store


def test_owner_quit_before_the_year_ended(tmp_path):
    store = make_store(tmp_path)
    rosters = {r["roster_id"]: r for r in store.read_rosters("dyn", "2023")}
    assert rosters[11]["owner_id"] == "deek" and rosters[11]["owner_inherited"] == "2022"
    named = owners(store.read_users("dyn", "2023"), store.read_rosters("dyn", "2023"))
    assert (named[11].display_name, named[11].team_name) == ("DeekBurg", "ProjectRestoration")


def test_vacant_in_the_first_stored_season_takes_the_later_owner(tmp_path):
    store = make_store(tmp_path)
    rosters = {r["roster_id"]: r for r in store.read_rosters("dyn", "2021")}
    assert rosters[13]["owner_id"] == "b" and rosters[13]["owner_inherited"] == "2024"
    assert any(u["user_id"] == "b" for u in store.read_users("dyn", "2021"))


def test_never_owned_stays_vacant(tmp_path):
    store = make_store(tmp_path)
    rosters = {r["roster_id"]: r for r in store.read_rosters("dyn", "2023")}
    assert not rosters[12]["owner_id"] and "owner_inherited" not in rosters[12]
    assert store.read_season("dyn", "2024").rosters[2]["owner_id"] is None


def test_stored_files_untouched(tmp_path):
    store = make_store(tmp_path)
    path = store.season_dir("dyn", "2023") / "rosters.json"
    before = path.read_text(encoding="utf-8")
    store.read_season("dyn", "2023")
    assert path.read_text(encoding="utf-8") == before
    assert json.loads(before)[1]["owner_id"] is None
