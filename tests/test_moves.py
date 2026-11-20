"""Moves from stored transactions (src/ffapp/moves.py): rows, trades, move WAR and waiver overpay.

Transactions follow Sleeper's shape (type, status, leg, status_updated, adds, drops, draft_picks,
waiver_budget, settings.waiver_bid, roster_ids), as stored by the sync."""

from ffapp.managers import windows
from ffapp.moves import league_moves, waiver_overpay
from ffapp.store import Store

OWNERS = {"2026": {1: "me", 2: "them", 3: "third"}}
NAMES = {"10": "Rico Dowdle", "11": "Tyler Bass", "12": "Kenny Coleman", "20": "J. Smith-Njigba", "21": "T. Etienne Jr.", "30": "Never Played"}


def tx(kind, leg, adds=None, drops=None, status="complete", bid=None, run=1000, rosters=None, picks=None, budget=None, tid=None):
    t = {"type": kind, "status": status, "leg": leg, "status_updated": run, "created": run, "adds": adds, "drops": drops,
         "roster_ids": rosters or sorted({*(adds or {}).values(), *(drops or {}).values()}), "draft_picks": picks or [],
         "waiver_budget": budget or [], "settings": {"waiver_bid": bid} if bid is not None else None,
         "transaction_id": tid or f"{kind}-{leg}-{run}-{sorted((adds or {}).items())}"}
    return t


def build(tmp_path, weeks, held, war, season="2026"):
    store = Store(tmp_path)
    store.write_transactions("league", season, weeks)
    (tmp_path / "leagues" / "league" / season / "league.json").write_text("{}", encoding="utf-8")
    timeline = [(season, w) for w in range(1, 15)]
    wins = {uid: windows(timeline, weeks_held, war, carry_over=True) for uid, weeks_held in held.items()}
    return league_moves(store, "league", OWNERS, timeline, wins, war, NAMES, {})


def on(player, weeks, season="2026"):
    return {(season, w): {player} for w in weeks}


def test_overpay_contested_uncontested_tie_and_other_runs():
    rows = [
        tx("waiver", 3, {"10": 1}, bid=41, run=1, tid="won"), tx("waiver", 3, {"10": 2}, bid=12, run=1, status="failed"),
        tx("waiver", 3, {"10": 3}, bid=60, run=9, status="failed"),           # another run: ignored
        tx("waiver", 5, {"11": 1}, bid=12, run=2, tid="alone"),
        tx("waiver", 8, {"12": 1}, bid=22, run=3, tid="tie"), tx("waiver", 8, {"12": 2}, bid=22, run=3, status="failed"),
    ]
    over = waiver_overpay(rows)
    assert over["won"] == {"over": 29, "tied": False, "next": 12}
    assert over["alone"] == {"over": 12, "tied": False, "next": None}
    assert over["tie"] == {"over": 0, "tied": True, "next": 22}


def test_higher_failed_bid_lost_for_another_reason_is_ignored():
    rows = [tx("waiver", 3, {"10": 1}, bid=10, run=1, tid="won"), tx("waiver", 3, {"10": 2}, bid=30, run=1, status="failed")]
    assert waiver_overpay(rows)["won"] == {"over": 10, "tied": False, "next": None}


def test_add_and_drop_in_one_move_and_claimed_by(tmp_path):
    weeks = {2: [tx("free_agent", 2, {"11": 1}, {"12": 1}, run=5)], 4: [tx("waiver", 4, {"12": 2}, bid=3, run=6)]}
    held = {"me": {**on("12", [1]), **on("11", range(2, 15))}, "them": on("12", range(4, 15))}
    war = {("2026", w, "11"): 0.1 for w in range(2, 6)} | {("2026", w, "12"): 0.2 for w in range(2, 6)}
    lm = build(tmp_path, weeks, held, war)
    me = lm.moves["me"]["2026"]
    assert [(r["name"], r["via"], r["week"]) for r in me["added"]] == [("Tyler Bass", "free_agent", 2)]
    dropped = me["dropped"][0]
    assert (dropped["name"], dropped["via"], dropped["by"]) == ("Kenny Coleman", "free_agent", "them")
    assert dropped["war"] == 0.8, "departed window: every week away, on any roster"


def test_trade_with_pick_and_faab_never_repeats_as_rows(tmp_path):
    trade = tx("trade", 6, {"20": 1, "21": 2}, {"20": 2, "21": 1}, rosters=[1, 2],
               picks=[{"season": "2027", "round": 2, "roster_id": 2, "previous_owner_id": 2, "owner_id": 1}],
               budget=[{"sender": 1, "receiver": 2, "amount": 5}])
    held = {"me": {**on("21", range(1, 6)), **on("20", range(6, 15))}, "them": {**on("20", range(1, 6)), **on("21", range(6, 15))}}
    war = {("2026", w, "20"): 0.1 for w in range(6, 15)} | {("2026", w, "21"): 0.05 for w in range(6, 15)}
    lm = build(tmp_path, {6: [trade]}, held, war)
    me = lm.moves["me"]["2026"]
    assert not me["added"] and not me["dropped"]
    side = me["trades"][0]
    assert side["with"] == ["them"] and side["week"] == 6
    assert side["got"] == {"players": [{"pid": "20", "name": "J. Smith-Njigba", "pos": None, "war": 0.9}], "picks": [{"season": "2027", "round": 2}], "faab": 0}
    assert side["gave"] == {"players": [{"pid": "21", "name": "T. Etienne Jr.", "pos": None, "war": 0.45}], "picks": [], "faab": 5}
    assert lm.moves["them"]["2026"]["trades"][0]["got"]["faab"] == 5


def test_no_games_and_pending(tmp_path):
    weeks = {5: [tx("free_agent", 5, {"30": 1}, run=1)], 6: [tx("free_agent", 6, None, {"30": 1}, run=2)],
             12: [tx("free_agent", 12, {"11": 1}, run=3)]}
    held = {"me": {**on("30", [5]), **on("11", range(12, 15))}}
    war = {("2026", w, "10"): 0.1 for w in range(1, 11)}      # scored through week 10; player 30 never had a game
    me = build(tmp_path, weeks, held, war).moves["me"]["2026"]
    never = next(r for r in me["added"] if r["pid"] == "30")
    assert never["war"] is None and "pending" not in never
    later = next(r for r in me["added"] if r["pid"] == "11")
    assert later["war"] is None and later["pending"] is True, "nothing after week 10 is scored yet"


def test_faab_biggest_bid_and_overpaid_total(tmp_path):
    weeks = {3: [tx("waiver", 3, {"10": 1}, bid=41, run=1), tx("waiver", 3, {"10": 2}, bid=12, run=1, status="failed")],
             5: [tx("waiver", 5, {"11": 1}, bid=12, run=2)]}
    lm = build(tmp_path, weeks, {"me": {**on("10", range(3, 15)), **on("11", range(5, 15))}}, {})
    assert lm.faab["me"]["2026"] == {"biggest": {"bid": 41, "pid": "10", "name": "Rico Dowdle", "week": 3}, "overpaid": 41}
    lost = [b for b in lm.bids if not b.won]
    assert [(b.user, b.bid, b.winner, b.winning_bid) for b in lost] == [("them", 12, "me", 41)]


def test_dynasty_trade_window_across_seasons(tmp_path):
    store = Store(tmp_path)
    for season in ("2025", "2026"):
        (tmp_path / "leagues" / "league" / season).mkdir(parents=True)
        (tmp_path / "leagues" / "league" / season / "league.json").write_text("{}", encoding="utf-8")
    store.write_transactions("league", "2025", {10: [tx("trade", 10, {"20": 1}, {"20": 2}, rosters=[1, 2])]})
    store.write_transactions("league", "2026", {1: []})
    timeline = [(s, w) for s in ("2025", "2026") for w in range(1, 15)]
    held = {"me": {(s, w): {"20"} for s, w in timeline if (s, w) >= ("2025", 10)}, "them": {(s, w): {"20"} for s, w in timeline if (s, w) < ("2025", 10)}}
    war = {(s, w, "20"): 0.1 for s, w in timeline}
    wins = {u: windows(timeline, h, war, carry_over=True) for u, h in held.items()}
    owners = {"2025": {1: "me", 2: "them"}, "2026": {1: "me", 2: "them"}}
    lm = league_moves(store, "league", owners, timeline, wins, war, NAMES, {})
    got = lm.moves["me"]["2025"]["trades"][0]["got"]["players"][0]
    assert got["war"] == round(0.1 * (5 + 14), 2), "weeks 10-14 of 2025 and all of 2026"
