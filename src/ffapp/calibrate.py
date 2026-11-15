"""Replay completed seasons through the simulation and score the odds against what happened.

Three levels, from most to least data:

* score  - each team's simulated score for the next week vs the points it scored
           (is the noise the right width?)
* game   - the simulated chance of winning the next matchup vs the real result
* season - the published chances (playoffs, bye, title, ...) vs the real outcome,
           compared with a naive standings baseline

Plus the lineup gap: what the best projected lineup gives up to the lineup managers
actually started. Pure metric functions take arrays and dicts; the driver walks the
stored seasons and writes ``data/calibration/``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ffapp.bracket import BracketRules
from ffapp.config import Config
from ffapp.drift import DIAGNOSTIC_HORIZONS, diagnostic, estimate_for_league
from ffapp.league import resolve_settings, starter_slots
from ffapp.lineup import lineup_points
from ffapp.noise import build_pools
from ffapp.odds import fixed_records, lineup_from_projections, regular_season_range, simulate_as_of
from ffapp.scoring import record_points
from ffapp.simulate import SimInputs, SimResult
from ffapp.standings import TeamRecord, pairings, regular_season_records, seeds
from ffapp.store import SeasonData, Store, write_json

log = logging.getLogger(__name__)

OUTCOMES = ("playoffs", "bye", "final", "title", "losers_bracket", "last", "avoid_losers_bye")
REGULAR_SEASON_OUTCOMES = ("playoffs", "bye", "losers_bracket", "last", "avoid_losers_bye")
INTERVALS = (0.50, 0.80, 0.95)
BIN_WIDTH = 0.10
DEFAULT_RUNS = 10_000


# -- which league-seasons ---------------------------------------------------------


def completed_seasons(store: Store, config: Config) -> list[tuple[str, str]]:
    """(league_key, season) for every stored season Sleeper marks complete."""
    found = []
    for league_key in config.leagues:
        for season in store.seasons(league_key):
            league = store.read_league(league_key, season)
            if league and league.get("status") == "complete":
                found.append((league_key, season))
    return found


# -- ground truth ------------------------------------------------------------------


def final_records(data: SeasonData) -> dict[int, TeamRecord]:
    roster_ids = [int(r["roster_id"]) for r in data.rosters]
    return regular_season_records(data.matchups, regular_season_range(data.league), roster_ids=roster_ids)


def season_outcomes(data: SeasonData) -> dict[int, dict[str, bool]]:
    """Per roster: did each season outcome happen, from final standings and the stored winners bracket."""
    rules = BracketRules.from_league(data.league)
    seed_of = seeds(final_records(data))
    n = len(seed_of)
    decider = next((g for g in data.winners_bracket if g.get("p") == 1 and g.get("w") is not None), None)
    if decider is None:
        raise ValueError(f"{data.season}: winners bracket has no decided championship game")
    champion, runner_up = int(decider["w"]), int(decider["l"])
    return {
        rid: {
            "playoffs": seed <= rules.playoff_teams,
            "bye": seed <= 2,
            "final": rid in (champion, runner_up),
            "title": rid == champion,
            "losers_bracket": seed > rules.playoff_teams,
            "last": seed == n,
            "avoid_losers_bye": seed <= n - 2,
        }
        for rid, seed in seed_of.items()
    }


def included_as_of_weeks(outcome: str, rules: BracketRules) -> range:
    """As-of weeks at which ``outcome`` is still undecided in general."""
    if outcome in REGULAR_SEASON_OUTCOMES:
        return range(0, rules.playoff_week_start - 1)  # decided when the last regular week is scored
    if outcome == "final":
        return range(0, rules.week_for_round(2))  # decided by the semifinal week
    if outcome == "title":
        return range(0, rules.week_for_round(3))
    raise ValueError(f"unknown outcome {outcome!r}")


# -- metrics -------------------------------------------------------------------------


def pit(samples: np.ndarray, actual: float) -> float:
    """Where ``actual`` falls in the simulated distribution (0-1), ties counted half."""
    samples = np.asarray(samples, dtype=float)
    return float(np.mean(samples < actual) + 0.5 * np.mean(samples == actual))


def interval_coverage(samples: np.ndarray, actual: float, levels=INTERVALS) -> dict[str, bool]:
    """Whether ``actual`` lies inside each central interval of the samples, keyed by percent."""
    samples = np.asarray(samples, dtype=float)
    hits = {}
    for level in levels:
        lo, hi = np.quantile(samples, [(1 - level) / 2, 1 - (1 - level) / 2])
        hits[_level_key(level)] = bool(lo <= actual <= hi)
    return hits


def mean_bias(samples: np.ndarray, actual: float) -> float:
    """Simulated mean minus actual: positive when the simulation is too optimistic."""
    return float(np.mean(samples) - actual)


def win_probability(a: np.ndarray, b: np.ndarray) -> float:
    """Share of runs in which ``a`` outscores ``b``, ties counted half."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(np.mean(a > b) + 0.5 * np.mean(a == b))


def reliability_bins(probabilities, outcomes, width: float = BIN_WIDTH) -> list[dict]:
    """Group predictions into bins of ``width`` and report predicted mean, observed rate and count per bin."""
    p = np.asarray(probabilities, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    count = int(round(1 / width))
    bins = []
    for k in range(count):
        lo, hi = k * width, (k + 1) * width
        mask = (p >= lo) & ((p < hi) if k < count - 1 else (p <= hi))
        n = int(mask.sum())
        bins.append(
            {
                "lo": round(lo, 2),
                "hi": round(hi, 2),
                "count": n,
                "predicted": round(float(p[mask].mean()), 4) if n else None,
                "observed": round(float(y[mask].mean()), 4) if n else None,
            }
        )
    return bins


def brier(probabilities, outcomes) -> float | None:
    p = np.asarray(probabilities, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    return float(np.mean((p - y) ** 2)) if len(p) else None


def skill(model_brier: float | None, baseline_brier: float | None) -> float | None:
    if model_brier is None or not baseline_brier:
        return None
    return 1.0 - model_brier / baseline_brier


def base_rates(n_teams: int, playoff_teams: int) -> dict[str, float]:
    return {
        "playoffs": playoff_teams / n_teams,
        "bye": 2 / n_teams,
        "final": 2 / n_teams,
        "title": 1 / n_teams,
        "losers_bracket": (n_teams - playoff_teams) / n_teams,
        "last": 1 / n_teams,
        "avoid_losers_bye": (n_teams - 2) / n_teams,
    }


def baseline_probability(
    outcome: str,
    records: dict[int, TeamRecord],
    remaining_weeks: int,
    total_weeks: int,
    n_teams: int,
    playoff_teams: int = 6,
) -> dict[int, float]:
    """A standings reader's chance: base rate before the season, drifting to the extrapolated standings.

    Each team's record is extrapolated over the remaining weeks (``wins + win% * remaining``),
    teams are ranked on it (then points scored), the qualifying positions get the outcome and
    the rest do not, and that 0/1 is blended with the base rate by the share of the season left.
    """
    base = base_rates(n_teams, playoff_teams)[outcome]
    f = max(0.0, min(1.0, remaining_weeks / total_weeks)) if total_weeks else 0.0

    def projected(rec: TeamRecord) -> float:
        rate = rec.win_value / rec.games if rec.games else 0.5
        return rec.win_value + rate * remaining_weeks

    order = sorted(records, key=lambda rid: (projected(records[rid]), round(records[rid].points_for, 2), -rid), reverse=True)
    result = {}
    for rank, rid in enumerate(order, start=1):
        if outcome == "playoffs":
            indicator = float(rank <= playoff_teams)
        elif outcome == "bye":
            indicator = float(rank <= 2)
        elif outcome == "losers_bracket":
            indicator = float(rank > playoff_teams)
        elif outcome == "last":
            indicator = float(rank == n_teams)
        elif outcome == "avoid_losers_bye":
            indicator = float(rank <= n_teams - 2)
        elif outcome == "final":
            indicator = 2 / playoff_teams if rank <= playoff_teams else 0.0
        elif outcome == "title":
            indicator = 1 / playoff_teams if rank <= playoff_teams else 0.0
        else:
            raise ValueError(f"unknown outcome {outcome!r}")
        result[rid] = f * base + (1 - f) * indicator
    return result


# -- lineup gap ------------------------------------------------------------------------


def lineup_gap(store: Store, config: Config, league_key: str, data: SeasonData, week: int) -> list[dict]:
    """Per team that played in ``week``: best-projected lineup minus the lineup actually started."""
    projections = store.read_projections(data.season, week)
    if not projections:
        return []
    scoring = resolve_settings(config, league_key, data.league, week)
    slots = starter_slots(data.league)
    rows = []
    for team in data.matchups.get(week, []):
        starters = [str(p) for p in (team.get("starters") or []) if str(p) not in ("0", "", "None")]
        if team.get("matchup_id") is None or not starters:
            continue
        points = team.get("players_points") or {}
        best = lineup_from_projections(projections, scoring, slots, [str(p) for p in (team.get("players") or [])])
        projected_started = sum(record_points(projections[p], scoring) for p in starters if p in projections)
        actual_best = sum(float(points.get(s.player_id) or 0.0) for s in best)
        rows.append(
            {
                "week": week,
                "roster_id": int(team["roster_id"]),
                "projected_gap": round(lineup_points(best) - projected_started, 2),
                "actual_gap": round(actual_best - float(team.get("points") or 0.0), 2),
            }
        )
    return rows


# -- replay ------------------------------------------------------------------------------


def replay_season(
    store: Store,
    config: Config,
    league_key: str,
    season: str,
    *,
    runs: int = DEFAULT_RUNS,
    seed: int | None = None,
    scale: float | None = None,
    replacement_floor: bool = True,
    roster_drift: bool = True,
) -> Iterator[tuple[int, SimInputs, SimResult, dict]]:
    """Replay one completed season as of weeks 0..16 with leave-season-out noise and drift, storing each payload."""
    data = store.read_season(league_key, season)
    rules = BracketRules.from_league(data.league)
    noise = build_pools(store, config, exclude_after=(season, 0), scale=scale)
    drift = estimate_for_league(store, config, league_key, exclude_season=season, floor=replacement_floor) if roster_drift else None
    for as_of in range(0, rules.week_for_round(rules.rounds)):
        inputs, result, payload = simulate_as_of(
            store, config, league_key, data, as_of, current=False, noise=noise, runs=runs, seed=seed,
            replacement_floor=replacement_floor, drift=drift,
        )
        store.write_odds(league_key, season, as_of, payload)
        yield as_of, inputs, result, payload


def _level_key(level: float) -> str:
    return str(int(round(level * 100)))


def season_rows(
    store: Store,
    config: Config,
    league_key: str,
    season: str,
    *,
    runs: int,
    seed: int | None,
    scale: float | None,
    replacement_floor: bool = True,
    roster_drift: bool = True,
) -> dict:
    """Replay one season and turn every as-of result into comparable rows."""
    data = store.read_season(league_key, season)
    rules = BracketRules.from_league(data.league)
    n_teams = len(data.rosters)
    regular = list(regular_season_range(data.league))
    last_regular = regular[-1]
    actual_outcomes = season_outcomes(data)
    included = {o: included_as_of_weeks(o, rules) for o in OUTCOMES}

    season_level, game_level, score_level = [], [], []
    residual_scale = None
    model = None
    for as_of, inputs, result, payload in replay_season(
        store, config, league_key, season, runs=runs, seed=seed, scale=scale, replacement_floor=replacement_floor, roster_drift=roster_drift
    ):
        residual_scale = payload["residual_scale"]
        model = payload.get("model")
        index = {rid: i for i, rid in enumerate(result.team_ids)}
        remaining = len(inputs.schedule)
        records = fixed_records(data, as_of)

        # season level
        by_roster = {t["roster_id"]: t for t in payload["teams"]}
        for outcome in OUTCOMES:
            if as_of not in included[outcome]:
                continue
            baseline = baseline_probability(outcome, records, remaining, len(regular), n_teams, rules.playoff_teams)
            for rid, team in by_roster.items():
                predicted = team[outcome] if outcome != "avoid_losers_bye" else 1.0 - team["seed_distribution"][-1] - team["seed_distribution"][-2]
                season_level.append(
                    {
                        "as_of": as_of,
                        "roster_id": rid,
                        "outcome": outcome,
                        "predicted": round(float(predicted), 4),
                        "baseline": round(baseline[rid], 4),
                        "actual": bool(actual_outcomes[rid][outcome]),
                    }
                )

        # next regular-season week: scores and games
        week = as_of + 1
        if week > last_regular or week not in result.weekly_scores:
            continue
        scores = result.weekly_scores[week]
        rows_by_rid = {int(t["roster_id"]): t for t in data.matchups.get(week, [])}
        for rid, team in rows_by_rid.items():
            if rid not in index:
                continue
            sims = scores[:, index[rid]]
            actual = float(team.get("points") or 0.0)
            points = team.get("players_points") or {}
            sim_lineup = inputs.starters.get(rid, {}).get(week, [])
            sim_lineup_actual = sum(float(points.get(s.player_id) or 0.0) for s in sim_lineup)
            score_level.append(
                {
                    "as_of": as_of,
                    "week": week,
                    "roster_id": rid,
                    "actual": round(actual, 2),
                    "sim_lineup_actual": round(sim_lineup_actual, 2),
                    "sim_mean": round(float(sims.mean()), 2),
                    "sim_sd": round(float(sims.std()), 2),
                    "pit": round(pit(sims, actual), 4),
                    "pit_sim_lineup": round(pit(sims, sim_lineup_actual), 4),
                    "in": interval_coverage(sims, actual),
                    "in_sim_lineup": interval_coverage(sims, sim_lineup_actual),
                    "starters": len(sim_lineup),
                }
            )
        for a, b in pairings(data.matchups.get(week, [])):
            ra, rb = int(a["roster_id"]), int(b["roster_id"])
            if ra not in index or rb not in index:
                continue
            p_a = win_probability(scores[:, index[ra]], scores[:, index[rb]])
            fav, dog, p_fav = (ra, rb, p_a) if p_a >= 0.5 else (rb, ra, 1.0 - p_a)
            pa, pb = float(a.get("points") or 0.0), float(b.get("points") or 0.0)
            fav_points, dog_points = (pa, pb) if fav == ra else (pb, pa)
            won = 1.0 if fav_points > dog_points else 0.0 if fav_points < dog_points else 0.5
            game_level.append(
                {"as_of": as_of, "week": week, "favourite": fav, "underdog": dog, "p_favourite": round(p_fav, 4), "favourite_won": won}
            )

    return {
        "league_key": league_key,
        "season": season,
        "runs": runs,
        "seed": seed,
        "residual_scale": residual_scale,
        "model": model,
        "season_rows": season_level,
        "game_rows": game_level,
        "score_rows": score_level,
    }


def lineup_rows(store: Store, config: Config, league_key: str, season: str) -> list[dict]:
    """Lineup gaps for every scored week of a stored season (current season included)."""
    data = store.read_season(league_key, season)
    completed = int(data.league.get("settings", {}).get("last_scored_leg") or 0)
    rows = []
    for week in sorted(data.matchups):
        if week <= completed:
            rows.extend(lineup_gap(store, config, league_key, data, week))
    return rows


# -- aggregation --------------------------------------------------------------------------


def _r(x: float | None, nd: int = 4) -> float | None:
    return None if x is None else round(float(x), nd)


def aggregate(season_files: list[dict], lineup_by_league: dict[str, list[dict]]) -> dict:
    """Per-league and overall sections from the rows of every replayed season."""
    leagues = sorted({f["league_key"] for f in season_files} | set(lineup_by_league))
    sections = {}
    for league in leagues + ["overall"]:
        files = [f for f in season_files if league == "overall" or f["league_key"] == league]
        lineups = [r for key, rows in lineup_by_league.items() if league == "overall" or key == league for r in rows]
        sections[league] = _section(files, lineups)
    overall = sections.pop("overall")
    return {"leagues": sections, "overall": overall}


def _section(files: list[dict], lineups: list[dict]) -> dict:
    season_rows = [r for f in files for r in f["season_rows"]]
    game_rows = [r for f in files for r in f["game_rows"]]
    score_rows = [r for f in files for r in f["score_rows"]]
    team_seasons = sum(len({r["roster_id"] for r in f["season_rows"]}) for f in files)

    season = {}
    for outcome in OUTCOMES:
        rows = [r for r in season_rows if r["outcome"] == outcome]
        p = [r["predicted"] for r in rows]
        b = [r["baseline"] for r in rows]
        y = [r["actual"] for r in rows]
        model, base = brier(p, y), brier(b, y)
        season[outcome] = {
            "bins": reliability_bins(p, y),
            "brier": _r(model),
            "baseline_brier": _r(base),
            "skill": _r(skill(model, base)),
            "cases": len(rows),
            "team_seasons": team_seasons,
            "observed_rate": _r(np.mean(y)) if rows else None,
        }

    p = [r["p_favourite"] for r in game_rows]
    y = [r["favourite_won"] for r in game_rows]
    game = {"bins": [b for b in reliability_bins(p, y) if b["hi"] > 0.5], "brier": _r(brier(p, y)), "games": len(game_rows)}

    def coverage(key: str) -> dict[str, float | None]:
        return {
            _level_key(level): _r(np.mean([r[key][_level_key(level)] for r in score_rows])) if score_rows else None
            for level in INTERVALS
        }

    def histogram(key: str) -> list[int]:
        values = np.asarray([r[key] for r in score_rows], dtype=float)
        counts, _ = np.histogram(values, bins=10, range=(0.0, 1.0)) if len(values) else (np.zeros(10, dtype=int), None)
        return [int(c) for c in counts]

    score = {
        "team_weeks": len(score_rows),
        "nominal": {_level_key(level): level for level in INTERVALS},
        "coverage": coverage("in"),
        "coverage_sim_lineup": coverage("in_sim_lineup"),
        "mean_bias": _r(np.mean([r["sim_mean"] - r["actual"] for r in score_rows]), 2) if score_rows else None,
        "mean_bias_sim_lineup": _r(np.mean([r["sim_mean"] - r["sim_lineup_actual"] for r in score_rows]), 2) if score_rows else None,
        "mean_sim_sd": _r(np.mean([r["sim_sd"] for r in score_rows]), 2) if score_rows else None,
        "pit_histogram": histogram("pit"),
        "pit_histogram_sim_lineup": histogram("pit_sim_lineup"),
    }

    lineup = {
        "team_weeks": len(lineups),
        "projected_gap": _r(np.mean([r["projected_gap"] for r in lineups]), 2) if lineups else None,
        "actual_gap": _r(np.mean([r["actual_gap"] for r in lineups]), 2) if lineups else None,
    }
    return {"season": season, "game": game, "score": score, "lineup": lineup}


CAVEATS = [
    "Sleeper serves only the final version of past projections, which may include game-day updates, so replayed odds are slightly sharper than the live odds were.",
    "Rows within one season are not independent: a team's week-5 and week-6 playoff chances resolve to the same outcome. Case counts are shown next to the number of independent team-seasons or games.",
    "The baseline is a simple standings extrapolation, not a rival model; skill above it shows the simulation adds information beyond the record.",
    "Noise pools for each replayed season come from every other stored season, including later ones; residuals are treated as stationary.",
]


def build_report(
    season_files: list[dict],
    lineup_by_league: dict[str, list[dict]],
    *,
    runs: int,
    seed: int | None,
    scale: float,
    replacement_floor: bool = True,
    roster_drift: bool = True,
    replacement_top_n: int | None = None,
    drift_models: dict[str, dict] | None = None,
    drift_diagnostic: dict[str, dict] | None = None,
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": runs,
        "seed": seed,
        "residual_scale": scale,
        "replacement_floor": replacement_floor,
        "roster_drift": roster_drift,
        "replacement_top_n": replacement_top_n,
        "drift_models": drift_models or {},
        "drift_diagnostic": drift_diagnostic or {},
        "seasons": [{"league_key": f["league_key"], "season": f["season"]} for f in season_files],
        "outcomes": list(OUTCOMES),
        "caveats": CAVEATS,
        **aggregate(season_files, lineup_by_league),
    }


# -- markdown --------------------------------------------------------------------------------


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{x * 100:.1f}%"


def _num(x: float | None, nd: int = 4) -> str:
    return "–" if x is None else f"{x:.{nd}f}"


def render_markdown(report: dict) -> str:
    out = ["# Monte Carlo calibration", ""]
    seasons = ", ".join(f"{s['league_key']} {s['season']}" for s in report["seasons"])
    switches = (
        f"replacement floor {'on' if report.get('replacement_floor', True) else 'off'}"
        + (f" (top {report['replacement_top_n']})" if report.get("replacement_top_n") else "")
        + f" · roster drift {'on' if report.get('roster_drift', True) else 'off'}"
    )
    out += [
        f"Generated {report['generated_at']} · {report['runs']:,} runs per replay · residual scale {report['residual_scale']} · {switches} · seed {report['seed'] if report['seed'] is not None else 'per league-season-week'}",
        "",
        f"Seasons replayed: {seasons}.",
        "",
    ]
    if report.get("drift_diagnostic"):
        out += [
            "## Roster drift diagnostic",
            "",
            "How well a team's projected strength predicts its true strength k weeks ahead: slope 1 = the edge fully survives, below 1 = it reverts toward the league mean; sd = roster-change noise the simulation would miss without drift. Frozen = the roster held as of the as-of week; floored = the same with every slot at least replacement level.",
            "",
        ]
        for league, diag in report["drift_diagnostic"].items():
            out += [f"### {league} (top {diag.get('top_n')}, seasons {', '.join(diag.get('seasons', []))})", "", "| weeks ahead | frozen slope | frozen sd | floored slope | floored sd |", "|---|---|---|---|---|"]
            for k in diag.get("horizons", []):
                fr = diag.get("frozen", {}).get(str(k))
                fl = diag.get("floored", {}).get(str(k))
                if fr and fl:
                    out.append(f"| {k} | {_num(fr['slope'], 3)} | {_num(fr['sd'], 2)} | {_num(fl['slope'], 3)} | {_num(fl['sd'], 2)} |")
            model = report.get("drift_models", {}).get(league)
            if model:
                note = model.get("note") or ""
                slopes = model.get("slopes") or []
                out.append("")
                out.append(
                    f"Drift model in force: {note if note else 'slopes ' + ', '.join(f'{s:.2f}' for s in slopes[:6]) + ('…' if len(slopes) > 6 else '')} (seasons {', '.join(model.get('seasons', []))})."
                )
            out += [""]
    for name, section in [("Overall", report["overall"])] + [(k, v) for k, v in report["leagues"].items()]:
        out += [f"## {name}", ""]
        sc = section["score"]
        out += [
            f"### Score level ({sc['team_weeks']} team-weeks)",
            "",
            "| interval | nominal | observed (started lineup) | observed (simulated lineup) |",
            "|---|---|---|---|",
        ]
        for level in INTERVALS:
            key = _level_key(level)
            out.append(f"| {key}% | {_pct(level)} | {_pct(sc['coverage'][key])} | {_pct(sc['coverage_sim_lineup'][key])} |")
        out += [
            "",
            f"Mean simulated minus actual: {_num(sc['mean_bias'], 2)} points vs the started lineup, {_num(sc['mean_bias_sim_lineup'], 2)} vs the simulated lineup's actual points. Mean simulated SD {_num(sc['mean_sim_sd'], 2)}.",
            "",
            f"PIT histogram (10 bins, started lineup): {sc['pit_histogram']}",
            "",
        ]
        g = section["game"]
        out += [f"### Game level ({g['games']} games, Brier {_num(g['brier'])})", "", "| favourite's chance | predicted | observed | games |", "|---|---|---|---|"]
        for b in g["bins"]:
            out.append(f"| {_pct(b['lo'])}–{_pct(b['hi'])} | {_pct(b['predicted'])} | {_pct(b['observed'])} | {b['count']} |")
        out += [""]
        out += ["### Season level", "", "| outcome | cases | team-seasons | observed | Brier | baseline | skill |", "|---|---|---|---|---|---|---|"]
        for outcome in report["outcomes"]:
            s = section["season"][outcome]
            out.append(
                f"| {outcome} | {s['cases']} | {s['team_seasons']} | {_pct(s['observed_rate'])} | {_num(s['brier'])} | {_num(s['baseline_brier'])} | {_num(s['skill'], 3)} |"
            )
        out += [""]
        for outcome in report["outcomes"]:
            s = section["season"][outcome]
            out += [f"#### {outcome}: reliability", "", "| predicted | observed | cases |", "|---|---|---|"]
            for b in s["bins"]:
                if b["count"]:
                    out.append(f"| {_pct(b['lo'])}–{_pct(b['hi'])} ({_pct(b['predicted'])}) | {_pct(b['observed'])} | {b['count']} |")
            out += [""]
        lg = section["lineup"]
        out += [
            f"### Lineup gap ({lg['team_weeks']} team-weeks)",
            "",
            f"Best projected lineup minus started lineup: {_num(lg['projected_gap'], 2)} projected points, {_num(lg['actual_gap'], 2)} actual points.",
            "",
        ]
    out += ["## Caveats", ""] + [f"- {c}" for c in report["caveats"]] + [""]
    return "\n".join(out)


# -- driver ------------------------------------------------------------------------------------


def calibration_dir(store: Store) -> Path:
    return store.root / "calibration"


def write_report(store: Store, report: dict) -> tuple[Path, Path]:
    base = calibration_dir(store)
    json_path, md_path = base / "report.json", base / "report.md"
    write_json(json_path, report)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def run_calibration(
    store: Store,
    config: Config,
    *,
    runs: int = DEFAULT_RUNS,
    seed: int | None = None,
    scale: float | None = None,
    replacement_floor: bool = True,
    roster_drift: bool = True,
    progress=None,
) -> dict:
    """Replay every completed season, write rows and the report, return the report."""
    scale_used = config.simulation.residual_scale if scale is None else float(scale)
    season_files = []
    for league_key, season in completed_seasons(store, config):
        rows = season_rows(
            store, config, league_key, season, runs=runs, seed=seed, scale=scale_used,
            replacement_floor=replacement_floor, roster_drift=roster_drift,
        )
        write_json(calibration_dir(store) / "rows" / league_key / f"{season}.json", rows)
        season_files.append(rows)
        if progress:
            progress(league_key, season, rows)
    lineup_by_league = {
        key: [r for season in store.seasons(key) for r in lineup_rows(store, config, key, season)] for key in config.leagues
    }
    by_league: dict[str, list[str]] = {}
    for league_key, season in completed_seasons(store, config):
        by_league.setdefault(league_key, []).append(season)
    drift_models = {key: estimate_for_league(store, config, key, floor=replacement_floor).to_dict() for key in by_league}
    drift_diagnostic = {key: diagnostic(store, config, key, seasons) for key, seasons in by_league.items()}
    report = build_report(
        season_files, lineup_by_league, runs=runs, seed=seed, scale=scale_used,
        replacement_floor=replacement_floor, roster_drift=roster_drift,
        replacement_top_n=config.simulation.replacement_top_n,
        drift_models=drift_models, drift_diagnostic=drift_diagnostic,
    )
    write_report(store, report)
    return report
