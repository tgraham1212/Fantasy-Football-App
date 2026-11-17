"""Site data for the Games page: one small file per week plus an index.

``site/data/<league>/games/index.json``: the season, the current week and every week with
its label and kind (``final``, ``current``, ``upcoming``). ``week_NN.json``: the week's games
ready to draw. Finished weeks show the prediction of record with actual scores; other weeks
show the latest forecast. Each team carries its owner, mean, win probability, the three key
players, the full lineup with names, and who is expected not to play.
"""

from __future__ import annotations

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.games import season_weeks
from ffapp.injuries import not_playing
from ffapp.league import resolve_settings
from ffapp.odds import completed_weeks, current_season
from ffapp.store import Store

FLEX_KEY = ("RB", "WR", "TE")


def player_names(store: Store, season: str, week: int) -> dict[str, str]:
    """Display names from the crosswalk, overridden by the week's projection records."""
    names = {pid: rec.get("name") for pid, rec in (store.read_crosswalk() or {}).items() if rec.get("name")}
    for pid, rec in store.read_projections(season, week).items():
        name = " ".join(x for x in (rec.get("first_name"), rec.get("last_name")) if x)
        if name:
            names[pid] = name
    return names


def key_players(lineup: list[list]) -> list[list]:
    """QB, the top RB, the top WR, then the top remaining RB/WR/TE, from the lineup used.

    A slot the model fills at replacement level stays in (shown as a free agent), so the card
    says what the model is counting on rather than naming a rostered player it benched."""
    rows = list(lineup)
    picked: list[list] = []

    def best(positions) -> list | None:
        pool = [r for r in rows if r[2] in positions and not any(r is p for p in picked)]
        return max(pool, key=lambda r: r[3]) if pool else None

    for positions in (("QB",), ("RB",), ("WR",), FLEX_KEY):
        choice = best(positions)
        if choice is not None:
            picked.append(choice)
    return picked


def named(rows: list[list], names: dict[str, str]) -> list[dict]:
    return [
        {"slot": r[0], "player_id": r[1], "name": names.get(r[1], r[1]) if r[1] else "Free agent (replacement level)",
         "position": r[2], "projected": r[3], "replacement": r[1] is None}
        for r in rows
    ]


def week_label(week: int, rules: BracketRules) -> str:
    if week < rules.playoff_week_start:
        return f"Week {week}"
    round_no = week - rules.playoff_week_start + 1
    title = {1: "Playoffs round 1", 2: "Semifinals", 3: "Final"}.get(round_no, f"Playoffs round {round_no}")
    return f"{title} (week {week})"


def games_export(store: Store, config: Config, league_key: str, owners: dict[int, dict]) -> dict | None:
    """``{"index": ..., "weeks": {week: payload}}`` for the current season, or None without game files."""
    season = current_season(store, league_key)
    if season is None:
        return None
    data = store.read_season(league_key, season)
    rules = BracketRules.from_league(data.league)
    as_of = completed_weeks(data.league)
    crosswalk = store.read_crosswalk() or {}
    teams_of = {pid: rec.get("team") for pid, rec in crosswalk.items() if rec.get("team")}
    current_roster = {int(r["roster_id"]): [str(p) for p in (r.get("players") or [])] for r in data.rosters}
    weeks_out: dict[int, dict] = {}
    index_weeks = []
    for week in season_weeks(data.league):
        stored = store.read_games(league_key, season, week)
        if not stored:
            continue
        final = week <= as_of
        block = stored.get("record") if final else stored.get("forecast")
        if not block:
            continue
        kind = "final" if final else "current" if week == as_of + 1 else "upcoming"
        names = player_names(store, season, week)
        projections = store.read_projections(season, week)
        scoring = resolve_settings(config, league_key, data.league, week)
        week_rows = {int(r["roster_id"]): [str(p) for p in (r.get("players") or [])] for r in data.matchups.get(week, [])}
        games = []
        for g in block["games"]:
            teams = []
            for i, t in enumerate(g["teams"]):
                rid = int(t["roster_id"])
                roster = week_rows.get(rid) if final and week_rows.get(rid) else current_roster.get(rid, [])
                out = not_playing(store, season, week, roster, projections, scoring, teams_of)
                owner = owners.get(rid, {})
                teams.append(
                    {
                        "roster_id": rid,
                        "display_name": owner.get("display_name"),
                        "team_name": owner.get("team_name"),
                        "mean": t["mean"],
                        "win_prob": t["win_prob"],
                        "key_players": named(key_players(t["lineup"]), names),
                        "lineup": named(t["lineup"], names),
                        "not_playing": [{"player_id": o["player_id"], "name": names.get(o["player_id"], o["player_id"]), "reason": o["reason"]} for o in out],
                        "actual": (g.get("actual") or [None, None])[i],
                    }
                )
            games.append(
                {
                    "key": g["key"],
                    "bracket": g.get("bracket", "regular"),
                    "round": g.get("round"),
                    "match": g.get("match"),
                    "place": g.get("place"),
                    "projected": bool(g.get("projected")),
                    "frequency": g.get("frequency"),
                    "seeds": g.get("seeds"),
                    "hist": g["hist"],
                    "winner": g.get("winner"),
                    "teams": teams,
                }
            )
        byes = [
            {**b, "display_name": owners.get(b["roster_id"], {}).get("display_name"), "team_name": owners.get(b["roster_id"], {}).get("team_name")}
            for b in (block.get("byes") or [])
        ]
        weeks_out[week] = {
            "league_key": league_key,
            "season": season,
            "week": week,
            "label": week_label(week, rules),
            "kind": kind,
            "playoffs": week >= rules.playoff_week_start,
            "source": block.get("source", "forecast"),
            "forecast_as_of": block.get("as_of_week"),
            "generated_at": block.get("generated_at"),
            "toilet_bowl": rules.toilet_bowl,
            "games": games,
            "byes": byes,
        }
        index_weeks.append({"week": week, "label": week_label(week, rules), "kind": kind, "file": f"week_{week:02d}.json"})
    if not weeks_out:
        return None
    available = [w["week"] for w in index_weeks]
    current = min((w for w in available if w > as_of), default=available[-1])
    return {"index": {"season": season, "current": current, "weeks": index_weeks}, "weeks": weeks_out}
