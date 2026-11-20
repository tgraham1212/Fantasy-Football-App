"""Per-manager history for the Managers page: identity across seasons, final places and honours,
head to head, records with all-time ranks, luck, rivals, player move windows and best players.

Every figure is computed here from stored league data and exported as one file per league
(``site/data/<league>/managers.json``); the page only renders. See Calculations.txt section 19.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ffapp.bracket import BracketRules
from ffapp.store import SeasonData, Store

log = logging.getLogger(__name__)


# ---- identity -------------------------------------------------------------------------------

@dataclass
class Manager:
    """One league member across seasons, keyed by Sleeper user id."""

    user_id: str
    name: str = ""                                                # latest display name
    seasons: list[str] = field(default_factory=list)              # seasons with a roster, ascending
    roster_by_season: dict[str, int] = field(default_factory=dict)
    team_names: dict[str, str] = field(default_factory=dict)      # season -> team name
    logo: str | None = None                                       # latest team logo URL
    avatar: str | None = None                                     # latest Sleeper avatar id
    current: bool = False

    @property
    def first(self) -> str:
        return self.seasons[0]

    @property
    def last(self) -> str:
        return self.seasons[-1]


def roster_owners(store: Store, league_key: str, season: str) -> dict[int, str]:
    """roster_id -> user id for one season, vacant rosters read as their inherited owner."""
    return {int(r["roster_id"]): str(r["owner_id"]) for r in store.read_rosters(league_key, season) if r.get("owner_id")}


def managers_for_league(store: Store, league_key: str) -> dict[str, Manager]:
    """Every manager who held a roster in any stored season, in order of first season then name.

    A manager is current when they hold a roster in the latest stored season, retired otherwise.
    Names, logos and avatars come from the latest season the manager appears in, so a renamed
    account shows its newest name everywhere.
    """
    seasons = store.seasons(league_key)
    out: dict[str, Manager] = {}
    for season in seasons:
        users = {str(u.get("user_id")): u for u in store.read_users(league_key, season)}
        for rid, uid in sorted(roster_owners(store, league_key, season).items()):
            m = out.setdefault(uid, Manager(user_id=uid))
            m.seasons.append(season)
            m.roster_by_season[season] = rid
            user = users.get(uid, {})
            meta = user.get("metadata") or {}
            m.name = str(user.get("display_name") or m.name or uid)
            m.team_names[season] = str(meta.get("team_name") or f"Team {m.name}")
            m.logo = meta.get("avatar") or m.logo
            m.avatar = user.get("avatar") or m.avatar
    latest = seasons[-1] if seasons else None
    for m in out.values():
        m.current = m.last == latest
    return dict(sorted(out.items(), key=lambda kv: (kv[1].first, kv[1].name.lower())))


# ---- final places ---------------------------------------------------------------------------

def bracket_places(data: SeasonData) -> dict[int, int]:
    """roster_id -> final place from the stored placement games; {} when the brackets are not done.

    Winners bracket: the game marked ``p`` decides places p (winner) and p + 1 (loser).
    Toilet bowl (losers bracket where the lower scorer advances): Sleeper's ``w`` is the team that
    advanced, so the p-1 "winner" is the toilet bowl champion in last place: w gets 13 - p and l gets
    12 - p. Consolation bracket (higher scorer advances): w gets 6 + p and l gets 7 + p.
    """
    rules = BracketRules.from_league(data.league)
    places: dict[int, int] = {}
    for game in data.winners_bracket:
        p, w, loser = game.get("p"), game.get("w"), game.get("l")
        if p and w is not None and loser is not None:
            places[int(w)], places[int(loser)] = int(p), int(p) + 1
    for game in data.losers_bracket:
        p, w, loser = game.get("p"), game.get("w"), game.get("l")
        if p and w is not None and loser is not None:
            if rules.toilet_bowl:
                places[int(w)], places[int(loser)] = 13 - int(p), 12 - int(p)
            else:
                places[int(w)], places[int(loser)] = 6 + int(p), 7 + int(p)
    teams = len(data.rosters)
    return places if len(places) == teams and sorted(places.values()) == list(range(1, teams + 1)) else {}


def regular_season_order(data: SeasonData) -> list[int]:
    """Roster ids by regular-season wins, then points for (Sleeper's tiebreak), best first."""
    def key(r):
        s = r.get("settings") or {}
        points = float(s.get("fpts") or 0) + float(s.get("fpts_decimal") or 0) / 100
        return (-int(s.get("wins") or 0), int(s.get("losses") or 0), -points)
    return [int(r["roster_id"]) for r in sorted(data.rosters, key=key)]


def final_places(data: SeasonData) -> tuple[dict[int, int], bool]:
    """(roster_id -> final place, from_brackets). Seasons without finished brackets fall back to the
    regular-season order (from_brackets False)."""
    places = bracket_places(data)
    if places:
        return places, True
    return {rid: i + 1 for i, rid in enumerate(regular_season_order(data))}, False


def season_complete(data: SeasonData) -> bool:
    return data.status == "complete" and bool(bracket_places(data))


# ---- games ----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Game:
    """One finished game from one manager's side."""

    season: str
    week: int
    playoff: bool          # a winners-bracket game
    user: str
    opp: str
    roster: int
    opp_roster: int
    points: float
    opp_points: float

    @property
    def result(self) -> str:
        return "W" if self.points > self.opp_points else "L" if self.points < self.opp_points else "T"

    @property
    def margin(self) -> float:
        return round(self.points - self.opp_points, 2)


def season_games(store: Store, league_key: str, season: str) -> list[Game]:
    """Every finished regular-season game and winners-bracket playoff game of a season, from both
    sides. Weeks after Sleeper's last scored week are left out, so a live week never counts."""
    from ffapp.odds import completed_weeks, regular_season_range

    data = store.read_season(league_key, season)
    owners = roster_owners(store, league_key, season)
    done = completed_weeks(data.league)
    rules = BracketRules.from_league(data.league)
    games: list[Game] = []

    def add(week: int, a: int, b: int, playoff: bool) -> None:
        pts = {int(t["roster_id"]): float(t.get("points") or 0.0) for t in data.matchups.get(week, [])}
        if a in pts and b in pts and a in owners and b in owners:
            games.append(Game(season, week, playoff, owners[a], owners[b], a, b, pts[a], pts[b]))
            games.append(Game(season, week, playoff, owners[b], owners[a], b, a, pts[b], pts[a]))

    for week in regular_season_range(data.league):
        if week > done:
            break
        pairs: dict[int, list[int]] = {}
        for t in data.matchups.get(week, []):
            if t.get("matchup_id") is not None:
                pairs.setdefault(int(t["matchup_id"]), []).append(int(t["roster_id"]))
        for teams in pairs.values():
            if len(teams) == 2:
                add(week, teams[0], teams[1], False)
    for game in data.winners_bracket:
        week = rules.week_for_round(int(game.get("r") or 0))
        if week <= done and game.get("t1") and game.get("t2") and game.get("w") is not None:
            add(week, int(game["t1"]), int(game["t2"]), True)
    return games


def league_games(store: Store, league_key: str) -> list[Game]:
    out: list[Game] = []
    for season in store.seasons(league_key):
        out.extend(season_games(store, league_key, season))
    return sorted(out, key=lambda g: (g.season, g.week, g.user))


# ---- head to head, form and records -----------------------------------------------------------

def head_to_head(games: list[Game], user: str) -> dict[str, dict]:
    """opponent -> {wins, losses, ties, playoff_wins, playoff_losses, pf, pa, games, last}."""
    out: dict[str, dict] = {}
    for g in games:
        if g.user != user:
            continue
        row = out.setdefault(g.opp, {"wins": 0, "losses": 0, "ties": 0, "playoff_wins": 0, "playoff_losses": 0, "pf": 0.0, "pa": 0.0, "games": 0, "last": None})
        key = {"W": "wins", "L": "losses", "T": "ties"}[g.result]
        row[key] += 1
        if g.playoff and g.result != "T":
            row["playoff_wins" if g.result == "W" else "playoff_losses"] += 1
        row["pf"] = round(row["pf"] + g.points, 2)
        row["pa"] = round(row["pa"] + g.opp_points, 2)
        row["games"] += 1
        row["last"] = {"season": g.season, "week": g.week, "result": g.result, "points": g.points, "opp_points": g.opp_points}
    return out


def form(games: list[Game], user: str, season: str, n: int = 5) -> list[str]:
    """The manager's last ``n`` results of ``season``, oldest first ([] before week 1)."""
    return [g.result for g in games if g.user == user and g.season == season][-n:]


def _streaks(results: list[tuple[Game, str]], want: str) -> list[dict]:
    """Every run of consecutive ``want`` results within a season: {length, season, from, to}."""
    runs: list[dict] = []
    current: list[Game] = []
    for g, r in results + [(None, None)]:
        if g is not None and r == want and (not current or current[-1].season == g.season):
            current.append(g)
            continue
        if current:
            runs.append({"length": len(current), "season": current[0].season, "from": current[0].week, "to": current[-1].week})
        current = [g] if g is not None and r == want else []
    return runs


RECORD_KEYS = ("high_score", "low_score", "biggest_win", "biggest_loss", "closest_loss", "win_streak", "loss_streak", "season_points")


def _record_candidates(games: list[Game], season_points: dict[tuple[str, str], float]) -> dict[str, list[dict]]:
    """Every candidate value for every record type, league-wide: one entry per game, run or season."""
    cand: dict[str, list[dict]] = {k: [] for k in RECORD_KEYS}
    by_user: dict[str, list[Game]] = {}
    for g in games:
        by_user.setdefault(g.user, []).append(g)
        where = {"user": g.user, "season": g.season, "week": g.week, "opp": g.opp}
        cand["high_score"].append({**where, "value": g.points})
        cand["low_score"].append({**where, "value": g.points})
        if g.result == "W":
            cand["biggest_win"].append({**where, "value": g.margin})
        if g.result == "L":
            cand["biggest_loss"].append({**where, "value": -g.margin})
            cand["closest_loss"].append({**where, "value": -g.margin})
    for user, own in by_user.items():
        seq = [(g, g.result) for g in own]
        for want, key in (("W", "win_streak"), ("L", "loss_streak")):
            for run in _streaks(seq, want):
                cand[key].append({"user": user, **run, "value": run["length"]})
    for (user, season), pts in season_points.items():
        cand["season_points"].append({"user": user, "season": season, "value": round(pts, 2)})
    return cand


LOWER_IS_BETTER = {"low_score", "closest_loss"}


def _rank(value: float, values: list[float], lower_is_better: bool) -> int:
    """1-based rank of ``value`` among ``values``; ties share the better rank."""
    if lower_is_better:
        return 1 + sum(1 for v in values if v < value)
    return 1 + sum(1 for v in values if v > value)


def records(games: list[Game], season_points: dict[tuple[str, str], float]) -> dict[str, dict[str, dict]]:
    """user -> record type -> the manager's best entry, with ``rank`` among every entry in league
    history (ties share). Lowest score and closest loss rank lowest first; the rest highest first."""
    cand = _record_candidates(games, season_points)
    out: dict[str, dict[str, dict]] = {}
    for key, entries in cand.items():
        low = key in LOWER_IS_BETTER
        values = [e["value"] for e in entries]
        best: dict[str, dict] = {}
        for e in entries:
            cur = best.get(e["user"])
            if cur is None or (e["value"] < cur["value"] if low else e["value"] > cur["value"]):
                best[e["user"]] = e
        for user, e in best.items():
            out.setdefault(user, {})[key] = {**{k: v for k, v in e.items() if k != "user"}, "rank": _rank(e["value"], values, low)}
    return out


# ---- luck -------------------------------------------------------------------------------------

def all_play(games: list[Game]) -> dict[str, dict]:
    """user -> {wins, losses, ties}: each regular-season week, the score against every other team's."""
    by_week: dict[tuple[str, int], list[Game]] = {}
    for g in games:
        if not g.playoff:
            by_week.setdefault((g.season, g.week), []).append(g)
    out: dict[str, dict] = {}
    for week_games in by_week.values():
        for g in week_games:
            row = out.setdefault(g.user, {"wins": 0, "losses": 0, "ties": 0})
            for other in week_games:
                if other.user == g.user:
                    continue
                if g.points > other.points:
                    row["wins"] += 1
                elif g.points < other.points:
                    row["losses"] += 1
                else:
                    row["ties"] += 1
    return out


def luck(games: list[Game], bench: dict[str, float]) -> dict[str, dict]:
    """user -> all-play record, wins above all-play pace, points against per game against the league
    average, and points left on bench (from ``bench``: user -> sum of potential minus actual points)."""
    ap = all_play(games)
    regular = [g for g in games if not g.playoff]
    league_pa = sum(g.opp_points for g in regular) / len(regular) if regular else 0.0
    out: dict[str, dict] = {}
    for user, row in ap.items():
        own = [g for g in regular if g.user == user]
        played = row["wins"] + row["losses"] + row["ties"]
        share = (row["wins"] + 0.5 * row["ties"]) / played if played else 0.0
        wins = sum(1 for g in own if g.result == "W") + 0.5 * sum(1 for g in own if g.result == "T")
        pa = sum(g.opp_points for g in own) / len(own) if own else 0.0
        out[user] = {
            "all_play": row,
            "wins_above_pace": round(wins - share * len(own), 2),
            "pa_vs_league": round(pa - league_pa, 2),
            "bench_points": round(bench.get(user, 0.0), 2),
        }
    return out


def roster_bench_points(settings: dict) -> float:
    """Sleeper's potential points minus actual points for one roster-season (never below zero)."""
    potential = float(settings.get("ppts") or 0) + float(settings.get("ppts_decimal") or 0) / 100
    actual = float(settings.get("fpts") or 0) + float(settings.get("fpts_decimal") or 0) / 100
    return round(max(0.0, potential - actual), 2)


def bench_points(store: Store, league_key: str) -> dict[str, float]:
    """user -> points left on bench across seasons: Sleeper's potential points minus actual points."""
    out: dict[str, float] = {}
    for season in store.seasons(league_key):
        owners = roster_owners(store, league_key, season)
        for r in store.read_rosters(league_key, season):
            s = r.get("settings") or {}
            if "ppts" not in s:
                continue
            uid = owners.get(int(r["roster_id"]))
            if uid:
                out[uid] = out.get(uid, 0.0) + roster_bench_points(s)
    return out


def season_points(games: list[Game]) -> dict[tuple[str, str], float]:
    """(user, season) -> regular-season points for."""
    out: dict[tuple[str, str], float] = {}
    for g in games:
        if not g.playoff:
            out[(g.user, g.season)] = out.get((g.user, g.season), 0.0) + g.points
    return out


# ---- honours ----------------------------------------------------------------------------------

def honours(store: Store, league_key: str) -> dict[str, dict[str, list[str]]]:
    """user -> honour -> seasons, for completed seasons: champion, runner_up, regular_first,
    most_points, playoffs, toilet_bowl (only where the losers bracket is a toilet bowl)."""
    out: dict[str, dict[str, list[str]]] = {}
    for season in store.seasons(league_key):
        data = store.read_season(league_key, season)
        places = bracket_places(data)
        if data.status != "complete" or not places:
            continue
        owners = roster_owners(store, league_key, season)
        rules = BracketRules.from_league(data.league)

        def give(rid: int, key: str) -> None:
            uid = owners.get(rid)
            if uid:
                out.setdefault(uid, {}).setdefault(key, []).append(season)

        for rid, place in places.items():
            if place == 1:
                give(rid, "champion")
            elif place == 2:
                give(rid, "runner_up")
            if place <= rules.playoff_teams:
                give(rid, "playoffs")
            if rules.toilet_bowl and place == len(places):
                give(rid, "toilet_bowl")
        order = regular_season_order(data)
        give(order[0], "regular_first")
        def fpts(r):
            s = r.get("settings") or {}
            return float(s.get("fpts") or 0) + float(s.get("fpts_decimal") or 0) / 100
        top = max(data.rosters, key=fpts)
        give(int(top["roster_id"]), "most_points")
    return out


# ---- rivals -----------------------------------------------------------------------------------

NEMESIS_MIN_GAMES = 4


def nemesis(h2h: dict[str, dict]) -> str | None:
    """The opponent with the worst head-to-head record (lowest win share) over at least 4 games,
    ties broken by the larger points deficit; None when no opponent has 4 games."""
    rows = [(opp, r) for opp, r in h2h.items() if r["games"] >= NEMESIS_MIN_GAMES]
    if not rows:
        return None
    def key(item):
        _, r = item
        share = (r["wins"] + 0.5 * r["ties"]) / r["games"]
        return (share, r["pf"] - r["pa"])
    return min(rows, key=key)[0]


def config_rival(store: Store, league_key: str, rivals, manager: Manager) -> str | None:
    """The fixed rival from the league config: the owner of the rival roster in the manager's latest
    season. Raises ValueError when the config names a roster the league does not have."""
    season = manager.last
    owners = roster_owners(store, league_key, season)
    for a, b in rivals.pairs:
        for rid in (a, b):
            if rid not in owners:
                raise ValueError(f"rivals: roster {rid} does not exist in {league_key} {season}")
    rival_roster = rivals.rival_of(manager.roster_by_season[season])
    return owners.get(rival_roster) if rival_roster else None


def rivalry_record(games: list[Game], rivals, user: str) -> dict:
    """W-L-T in rivalry-week games against the rival roster, over the seasons with a rivalry week."""
    out = {"wins": 0, "losses": 0, "ties": 0, "seasons": []}
    for g in games:
        week = rivals.rivalry_week.get(g.season)
        if g.user == user and not g.playoff and week == g.week and rivals.rival_of(g.roster) == g.opp_roster:
            out[{"W": "wins", "L": "losses", "T": "ties"}[g.result]] += 1
            out["seasons"].append(g.season)
    return out


# ---- player move windows and players --------------------------------------------------------

def weekly_war(store: Store, league_key: str) -> dict[tuple[str, int, str], float]:
    """(season, week, player_id) -> the week's WAR: p(week) - p(replacement) for active weeks.

    A player's season WAR is the sum of these over the weeks he was active, so window WAR adds up
    exactly. Weeks he did not play have no entry (they add nothing)."""
    from ffapp.war import read_war, war_seasons, win_probability

    out: dict[tuple[str, int, str], float] = {}
    for season in war_seasons(store, league_key):
        payload = read_war(store, league_key, season) or {}
        constants = payload.get("constants") or {}
        sd = constants.get("opponent_sd")
        if not sd:
            continue
        base = {pos: win_probability(info["level"], constants["slot_mean"][pos], sd) for pos, info in (payload.get("replacement") or {}).items()
                if pos in constants.get("slot_mean", {})}
        for pid, player in (payload.get("players") or {}).items():
            pos = player.get("position")
            if pos not in base:
                continue
            for row in player.get("weekly") or []:
                if row.get("played") and row.get("p") is not None:
                    out[(str(season), int(row["week"]), str(pid))] = row["p"] - base[pos]
    return out


def roster_weeks(store: Store, league_key: str) -> tuple[list[tuple[str, int]], dict[str, dict[tuple[str, int], set[str]]]]:
    """(timeline, user -> week -> players). The timeline lists every stored (season, week) with
    matchup rosters, in order; a player is on a team in a week when he is in its matchup roster."""
    timeline: list[tuple[str, int]] = []
    held: dict[str, dict[tuple[str, int], set[str]]] = {}
    for season in store.seasons(league_key):
        data = store.read_season(league_key, season)
        owners = roster_owners(store, league_key, season)
        for week in sorted(data.matchups):
            rows = data.matchups[week]
            if not any(r.get("players") for r in rows):
                continue
            timeline.append((season, week))
            for r in rows:
                uid = owners.get(int(r["roster_id"]))
                if uid:
                    held.setdefault(uid, {})[(season, week)] = {str(p) for p in r.get("players") or []}
    return timeline, held


@dataclass
class Window:
    player: str
    kind: str                      # "added" or "departed"
    start: tuple[str, int]
    end: tuple[str, int]           # last week inside the window
    weeks: list[tuple[str, int]] = field(default_factory=list)
    war: float = 0.0
    returned: bool = False         # departed windows: he came back to the team


def windows(timeline: list[tuple[str, int]], user_weeks: dict[tuple[str, int], set[str]], war: dict, carry_over: bool) -> list[Window]:
    """Added windows (consecutive weeks on the team) and departed windows (from leaving until back on
    the team, or the end of the timeline), each summing the player's weekly WAR over its weeks.
    Without ``carry_over`` (redraft) every window ends with its season."""
    segments: list[list[tuple[str, int]]] = []
    for wk in timeline:
        if not carry_over and segments and segments[-1][-1][0] != wk[0]:
            segments.append([wk])
        elif segments:
            segments[-1].append(wk)
        else:
            segments.append([wk])
    players = sorted(set().union(*user_weeks.values())) if user_weeks else []
    out: list[Window] = []
    for pid in players:
        for seg in segments:
            on = [pid in user_weeks.get(wk, set()) for wk in seg]
            if not any(on):
                continue
            i = 0
            seen_on = False
            while i < len(seg):
                j = i
                while j < len(seg) and on[j] == on[i]:
                    j += 1
                run = seg[i:j]
                if on[i]:
                    out.append(Window(pid, "added", run[0], run[-1], run))
                    seen_on = True
                elif seen_on:  # only after he has been on the team
                    out.append(Window(pid, "departed", run[0], run[-1], run, returned=j < len(seg)))
                i = j
    for w in out:
        w.war = round(sum(war.get((s, wk, w.player), 0.0) for s, wk in w.weeks), 4)
    return out


def players_block(wins: list[Window], names: dict[str, str]) -> dict:
    """Best Player All-Time (most WAR in weeks on the team), most seasons on the team, and the one
    that got away (the largest single departed window)."""
    added: dict[str, dict] = {}
    for w in wins:
        if w.kind != "added":
            continue
        row = added.setdefault(w.player, {"war": 0.0, "seasons": set()})
        row["war"] += w.war
        row["seasons"].update(s for s, _ in w.weeks)
    best = max(added.items(), key=lambda kv: kv[1]["war"], default=None)
    most = max(added.items(), key=lambda kv: (len(kv[1]["seasons"]), kv[1]["war"]), default=None)
    away = max((w for w in wins if w.kind == "departed"), key=lambda w: w.war, default=None)
    return {
        "best": {"player_id": best[0], "name": names.get(best[0], best[0]), "war": round(best[1]["war"], 2), "seasons": len(best[1]["seasons"])} if best else None,
        "most_seasons": {"player_id": most[0], "name": names.get(most[0], most[0]), "seasons": len(most[1]["seasons"])} if most else None,
        "got_away": {"player_id": away.player, "name": names.get(away.player, away.player), "war": round(away.war, 2),
                     "from": list(away.start), "returned": away.returned} if away and away.war > 0 else None,
    }


def player_names(store: Store, league_key: str) -> dict[str, str]:
    """player_id -> name, from the WAR files (newest season wins)."""
    from ffapp.war import read_war, war_seasons

    out: dict[str, str] = {}
    for season in war_seasons(store, league_key):
        for pid, player in ((read_war(store, league_key, season) or {}).get("players") or {}).items():
            out[str(pid)] = player.get("name") or out.get(str(pid), str(pid))
    return out


def move_player_info(store: Store, league_key: str) -> tuple[dict[str, str], dict[str, str]]:
    """(player_id -> name, player_id -> position) for every player in the league's transactions:
    the WAR files first (newest season wins), then the season's stat and projection records for
    players who never had a game, then the ESPN crosswalk (Sleeper names)."""
    from ffapp.news import stat_names
    from ffapp.war import read_war, war_seasons

    names: dict[str, str] = {}
    positions: dict[str, str] = {}
    for season in war_seasons(store, league_key):
        for pid, player in ((read_war(store, league_key, season) or {}).get("players") or {}).items():
            if player.get("name"):
                names[str(pid)] = player["name"]
            if player.get("position"):
                positions[str(pid)] = player["position"]
    for season in store.seasons(league_key):
        wanted = {str(p) for week in store.read_transactions(league_key, season).values() for t in week
                  for side in ("adds", "drops") for p in (t.get(side) or {})}
        if wanted - names.keys():
            more_names, more_pos = stat_names(store, season)
            for pid in wanted - names.keys():
                if pid in more_names:
                    names[pid] = more_names[pid]
                    positions.setdefault(pid, more_pos.get(pid))
    for pid, info in (store.read_crosswalk() or {}).items():   # last: Sleeper's player list as saved for ESPN matching
        if pid not in names and info.get("name"):
            names[pid] = info["name"]
            positions.setdefault(pid, info.get("position"))
    return names, positions


def faab_by_season(store: Store, league_key: str, user: str) -> dict[str, dict]:
    """season -> {spent, budget} from Sleeper's FAAB used per roster and the league's budget."""
    out: dict[str, dict] = {}
    for season in store.seasons(league_key):
        data = store.read_season(league_key, season)
        budget = int((data.league.get("settings") or {}).get("waiver_budget") or 0)
        owners = roster_owners(store, league_key, season)
        for r in data.rosters:
            if owners.get(int(r["roster_id"])) == user and budget:
                out[season] = {"spent": int((r.get("settings") or {}).get("waiver_budget_used") or 0), "budget": budget}
    return out


# ---- the exported manager file ----------------------------------------------------------------

def _record(games: list[Game], user: str, season: str | None = None, playoff: bool = False) -> dict:
    own = [g for g in games if g.user == user and g.playoff == playoff and (season is None or g.season == season)]
    w = sum(1 for g in own if g.result == "W")
    los = sum(1 for g in own if g.result == "L")
    t = sum(1 for g in own if g.result == "T")
    return {"wins": w, "losses": los, "ties": t, "win_rate": round((w + 0.5 * t) / len(own), 4) if own else None}


def _team_name_history(m: Manager) -> list[dict]:
    """Team names newest first, consecutive seasons with the same name merged."""
    out: list[dict] = []
    for season in m.seasons:
        name = m.team_names[season]
        if out and out[-1]["name"] == name:
            out[-1]["to"] = season
        else:
            out.append({"name": name, "from": season, "to": season})
    return out[::-1]


def _game_row(g: Game, names: dict[str, str]) -> dict:
    return {"season": g.season, "week": g.week, "result": g.result, "points": round(g.points, 2), "opp_points": round(g.opp_points, 2),
            "opp": names.get(g.opp, g.opp), "opp_user": g.opp, "opp_roster": g.opp_roster, "playoff": g.playoff}


def _season_points_by_player(data: SeasonData, rid: int) -> dict[str, float]:
    """player_id -> points scored while on this roster in regular-season and playoff weeks."""
    out: dict[str, float] = {}
    for rows in data.matchups.values():
        for r in rows:
            if int(r["roster_id"]) == rid:
                for pid, pts in (r.get("players_points") or {}).items():
                    out[str(pid)] = out.get(str(pid), 0.0) + float(pts or 0.0)
    return out


def _latest_week_points(data: SeasonData, rid: int) -> dict | None:
    """Starter and bench points in the latest week with scores."""
    for week in sorted(data.matchups, reverse=True):
        for r in data.matchups[week]:
            if int(r["roster_id"]) == rid and r.get("points"):
                starters = sum(float(p or 0) for p in r.get("starters_points") or [])
                total = sum(float(p or 0) for p in (r.get("players_points") or {}).values())
                return {"week": week, "starters": round(starters, 2), "bench": round(max(0.0, total - starters), 2)}
    return None


def _roster_rows(data: SeasonData, rid: int, team: dict | None, statuses: dict[str, str], byes: set[str]) -> list[dict]:
    """The roster in lineup order (slots from the league), then bench, IR and taxi. ``status`` is the
    raw Sleeper status (Questionable included); ``bye`` is set when his NFL team has no game this week."""
    from ffapp.league import starter_slots

    roster = next((r for r in data.rosters if int(r["roster_id"]) == rid), {})
    info = {p["id"]: p for p in (team or {}).get("players", [])}
    rows: list[dict] = []

    def row(slot: str, pid: str) -> dict:
        p = info.get(str(pid), {})
        return {"slot": slot, "player_id": str(pid), "name": p.get("name", str(pid)), "position": p.get("position"),
                "ppg": p.get("ppg"), "status": statuses.get(str(pid)), "bye": p.get("team") in byes, "nfl_team": p.get("team")}

    starters = [str(p) for p in roster.get("starters") or [] if p and p != "0"]
    for slot, pid in zip(starter_slots(data.league), roster.get("starters") or []):
        if pid and pid != "0":
            rows.append(row(slot, pid))
    reserve = {str(p) for p in roster.get("reserve") or []}
    taxi = {str(p) for p in roster.get("taxi") or []}
    for pid in roster.get("players") or []:
        pid = str(pid)
        if pid not in starters and pid not in reserve and pid not in taxi:
            rows.append(row("BN", pid))
    rows += [row("IR", p) for p in roster.get("reserve") or []]
    rows += [row("TX", p) for p in roster.get("taxi") or []]
    return rows


def managers_export(store: Store, config, league_key: str, league_payload: dict, games_payload: dict | None,
                    positions_payload: dict | None) -> dict:
    """Every block the Managers page shows, for every current and retired manager of one league."""
    from ffapp.moves import league_moves
    from ffapp.news import league_context, manager_stories
    from ffapp.ratings import read_ratings

    managers = managers_for_league(store, league_key)
    games = league_games(store, league_key)
    names = {u: m.name for u, m in managers.items()}
    sp = season_points(games)
    recs = records(games, sp)
    lk = luck(games, bench_points(store, league_key))
    hon = honours(store, league_key)
    rivals = config.leagues[league_key].rivals
    timeline, held = roster_weeks(store, league_key)
    war = weekly_war(store, league_key)
    pnames = player_names(store, league_key)
    carry = not BracketRules.from_league(store.read_season(league_key, store.seasons(league_key)[-1]).league).toilet_bowl
    ratings = (read_ratings(store, league_key) or {}).get("managers", {})
    seasons_data = {s: store.read_season(league_key, s) for s in store.seasons(league_key)}
    owners_by_season = {s: roster_owners(store, league_key, s) for s in seasons_data}
    wins_by_user = {uid: windows(timeline, held.get(uid, {}), war, carry) for uid in managers}
    move_names, move_positions = move_player_info(store, league_key)
    lm = league_moves(store, league_key, owners_by_season, timeline, wins_by_user, war, move_names, move_positions)
    news_ctx = league_context(store, league_key, managers, games, rivals)
    news_ctx["moves"] = lm
    places = {s: final_places(d) for s, d in seasons_data.items()}
    pos_files = (positions_payload or {}).get("files", {})
    current = league_payload["season"]
    teams_now = {int(t["roster_id"]): t for t in league_payload["teams"]}
    standings = sorted(league_payload["teams"], key=lambda t: (-(t.get("wins") or 0), -(t.get("points_for") or 0)))
    position_now = {int(t["roster_id"]): i + 1 for i, t in enumerate(standings)}
    next_games = _next_games(games_payload)
    statuses, byes = _current_statuses_and_byes(store, current, next_games)

    out = []
    for uid, m in managers.items():
        season = m.last
        rid = m.roster_by_season[season]
        data = seasons_data[season]
        h2h = head_to_head(games, uid)
        rival_uid = config_rival(store, league_key, rivals, m) if rivals else nemesis(h2h)
        team_file = pos_files.get(season, {})
        team = next((t for t in team_file.get("teams", []) if int(t["roster_id"]) == rid), None)
        own_games = [g for g in games if g.user == uid and g.season == season]
        rating = (ratings.get(uid) or {}).get("history") or []
        wins = wins_by_user[uid]
        player_pts = _season_points_by_player(data, rid)
        top = max(player_pts.items(), key=lambda kv: kv[1], default=None)
        played_any = bool(own_games)
        projected_top = None
        if m.current and not played_any and team:
            best = max(team.get("players", []), key=lambda p: p.get("ppg") or 0, default=None)
            if best:
                projected_top = {"player_id": best["id"], "name": best["name"], "position": best.get("position"), "points": round((best.get("ppg") or 0) * (best.get("projected") or 0), 1)}
        live = teams_now.get(rid) if m.current else None
        nxt = next_games.get(rid) if m.current else None
        out.append({
            "user_id": uid, "name": m.name, "current": m.current, "first": m.first, "last": m.last, "roster_id": rid if m.current else None,
            "team_name": m.team_names[season], "team_names": _team_name_history(m), "logo": m.logo, "avatar": m.avatar,
            "banners": {"champion": hon.get(uid, {}).get("champion", []), "toilet_bowl": hon.get(uid, {}).get("toilet_bowl", [])},
            "form": form(games, uid, current) if m.current else None,
            "all_time": _record(games, uid), "playoff_record": _record(games, uid, playoff=True),
            "rating": {"mu": rating[-1]["mu"], "season": rating[-1]["season"]} if rating else None,
            "rival": {"user_id": rival_uid, "name": names.get(rival_uid)} if rival_uid else None,
            "tiles": {
                "position": position_now.get(rid) if m.current else places[season][0].get(rid),
                "record": _record(games, uid, season),
                "points_for": round(sp.get((uid, season), 0.0), 2),
                "last_result": _game_row(own_games[-1], names) if own_games else None,
                "next": ({**nxt, "opp": names.get(_owner(store, league_key, current, nxt["opp_roster"])), "opp_user": _owner(store, league_key, current, nxt["opp_roster"]),
                          "rivalry": bool(rivals and rivals.rivalry_week.get(current) == nxt["week"] and rivals.rival_of(rid) == nxt["opp_roster"])} if nxt else None),
                "top_scorer": ({"player_id": top[0], "name": pnames.get(top[0]) or _player_name(team, top[0]), "points": round(top[1], 1), "position": _player_pos(team, top[0])} if top and played_any else None),
                "top_projected": projected_top,
                "forecast": {"playoffs": live.get("playoffs"), "change": live.get("change", {}).get("playoffs") if isinstance(live.get("change"), dict) else None} if live else None,
            },
            "roster": _roster_rows(data, rid, team, statuses if m.current else {}, byes if m.current else set()),
            "replacement": {pos: info.get("replacement") for pos, info in team_file.get("positions", {}).items()},
            "week_points": _latest_week_points(data, rid),
            "history": {
                "finishes": [{"season": s, "place": places[s][0].get(m.roster_by_season[s]), "final": places[s][1]} for s in m.seasons],
                "forecast_finish": _forecast_finish(live) if live else None,
                "honours": hon.get(uid, {}),
                "luck": lk.get(uid),
            },
            "head_to_head": _h2h_rows(h2h, names, rival_uid),
            "records": recs.get(uid, {}),
            "rivalry": rivalry_record(games, rivals, uid) if rivals else None,
            "faab": {s: {**f, **lm.faab.get(uid, {}).get(s, {"biggest": None, "overpaid": 0})} for s, f in faab_by_season(store, league_key, uid).items()},
            "moves": lm.moves.get(uid, {}),
            "players": players_block(wins, pnames),
            "news": manager_stories(store, league_key, m, news_ctx),
        })
    return {"league_key": league_key, "season": current, "toilet_bowl": not carry, "managers": out}


def _current_statuses_and_byes(store: Store, season: str, next_games: dict[int, dict]) -> tuple[dict[str, str], set[str]]:
    """The latest saved Sleeper statuses, and the NFL teams on bye in the current week."""
    from ffapp.injuries import statuses_for_week
    from ffapp.schedule import Schedule

    statuses = statuses_for_week(store, season, 99) or {}
    week = next(iter(next_games.values()), {}).get("week")
    byes: set[str] = set()
    if week:
        schedule = Schedule(store, season)
        for team in ("ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
                     "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"):
            if schedule.on_bye(week, team):
                byes.add(team)
    return statuses, byes


def _owner(store: Store, league_key: str, season: str, rid: int | None) -> str | None:
    return roster_owners(store, league_key, season).get(rid) if rid else None


def _player_name(team: dict | None, pid: str) -> str:
    return next((p["name"] for p in (team or {}).get("players", []) if p["id"] == pid), pid)


def _player_pos(team: dict | None, pid: str) -> str | None:
    return next((p.get("position") for p in (team or {}).get("players", []) if p["id"] == pid), None)


def _forecast_finish(team: dict) -> int | None:
    """The most likely final seed from the forecast's seed distribution."""
    dist = team.get("seed_distribution") or []
    return max(range(len(dist)), key=lambda i: dist[i]) + 1 if dist else None


def _next_games(games_payload: dict | None) -> dict[int, dict]:
    """roster_id -> the current week's game: {week, opp_roster, win_prob} from the Games export."""
    if not games_payload:
        return {}
    week = games_payload["index"]["current"]
    payload = games_payload["weeks"].get(week) or {}
    out: dict[int, dict] = {}
    for game in payload.get("games", []):
        view = (game.get("views") or {}).get(game.get("default_view") or "model") or {}
        teams = view.get("teams") or game.get("teams") or []
        if len(teams) == 2:
            for a, b in ((teams[0], teams[1]), (teams[1], teams[0])):
                out[int(a["roster_id"])] = {"week": week, "opp_roster": int(b["roster_id"]), "win_prob": a.get("win_prob"), "final": game.get("winner") is not None}
    return out


def _h2h_rows(h2h: dict[str, dict], names: dict[str, str], rival: str | None) -> list[dict]:
    rows = [{"user_id": u, "name": names.get(u, u), "rival": u == rival, **r} for u, r in h2h.items()]
    return sorted(rows, key=lambda r: (not r["rival"], -r["games"], r["name"].lower()))
