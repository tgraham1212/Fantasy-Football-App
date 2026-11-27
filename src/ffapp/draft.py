"""Draft grades for the League sub-tab's Draft tab: every stored draft of a league, each pick graded
on draft day against ADP (Steal/Reach, in picks) and in retrospect against the WAR its draft slot
usually produces in this league (Hit/Bust, in WAR), with Unlucky picks and the Managers summaries,
exported as one file per league (``site/data/<league>/draft.json``); the page only renders. See
Calculations.txt section 25.

- The draft is the one named in each season's league settings (the sync stores no other), so the
  dynasty league's 2022 startup draft, which only moved rosters over from Yahoo, is never graded.
- Redraft: ADP difference = pick number - half-PPR ADP; a steal at +12 (a full round), a reach at -12.
  Rookie draft (dynasty league): pick number - ADP rank among that draft's Players by dynasty
  half-PPR ADP; steal / reach at +/-6 (half a round). A running back or wide receiver with one of
  the two lowest ADPs at his position still available is never a reach. Keepers and Players
  without an ADP have no Steal/Reach grade.
- Grading window: the draft season (redraft) or the draft season and the next (rookie draft), WAR
  on every roster. Slot WAR = mean window WAR of picks within 6 (redraft) or 3 (rookie) slots across
  the league's drafts whose window is complete, keepers left out; while a window is in progress it
  is scaled by the share of the window's regular-season weeks played. Hit at +0.75 / +1.0 WAR above
  slot WAR, bust at as much below.
- Unlucky: missed more than half of his NFL team's regular-season games in the window so far while
  listed IR, PUP or Out (nflverse injury reports, ``ffapp.injury_reports``);
  an unlucky pick is graded Unlucky in place of Bust (a hit stays a hit).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean

from ffapp.managers import managers_for_league, roster_owners
from ffapp.store import Store

log = logging.getLogger(__name__)

DYNASTY_LEAGUE_TYPE = 2  # Sleeper settings.type: 0 redraft, 1 keeper, 2 dynasty (rookie drafts)
REDRAFT = {"kind": "redraft", "adp": "adp_half_ppr", "steal": 12, "hit": 0.75, "slots": 6, "window": 1}
ROOKIE = {"kind": "rookie", "adp": "adp_dynasty_half_ppr", "steal": 6, "hit": 1.0, "slots": 3, "window": 2}
EXEMPT_POSITIONS = ("RB", "WR")
EXEMPT_DEPTH = 2  # the two lowest ADPs left at the position


def rules_for(league: dict) -> dict:
    return ROOKIE if int((league.get("settings") or {}).get("type") or 0) == DYNASTY_LEAGUE_TYPE else REDRAFT


def regular_weeks(league: dict) -> int:
    settings = league.get("settings") or {}
    return int(settings.get("playoff_week_start") or 15) - int(settings.get("start_week") or 1)


# -- per-season facts: WAR, weeks played, games -------------------------------------------------


@dataclass
class SeasonFacts:
    complete: bool
    weeks: int  # regular-season weeks in the season
    played: int  # regular-season weeks played so far
    war: dict[str, float] = field(default_factory=dict)  # player id -> WAR
    team_weeks: dict[str, set[int]] = field(default_factory=dict)  # NFL team -> regular weeks it played
    player_weeks: dict[str, dict[int, str]] = field(default_factory=dict)  # player id -> week -> team (row present)
    games: dict[str, int] = field(default_factory=dict)  # player id -> regular-season games played
    played_weeks: dict[str, set[int]] = field(default_factory=dict)  # player id -> weeks with a game played
    injured: dict[str, set[int]] = field(default_factory=dict)  # player id -> weeks listed IR, PUP or Out (nflverse)


def season_facts(store: Store, league_key: str, season: str) -> SeasonFacts | None:
    league = store.read_league(league_key, season)
    if league is None:
        return None
    weeks = regular_weeks(league)
    war_path = store.root / "war" / league_key / f"{season}.json"
    war_file = {}
    if war_path.exists():
        import json
        war_file = json.loads(war_path.read_text(encoding="utf-8"))
    complete = league.get("status") == "complete"
    played = weeks if complete else min(weeks, int(war_file.get("through_week") or 0))
    facts = SeasonFacts(complete=complete, weeks=weeks, played=played,
                        war={pid: float(p.get("war") or 0.0) for pid, p in (war_file.get("players") or {}).items()})
    for week in range(1, played + 1):
        for pid, row in (store.read_stats(season, week) or {}).items():
            team = row.get("team")
            if not team:
                continue
            facts.player_weeks.setdefault(pid, {})[week] = team
            if (row.get("stats") or {}).get("gp"):
                facts.team_weeks.setdefault(team, set()).add(week)
                facts.games[pid] = facts.games.get(pid, 0) + 1
                facts.played_weeks.setdefault(pid, set()).add(week)
    from ffapp.injury_reports import read_reports
    for week, rows in read_reports(store, season).items():
        if int(week) <= played:
            for pid in rows:
                facts.injured.setdefault(pid, set()).add(int(week))
    return facts


def team_games(facts: SeasonFacts, pid: str, fallback_team: str | None) -> tuple[int, int]:
    """(games his NFL team played so far, those he missed while listed IR, PUP or Out), his team
    each week taken from his nearest stats row (earlier first), else ``fallback_team``."""
    rows = facts.player_weeks.get(pid, {})
    played, injured = facts.played_weeks.get(pid, set()), facts.injured.get(pid, set())
    total = hurt = 0
    for week in range(1, facts.played + 1):
        team = rows.get(week)
        if team is None:
            earlier = [w for w in rows if w < week]
            later = [w for w in rows if w > week]
            team = rows[max(earlier)] if earlier else rows[min(later)] if later else fallback_team
        if team and week in facts.team_weeks.get(team, set()):
            total += 1
            hurt += week not in played and week in injured
    return total, hurt


# -- grades ---------------------------------------------------------------------------------------


def adp_differences(picks: list[dict], adp: dict[str, dict], rules: dict) -> dict[str, dict]:
    """Player id -> {adp, adp_rank, adp_pos_rank, adp_diff, steal_reach} for every pick (4.11.1).

    ``adp_diff`` is None for keepers and Players without an ADP; ``steal_reach`` is "steal", "reach"
    or None. Ranks are among the draft's Players with an ADP."""
    key = rules["adp"]
    value = {p["player_id"]: (adp.get(p["player_id"]) or {}).get(key) for p in picks}
    ranked = sorted((p for p in picks if value[p["player_id"]] is not None), key=lambda p: (value[p["player_id"]], p["pick_no"]))
    rank, pos_rank, seen = {}, {}, {}
    for i, p in enumerate(ranked):
        pos = position(p)
        seen[pos] = seen.get(pos, 0) + 1
        rank[p["player_id"]], pos_rank[p["player_id"]] = i + 1, seen[pos]

    # the pool still available as each pick is made: every Player with an ADP (redraft) or the draft's
    # Players (rookie draft), less earlier picks and every keeper
    if rules["kind"] == "redraft":
        pool = {pid: (rec.get("position"), rec[key]) for pid, rec in adp.items() if rec.get(key) is not None}
    else:
        pool = {p["player_id"]: (position(p), value[p["player_id"]]) for p in picks if value[p["player_id"]] is not None}
    taken = {p["player_id"] for p in picks if p.get("is_keeper")}

    out: dict[str, dict] = {}
    for p in sorted(picks, key=lambda x: x["pick_no"]):
        pid = p["player_id"]
        entry = {"adp": value[pid], "adp_rank": rank.get(pid), "adp_pos_rank": pos_rank.get(pid), "adp_diff": None, "steal_reach": None}
        if not p.get("is_keeper") and value[pid] is not None:
            expected = value[pid] if rules["kind"] == "redraft" else rank[pid]
            diff = round(p["pick_no"] - expected, 1)
            entry["adp_diff"] = diff
            if diff >= rules["steal"]:
                entry["steal_reach"] = "steal"
            elif diff <= -rules["steal"] and not best_left(pid, position(p), value[pid], pool, taken):
                entry["steal_reach"] = "reach"
        out[pid] = entry
        taken.add(pid)
    return out


def best_left(pid: str, pos: str, own: float, pool: dict[str, tuple], taken: set[str]) -> bool:
    """True when the Player is an RB or WR with one of the two lowest ADPs at his position still available (4.11.1.2)."""
    if pos not in EXEMPT_POSITIONS:
        return False
    left = sorted(a for q, (qp, a) in pool.items() if qp == pos and q not in taken and q != pid)
    return sum(a < own for a in left) < EXEMPT_DEPTH


def position(pick: dict) -> str:
    return str((pick.get("metadata") or {}).get("position") or "")


@dataclass
class Window:
    war: float
    games: int
    possible: int
    share: float  # share of the window's regular-season weeks played
    complete: bool
    injured: int = 0  # team games missed while listed IR, PUP or Out


def window_for(pick: dict, season: str, rules: dict, facts: dict[str, SeasonFacts | None]) -> Window:
    """WAR on every roster, games and team games over the grading window (4.11.2.1)."""
    pid = pick["player_id"]
    team = (pick.get("metadata") or {}).get("team")
    war = games = possible = played = weeks = injured = 0
    complete = True
    for k in range(rules["window"]):
        f = facts.get(str(int(season) + k))
        if f is None:
            complete = False
            weeks += regular_weeks_guess(facts, season)
            continue
        war += f.war.get(pid, 0.0)
        games += f.games.get(pid, 0)
        team_total, hurt = team_games(f, pid, team)
        possible += team_total
        injured += hurt
        played += f.played
        weeks += f.weeks
        complete = complete and f.complete
    return Window(round(war, 4), games, possible, (played / weeks) if weeks else 0.0, complete, injured)


def regular_weeks_guess(facts: dict[str, SeasonFacts | None], season: str) -> int:
    f = facts.get(season)
    return f.weeks if f else 14


def slot_war(pick_no: int, history: list[tuple[int, float]], slots: int) -> float | None:
    """Mean window WAR of picks within ``slots`` of ``pick_no`` in drafts with a complete window (4.11.2.2)."""
    near = [w for n, w in history if abs(n - pick_no) <= slots]
    return mean(near) if near else None


def grade_draft(draft: dict, season: str, rules: dict, adp: dict, facts: dict, history: list[tuple[int, float]],
                owners: dict[int, str], slot_owner: dict[int, str]) -> list[dict]:
    """Every pick of one draft with both grades, ranks and games."""
    picks = sorted(draft.get("picks") or [], key=lambda p: p["pick_no"])
    teams = int(((draft.get("draft") or {}).get("settings") or {}).get("teams") or 12)
    diffs = adp_differences(picks, adp, rules)
    windows = {p["player_id"]: window_for(p, season, rules, facts) for p in picks}
    by_war = sorted(picks, key=lambda p: (-windows[p["player_id"]].war, p["pick_no"]))
    war_rank, war_pos_rank, seen = {}, {}, {}
    for i, p in enumerate(by_war):
        pos = position(p)
        seen[pos] = seen.get(pos, 0) + 1
        war_rank[p["player_id"]], war_pos_rank[p["player_id"]] = i + 1, seen[pos]

    out = []
    for p in picks:
        pid, meta, w = p["player_id"], p.get("metadata") or {}, windows[p["player_id"]]
        base = slot_war(p["pick_no"], history, rules["slots"]) if not p.get("is_keeper") else None
        scaled = None if base is None else round(base * (1.0 if w.complete else w.share), 2)
        gap = None if scaled is None else round(w.war - scaled, 2)
        unlucky = w.possible > 0 and w.injured > w.possible / 2   # missed over half his team's games injured (4.11.2.3)
        hit_bust = None
        if gap is not None and gap >= rules["hit"]:
            hit_bust = "hit"            # a hit stays a hit, games missed or not
        elif unlucky:
            hit_bust = "unlucky"        # in place of a bust (4.11.2.3.1)
        elif gap is not None and gap <= -rules["hit"]:
            hit_bust = "bust"
        user = owners.get(int(p["roster_id"])) if p.get("roster_id") is not None else None
        slot_user = slot_owner.get(int(p["draft_slot"]), user)
        out.append({
            "no": p["pick_no"], "round": p["round"], "slot": p["draft_slot"], "label": pick_label(p["round"], p["pick_no"], teams),
            "user": user, "slot_user": slot_user, "keeper": bool(p.get("is_keeper")),
            "player": {"id": pid, "first": meta.get("first_name") or "", "last": meta.get("last_name") or "",
                       "pos": position(p), "team": meta.get("team") or "FA", "exp": int(meta.get("years_exp") or 0)},
            **diffs[pid],
            "war": round(w.war, 2), "war_rank": war_rank[pid], "war_pos_rank": war_pos_rank[pid],
            "slot_war": scaled, "war_gap": gap, "hit_bust": hit_bust, "games": w.games, "games_possible": w.possible, "games_injured": w.injured,
        })
    return out


def pick_label(round_no: int, pick_no: int, teams: int) -> str:
    """"Round.pick within the round" ("2.01" is the round's first pick, which in a snake draft is
    the last slot's); the board places picks by draft slot, the label by order of selection."""
    return f"{round_no}.{(int(pick_no) - 1) % teams + 1:02d}"


def summary(picks: list[dict], seasons: dict[int, str] | None = None) -> list[dict]:
    """Per Manager: picks, mean ADP difference (0.1), mean WAR above slot WAR (0.01), total WAR, best
    pick and unlucky picks, each pick counted for the Manager who made it (4.11.4, 4.11.4.1)."""
    rows: dict[str, list[dict]] = {}
    for p in picks:
        if p["user"]:
            rows.setdefault(p["user"], []).append(p)
    out = []
    for user, mine in rows.items():
        diffs = [p["adp_diff"] for p in mine if p["adp_diff"] is not None]
        gaps = [p for p in mine if p["war_gap"] is not None]
        best = max(gaps, key=lambda p: p["war_gap"]) if gaps else None
        out.append({
            "user": user, "picks": len(mine),
            "adp_diff": round(mean(diffs), 1) if diffs else None,
            "war_gap": round(mean(p["war_gap"] for p in gaps), 2) if gaps else None,
            "war": round(sum(p["war"] for p in mine), 2),
            "best": None if best is None else {"label": best["label"], "season": best.get("season"), "player": best["player"],
                                               "war_gap": best["war_gap"]},
            "unlucky": sum(1 for p in mine if p["hit_bust"] == "unlucky"),
        })
    out.sort(key=lambda r: (-(r["war_gap"] if r["war_gap"] is not None else -99), r["user"]))
    return out


# -- keepers (redraft) -------------------------------------------------------------------------------

KEEPERS_FROM = "2025"  # the league's current keeper rules; Sleeper's 2022-2024 flags followed earlier ones


def configured_keepers(config, league_key: str, season: str) -> set[str]:
    """Sleeper ids kept in ``season`` per the league configuration (4.11.5); none before 2025."""
    league = (getattr(config, "leagues", None) or {}).get(league_key)
    if league is None or season < KEEPERS_FROM:
        return set()
    return set(getattr(league, "keepers", {}).get(season, ()))


def read_draft_with_keepers(store: Store, config, league_key: str, season: str) -> dict | None:
    """The stored draft with the configured keepers flagged ``is_keeper`` like Sleeper's own (4.11.5)."""
    stored = store.read_draft(league_key, season)
    kept = configured_keepers(config, league_key, season)
    if stored and kept:
        stored = {**stored, "picks": [{**p, "is_keeper": True} if p.get("player_id") in kept else p for p in stored.get("picks") or []]}
    return stored


def kept_in(store: Store, config, league_key: str, season: str) -> set[str]:
    stored = read_draft_with_keepers(store, config, league_key, season)
    return {p["player_id"] for p in (stored or {}).get("picks") or [] if p.get("is_keeper")}


def moved_off(store: Store, league_key: str, season: str) -> set[tuple[str, int]]:
    """(player id, roster id) for every completed move of a Player off a roster in the season: drops,
    trades away and commissioner moves, through the championship week."""
    out = set()
    for rows in store.read_transactions(league_key, season).values():
        for tx in rows or []:
            if tx.get("status") != "complete":
                continue
            for pid, rid in (tx.get("drops") or {}).items():
                if rid is not None:
                    out.add((str(pid), int(rid)))
    return out


def keeper_eligible(store: Store, config, league_key: str) -> dict | None:
    """Keeper eligibility for the season after the latest redraft draft (4.11.6 to 4.11.6.3): Players
    drafted by a Manager and kept on that roster through the championship week, priced one round
    higher (round 1 not eligible), a Player kept this season at a 1st unless also kept the season
    before. While the season is in progress the list runs through the latest week and is not final."""
    seasons = [s for s in store.seasons(league_key) if store.read_draft(league_key, s)]
    if not seasons:
        return None
    season = seasons[-1]
    league = store.read_league(league_key, season) or {}
    if rules_for(league)["kind"] != "redraft":
        return None
    picks = (read_draft_with_keepers(store, config, league_key, season) or {}).get("picks") or []
    before = kept_in(store, config, league_key, str(int(season) - 1)) if str(int(season) - 1) >= KEEPERS_FROM else set()
    off = moved_off(store, league_key, season)
    on_roster = {(str(pid), int(r["roster_id"])) for r in store.read_rosters(league_key, season) for pid in (r.get("players") or [])}
    owners = roster_owners(store, league_key, season)
    rows: dict[str, list[dict]] = {u: [] for u in owners.values() if u}
    for p in picks:
        pid, rid = str(p["player_id"]), int(p["roster_id"])
        if (pid, rid) in off or (pid, rid) not in on_roster:
            continue
        if p.get("is_keeper"):
            if pid in before:
                continue                       # kept two seasons running: not eligible
            price, second = 1, True
        elif int(p["round"]) == 1:
            continue                           # a first-round pick can't be kept
        else:
            price, second = int(p["round"]) - 1, False
        meta = p.get("metadata") or {}
        user = owners.get(rid)
        if user:
            rows.setdefault(user, []).append({
                "player": {"id": pid, "first": meta.get("first_name") or "", "last": meta.get("last_name") or "",
                           "pos": position(p), "team": meta.get("team") or "FA"},
                "drafted_round": int(p["round"]), "price_round": price, "second_year": second})
    return {
        "for_season": str(int(season) + 1), "season": season, "final": league.get("status") == "complete",
        "rows": [{"user": u, "players": sorted(ps, key=lambda x: (x["price_round"], x["player"]["last"]))} for u, ps in rows.items()],
    }


def keeper_eligible_ids(store: Store, config, league_key: str) -> set[str]:
    """Sleeper ids keeper eligible for next season (the Managers page's "KE" badge, 4.4.6.5)."""
    ke = keeper_eligible(store, config, league_key)
    return {pl["player"]["id"] for row in (ke or {}).get("rows", []) for pl in row["players"]}


def draft_export(store: Store, config, league_key: str) -> dict:
    """The draft file for one league: every stored draft, graded, with both Managers summaries (4.11)."""
    seasons = [s for s in store.seasons(league_key) if store.read_draft(league_key, s)]
    facts: dict[str, SeasonFacts | None] = {s: season_facts(store, league_key, s) for s in store.seasons(league_key)}
    rules = rules_for(store.read_league(league_key, seasons[-1])) if seasons else REDRAFT

    # slot-WAR history: non-keeper picks of drafts whose window is complete
    windows_by_season: dict[str, list[tuple[dict, Window]]] = {}
    history: list[tuple[int, float]] = []
    for s in seasons:
        picks = read_draft_with_keepers(store, config, league_key, s).get("picks") or []
        ws = [(p, window_for(p, s, rules, facts)) for p in picks]
        windows_by_season[s] = ws
        if ws and all(w.complete for _, w in ws):
            history += [(p["pick_no"], w.war) for p, w in ws if not p.get("is_keeper")]

    out_seasons, everything = {}, []
    for s in seasons:
        stored = read_draft_with_keepers(store, config, league_key, s)
        owners = roster_owners(store, league_key, s)
        slot_roster = {int(k): int(v) for k, v in ((stored.get("draft") or {}).get("slot_to_roster_id") or {}).items() if v is not None}
        slot_owner = {slot: owners.get(rid) for slot, rid in slot_roster.items()}
        picks = grade_draft(stored, s, rules, store.read_adp(s), facts, history, owners, slot_owner)
        for p in picks:
            p["season"] = s
        everything += picks
        d = stored.get("draft") or {}
        teams = int((d.get("settings") or {}).get("teams") or len(slot_owner) or 12)
        out_seasons[s] = {
            "type": d.get("type"), "status": d.get("status"), "rounds": int((d.get("settings") or {}).get("rounds") or 0),
            "slots": [{"slot": n, "user": slot_owner.get(n)} for n in range(1, teams + 1)],
            "window_complete": all(w.complete for _, w in windows_by_season[s]) if windows_by_season[s] else False,
            "has_adp": store.has_adp(s),
            "picks": picks, "summary": summary(picks),
        }
    ke = keeper_eligible(store, config, league_key)
    if ke:
        out_seasons[ke["season"]]["keepers"] = ke
    managers = managers_for_league(store, league_key)
    return {
        "league_key": league_key,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latest": seasons[-1] if seasons else None,
        "rules": {k: rules[k] for k in ("kind", "steal", "hit", "slots", "window")},
        "managers": {u: {"name": m.name, "team_name": m.team_names.get(m.last), "logo": m.logo, "avatar": m.avatar, "current": m.current}
                     for u, m in managers.items()},
        "seasons": out_seasons,
        "all_drafts": summary(everything),
    }
