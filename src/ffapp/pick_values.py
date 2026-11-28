"""Rookie pick values: what a dynasty rookie pick has been worth over its Player's first 8 seasons.

- Rookie order: the 2013-2021 classes from the committed rookie order record (built once from DLF
  mock draft ADP, see ``mizelle.py``), the 2022 onward classes from this league's rookie drafts (2022:
  the startup draft's rookies in pick order).
- History WAR: 2013-2021 through the unchanged ``war.build_war``, run on a ``HistoryStore`` rooted at
  ``data/history/`` with the dynasty league's settings (weeks 1-14, yearly start-percentage cut).
- Model: picks grouped Early (1-4), Middle (5-8), Late (9-12) of each round; a group's value is the
  sum over seasons 1-8 after the draft of the mean WAR of its picks that reached that season (a season
  without games counts 0); values forced non-increasing in pick order (pool adjacent violators).
- Unused picks: the group's value when the draft order is known, else the third the current Forecast's
  projected finish gives the original team (next draft), else the round's average group value.

The model is written by ``python -m ffapp pick-values`` from committed records alone and kept as the
record ``data/pick-values/model.json``; cold runs only read it. See ``Calculations.txt`` (Rookie pick values).
"""

from __future__ import annotations

import glob
import json
import random
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ffapp.config import Config
from ffapp.espn import normalise
from ffapp.scoring import PRECOMPUTED_KEYS
from ffapp.store import SeasonData, Store, read_json, write_json

LEAGUE = "dynasty"
HISTORY_SEASONS = tuple(str(y) for y in range(2013, 2022))
HISTORY_WEEKS = tuple(range(1, 15))
ROUNDS = 3
PER_ROUND = 12
SLOTS = ROUNDS * PER_ROUND
WINDOW = 8
THIRDS = ("Early", "Middle", "Late")
GROUPS = tuple((rnd, third) for rnd in range(1, ROUNDS + 1) for third in THIRDS)
BOOT_DRAWS = 2000
BOOT_SEED = 20261128
PLAYED_KEYS = ("gp", "gms_active")
KEEP_FIELDS = ("player_id", "first_name", "last_name", "position", "fantasy_positions", "team")
SOURCES = {
    "dlf": "Dynasty League Football startup mock draft ADP, May to August, collected by mizelle.net",
    "league": "This league's rookie drafts (2022: the startup draft's rookies in pick order)",
}


def model_path(store: Store) -> Path:
    return store.root / "pick-values" / "model.json"


def rookie_order_path(store: Store) -> Path:
    return store.root / "pick-values" / "rookie-order.json"


def read_model(store: Store) -> dict | None:
    p = model_path(store)
    return read_json(p) if p.exists() else None


# -- groups ------------------------------------------------------------------------------------


def group_of(slot: int) -> tuple[int, str]:
    """(round, third) of an overall slot 1..36: 1-4 Early, 5-8 Middle, 9-12 Late of each round."""
    rnd = (slot - 1) // PER_ROUND + 1
    within = (slot - 1) % PER_ROUND + 1
    return rnd, THIRDS[(within - 1) // 4]


def group_key(rnd: int, third: str) -> str:
    return f"{rnd}-{third}"


def non_increasing(values: list[float]) -> list[float]:
    """Pool adjacent violators with equal weights so the sequence never rises."""
    blocks: list[list[float]] = []  # [mean, weight, count]
    for v in values:
        blocks.append([v, 1.0, 1])
        while len(blocks) > 1 and blocks[-1][0] > blocks[-2][0]:
            b = blocks.pop(); a = blocks.pop()
            w = a[1] + b[1]
            blocks.append([(a[0] * a[1] + b[0] * b[1]) / w, w, a[2] + b[2]])
    out: list[float] = []
    for mean, _, count in blocks:
        out += [mean] * count
    return out


# -- history store -----------------------------------------------------------------------------


def keep_stat_keys(league: dict) -> set[str]:
    """The stat keys history records keep: what the league's scoring weights, the precomputed totals that
    mark a played week, WAR's stat totals and the games-played flags."""
    from ffapp.war import STAT_KEYS

    keys = {k for k, v in (league.get("scoring_settings") or {}).items() if v}
    keys |= set(PRECOMPUTED_KEYS) | set(PLAYED_KEYS)
    for ks in STAT_KEYS.values():
        keys |= set(ks)
    return keys


def slim_record(rec: dict, keep: set[str]) -> dict:
    out = {k: rec[k] for k in KEEP_FIELDS if k in rec}
    out["stats"] = {k: v for k, v in (rec.get("stats") or {}).items() if k in keep}
    return out


class HistoryStore(Store):
    """``data/history/``: 2013-2021 stats and ESPN season snapshots, apart from the league seasons, read
    through the base store's dynasty settings so ``war.build_war`` runs unchanged (yearly cut)."""

    def __init__(self, base: Store, league_key: str = LEAGUE):
        super().__init__(base.root / "history")
        self.base = base
        self.league_key = league_key
        self.active_season: str | None = None

    def latest_league(self) -> dict:
        seasons = self.base.seasons(self.league_key)
        if not seasons:
            raise FileNotFoundError(f"no stored {self.league_key} season to take settings from")
        return self.base.read_league(self.league_key, seasons[-1]) or {}

    def seasons(self, league_key: str) -> list[str]:
        return [s for s in HISTORY_SEASONS if self.stats_weeks(s)]

    def read_league(self, league_key: str, season: str) -> dict | None:
        league = json.loads(json.dumps(self.latest_league()))
        league["season"] = str(season)
        league["status"] = "complete"
        league.setdefault("settings", {})["last_scored_leg"] = HISTORY_WEEKS[-1]
        return league

    def read_season(self, league_key: str, season: str) -> SeasonData:
        return SeasonData(league=self.read_league(league_key, season), users=[], rosters=[], matchups={})

    def espn_weeks(self, season: str) -> list[int]:
        return []  # the season-long snapshot only: the yearly cut

    def read_crosswalk(self) -> dict[str, dict] | None:
        """The base crosswalk plus, for the active season, stat-line Players whose name and position it
        lacks: Players retired before the crosswalk was made (history only; league WAR is unchanged)."""
        cw = dict(self.base.read_crosswalk() or {})
        if not self.active_season:
            return cw
        known = {(normalise(r.get("name") or ""), r.get("position")) for r in cw.values()}
        for week in self.stats_weeks(self.active_season):
            for pid, rec in self.read_stats(self.active_season, week).items():
                name = " ".join(x for x in (rec.get("first_name"), rec.get("last_name")) if x)
                key = (normalise(name), rec.get("position"))
                if pid in cw or not name or key in known:
                    continue
                cw[pid] = {"espn_id": None, "name": name, "position": rec.get("position"), "team": rec.get("team")}
                known.add(key)
        return cw


@dataclass
class HistoryFetchReport:
    snapshots: int = 0
    weeks: int = 0
    skipped: int = 0


def history_fetch(client, espn, base: Store, seasons=HISTORY_SEASONS, weeks=HISTORY_WEEKS, progress=None) -> HistoryFetchReport:
    """Sleeper weekly stats (slimmed) and ESPN season snapshots for history seasons into ``data/history/``,
    skipping files already present. Run by hand; never part of a cold run."""
    from ffapp.espn import slim_snapshot, snapshot_payload
    from ffapp.projections import to_record
    from ffapp.stats import fetch_week, played

    hs = HistoryStore(base)
    keep = keep_stat_keys(hs.latest_league())
    report = HistoryFetchReport()
    for season in seasons:
        if hs.read_espn_season(season) is None:
            hs.write_espn_season(season, snapshot_payload(season, None, slim_snapshot(espn.players(season))))
            report.snapshots += 1
        have = set(hs.stats_weeks(season))
        for week in weeks:
            if week in have:
                report.skipped += 1
                continue
            rows = fetch_week(client, season, week)
            records = {str(r["player_id"]): slim_record(to_record(r), keep) for r in rows if played(r)}
            hs.write_stats(season, week, records)
            report.weeks += 1
        if progress:
            progress(season, hs.stats_weeks(season))
    return report


def history_war(base: Store, config: Config, season: str) -> dict:
    """One history season's WAR file payload, in memory (not stored)."""
    from ffapp.war import build_war

    hs = HistoryStore(base)
    hs.active_season = str(season)
    return build_war(hs, config, LEAGUE, str(season))


# -- rookie order -------------------------------------------------------------------------------


def read_rookie_order(base: Store) -> dict:
    p = rookie_order_path(base)
    return read_json(p) if p.exists() else {"classes": {}}


def league_order(base: Store, season: str, league_key: str = LEAGUE) -> list[dict]:
    """This league's rookie draft as slots 1..36 (2022: the startup draft's rookies in pick order)."""
    d = base.read_draft(league_key, season)
    if not d:
        return []
    picks = sorted(d.get("picks") or [], key=lambda p: int(p.get("pick_no") or 0))
    if season == "2022":
        picks = [p for p in picks if str((p.get("metadata") or {}).get("years_exp")) == "0"]
    out = []
    for i, p in enumerate(picks[:SLOTS]):
        m = p.get("metadata") or {}
        out.append({"slot": i + 1, "sleeper_id": str(p["player_id"]) if p.get("player_id") else None,
                    "name": f'{m.get("first_name", "")} {m.get("last_name", "")}'.strip(), "position": m.get("position")})
    return out


def class_orders(base: Store, league_key: str = LEAGUE) -> dict[str, dict]:
    """Every rookie class: ``{season: {"source": "dlf"|"league", "slots": [...]}}``."""
    out: dict[str, dict] = {}
    for season, slots in sorted((read_rookie_order(base).get("classes") or {}).items()):
        out[season] = {"source": "dlf", "slots": slots}
    for season in base.seasons(league_key):
        if season in out:
            continue
        slots = league_order(base, season, league_key)
        if slots:
            out[season] = {"source": "league", "slots": slots}
    return out


# -- WAR by season ------------------------------------------------------------------------------


def last_finished_season(base: Store, league_key: str = LEAGUE) -> str | None:
    done = [s for s in base.seasons(league_key) if str((base.read_league(league_key, s) or {}).get("status")) == "complete"]
    return done[-1] if done else None


def war_by_season(base: Store, config: Config, through: str, league_key: str = LEAGUE) -> dict[str, dict[str, float]]:
    """``{season: {sleeper_id: war}}`` for every history season and every finished league season."""
    from ffapp.war import build_war, read_war

    out: dict[str, dict[str, float]] = {}
    for season in HistoryStore(base).seasons(league_key):
        out[season] = {pid: p["war"] for pid, p in history_war(base, config, season)["players"].items()}
    for season in base.seasons(league_key):
        if season > through:
            continue
        payload = read_war(base, league_key, season) or build_war(base, config, league_key, season)
        out[season] = {pid: p["war"] for pid, p in payload["players"].items()}
    return out


# -- model ---------------------------------------------------------------------------------------


def pick_rows(orders: dict[str, dict], war: dict[str, dict[str, float]], through: str) -> list[dict]:
    """One row per pick: class, slot, Player and his WAR in each season reached (up to 8)."""
    rows = []
    for cls, info in sorted(orders.items()):
        if cls > through:  # no finished season yet
            continue
        for s in info["slots"]:
            pid = s.get("sleeper_id")
            seasons = [str(int(cls) + k) for k in range(WINDOW) if str(int(cls) + k) <= through]
            vals = [round(float(war.get(season, {}).get(pid, 0.0)) if pid else 0.0, 4) for season in seasons]
            rows.append({"class": cls, "slot": int(s["slot"]), "sleeper_id": pid, "name": s.get("name"),
                         "position": s.get("position"), "war": vals, "source": info["source"]})
    return rows


def season_means(rows: list[dict]) -> list[tuple[float, int]]:
    out = []
    for k in range(WINDOW):
        vals = [r["war"][k] for r in rows if len(r["war"]) > k]
        if not vals:
            break
        out.append((statistics.fmean(vals), len(vals)))
    return out


def boot_range(rows: list[dict], draws: int = BOOT_DRAWS, seed: int = BOOT_SEED) -> tuple[float, float]:
    """80% range of the 8-season sum, resampling the picks within each season."""
    rnd = random.Random(seed)
    per_season = [[r["war"][k] for r in rows if len(r["war"]) > k] for k in range(WINDOW)]
    per_season = [v for v in per_season if v]
    sums = sorted(sum(statistics.fmean(rnd.choices(v, k=len(v))) for v in per_season) for _ in range(draws))
    return sums[int(0.1 * draws)], sums[int(0.9 * draws) - 1]


def build_model(orders: dict[str, dict], war: dict[str, dict[str, float]], through: str,
                draws: int = BOOT_DRAWS, seed: int = BOOT_SEED) -> dict:
    rows = pick_rows(orders, war, through)
    groups: dict[str, dict] = {}
    measured = []
    for rnd, third in GROUPS:
        sel = [r for r in rows if group_of(r["slot"]) == (rnd, third)]
        means = season_means(sel)
        total = sum(m for m, _ in means)
        lo, hi = boot_range(sel, draws, seed)
        cum, acc = [], 0.0
        for m, n in means:
            acc += m
            cum.append({"season": len(cum) + 1, "mean": round(m, 4), "total": round(acc, 4), "picks": n})
        groups[group_key(rnd, third)] = {"round": rnd, "third": third, "measured": round(total, 4),
                                         "range": [round(lo, 4), round(hi, 4)], "picks": len(sel),
                                         "picks_full": means[-1][1] if len(means) == WINDOW else 0, "seasons": cum}
        measured.append(total)
    for (rnd, third), value in zip(GROUPS, non_increasing(measured)):
        groups[group_key(rnd, third)]["value"] = round(value, 4)
    rounds = {}
    for rnd in range(1, ROUNDS + 1):
        sel = [r for r in rows if group_of(r["slot"])[0] == rnd]
        rounds[str(rnd)] = {"seasons": [{"season": i + 1, "mean": round(m, 4), "picks": n} for i, (m, n) in enumerate(season_means(sel))],
                            "average_value": round(statistics.fmean(groups[group_key(rnd, t)]["value"] for t in THIRDS), 4)}
    slots = []
    for slot in range(1, SLOTS + 1):
        sel = [r for r in rows if r["slot"] == slot]
        means = season_means(sel)
        best = max((r for r in sel if r["sleeper_id"]), key=lambda r: sum(r["war"]), default=None)
        slots.append({"slot": slot, "label": slot_label(slot),
                      "total3": round(sum(m for m, _ in means[:3]), 4) if len(means) >= 3 else None, "picks3": means[2][1] if len(means) >= 3 else 0,
                      "total8": round(sum(m for m, _ in means), 4) if len(means) == WINDOW else None, "picks8": means[-1][1] if len(means) == WINDOW else 0,
                      "best": {"name": best["name"], "class": best["class"], "war": round(sum(best["war"]), 2)} if best else None})
    flagged = [{"class": r["class"], "slot": r["slot"], "name": r["name"]} for r in rows if not r["sleeper_id"]]
    return {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "through_season": through,
        "classes": {c: {"source": o["source"], "picks": len(o["slots"])} for c, o in sorted(orders.items()) if c <= through},
        "window": WINDOW,
        "groups": groups,
        "rounds": rounds,
        "slots": slots,
        "flagged": flagged,
        "sources": SOURCES,
    }


def slot_label(slot: int) -> str:
    return f"{(slot - 1) // PER_ROUND + 1}.{(slot - 1) % PER_ROUND + 1:02d}"


def write_model(base: Store, config: Config, league_key: str = LEAGUE) -> dict:
    """Build the model from committed records alone and write the record."""
    through = last_finished_season(base, league_key)
    if through is None:
        raise FileNotFoundError(f"no finished {league_key} season stored")
    orders = class_orders(base, league_key)
    if not any(o["source"] == "dlf" for o in orders.values()):
        raise FileNotFoundError("no rookie order record: run `ffapp rookie-adp-fetch` first")
    model = build_model(orders, war_by_season(base, config, through, league_key), through)
    write_json(model_path(base), model)
    return model


# -- unused picks -------------------------------------------------------------------------------


def forecast_thirds(base: Store, league_key: str = LEAGUE) -> dict[int, str]:
    """original roster_id -> third of the round from the latest as-of Forecast's projected finish
    (worst first: ascending playoff, semifinal, final and title shares, then projected wins)."""
    for season in reversed(base.seasons(league_key)):
        files = sorted(glob.glob(str(base.root / "odds" / league_key / season / "asof_*.json")))
        if not files:
            continue
        teams = read_json(Path(files[-1])).get("teams") or []
        order = sorted(teams, key=lambda t: (t.get("playoffs", 0), t.get("semifinal", 0), t.get("final", 0), t.get("title", 0), t.get("proj_wins", 0)))
        n = max(len(order), 1)
        return {int(t["roster_id"]): THIRDS[min(2, i * 3 // n)] for i, t in enumerate(order)}
    return {}


def draft_slot_of(base: Store, season: str, original_roster: int, league_key: str = LEAGUE) -> int | None:
    """The original roster's slot in a season's draft once its order is set, else None."""
    d = base.read_draft(league_key, str(season)) if base.has_season(league_key, str(season)) else None
    order = ((d or {}).get("draft") or {}).get("slot_to_roster_id") or {}
    for slot, rid in order.items():
        if rid is not None and int(rid) == int(original_roster):
            return int(slot)
    return None


def pick_value(base: Store, model: dict | None, season: str, rnd: int, original_roster: int,
               league_key: str = LEAGUE, thirds: dict[int, str] | None = None) -> dict:
    """``{value, group, basis}`` for a pick not yet used; ``value`` None without a model."""
    rnd = int(rnd)
    seasons = base.seasons(league_key)
    current = seasons[-1] if seasons else str(season)
    slot = draft_slot_of(base, season, original_roster, league_key)
    if slot is not None:
        third, basis = THIRDS[(slot - 1) // 4], "slot"
    elif int(season) <= int(current) + 1:
        third = (thirds if thirds is not None else forecast_thirds(base, league_key)).get(int(original_roster))
        basis = "forecast" if third else "round_average"
    else:
        third, basis = None, "round_average"
    if model is None:
        return {"value": None, "group": group_key(rnd, third) if third else None, "basis": basis}
    if third:
        return {"value": model["groups"][group_key(rnd, third)]["value"], "group": group_key(rnd, third), "basis": basis}
    return {"value": model["rounds"][str(rnd)]["average_value"], "group": None, "basis": "round_average"}


# -- export --------------------------------------------------------------------------------------


def pick_values_export(base: Store) -> dict | None:
    """The site's pick values file from the record; None without a model."""
    model = read_model(base)
    if model is None:
        return None
    return {k: model[k] for k in ("built_at", "through_season", "classes", "window", "groups", "rounds", "slots", "sources")}
