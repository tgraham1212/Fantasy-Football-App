"""Moves for the Managers page, from the stored Sleeper transactions.

Each completed transaction becomes moves for the managers involved:

- waiver, free-agent and commissioner moves give one *added* or *dropped* row per player;
- a trade gives one entry per side, listing the players, picks and FAAB each side got and gave
  (players moved in a trade never repeat as added or dropped rows).

A move's WAR is the WAR of the matching move window (``managers.windows``): the added window for
an add or a player got in a trade, the departed window for a drop or a player given away, starting
at the first matchup week at or after the move. A window with no game for the player gives
``war: None`` ("no games"). Picks carry no WAR.

Waiver overpay compares a won claim with the failed claims for the same player in the same waiver
run (same ``status_updated``): overpay = bid - the highest failed bid at or below it; with no such
bid the whole bid counts; an equal bid is a tie won on waiver priority, with no overpay.
See ``Calculations.txt`` (Waiver overpay).
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

from ffapp.store import Store

MOVE_TYPES = {"waiver", "free_agent", "commissioner"}


@dataclass
class Bid:
    """A waiver claim in one run: who bid what on which player, and whether it won."""

    season: str
    week: int
    player: str
    user: str
    bid: int
    won: bool
    run: int                      # status_updated: claims in the same waiver run share it
    winner: str | None = None     # for a lost claim: the manager who won the player in that run
    winning_bid: int | None = None


@dataclass
class LeagueMoves:
    """Everything the export and the news need, per manager."""

    moves: dict[str, dict[str, dict]] = field(default_factory=dict)   # user -> season -> {added, dropped, trades}
    faab: dict[str, dict[str, dict]] = field(default_factory=dict)    # user -> season -> {biggest, overpaid}
    bids: list[Bid] = field(default_factory=list)                     # every won and lost claim in a contested or paid run


def _ordered(weeks: dict[int, list]) -> list[dict]:
    rows = [t for week in sorted(weeks) for t in weeks[week]]
    return sorted(rows, key=lambda t: (int(t.get("leg") or 0), int(t.get("status_updated") or t.get("created") or 0)))


def _bid(t: dict) -> int:
    return int((t.get("settings") or {}).get("waiver_bid") or 0)


def waiver_overpay(transactions: list[dict]) -> dict[str, dict]:
    """transaction_id of each won claim -> {"over": overpay or None, "tied": bool, "next": highest failed bid or None}.

    Failed claims count only when they are for the same player in the same run and bid no more
    than the winner (a higher failed bid lost for another reason, such as roster space)."""
    failed: dict[tuple[str, int], list[int]] = {}
    for t in transactions:
        if t.get("type") == "waiver" and t.get("status") == "failed" and t.get("adds"):
            for pid in t["adds"]:
                failed.setdefault((str(pid), int(t.get("status_updated") or 0)), []).append(_bid(t))
    out: dict[str, dict] = {}
    for t in transactions:
        if t.get("type") != "waiver" or t.get("status") != "complete" or not t.get("adds"):
            continue
        bid = _bid(t)
        rivals = [b for pid in t["adds"] for b in failed.get((str(pid), int(t.get("status_updated") or 0)), []) if b <= bid]
        nxt = max(rivals) if rivals else None
        if nxt is not None and nxt == bid:
            out[str(t["transaction_id"])] = {"over": 0, "tied": True, "next": nxt}
        else:
            out[str(t["transaction_id"])] = {"over": bid - (nxt or 0), "tied": False, "next": nxt}
    return out


def _window_index(wins) -> dict[tuple[str, str], list]:
    """(player, kind) -> windows sorted by start."""
    out: dict[tuple[str, str], list] = {}
    for w in wins:
        out.setdefault((w.player, w.kind), []).append(w)
    for v in out.values():
        v.sort(key=lambda w: w.start)
    return out


class _Timeline:
    """Positions of stored matchup weeks, to find the first week at or after a move."""

    def __init__(self, timeline: list[tuple[str, int]]):
        self.weeks = [(s, int(w)) for s, w in timeline]

    def at_or_after(self, season: str, week: int) -> int:
        return bisect_left(self.weeks, (season, int(week)))


def _move_war(index, tl: _Timeline, war: dict, scored: int, pid: str, kind: str, start: int, stop: int) -> dict:
    """``{"war": x}`` for the player's ``kind`` window that starts in [start, stop) on the timeline;
    ``{"war": None}`` ("no games") when there is none or it holds no game for him; and
    ``{"war": None, "pending": True}`` ("no games yet") when nothing after the move has been scored
    yet (``scored`` is the timeline position of the last week with WAR)."""
    for w in index.get((pid, kind), []):
        pos = tl.at_or_after(*w.start)
        if start <= pos < stop:
            if any((s, wk, pid) in war for s, wk in w.weeks):
                return {"war": round(w.war, 2)}
            return {"war": None, "pending": True} if pos > scored else {"war": None}
        if pos >= stop:
            break
    return {"war": None, "pending": True} if start > scored else {"war": None}


def league_moves(store: Store, league_key: str, owners_by_season: dict[str, dict[int, str]], timeline: list[tuple[str, int]],
                 wins_by_user: dict[str, list], war: dict, names: dict[str, str], positions: dict[str, str]) -> LeagueMoves:
    """Moves, FAAB extras and waiver bids for every manager of one league."""
    out = LeagueMoves()
    tl = _Timeline(timeline)
    index = {uid: _window_index(w) for uid, w in wins_by_user.items()}
    end = len(tl.weeks)
    scored_weeks = {(s, wk) for s, wk, _ in war}
    scored = max((tl.at_or_after(s, wk) for s, wk in scored_weeks), default=-1)

    # pass 1: every completed move as (season, week, user, player, kind), to bound each window
    events: dict[tuple[str, str], list[int]] = {}   # (user, player) -> timeline positions of moves involving him
    seasons = store.seasons(league_key)
    parsed: list[tuple[str, dict]] = []
    for season in seasons:
        rows = _ordered(store.read_transactions(league_key, season))
        parsed.append((season, rows))
        owners = owners_by_season.get(season, {})
        for t in rows:
            if t.get("status") != "complete":
                continue
            pos = tl.at_or_after(season, int(t.get("leg") or 1))
            for pid, rid in list((t.get("adds") or {}).items()) + list((t.get("drops") or {}).items()):
                uid = owners.get(int(rid))
                if uid:
                    events.setdefault((uid, str(pid)), []).append(pos)

    def stop_after(uid: str, pid: str, pos: int) -> int:
        later = [p for p in events.get((uid, pid), []) if p > pos]
        return min(later) if later else end

    def player(pid: str) -> dict:
        return {"pid": pid, "name": names.get(pid, pid), "pos": positions.get(pid)}

    for season, rows in parsed:
        owners = owners_by_season.get(season, {})
        over = waiver_overpay(rows)
        # the next add of each player by anyone, for "claimed by"
        adds_by_player: dict[str, list[tuple[int, str]]] = {}
        for t in rows:
            if t.get("status") == "complete":
                pos = tl.at_or_after(season, int(t.get("leg") or 1))
                for pid, rid in (t.get("adds") or {}).items():
                    if owners.get(int(rid)):
                        adds_by_player.setdefault(str(pid), []).append((pos, owners[int(rid)]))

        for t in rows:
            kind, status = t.get("type"), t.get("status")
            week = int(t.get("leg") or 1)
            pos = tl.at_or_after(season, week)
            if kind == "waiver":
                _collect_bids(out, t, season, week, owners, rows)
            if status != "complete":
                continue
            if kind in MOVE_TYPES:
                for pid, rid in (t.get("adds") or {}).items():
                    uid = owners.get(int(rid))
                    if not uid:
                        continue
                    pid = str(pid)
                    row = {**player(pid), "week": week, "via": kind,
                           **_move_war(index.get(uid, {}), tl, war, scored, pid, "added", pos, max(stop_after(uid, pid, pos), pos + 1))}
                    if kind == "waiver":
                        row["bid"] = _bid(t)
                        info = over.get(str(t["transaction_id"]), {})
                        row["over"] = info.get("over", 0)
                        if info.get("tied"):
                            row["tied"] = True
                        if info.get("next") is not None:
                            row["next"] = info["next"]   # absent: no other bids
                    _bucket(out, uid, season)["added"].append(row)
                for pid, rid in (t.get("drops") or {}).items():
                    uid = owners.get(int(rid))
                    if not uid:
                        continue
                    pid = str(pid)
                    back = stop_after(uid, pid, pos)
                    claimed = next((u for p, u in adds_by_player.get(pid, []) if p >= pos and u != uid and p < back), None)
                    row = {**player(pid), "week": week, "via": kind,
                           **_move_war(index.get(uid, {}), tl, war, scored, pid, "departed", pos, max(back, pos + 1))}
                    if claimed:
                        row["by"] = claimed
                    _bucket(out, uid, season)["dropped"].append(row)
            elif kind == "trade":
                for rid in t.get("roster_ids") or []:
                    uid = owners.get(int(rid))
                    if not uid:
                        continue
                    got = [str(p) for p, r in (t.get("adds") or {}).items() if int(r) == int(rid)]
                    gave = [str(p) for p, r in (t.get("drops") or {}).items() if int(r) == int(rid)]
                    picks = t.get("draft_picks") or []
                    budget = t.get("waiver_budget") or []
                    side = {
                        "week": week,
                        "with": [owners[int(r)] for r in t.get("roster_ids") or [] if int(r) != int(rid) and owners.get(int(r))],
                        "got": {"players": [{**player(p), **_move_war(index.get(uid, {}), tl, war, scored, p, "added", pos, max(stop_after(uid, p, pos), pos + 1))} for p in got],
                                "picks": [{"season": str(k["season"]), "round": int(k["round"])} for k in picks if int(k.get("owner_id") or 0) == int(rid)],
                                "faab": sum(int(b.get("amount") or 0) for b in budget if int(b.get("receiver") or 0) == int(rid))},
                        "gave": {"players": [{**player(p), **_move_war(index.get(uid, {}), tl, war, scored, p, "departed", pos, max(stop_after(uid, p, pos), pos + 1))} for p in gave],
                                 "picks": [{"season": str(k["season"]), "round": int(k["round"])} for k in picks if int(k.get("previous_owner_id") or 0) == int(rid)],
                                 "faab": sum(int(b.get("amount") or 0) for b in budget if int(b.get("sender") or 0) == int(rid))},
                    }
                    _bucket(out, uid, season)["trades"].append(side)

        # FAAB extras: the season's biggest winning bid and the overpaid total
        for uid, by_season in out.moves.items():
            bucket = by_season.get(season)
            if not bucket:
                continue
            won = [r for r in bucket["added"] if r["via"] == "waiver"]
            if won:
                big = max(won, key=lambda r: (r["bid"], -r["week"]))
                out.faab.setdefault(uid, {})[season] = {
                    "biggest": {"bid": big["bid"], "pid": big["pid"], "name": big["name"], "week": big["week"]} if big["bid"] > 0 else None,
                    "overpaid": sum(r.get("over") or 0 for r in won),
                }
    return out


def _bucket(out: LeagueMoves, uid: str, season: str) -> dict:
    return out.moves.setdefault(uid, {}).setdefault(season, {"added": [], "dropped": [], "trades": []})


def _collect_bids(out: LeagueMoves, t: dict, season: str, week: int, owners: dict[int, str], rows: list[dict]) -> None:
    """Keep each waiver claim with its run's winner, for the big-bid and outbid stories."""
    if not t.get("adds"):
        return
    pid, rid = next(iter(t["adds"].items()))
    uid = owners.get(int(rid))
    if not uid:
        return
    run = int(t.get("status_updated") or 0)
    if t.get("status") == "complete":
        out.bids.append(Bid(season, week, str(pid), uid, _bid(t), True, run))
    elif t.get("status") == "failed":
        winner = next((w for w in rows if w.get("type") == "waiver" and w.get("status") == "complete" and w.get("adds")
                       and str(pid) in {str(p) for p in w["adds"]} and int(w.get("status_updated") or 0) == run), None)
        if winner is None or _bid(winner) < _bid(t):
            return   # failed for another reason (roster space, player gone): not outbid
        wuid = owners.get(int(next(iter(winner["adds"].values()))))
        out.bids.append(Bid(season, week, str(pid), uid, _bid(t), False, run, winner=wuid, winning_bid=_bid(winner)))
