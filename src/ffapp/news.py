"""Team News for the Managers page: short stories about each manager's season, generated from stored
data. Stories are exported as data (a type, the week, a date, a link target and named fields); the
page turns each type into text with a template that has a copy ID in site-copy.txt, so the owner can
reword any story. See Calculations.txt section 20.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from ffapp.injuries import OUT_STATUSES
from ffapp.league import FLEX_ELIGIBLE, starter_slots
from ffapp.lineup import Candidate, best_lineup
from ffapp.store import Store

FORECAST_MOVE = 0.10          # a forecast story needs a change of at least 10 points in a week
BIG_FORECAST_MOVE = 0.20      # ... and 20 points to outrank a result for the feature story
STREAK_MIN = 3
TRENDING_TOP = 10
PLAYER_STORIES_PER_WEEK = 3
PLAYER_TYPES = {"injury", "practice", "depth", "trending", "milestone", "totw"}
PRIORITY = {  # higher first; also decides the feature story
    "final_season": 11, "record": 10, "forecast_big": 9, "result": 8, "rivalry_result": 7, "streak": 6, "forecast": 5,
    "milestone": 4, "injury": 4, "totw": 3, "depth": 3, "practice": 2, "trending": 2, "rivalry_preview": 2,
}
LINK = {"result": "games", "rivalry_result": "games", "rivalry_preview": "games", "forecast": "predictions", "forecast_big": "predictions",
        "record": "managers", "streak": "managers", "final_season": "managers", "milestone": "war", "injury": "positions",
        "practice": "positions", "depth": "positions", "trending": "positions", "totw": "games"}
PRACTICE_STORY = {"DNP", "Limited", "LP"}
FEATURE_TYPES = {"result", "rivalry_result", "record", "forecast_big", "final_season"}


def labor_day(year: int) -> date:
    d = date(year, 9, 1)
    return d + timedelta(days=(0 - d.weekday()) % 7)


def week_date(season: str, week: int, day: str = "mon") -> str:
    """The NFL week's date: games end on the Monday ``week`` weeks after Labor Day; Thursday is the
    week's practice-report and preview day."""
    monday = labor_day(int(season)) + timedelta(days=7 * int(week))
    return (monday - timedelta(days=4) if day == "thu" else monday).isoformat()


@dataclass
class Story:
    type: str
    season: str
    week: int
    at: str
    fields: dict = field(default_factory=dict)

    @property
    def priority(self) -> int:
        return PRIORITY[self.type]

    def export(self) -> dict:
        kind = "forecast" if self.type == "forecast_big" else self.type
        return {"type": kind, "week": self.week, "at": self.at, "link": LINK[self.type], "fields": self.fields}


# ---- league-wide inputs, read once ---------------------------------------------------------------

def stat_names(store: Store, season: str) -> tuple[dict[str, str], dict[str, str]]:
    """(player_id -> name, player_id -> position) from the season's stat and projection records."""
    names: dict[str, str] = {}
    positions: dict[str, str] = {}
    for reader, weeks in ((store.read_projections, store.projection_weeks(season)), (store.read_stats, store.stats_weeks(season))):
        for week in weeks:
            for pid, rec in reader(season, week).items():
                full = f"{rec.get('first_name') or ''} {rec.get('last_name') or ''}".strip()
                if full:
                    names[str(pid)] = full
                if rec.get("position"):
                    positions[str(pid)] = rec["position"]
    return names, positions


def team_of_the_week(league: dict, rows: list[dict], positions: dict[str, str]) -> set[str]:
    """The league's best legal lineup that week from every rostered player's actual points."""
    seen: set[str] = set()
    candidates: list[Candidate] = []
    for r in rows:
        for pid, pts in (r.get("players_points") or {}).items():
            pos = positions.get(str(pid))
            if pos and str(pid) not in seen:
                seen.add(str(pid))
                candidates.append(Candidate(str(pid), pos, (pos,), float(pts or 0.0)))
    return {s.player_id for s in best_lineup(starter_slots(league), candidates)}


# ---- per-manager stories -------------------------------------------------------------------------

def manager_stories(store: Store, league_key: str, manager, ctx: dict) -> list[dict]:
    """Stories for one manager's season (the current season, or a retired manager's last), newest
    first, with the feature story first."""
    season = manager.last
    rid = manager.roster_by_season[season]
    user = manager.user_id
    data = ctx["seasons"][season]
    names, positions = ctx["names"][season]
    games = [g for g in ctx["games"] if g.season == season and g.user == user]
    stories: list[Story] = []
    player = lambda pid: names.get(str(pid), str(pid))  # noqa: E731

    # results, streaks, rivalry results, team of the week, records
    best_before = dict(ctx["best_before"].get(user, {}))
    league_top = ctx["league_scores"]
    streak_result, streak_len = None, 0
    rivals = ctx["rivals"]
    for g in games:
        rows = data.matchups.get(g.week, [])
        mine = next((r for r in rows if int(r["roster_id"]) == rid), {})
        starters_pts = dict(zip(mine.get("starters") or [], mine.get("starters_points") or []))
        top = max(starters_pts.items(), key=lambda kv: kv[1] or 0, default=(None, 0))
        at = week_date(season, g.week)
        is_rivalry = bool(rivals and rivals.rivalry_week.get(season) == g.week and not g.playoff and rivals.rival_of(g.roster) == g.opp_roster)
        stories.append(Story("rivalry_result" if is_rivalry else "result", season, g.week, at, {
            "result": g.result, "points": g.points, "opp_points": g.opp_points, "opp": ctx["names_by_user"].get(g.opp, g.opp),
            "opp_user": g.opp, "top_player": player(top[0]) if top[0] else None, "top_points": top[1], "playoff": g.playoff}))
        if g.result == streak_result:
            streak_len += 1
        else:
            streak_result, streak_len = g.result, 1
        if streak_len >= STREAK_MIN and g.result in ("W", "L"):
            stories.append(Story("streak", season, g.week, at, {"result": g.result, "length": streak_len}))
        previous = best_before.get("high_score")
        if previous is not None and g.points > previous:
            rank = 1 + sum(1 for v in league_top if v > g.points)
            stories.append(Story("record", season, g.week, at, {"kind": "high_score", "value": g.points, "previous": previous, "rank": rank if rank <= 3 else None}))
        best_before["high_score"] = max(previous or 0.0, g.points)
        totw = ctx["totw"].get((season, g.week), set())
        on_team = [pid for pid in mine.get("players") or [] if str(pid) in totw]
        if on_team:
            stories.append(Story("totw", season, g.week, at, {"players": [player(p) for p in on_team]}))

    # forecast moves
    odds = ctx["odds"].get(season, {})
    weeks = sorted(odds)
    for a, b in zip(weeks, weeks[1:]):
        before, after = odds[a].get(rid), odds[b].get(rid)
        if before is None or after is None:
            continue
        change = after - before
        if abs(change) >= FORECAST_MOVE:
            kind = "forecast_big" if abs(change) >= BIG_FORECAST_MOVE else "forecast"
            stories.append(Story(kind, season, b, week_date(season, b), {"from": round(before, 3), "to": round(after, 3), "change": round(change, 3)}))

    # player news: injuries, practice, depth chart, trending, WAR milestones
    roster_now = ctx["roster_players"].get((season, rid), set())
    starters_now = ctx["starters_now"].get((season, rid), set())
    status_weeks = ctx["statuses"].get(season, {})
    detail_weeks = ctx["details"].get(season, {})
    for week in sorted(status_weeks):
        prev = status_weeks.get(week - 1, {})
        details = detail_weeks.get(week, {})
        for pid, status in status_weeks[week].items():
            if pid in roster_now and status in OUT_STATUSES and prev.get(pid) not in OUT_STATUSES:
                stories.append(Story("injury", season, week, week_date(season, week, "thu"),
                                     {"player": player(pid), "status": OUT_STATUSES[status], "body_part": details.get(pid, {}).get("body_part")}))
    for week in sorted(detail_weeks):
        prev = detail_weeks.get(week - 1, {})
        for pid, info in detail_weeks[week].items():
            if pid not in roster_now:
                continue
            if pid in starters_now and info.get("practice") in PRACTICE_STORY:
                stories.append(Story("practice", season, week, week_date(season, week, "thu"), {"player": player(pid), "practice": info["practice"]}))
            old = prev.get(pid, {}).get("depth")
            if old is not None and info.get("depth") is not None and old != info["depth"]:
                stories.append(Story("depth", season, week, week_date(season, week, "thu"),
                                     {"player": player(pid), "from": old, "to": info["depth"], "depth_pos": info.get("depth_pos")}))
    trending = ctx["trending"].get(season)
    if trending:
        for i, row in enumerate(trending["adds"][:TRENDING_TOP]):
            if str(row.get("player_id")) in roster_now:
                week = ctx["current_week"] or (games[-1].week if games else 1)
                stories.append(Story("trending", season, week, trending["saved_at"][:10], {"player": player(row["player_id"]), "rank": i + 1}))
    cumulative: dict[str, float] = {}
    for (s, week, pid), value in sorted(ctx["weekly_war"].items()):
        if s != season or pid not in ctx["held_weeks"].get((season, week, rid), set()):
            continue
        before = cumulative.get(pid, 0.0)
        cumulative[pid] = before + value
        if int(cumulative[pid]) > int(before) and cumulative[pid] >= 1:
            stories.append(Story("milestone", season, week, week_date(season, week), {"player": player(pid), "war": int(cumulative[pid])}))

    # rivalry preview for the coming week
    upcoming = (ctx["current_week"] or 0)
    if manager.current and rivals and rivals.rivalry_week.get(season) == upcoming and upcoming not in {g.week for g in games}:
        rival_roster = rivals.rival_of(rid)
        owners = ctx["owners"][season]
        stories.append(Story("rivalry_preview", season, upcoming, week_date(season, upcoming, "thu"),
                             {"opp": ctx["names_by_user"].get(owners.get(rival_roster), ""), "opp_user": owners.get(rival_roster)}))

    if not manager.current:
        place = ctx["places"].get(season, {}).get(rid)
        last_week = games[-1].week if games else 17
        stories.append(Story("final_season", season, last_week, week_date(season, last_week), {"season": season, "place": place}))
    return [s.export() for s in order_stories(stories)]


def order_stories(stories: list[Story]) -> list[Story]:
    """Cap player stories at three per week (highest priority kept), sort newest first, and move the
    feature story (the latest week's highest priority) to the front."""
    kept: list[Story] = []
    by_week: dict[int, list[Story]] = {}
    for s in stories:
        by_week.setdefault(s.week, []).append(s)
    for week, items in by_week.items():
        players = sorted((s for s in items if s.type in PLAYER_TYPES), key=lambda s: -s.priority)[:PLAYER_STORIES_PER_WEEK]
        kept.extend([s for s in items if s.type not in PLAYER_TYPES] + players)
    kept.sort(key=lambda s: (s.week, s.at, s.priority), reverse=True)
    if kept:
        # the feature comes from the latest week with a game (or a retired manager's final-season
        # story), where a record or a big forecast move outranks the result
        headline = [s for s in kept if s.type in FEATURE_TYPES]
        if headline:
            latest = max(s.week for s in headline)
            feature = max((s for s in headline if s.week == latest), key=lambda s: s.priority)
        else:
            feature = kept[0]
        kept.remove(feature)
        kept.insert(0, feature)
    return kept


def league_context(store: Store, league_key: str, managers: dict, games: list, rivals) -> dict:
    """Everything the stories need, read once per league."""
    from ffapp.managers import final_places, roster_owners, roster_weeks, weekly_war

    seasons_needed = sorted({m.last for m in managers.values()})
    ctx: dict = {"games": games, "rivals": rivals, "names_by_user": {u: m.name for u, m in managers.items()},
                 "seasons": {}, "names": {}, "totw": {}, "odds": {}, "statuses": {}, "details": {}, "trending": {},
                 "roster_players": {}, "starters_now": {}, "owners": {}, "places": {}, "held_weeks": {}}
    ctx["weekly_war"] = weekly_war(store, league_key)
    timeline, held = roster_weeks(store, league_key)
    for season in seasons_needed:
        data = store.read_season(league_key, season)
        ctx["seasons"][season] = data
        ctx["names"][season] = stat_names(store, season)
        ctx["owners"][season] = roster_owners(store, league_key, season)
        ctx["places"][season] = final_places(data)[0]
        _, positions = ctx["names"][season]
        for week, rows in data.matchups.items():
            if any(r.get("players_points") for r in rows):
                ctx["totw"][(season, week)] = team_of_the_week(data.league, rows, positions)
            for r in rows:
                ctx["held_weeks"][(season, week, int(r["roster_id"]))] = {str(p) for p in r.get("players") or []}
        for r in store.read_rosters(league_key, season):
            ctx["roster_players"][(season, int(r["roster_id"]))] = {str(p) for f in ("players", "reserve", "taxi") for p in r.get(f) or []}
            ctx["starters_now"][(season, int(r["roster_id"]))] = {str(p) for p in r.get("starters") or []}
        ctx["odds"][season] = {w: {int(t["roster_id"]): t.get("playoffs") for t in (store.read_odds(league_key, season, w) or {}).get("teams", [])}
                               for w in store.odds_weeks(league_key, season)}
        ctx["statuses"][season] = _weekly(store.root / "injuries" / season, store.read_injuries, season)
        ctx["details"][season] = _weekly(store.root / "players" / season, store.read_player_details, season)
        files = sorted((store.root / "trending" / season).glob("*.json")) if (store.root / "trending" / season).exists() else []
        if files:
            from ffapp.store import read_json
            ctx["trending"][season] = read_json(files[-1])
    from ffapp.odds import completed_weeks

    latest = store.seasons(league_key)[-1] if store.seasons(league_key) else None
    ctx["current_week"] = completed_weeks(ctx["seasons"][latest].league) + 1 if latest in ctx["seasons"] else None
    # league scores and each manager's best score before the current season, for record stories
    ctx["league_scores"] = [g.points for g in games]
    best_before: dict[str, dict] = {}
    for g in games:
        if g.season < (latest or ""):
            row = best_before.setdefault(g.user, {})
            row["high_score"] = max(row.get("high_score", 0.0), g.points)
    ctx["best_before"] = best_before
    return ctx


def _weekly(folder, reader, season: str) -> dict[int, dict]:
    if not folder.exists():
        return {}
    weeks = sorted(int(p.stem.split("_")[1]) for p in folder.glob("week_*.json"))
    return {w: reader(season, w) or {} for w in weeks}
