"""Site data for the Games page: one small file per week plus an index.

``site/data/<league>/games/index.json``: the season, the current week and every week with
its label and kind (``final``, ``current``, ``upcoming``). ``week_NN.json``: the week's games
ready to draw. Finished weeks show the prediction of record with actual scores; other weeks
show the latest forecast. Each team carries its owner, mean, win probability, the four key
players, the full lineup with names, and who is expected not to play. Each card carries its
``state`` (docs/games-page-states.md), which decides how the page draws it.
"""

from __future__ import annotations

from ffapp.bracket import BracketRules
from ffapp.card_states import GAMES_OVER, card_state, impact_ranked
from ffapp.config import Config
from ffapp.games import game_key, season_weeks
from ffapp.injuries import not_playing
from ffapp.league import resolve_settings
from ffapp.live import player_team
from ffapp.odds import completed_weeks, current_season
from ffapp.schedule import Schedule
from ffapp.store import Store

FLEX_KEY = ("RB", "WR", "TE")
IMPACT_STATES = (*GAMES_OVER, "final")   # key players ranked by win probability added; full lineup in the Model view
EMPTY_SLOTS = {"0", "", "None"}


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


def named(
    rows: list[list],
    names: dict[str, str],
    *,
    final: bool = False,
    points: dict[str, float] | None = None,
    wpa: dict[str, float] | None = None,
    kickoffs: dict[str, str] | None = None,
) -> list[dict]:
    """Display rows. Status: a live-locked row carries its own (final / in_progress with clock); every
    player of a finished week is final with his Sleeper points; others are scheduled with a kickoff."""
    out = []
    for r in rows:
        pid = r[1]
        # no player: a replacement fill (Model view) carries its level; an empty slot carries 0.0
        filler = "Free agent (replacement level)" if r[3] else "Empty slot"
        row = {"slot": r[0], "player_id": pid, "name": names.get(pid, pid) if pid else filler,
               "position": r[2], "projected": r[3], "replacement": pid is None,
               "status": None, "points": None, "clock": None, "kickoff": None, "wpa": None}
        if len(r) >= 8:
            row.update(status=r[4], points=r[5], clock=r[6])
        elif final and pid:
            row.update(status="final", points=round(float((points or {}).get(pid, 0.0)), 2))
        elif pid and kickoffs:
            row["kickoff"] = kickoffs.get(pid)
        if pid and wpa and pid in wpa:
            row["wpa"] = wpa[pid]
        out.append(row)
    return out


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
    schedule = Schedule(store, season)
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
        week_points = {int(r["roster_id"]): {str(k): float(v or 0.0) for k, v in (r.get("players_points") or {}).items()} for r in data.matchups.get(week, [])}
        kickoff_of = {}
        if not final:
            for pid, rec in projections.items():
                team = rec.get("team") or teams_of.get(pid)
                game = schedule.game_for(week, team) if team else None
                if game:
                    kickoff_of[pid] = game["kickoff_utc"]
        stored_views = stored.get("views") or {}
        live_week = bool(block.get("live"))
        starters_of = {int(r["roster_id"]): {str(p) for p in (r.get("starters") or []) if str(p) not in ("0", "")} for r in data.matchups.get(week, [])}

        matchup_rows = {int(r["roster_id"]): r for r in data.matchups.get(week, [])}

        def game_state_of(pid: str, live_status: dict[str, str]) -> str:
            """none / scheduled / in_progress / final for one rostered player (a starter's live row wins)."""
            if pid in EMPTY_SLOTS:
                return "none"
            if pid in live_status:
                return live_status[pid]
            team = player_team(pid, projections.get(pid), crosswalk)
            game = schedule.game_for(week, team) if team else None
            return game["state"] if game else "none"

        def card_state_of(g: dict, pair_views: dict | None) -> str:
            if kind != "current":
                return card_state(kind, bool(g.get("projected")), [])
            live_status = {}
            for t in ((pair_views or {}).get("actual") or {}).get("teams", []):
                for r in t.get("lineup", []):
                    if len(r) >= 8 and r[1] and r[4]:
                        live_status[str(r[1])] = r[4]
            teams = []
            for t in g["teams"]:
                row = matchup_rows.get(int(t["roster_id"])) or {}
                starters = [str(p) for p in row.get("starters") or []]
                bench = [str(p) for p in row.get("players") or [] if str(p) not in starters]
                teams.append({"starters": [game_state_of(p, live_status) for p in starters] or ["scheduled"],
                              "bench": [game_state_of(p, live_status) for p in bench]})
            return card_state(kind, bool(g.get("projected")), teams)

        def team_out(t: dict, i: int, actual_scores: list | None, view: str, played: bool, state: str) -> dict:
            rid = int(t["roster_id"])
            roster = week_rows.get(rid) if final and week_rows.get(rid) else current_roster.get(rid, [])
            out = not_playing(store, season, week, roster, projections, scoring, teams_of)
            owner = owners.get(rid, {})
            wpa = t.get("wpa") if view == "actual" else None
            rows = named(t["lineup"], names, final=final, points=week_points.get(rid), wpa=wpa, kickoffs=kickoff_of)
            if state in IMPACT_STATES:
                # finished games: the starters who swung the result most; the Model view shows the full lineup
                keys = impact_ranked([r for r in rows if r["player_id"]]) if view == "actual" else []
            else:
                keys = named(key_players(t["lineup"]), names, final=final, points=week_points.get(rid), wpa=wpa, kickoffs=kickoff_of)
            if view == "model" and played:
                started = starters_of.get(rid, set())
                for row in rows + keys:
                    row["benched"] = bool(row["player_id"]) and row["player_id"] not in started
            return {
                "roster_id": rid,
                "display_name": owner.get("display_name"),
                "team_name": owner.get("team_name"),
                "mean": t["mean"],
                "win_prob": t["win_prob"],
                "key_players": keys,
                "lineup": rows,
                "points_so_far": t.get("points_so_far"),
                "to_play": t.get("to_play"),
                "lineup_choices": t.get("lineup_choices"),
                "not_playing": [{"player_id": o["player_id"], "name": names.get(o["player_id"], o["player_id"]), "reason": o["reason"]} for o in out],
                "actual": (actual_scores or [None, None])[i],
            }

        games = []
        for g in block["games"]:
            pair = game_key(*(t["roster_id"] for t in g["teams"]))
            pair_views = stored_views.get(pair) if (final or live_week) else None
            actual_scores = g.get("actual")
            state = card_state_of(g, pair_views)
            views = {}
            if pair_views:
                for name in ("model", "actual"):
                    v = pair_views[name]
                    order = [t["roster_id"] for t in g["teams"]]
                    vteams = sorted(v["teams"], key=lambda t: order.index(t["roster_id"]))
                    hist = v["hist"] if vteams[0]["roster_id"] == v["teams"][0]["roster_id"] else {**v["hist"], "shares": list(reversed(v["hist"]["shares"]))}
                    views[name] = {"source": v.get("source"), "hist": hist, "teams": [team_out(t, i, actual_scores, name, True, state) for i, t in enumerate(vteams)]}
                default = "actual"
            else:
                name = "actual" if final else "model"  # records without views fall back to the record as the actual view
                views[name] = {"source": g.get("source") or block.get("source", "forecast"), "hist": g["hist"], "teams": [team_out(t, i, actual_scores, name, False, state) for i, t in enumerate(g["teams"])]}
                default = name
            leader = None
            if state in GAMES_OVER:
                # the winner check before Sleeper scores the week: whoever is ahead (none on a tie)
                pts = [(t.get("points_so_far") if t.get("points_so_far") is not None else t.get("actual"), t["roster_id"]) for t in views[default]["teams"]]
                if all(p is not None for p, _ in pts) and pts[0][0] != pts[1][0]:
                    leader = max(pts)[1]
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
                    "winner": g.get("winner"),
                    "leader": leader,
                    "state": state,
                    "default_view": default,
                    "views": views,
                    "hist": views[default]["hist"],
                    "teams": views[default]["teams"],
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
            "live": bool(block.get("live")),
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
