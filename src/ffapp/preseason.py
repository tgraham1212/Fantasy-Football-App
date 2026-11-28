"""The preseason Forecast for the League sub-tab's Preseason tab: made once per league-season when the
draft is complete, from each Player's preseason projected season stat line, with injury absences
filled from the bench, and each team graded A+ to F. Stored as a record
(``data/preseason/<league>/<season>.json``) and exported as ``site/data/<league>/preseason.json``. See
Calculations.txt section 26.

- Values: the season line scored with the league-season's scoring / 17, 0 in the bye week. ESPN's
  season projections (kickers and defences: ESPN's projected season points); 2023, whose ESPN lines
  are blank for many top Players, uses Sleeper's season projections, else the week-1 Projection.
- Rosters: drafted (redraft) or week-1 without taxi (dynasty); a missing kicker or defence plays
  replacement level (Calc 14).
- Absences: every rostered Player misses each simulated week at his position's pooled rate; slots
  are filled with the best healthy eligible Player, else replacement level. Scores carry the
  Forecasts' residual noise; standings, seeds and brackets are the season simulation's own.
- Wins Saved: the same draws with absent starters at replacement level instead of the bench.
"""

from __future__ import annotations

import logging
import re
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from ffapp.bracket import BracketRules
from ffapp.draft import rules_for
from ffapp.league import FLEX_ELIGIBLE, starter_slots
from ffapp.managers import final_places, managers_for_league, roster_owners
from ffapp.odds import fixed_records, regular_season_range
from ffapp.scoring import projected_points
from ffapp.simulate import SimInputs, simulate, summarize
from ffapp.standings import pairings
from ffapp.store import SeasonData, Store, read_json, write_json

log = logging.getLogger(__name__)

GAMES = 17
RUNS = 10_000
ABSENCE = {"QB": 0.106, "RB": 0.119, "WR": 0.114, "TE": 0.102, "K": 0.044, "DEF": 0.0}  # 1.5.3, pooled 2021-2025
ESPN_STATS = {"3": "pass_yd", "4": "pass_td", "19": "pass_2pt", "20": "pass_int", "24": "rush_yd", "25": "rush_td", "26": "rush_2pt",
              "42": "rec_yd", "43": "rec_td", "44": "rec_2pt", "53": "rec", "72": "fum_lost"}
ESPN_POSITIONS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DEF"}
SLEEPER_SEASON_ONLY = {"2023"}
WEEK1_POSITIONS = ("K", "DEF")  # ESPN's 2023 season lines are blank for many top Players (1.5.1.1)
SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")


# -- matching (1.5.1.2) -----------------------------------------------------------------------------


def norm_name(name: str) -> str:
    s = re.sub(r"[.'`’]", "", (name or "").lower()).replace("-", " ")
    return " ".join(SUFFIX.sub("", s).split())


def espn_lines(players: list, season: str) -> list[dict]:
    """``[{name, position, team, stats, applied}]``: each ESPN Player's preseason season line."""
    from ffapp.espn import ESPN_TEAMS

    out = []
    for p in players or []:
        pl = p.get("player", p)
        pos = ESPN_POSITIONS.get(pl.get("defaultPositionId"))
        if not pos:
            continue
        for s in pl.get("stats") or []:
            if s.get("seasonId") == int(season) and s.get("statSourceId") == 1 and s.get("statSplitTypeId") == 0 and (s.get("stats") or s.get("appliedTotal")):
                out.append({"name": pl.get("fullName") or "", "position": pos, "team": ESPN_TEAMS.get(pl.get("proTeamId")),
                            "stats": {ESPN_STATS[k]: float(v) for k, v in (s.get("stats") or {}).items() if k in ESPN_STATS},
                            "applied": float(s.get("appliedTotal") or 0.0)})
                break
    return out


def match_lines(lines: list[dict], players: dict[str, dict]) -> dict[str, dict]:
    """Sleeper id -> ESPN line, by normalised name and position (NFL team breaks ties); a defence by
    its team. ``players``: Sleeper id -> {first, last, position, team}."""
    by_key: dict[tuple, list[dict]] = {}
    for line in lines:
        key = ("DEF", line["team"]) if line["position"] == "DEF" else (line["position"], norm_name(line["name"]))
        by_key.setdefault(key, []).append(line)
    out = {}
    for pid, p in players.items():
        if p["position"] == "DEF":
            found = by_key.get(("DEF", p.get("team") or pid))
        else:
            found = by_key.get((p["position"], norm_name(f"{p.get('first', '')} {p.get('last', '')}")))
        if found:
            same_team = [x for x in found if x["team"] and x["team"] == p.get("team")]
            out[pid] = (same_team or found)[0]
    return out


# -- values (1.5.1, 1.5.1.1) --------------------------------------------------------------------------


def line_value(line: dict, position: str, scoring: dict[str, float]) -> float:
    """Per-game value of a season line: scored with the league's scoring / 17 (K and DEF: ESPN's points / 17)."""
    if position in ("K", "DEF") or not line.get("stats"):
        return round(line.get("applied", 0.0) / GAMES, 3)
    return round(projected_points(line["stats"], scoring) / GAMES, 3)


@dataclass
class Values:
    per_game: dict[str, float]
    source: dict[str, str]
    unmatched: list[str]
    levels: dict[str, float]  # preseason replacement level by position, on the same scale (1.5.2.1)


REPLACEMENT_TOP_N = 3


def pool_levels(free: dict[str, list[float]]) -> dict[str, float]:
    """Preseason replacement level: the mean value of the 3 best Players at each position on no roster."""
    out = {}
    for pos, vals in free.items():
        best = sorted(vals, reverse=True)[:REPLACEMENT_TOP_N]
        out[pos] = round(sum(best) / len(best), 3) if best else 0.0
    return out


def under_way(league: dict) -> bool:
    """The season has played a week (an in-season backfill), so no season line is preseason any more."""
    from ffapp.odds import completed_weeks

    return league.get("status") == "in_season" and completed_weeks(league) > 0


def preseason_values(store: Store, client, league: dict, season: str, players: dict[str, dict]) -> Values:
    """Each rostered Player's per-game value and its source."""
    scoring = league.get("scoring_settings") or {}
    per_game, source, unmatched = {}, {}, []
    free: dict[str, list[float]] = {pos: [] for pos in ABSENCE}
    if under_way(league):
        # ESPN's and Sleeper's season lines for the season in progress are live (updated, and blank for
        # Players since hurt): only the week-1 Projections stored before kickoff are preseason (1.5.1.1)
        week1 = store.read_projections(season, 1) or {}
        for pid, rec in week1.items():
            pos = rec.get("position")
            value = round(projected_points(rec.get("stats") or {}, scoring), 3)
            if pid in players:
                per_game[pid], source[pid] = value, "week1"
            elif pos in free and value > 0:
                free[pos].append(value)
        unmatched = [pid for pid in players if pid not in per_game]
        return Values(per_game, source, sorted(unmatched), pool_levels(free))
    if season in SLEEPER_SEASON_ONLY:
        rows = {r.get("player_id"): r for r in (client.season_projections(season) or [])}
        for pid, r in rows.items():
            pos = (r.get("player") or {}).get("position")
            if pos in free and pid not in players:
                pts = projected_points(r.get("stats") or {}, scoring)
                if pts > 0:
                    free[pos].append(pts / GAMES)
        week1 = store.read_projections(season, 1) or {}
        for pid, p in players.items():
            stats = (rows.get(pid) or {}).get("stats") or {}
            pts = projected_points(stats, scoring) if any(k in stats for k in ("pass_yd", "rush_yd", "rec_yd", "rec", "fgm", "xpm", "pts_allow")) else 0.0
            if pts > 0:
                per_game[pid], source[pid] = round(pts / GAMES, 3), "sleeper"
            elif week1.get(pid):
                per_game[pid], source[pid] = round(projected_points(week1[pid].get("stats") or {}, scoring), 3), "week1"
            else:
                unmatched.append(pid)
    else:
        from ffapp.espn import EspnClient

        lines = espn_lines(EspnClient(client).season_projections(season), season)
        matched = match_lines(lines, players)
        taken = {id(line) for line in matched.values()}
        for line in lines:
            if id(line) not in taken and line["position"] in free:
                free[line["position"]].append(line_value(line, line["position"], scoring))
        for pid, p in players.items():
            if p["position"] in WEEK1_POSITIONS:
                continue
            if pid in matched:
                per_game[pid], source[pid] = line_value(matched[pid], p["position"], scoring), "espn"
            else:
                unmatched.append(pid)
    # kickers and defences: ESPN scores them with stat ids of their own and serves no season points,
    # so they take their week-1 Projection, scored with the league's scoring (1.5.1.1)
    week1 = store.read_projections(season, 1) or {}
    for pos in WEEK1_POSITIONS:
        free[pos] = []
    for pid, rec in week1.items():
        pos = rec.get("position")
        if pos not in WEEK1_POSITIONS:
            continue
        value = round(projected_points(rec.get("stats") or {}, scoring), 3)
        if pid in players:
            per_game[pid], source[pid] = value, "week1"
        elif value > 0:
            free[pos].append(value)
    for pid, p in players.items():
        if p["position"] in WEEK1_POSITIONS and pid not in per_game:
            unmatched.append(pid)
    return Values(per_game, source, sorted(set(unmatched)), pool_levels(free))


# -- rosters, byes, replacement (1.5.2, 1.5.2.1) -------------------------------------------------------


def preseason_rosters(store: Store, league_key: str, data: SeasonData) -> tuple[dict[int, list[str]], dict[str, dict]]:
    """(roster id -> Player ids, Player id -> {first, last, position, team}): the drafted rosters in
    redraft, the week-1 rosters without taxi Players in dynasty."""
    players: dict[str, dict] = {}
    rosters: dict[int, list[str]] = {int(r["roster_id"]): [] for r in data.rosters}
    if rules_for(data.league)["kind"] == "redraft":
        for p in (store.read_draft(league_key, data.season) or {}).get("picks") or []:
            m = p.get("metadata") or {}
            rosters.setdefault(int(p["roster_id"]), []).append(str(p["player_id"]))
            players[str(p["player_id"])] = {"first": m.get("first_name") or "", "last": m.get("last_name") or "",
                                            "position": m.get("position"), "team": m.get("team")}
        return rosters, players
    taxi = {str(pid) for r in data.rosters for pid in (r.get("taxi") or [])}
    details = latest_player_details(store)
    war_path = store.root / "war" / league_key / f"{data.season}.json"
    season_war = (read_json(war_path) or {}).get("players", {}) if war_path.exists() else {}
    for row in data.matchups.get(min(data.matchups) if data.matchups else 1, []):
        for pid in row.get("players") or []:
            pid = str(pid)
            if pid in taxi:
                continue
            rosters.setdefault(int(row["roster_id"]), []).append(pid)
            d, w = details.get(pid) or {}, season_war.get(pid) or {}
            players[pid] = {"first": d.get("first_name") or "", "last": d.get("last_name") or (w.get("name") or pid),
                            "position": d.get("position") or w.get("position") or ("DEF" if not pid.isdigit() else None),
                            "team": w.get("team") or (pid if not pid.isdigit() else d.get("team"))}
    return rosters, players


def latest_player_details(store: Store) -> dict[str, dict]:
    """Player id -> Sleeper's details from the newest stored week (names and positions rarely change)."""
    base = store.root / "players"
    files = sorted(base.glob("*/week_*.json")) if base.exists() else []
    return (read_json(files[-1]) or {}) if files else {}


def bye_weeks(store: Store, season: str, weeks: list[int]) -> dict[str, set[int]]:
    """NFL team -> its bye weeks among ``weeks``: from the stored NFL schedule's byes when present,
    else the weeks a team played no game in the weekly stats."""
    byes: dict[str, set[int]] = {}
    played: dict[str, set[int]] = {}
    for w in weeks:
        rec = store.read_nfl_week(season, w)
        if rec and rec.get("byes") is not None:
            for t in rec.get("byes") or []:
                byes.setdefault(t, set()).add(w)
            continue
        for row in (store.read_stats(season, w) or {}).values():
            if row.get("team") and (row.get("stats") or {}).get("gp"):
                played.setdefault(row["team"], set()).add(w)
    for team, ws in played.items():
        byes.setdefault(team, set()).update(w for w in weeks if w not in ws and any(w in v for v in played.values()))
    return byes


# -- the absence hook (1.5.3, 1.5.3.1, 1.5.4.1) ----------------------------------------------------------


def eligible(slot: str, position: str) -> bool:
    return position == slot or position in FLEX_ELIGIBLE.get(slot, ())


class Lineups:
    """Builds each week's simulated team scores with absences, for ``simulate``'s ``scores_for_week``
    hook. ``bench`` False puts replacement level in an injured starter's slot instead of a bench
    Player (Wins Saved); byes are covered from the bench either way. The random draws are the same in
    both modes, so the two runs differ only by the bench."""

    def __init__(self, team_ids, rosters, players, values, slots, levels, byes, noise, runs, without_bench: int | None = None):
        """``without_bench``: the index of the one team whose injured starters give way to replacement
        level instead of its bench (Wins Saved); every other team keeps its bench."""
        self.team_ids, self.slots, self.levels, self.noise, self.runs = team_ids, slots, levels, noise, runs
        self.without_bench = without_bench
        self.squads = []
        for rid in team_ids:
            ids = sorted(rosters.get(rid, []), key=lambda pid: -values.get(pid, 0.0))
            self.squads.append([(pid, players[pid]["position"], values.get(pid, 0.0), players[pid].get("team")) for pid in ids
                                if players.get(pid, {}).get("position") in ABSENCE])
        self.byes = byes

    def level(self, slot: str) -> float:
        """Replacement level for a slot; a flex slot takes the lowest of its eligible positions."""
        if slot in FLEX_ELIGIBLE:
            return min(self.levels.get(pos, 0.0) for pos in FLEX_ELIGIBLE[slot])
        return self.levels.get(slot, 0.0)

    def fill_position(self, slot: str) -> str:
        if slot in FLEX_ELIGIBLE:
            return min(FLEX_ELIGIBLE[slot], key=lambda pos: self.levels.get(pos, 0.0))
        return slot

    def _fill(self, squad, out_mask, allowed):
        """(runs, slots) chosen Player index per slot (-1: none), greedy by value."""
        runs = self.runs
        used = np.zeros((runs, len(squad)), dtype=bool)
        chosen = np.full((runs, len(self.slots)), -1)
        for s, slot in enumerate(self.slots):
            filled = np.zeros(runs, dtype=bool)
            for i, (_, pos, val, _) in enumerate(squad):
                if not eligible(slot, pos):
                    continue
                take = ~filled & ~out_mask[:, i] & ~used[:, i] & allowed[:, i, s]
                chosen[take, s] = i
                used[take, i] = True
                filled |= take
        return chosen

    def __call__(self, week: int, rng: np.random.Generator) -> np.ndarray:
        runs = self.runs
        scores = np.zeros((runs, len(self.team_ids)))
        for t, squad in enumerate(self.squads):
            n = len(squad)
            bye = np.array([week in self.byes.get(team or "", set()) for _, _, _, team in squad], dtype=bool)
            hurt = np.column_stack([rng.random(runs) < ABSENCE[pos] for _, pos, _, _ in squad]) if n else np.zeros((runs, 0), bool)
            draws = np.column_stack([val + self.noise.sample(pos, val, rng, runs) if val > 0 else np.zeros(runs)
                                     for _, pos, val, _ in squad]) if n else np.zeros((runs, 0))
            # a Player fills a slot only when worth at least its replacement level: below that, the
            # Manager would pick up a free agent (1.5.3.1)
            worth = np.array([[val >= self.level(slot) for slot in self.slots] for _, _, val, _ in squad], dtype=bool).reshape(n, len(self.slots))
            everyone = np.broadcast_to(worth[None, :, :], (runs, n, len(self.slots)))
            if t != self.without_bench:
                chosen = self._fill(squad, hurt | bye[None, :], everyone)
            else:
                # the week's lineup with byes covered, then injured starters give way to replacement level
                starters = self._fill(squad, np.broadcast_to(bye[None, :], (runs, n)).copy(), everyone)
                chosen = np.where(np.take_along_axis(hurt, np.maximum(starters, 0), axis=1) & (starters >= 0), -1, starters)
            fill = [self.level(slot) + self.noise.sample(self.fill_position(slot), self.level(slot), rng, runs) for slot in self.slots]
            for s, slot in enumerate(self.slots):
                idx = chosen[:, s]
                got = idx >= 0
                col = fill[s].copy()
                if n:
                    col[got] = draws[np.arange(runs)[got], idx[got]]
                scores[:, t] += col
        return scores


# -- the Forecast and grades (1.5.4 to 1.5.5.1) --------------------------------------------------------------


def grade(title: float, playoffs: float, last: float) -> str:
    """The letter in the specified order, then plus or minus near the band's edges."""
    if title >= 0.15:
        return "A+" if title >= 0.25 else "A-" if title < 0.18 else "A"
    if title >= 0.11:
        return "B+"
    if playoffs >= 0.65:
        return "B-" if playoffs < 0.72 else "B"
    if last >= 0.20:
        return "F"
    if playoffs >= 0.35:
        return "C+" if playoffs >= 0.58 else "C-" if playoffs < 0.42 else "C"
    if last >= 0.13:
        return "D-"
    return "D+" if playoffs >= 0.28 else "D"


def preseason_inputs(league_key: str, data: SeasonData) -> SimInputs:
    rules = BracketRules.from_league(data.league)
    team_ids = sorted(int(r["roster_id"]) for r in data.rosters)
    schedule = {}
    for week in regular_season_range(data.league):
        pairs = [(int(a["roster_id"]), int(b["roster_id"])) for a, b in pairings(data.matchups.get(week, []))]
        if pairs:
            schedule[week] = pairs
    return SimInputs(league_key=league_key, season=data.season, completed_weeks=0, rules=rules, team_ids=team_ids,
                     fixed=fixed_records(data, 0), schedule=schedule, starters={rid: {} for rid in team_ids})


def seed_for(league_key: str, season: str) -> int:
    return zlib.crc32(f"{league_key}:{season}:0".encode()) + 1


def make_forecast(store: Store, client, config, league_key: str, season: str, noise, runs: int = RUNS) -> dict:
    """The preseason Forecast record for one league-season (1.5)."""
    data = store.read_season(league_key, season)
    inputs = preseason_inputs(league_key, data)
    rosters, players = preseason_rosters(store, league_key, data)
    values = preseason_values(store, client, data.league, season, players)
    slots = starter_slots(data.league)
    levels = values.levels
    weeks = sorted(set(inputs.schedule) | {inputs.rules.week_for_round(r) for r in range(1, inputs.rules.rounds + 1)})
    byes = bye_weeks(store, season, weeks)
    seed = seed_for(league_key, season)
    def run(without_bench=None):
        hook = Lineups(inputs.team_ids, rosters, players, values.per_game, slots, levels, byes, noise, runs, without_bench)
        return simulate(inputs, noise, runs=runs, seed=seed, scores_for_week=hook)

    base = run()
    # Wins Saved: the same draws with only that team's injured starters at replacement level (1.5.4.1)
    saved = {rid: float(base.wins[:, i].mean() - run(i).wins[:, i].mean()) for i, rid in enumerate(inputs.team_ids)}
    regular = len(inputs.schedule)
    teams = []
    for row in summarize(base):
        title, playoffs, last = round(row["title"], 3), round(row["playoffs"], 3), round(row["last"], 3)
        teams.append({
            "roster_id": row["roster_id"], "title": title, "playoffs": playoffs, "last": last,
            "wins": round(row["proj_wins"], 1), "losses": round(row["proj_losses"], 1),
            "ppg": round(row["proj_points"] / regular, 1) if regular else 0.0,
            "wins_saved": 0.0 + round(saved[row["roster_id"]], 2),
            "grade": grade(row["title"], row["playoffs"], row["last"]),
        })
    teams.sort(key=lambda t: -t["title"])
    return {
        "league_key": league_key, "season": season, "made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": runs, "seed": seed, "absence": ABSENCE, "slots": slots, "replacement": levels,
        "values": dict(sorted(values.per_game.items())), "sources": dict(sorted(values.source.items())),
        "unmatched": [{"id": pid, "name": f"{players[pid]['first']} {players[pid]['last']}".strip(), "position": players[pid]["position"]}
                      for pid in values.unmatched if pid in players],
        "rosters": {str(k): v for k, v in sorted(rosters.items())},
        "teams": teams,
    }


# -- record, timing and export (1.5, 1.5.6 to 1.5.8) --------------------------------------------------------


def record_path(store: Store, league_key: str, season: str):
    return store.root / "preseason" / league_key / f"{season}.json"


def read_record(store: Store, league_key: str, season: str) -> dict | None:
    p = record_path(store, league_key, season)
    return read_json(p) if p.exists() else None


def due_seasons(store: Store, league_key: str) -> list[str]:
    """Seasons with a complete draft and no preseason record yet (1.5.8)."""
    from ffapp.sync import draft_complete

    return [s for s in store.seasons(league_key)
            if draft_complete(store.read_draft(league_key, s)) and not record_path(store, league_key, s).exists()]


def make_due(store: Store, client, config, league_key: str, noise, runs: int = RUNS) -> tuple[list[str], list[str]]:
    """Make and store every due preseason Forecast once; returns (made, warnings)."""
    made, warnings = [], []
    for season in due_seasons(store, league_key):
        try:
            record = make_forecast(store, client, config, league_key, season, noise, runs)
        except Exception as exc:  # noqa: BLE001 - a missing source must not stop the cold run
            log.warning("preseason %s %s failed: %s", league_key, season, exc)
            warnings.append(f"preseason Forecast for {league_key} {season} not made: {exc}")
            continue
        write_json(record_path(store, league_key, season), record)
        made.append(season)
    return made, warnings


def preseason_export(store: Store, config, league_key: str) -> dict:
    """The preseason file for one league: every stored preseason Forecast with Managers and, for finished
    seasons, each team's final place (1.5.6, 1.5.7)."""
    seasons = {}
    for season in store.seasons(league_key):
        rec = read_record(store, league_key, season)
        if not rec:
            continue
        data = store.read_season(league_key, season)
        places, from_brackets = final_places(data)
        final = data.league.get("status") == "complete" and from_brackets
        owners = roster_owners(store, league_key, season)
        # redraft: each team's rank by preseason points per week, its draft strength on paper (1.5.6.1)
        strength = {}
        if rules_for(data.league)["kind"] == "redraft":
            ordered = sorted(rec.get("teams") or [], key=lambda t: -t["ppg"])
            strength = {t["roster_id"]: 1 + sum(o["ppg"] > t["ppg"] for o in ordered) for t in ordered}
        seasons[season] = {
            "made_at": rec.get("made_at"), "final": final,
            "teams": [{**t, "user": owners.get(int(t["roster_id"])), "finish": places.get(int(t["roster_id"])) if final else None,
                       "draft_strength": strength.get(t["roster_id"])}
                      for t in rec.get("teams") or []],
            "unmatched": len(rec.get("unmatched") or []),
        }
    managers = managers_for_league(store, league_key)
    return {
        "league_key": league_key,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest": max(seasons) if seasons else None,
        "managers": {u: {"name": m.name, "team_name": m.team_names.get(m.last), "logo": m.logo, "avatar": m.avatar, "current": m.current}
                     for u, m in managers.items()},
        "seasons": seasons,
    }
