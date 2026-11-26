"""League records for the League sub-tab's Records page: champions, all-time standings, weekly and
season league records, and Player league records, computed from stored league data and exported as
one file per league (``site/data/<league>/records.json``); the page only renders.

Only Meaningful Games count: the regular season, winners-bracket games on the path to the championship,
the championship and the 3rd place game, and in a toilet-bowl league the toilet bowl games on its path
and its final. Equal values
share a rank and the oldest is listed first. See Calculations.txt section 23.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from ffapp.bracket import BracketRules
from ffapp.managers import (
    bracket_places, managers_for_league, roster_bench_points, roster_owners, roster_weeks, season_complete, weekly_war,
)
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)

TOP = 25
REGULAR = "regular"
PLAYOFFS, CHAMPIONSHIP, THIRD = "Playoffs", "Championship", "3rd Place"
TOILET, TOILET_FINAL = "Toilet Bowl", "Toilet Bowl Final"
WINNERS_KINDS = (PLAYOFFS, CHAMPIONSHIP, THIRD)
POSITIONS = ("ALL", "QB", "RB", "WR", "TE", "DEF", "K")


# ---- meaningful games --------------------------------------------------------------------------

def _team(value) -> int | None:
    return int(value) if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()) else None


def bracket_kinds(data: SeasonData) -> dict[tuple[int, frozenset[int]], str]:
    """(week, the two roster ids) -> kind, for every bracket game that matters.

    Winners bracket: no placement (Playoffs), placement 1 (Championship) or 3 (3rd Place). In a
    toilet-bowl league, losers bracket: no placement (Toilet Bowl) or placement 1 (Toilet Bowl Final).
    Placement games for other places and consolation brackets are left out."""
    rules = BracketRules.from_league(data.league)
    out: dict[tuple[int, frozenset[int]], str] = {}

    def add(game: dict, kind: str) -> None:
        a, b = _team(game.get("t1")), _team(game.get("t2"))
        if a is not None and b is not None:
            out[(rules.week_for_round(int(game.get("r") or 0)), frozenset((a, b)))] = kind

    for game in data.winners_bracket:
        p = game.get("p")
        if p in (None, 1, 3):
            add(game, CHAMPIONSHIP if p == 1 else THIRD if p == 3 else PLAYOFFS)
    if rules.toilet_bowl:
        for game in data.losers_bracket:
            p = game.get("p")
            if p in (None, 1):
                add(game, TOILET_FINAL if p == 1 else TOILET)
    return out


@dataclass(frozen=True)
class Played:
    """One finished game that matters, both sides."""

    season: str
    week: int
    kind: str
    a: str
    b: str
    a_roster: int
    b_roster: int
    a_points: float
    b_points: float

    def sides(self) -> tuple[tuple[str, str, int, float, float], tuple[str, str, int, float, float]]:
        """(user, opponent, roster, points, opponent points) from each side."""
        return ((self.a, self.b, self.a_roster, self.a_points, self.b_points),
                (self.b, self.a, self.b_roster, self.b_points, self.a_points))

    @property
    def winner_first(self) -> tuple[str, str, float, float]:
        if self.a_points >= self.b_points:
            return self.a, self.b, self.a_points, self.b_points
        return self.b, self.a, self.b_points, self.a_points


def season_games(store: Store, league_key: str, season: str) -> list[Played]:
    """Every finished game that matters in a season. Weeks after Sleeper's last scored week are left
    out, so a live week never counts."""
    from ffapp.odds import completed_weeks, regular_season_range

    data = store.read_season(league_key, season)
    owners = roster_owners(store, league_key, season)
    done = completed_weeks(data.league)
    regular = set(regular_season_range(data.league))
    kinds = bracket_kinds(data)
    out: list[Played] = []
    for week in sorted(data.matchups):
        if week > done:
            break
        pairs: dict[int, list[dict]] = {}
        for t in data.matchups[week]:
            if t.get("matchup_id") is not None:
                pairs.setdefault(int(t["matchup_id"]), []).append(t)
        for teams in pairs.values():
            if len(teams) != 2:
                continue
            a, b = int(teams[0]["roster_id"]), int(teams[1]["roster_id"])
            kind = REGULAR if week in regular else kinds.get((week, frozenset((a, b))))
            if kind is None or a not in owners or b not in owners:
                continue
            out.append(Played(season, week, kind, owners[a], owners[b], a, b,
                              float(teams[0].get("points") or 0.0), float(teams[1].get("points") or 0.0)))
    return out


# ---- ranking --------------------------------------------------------------------------------

def ranked(entries: list[dict], *, low: bool = False, tiebreak=None, distinct: bool = False, top: int = TOP) -> list[dict]:
    """The top entries by ``value``: highest first (``low``: lowest first), then oldest first, then
    ``tiebreak(entry)`` ascending. Equal values share a rank (1, 2, 2, 4) unless ``distinct``."""
    def key(e: dict):
        k = (e["value"] if low else -e["value"], str(e.get("season") or ""), int(e.get("week") or 0))
        return k + ((tiebreak(e),) if tiebreak else ())

    out: list[dict] = []
    for i, e in enumerate(sorted(entries, key=key)[:top]):
        same = out and not distinct and round(out[-1]["value"], 4) == round(e["value"], 4)
        out.append({**e, "rank": out[-1]["rank"] if same else i + 1})
    return out


# ---- the export -------------------------------------------------------------------------------

def _settings_points(settings: dict) -> float:
    return float(settings.get("fpts") or 0) + float(settings.get("fpts_decimal") or 0) / 100


def _record(w: int, l: int, t: int) -> dict:
    return {"wins": w, "losses": l, "ties": t}


def _pct(w: float, l: float, t: float) -> float:
    games = w + l + t
    return (w + 0.5 * t) / games if games else 0.0


class _Context:
    """Everything read once per league."""

    def __init__(self, store: Store, config, league_key: str):
        from ffapp.war import read_war, war_seasons

        self.store, self.config, self.key = store, config, league_key
        self.seasons = store.seasons(league_key)
        self.data = {s: store.read_season(league_key, s) for s in self.seasons}
        self.complete = {s for s in self.seasons if season_complete(self.data[s])}
        latest = self.seasons[-1] if self.seasons else None
        self.current = latest if latest and latest not in self.complete else None
        self.managers = managers_for_league(store, league_key)
        self.owners = {s: roster_owners(store, league_key, s) for s in self.seasons}
        self.places = {s: bracket_places(self.data[s]) for s in self.complete}
        self.rules = {s: BracketRules.from_league(self.data[s].league) for s in self.seasons}
        self.toilet_bowl = self.rules[latest].toilet_bowl if latest else True
        self.games = [g for s in self.seasons for g in season_games(store, league_key, s)]
        self.war = {s: (read_war(store, league_key, s) or {}).get("players") or {} for s in war_seasons(store, league_key)}
        self._stats: dict[tuple[str, int], dict] = {}

    def last_place(self, season: str) -> int:
        return len(self.places.get(season) or {}) or len(self.data[season].rosters)

    def place_of(self, season: str, user: str) -> int | None:
        rid = self.managers[user].roster_by_season.get(season) if user in self.managers else None
        return (self.places.get(season) or {}).get(rid) if rid is not None else None

    def made_playoffs(self, season: str, user: str) -> bool:
        place = self.place_of(season, user)
        return place is not None and place <= self.rules[season].playoff_teams

    def player(self, pid: str) -> tuple[str, str | None]:
        """(name, position) from the newest WAR file naming the player."""
        for season in reversed(sorted(self.war)):
            p = self.war[season].get(pid)
            if p:
                return p.get("name") or pid, p.get("position")
        return pid, None

    def nfl_team(self, pid: str, season: str, week: int) -> str | None:
        """The NFL team the player played for that week, from the stored weekly stats."""
        if pid.isalpha():
            return pid  # a defence's id is its team
        if (season, week) not in self._stats:
            self._stats[(season, week)] = self.store.read_stats(season, week) or {}
        return (self._stats[(season, week)].get(pid) or {}).get("team")


def _champions(ctx: _Context) -> list[dict]:
    war = weekly_war(ctx.store, ctx.key)
    _, held = roster_weeks(ctx.store, ctx.key)
    out = []
    for season in sorted(ctx.complete, reverse=True):
        places = ctx.places[season]
        owners = ctx.owners[season]
        by_place = {place: owners.get(rid) for rid, place in places.items()}
        champ = by_place.get(1)
        if not champ:
            continue
        rid = ctx.managers[champ].roster_by_season[season]
        roster = next((r for r in ctx.data[season].rosters if int(r["roster_id"]) == rid), {})
        s = roster.get("settings") or {}
        totals: dict[str, float] = {}
        last_week: dict[str, int] = {}
        for (sea, week), players in (held.get(champ) or {}).items():
            if sea != season:
                continue
            for pid in players:
                totals[pid] = totals.get(pid, 0.0) + war.get((season, week, pid), 0.0)
                last_week[pid] = max(last_week.get(pid, 0), week)
        best = None
        if totals:
            pid = max(totals, key=lambda p: totals[p])
            name, pos = ctx.player(pid)
            best = {"player_id": pid, "name": name, "position": pos, "war": round(totals[pid], 2),
                    "team": ctx.nfl_team(pid, season, last_week[pid])}
        out.append({
            "season": season,
            "champion": champ,
            "team_name": ctx.managers[champ].team_names.get(season),
            "runner_up": by_place.get(2),
            "last": by_place.get(ctx.last_place(season)),
            "record": _record(int(s.get("wins") or 0), int(s.get("losses") or 0), int(s.get("ties") or 0)),
            "points": round(_settings_points(s), 2),
            "best_player": best,
        })
    return out


def _standings(ctx: _Context) -> list[dict]:
    rows: dict[str, dict] = {}

    def row(user: str) -> dict:
        return rows.setdefault(user, {"user": user, "w": 0, "l": 0, "t": 0, "pf": 0.0, "pa": 0.0, "pw": 0, "pl": 0, "pt": 0})

    for g in ctx.games:
        for user, _, _, pts, opp in g.sides():
            r = row(user)
            res = "w" if pts > opp else "l" if pts < opp else "t"
            if g.kind == REGULAR:
                r[res] += 1
                r["pf"] += pts
                r["pa"] += opp
            elif g.kind in WINNERS_KINDS:
                r["p" + res] += 1
    out = []
    for user, m in ctx.managers.items():
        r = row(user)
        places = [ctx.place_of(s, user) for s in ctx.complete]
        last = [s for s in ctx.complete if ctx.place_of(s, user) == ctx.last_place(s)]
        out.append({
            "user": user, "current": m.current, "seasons": len(m.seasons), "first": m.first, "last_season": m.last,
            "record": _record(r["w"], r["l"], r["t"]), "pct": round(_pct(r["w"], r["l"], r["t"]), 4),
            "diff": round(r["pf"] - r["pa"], 2),
            "playoffs": sum(1 for s in ctx.complete if ctx.made_playoffs(s, user)),
            "playoff_record": _record(r["pw"], r["pl"], r["pt"]),
            "first_place": places.count(1), "second_place": places.count(2), "third_place": places.count(3),
            "last_place": len(last),
        })
    out.sort(key=lambda r: (not r["current"], -r["pct"], -r["diff"]))
    rank = 0
    for r in out:
        rank += 1
        r["rank"] = rank if r["current"] else None
    return out


WEEKLY_KEYS = ("high_team", "low_team", "high_matchup", "low_matchup", "blowout", "closest", "high_loss", "low_win")


def _weekly(ctx: _Context) -> dict[str, list[dict]]:
    cand: dict[str, list[dict]] = {k: [] for k in WEEKLY_KEYS}
    for g in ctx.games:
        when = {"season": g.season, "week": g.week, "kind": g.kind, "current": g.season == ctx.current}
        for user, opp, _, pts, opp_pts in g.sides():
            side = {**when, "user": user, "opp": opp, "score": [round(pts, 2), round(opp_pts, 2)]}
            cand["high_team"].append({**side, "value": round(pts, 2)})
            cand["low_team"].append({**side, "value": round(pts, 2)})
            if pts < opp_pts:
                cand["high_loss"].append({**side, "value": round(pts, 2)})
            if pts > opp_pts:
                cand["low_win"].append({**side, "value": round(pts, 2)})
        w, l, wp, lp = g.winner_first
        game = {**when, "user": w, "opp": l, "score": [round(wp, 2), round(lp, 2)]}
        cand["high_matchup"].append({**game, "value": round(wp + lp, 2)})
        cand["low_matchup"].append({**game, "value": round(wp + lp, 2)})
        cand["blowout"].append({**game, "value": round(wp - lp, 2)})
        cand["closest"].append({**game, "value": round(wp - lp, 2)})
    low = {"low_team", "low_matchup", "closest", "low_win"}
    return {k: ranked(v, low=k in low) for k, v in cand.items()}


SEASON_KEYS = ("most_points", "fewest_points", "most_against", "best_record", "worst_record", "best_missed", "worst_made",
               "luckiest", "unluckiest", "win_streak", "loss_streak", "bench", "lineup_gained", "lineup_lost")
FINISHED_ONLY = {"fewest_points", "worst_record", "best_missed", "worst_made"}  # a part-season cannot hold these


def _streak(results: list[str], want: str) -> int:
    best = cur = 0
    for r in results:
        cur = cur + 1 if r == want else 0
        best = max(best, cur)
    return best


def _season_rows(ctx: _Context, lineup: dict[tuple[str, int, str], float]) -> list[dict]:
    """One row per Manager-season with every season figure."""
    by: dict[tuple[str, str], dict] = {}
    weeks: dict[tuple[str, int], list[tuple[str, float]]] = {}
    for g in sorted(ctx.games, key=lambda g: (g.season, g.week)):
        for user, _, _, pts, opp in g.sides():
            r = by.setdefault((user, g.season), {"pf": 0.0, "pa": 0.0, "w": 0, "l": 0, "t": 0, "seq": [], "xw": 0.0})
            res = "W" if pts > opp else "L" if pts < opp else "T"
            r["seq"].append(res)
            if g.kind == REGULAR:
                r["pf"] += pts
                r["pa"] += opp
                r[res.lower()] += 1
                weeks.setdefault((g.season, g.week), []).append((user, pts))
    for (season, _), scores in weeks.items():  # all-play: the share of the other teams each score beat
        for user, pts in scores:
            others = [p for u, p in scores if u != user]
            if others:
                by[(user, season)]["xw"] += (sum(p < pts for p in others) + 0.5 * sum(p == pts for p in others)) / len(others)
    out = []
    for (user, season), r in by.items():
        if not (r["w"] + r["l"] + r["t"]):
            continue
        rid = ctx.managers[user].roster_by_season.get(season) if user in ctx.managers else None
        roster = next((x for x in ctx.data[season].rosters if int(x["roster_id"]) == rid), {})
        s = roster.get("settings") or {}
        place = ctx.place_of(season, user)
        if season == ctx.current:
            result = "in_progress"
        elif place in (1, 2, 3):
            result = {1: "first", 2: "second", 3: "third"}[place]
        elif place is not None and place == ctx.last_place(season):
            result = "toilet_bowl" if ctx.rules[season].toilet_bowl else "last"
        else:
            result = "playoffs" if ctx.made_playoffs(season, user) else "missed"
        choices = [v for (sea, _, u), v in lineup.items() if sea == season and u == user]
        out.append({
            "user": user, "season": season, "current": season == ctx.current, "result": result,
            "made": ctx.made_playoffs(season, user), "finished": season in ctx.complete,
            "pf": round(r["pf"], 2), "pa": round(r["pa"], 2), "record": _record(r["w"], r["l"], r["t"]),
            "pct": _pct(r["w"], r["l"], r["t"]), "luck": round(r["w"] + 0.5 * r["t"] - r["xw"], 2),
            "win_streak": _streak(r["seq"], "W"), "loss_streak": _streak(r["seq"], "L"),
            "bench": roster_bench_points(s) if "ppts" in s else None,
            "lineup": round(sum(choices), 1) if choices else None,
        })
    return out


def _season(ctx: _Context, lineup: dict[tuple[str, int, str], float]) -> dict[str, list[dict]]:
    rows = _season_rows(ctx, lineup)

    def entries(field: str, keep=lambda r: True) -> list[dict]:
        return [{"user": r["user"], "season": r["season"], "current": r["current"], "result": r["result"],
                 "record": r["record"], "value": r[field]} for r in rows if r[field] is not None and keep(r)]

    done = lambda r: r["finished"]  # noqa: E731
    out = {
        "most_points": ranked(entries("pf")),
        "fewest_points": ranked(entries("pf", done), low=True),
        "most_against": ranked(entries("pa")),
        "best_record": ranked(entries("pct"), tiebreak=lambda e: -_points_of(rows, e)),
        "worst_record": ranked(entries("pct", done), low=True, tiebreak=lambda e: _points_of(rows, e)),
        "best_missed": ranked(entries("pf", lambda r: r["finished"] and not r["made"])),
        "worst_made": ranked(entries("pf", lambda r: r["finished"] and r["made"]), low=True),
        "luckiest": ranked(entries("luck")),
        "unluckiest": ranked(entries("luck"), low=True),
        "win_streak": ranked(entries("win_streak")),
        "loss_streak": ranked(entries("loss_streak")),
        "bench": ranked(entries("bench")),
        "lineup_gained": ranked(entries("lineup")),
        "lineup_lost": ranked(entries("lineup"), low=True),
    }
    for key in ("best_record", "worst_record"):
        for e in out[key]:
            e["value"] = round(e["value"], 4)
    return out


def _points_of(rows: list[dict], e: dict) -> float:
    return next((r["pf"] for r in rows if r["user"] == e["user"] and r["season"] == e["season"]), 0.0)


def _players(ctx: _Context) -> dict[str, dict[str, list[dict]]]:
    """Best games, best bench games, career scoring and championships, per position and for all."""
    from ffapp.odds import completed_weeks

    games: list[dict] = []
    career: dict[str, dict] = {}
    for season in ctx.seasons:
        players = ctx.war.get(season) or {}
        data = ctx.data[season]
        done = completed_weeks(data.league)
        owners = ctx.owners[season]
        held: dict[tuple[int, str], str] = {}
        started: set[tuple[int, str]] = set()
        weeks = set()
        for week, rows in data.matchups.items():
            if week > done or not any(r.get("points") for r in rows):
                continue
            weeks.add(week)
            for r in rows:
                uid = owners.get(int(r["roster_id"]))
                for pid in r.get("players") or []:
                    if uid:
                        held[(week, str(pid))] = uid
                for pid in r.get("starters") or []:
                    started.add((week, str(pid)))
        for pid, p in players.items():
            pos = p.get("position")
            for wk in p.get("weekly") or []:
                week = int(wk.get("week") or 0)
                if not wk.get("played") or wk.get("score") is None or week not in weeks:
                    continue
                user = held.get((week, pid))
                status = "started" if (week, pid) in started else "bench" if user else "free_agent"
                pts = round(float(wk["score"]), 2)
                games.append({"player_id": pid, "position": pos, "season": season, "week": week, "value": pts,
                              "user": user, "status": status, "current": season == ctx.current})
                c = career.setdefault(pid, {"player_id": pid, "position": pos, "games": 0, "points": 0.0})
                c["games"] += 1
                c["points"] += pts
    titles: dict[str, dict] = {}
    for season in sorted(ctx.complete):
        data = ctx.data[season]
        final = next((g for g in data.winners_bracket if g.get("p") == 1 and _team(g.get("w")) is not None), None)
        if not final:
            continue
        rid = int(final["w"])
        week = ctx.rules[season].week_for_round(int(final.get("r") or 0))
        row = next((r for r in data.matchups.get(week, []) if int(r["roster_id"]) == rid), {})
        roster = next((r for r in data.rosters if int(r["roster_id"]) == rid), {})
        squad = {str(p) for p in (row.get("players") or [])} | {str(p) for p in (roster.get("reserve") or [])} | {str(p) for p in (roster.get("taxi") or [])}
        champ = ctx.owners[season].get(rid)
        for pid in squad:
            t = titles.setdefault(pid, {"player_id": pid, "value": 0, "seasons": [], "users": [], "war": 0.0})
            t["value"] += 1
            t["seasons"].append(season)
            if champ and champ not in t["users"]:
                t["users"].append(champ)
            t["war"] += float(((ctx.war.get(season) or {}).get(pid) or {}).get("war") or 0.0)

    def by_position(rows: list[dict], position_of, **kw) -> dict[str, list[dict]]:
        return {pos: ranked([r for r in rows if pos == "ALL" or position_of(r) == pos], **kw) for pos in POSITIONS}

    best = by_position(games, lambda r: r["position"])
    bench = by_position([g for g in games if g["status"] == "bench"], lambda r: r["position"])
    careers = [{**c, "value": round(c["points"], 2), "points": round(c["points"], 2), "ppg": round(c["points"] / c["games"], 2)} for c in career.values()]
    for c in careers:
        c["name"] = ctx.player(c["player_id"])[0]
    careers_ranked = by_position(careers, lambda r: r["position"], tiebreak=lambda e: e["name"], distinct=True)
    for t in titles.values():
        t["name"], t["position"] = ctx.player(t["player_id"])
        t["war"] = round(t["war"], 2)
    champs = by_position(list(titles.values()), lambda r: r["position"], tiebreak=lambda e: -e["war"], distinct=True)
    for lists in (best, bench):  # names and NFL teams only for the entries exported
        for rows in lists.values():
            for e in rows:
                e["name"] = ctx.player(e["player_id"])[0]
                e["team"] = ctx.nfl_team(e["player_id"], e["season"], e["week"])
    return {"best_games": best, "bench_games": bench, "career": careers_ranked, "championships": champs}


def records_export(store: Store, config, league_key: str, lineup: dict[tuple[str, int, str], float] | None = None) -> dict:
    """The league records file for one league. ``lineup`` is (season, week, user) -> lineup choices;
    computed from the stored data when not given."""
    ctx = _Context(store, config, league_key)
    if lineup is None:
        lineup = league_lineup_choices(store, config, league_key, ctx)
    return {
        "league_key": league_key,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "toilet_bowl": ctx.toilet_bowl,
        "current_season": ctx.current,
        "managers": {u: {"name": m.name, "team_name": m.team_names.get(m.last), "logo": m.logo, "avatar": m.avatar, "current": m.current}
                     for u, m in ctx.managers.items()},
        "champions": _champions(ctx),
        "standings": _standings(ctx),
        "weekly": _weekly(ctx),
        "season": _season(ctx, lineup),
        "players": _players(ctx),
    }


def league_lineup_choices(store: Store, config, league_key: str, ctx: _Context | None = None) -> dict[tuple[str, int, str], float]:
    """(season, week, user) -> lineup choices for every finished regular-season week."""
    from ffapp.views import season_lineup_choices

    ctx = ctx or _Context(store, config, league_key)
    out: dict[tuple[str, int, str], float] = {}
    for season in ctx.seasons:
        owners = ctx.owners[season]
        for (week, rid), value in season_lineup_choices(store, config, league_key, ctx.data[season]).items():
            if rid in owners:
                out[(season, week, owners[rid])] = value
    return out
