"""Command-line entry point: ``python -m ffapp <command>``."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from ffapp.config import DEFAULT_CONFIG_PATH, Config, ConfigError, load_config
from ffapp.sleeper import SleeperClient
from ffapp.store import DEFAULT_DATA_ROOT, Store

COMMANDS = ("sync", "projections", "stats", "replacement", "simulate", "verify-brackets", "export", "refresh", "calibrate")
log = logging.getLogger("ffapp")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ffapp",
        description="Sleeper league history and Monte Carlo playoff odds.",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="leagues config (default config/leagues.yaml)")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_ROOT, help="data directory (default data/)")
    parser.add_argument("--site-data", type=Path, default=Path("site") / "data", help="website data directory (default site/data)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", metavar="command", required=True)

    sync = sub.add_parser("sync", help="Pull league history from Sleeper into data/leagues")
    sync.add_argument("--full", action="store_true", help="Re-fetch completed seasons too")

    proj = sub.add_parser("projections", help="Refresh stored player projections")
    proj.add_argument("--backfill", action="store_true", help="Fetch every season in scope, not just the current one")

    stats = sub.add_parser("stats", help="Refresh stored weekly player stats (actual stat lines)")
    stats.add_argument("--backfill", action="store_true", help="Fetch every season in scope, not just the current one")

    sub.add_parser("replacement", help="Write replacement-level values for every stored season to data/replacement")

    sim = sub.add_parser("simulate", help="Run the playoff odds simulation")
    sim.add_argument("--backfill-season", action="store_true", help="Also produce odds for every earlier as-of week of the current season")
    sim.add_argument("--runs", type=int, default=10_000, help="Simulation runs (default 10000)")
    sim.add_argument("--seed", type=int, default=None, help="Random seed (default: derived from league, season and as-of week)")

    sub.add_parser("verify-brackets", help="Check bracket logic against every completed season")
    cal = sub.add_parser("calibrate", help="Replay completed seasons and score the odds against what happened")
    cal.add_argument("--runs", type=int, default=10_000, help="Simulation runs per replay (default 10000)")
    cal.add_argument("--seed", type=int, default=None, help="Random seed for every replay (default: derived per league, season and week)")
    cal.add_argument("--residual-scale", type=float, default=None, help="Evaluate this residual scale instead of the configured one; the config file is not changed")
    cal.add_argument("--no-replacement-floor", action="store_true", help="Replay without the replacement-level lineup floor (evaluation only)")
    cal.add_argument("--no-roster-drift", action="store_true", help="Replay without roster drift (evaluation only)")
    sub.add_parser("export", help="Write site/data/*.json for the website")
    refresh = sub.add_parser("refresh", help="sync, projections, stats, replacement, simulate and export in order")
    refresh.set_defaults(full=False, backfill=False, backfill_season=False, runs=10_000, seed=None)
    return parser


class Context:
    """Shared objects for one CLI invocation."""

    def __init__(self, args: argparse.Namespace, client: SleeperClient | None = None):
        self.args = args
        self.config: Config = load_config(args.config)
        self.store = Store(args.data)
        self.client = client or SleeperClient()


# -- commands -----------------------------------------------------------------


def cmd_sync(ctx: Context) -> int:
    from ffapp.sync import sync_all

    report = sync_all(ctx.client, ctx.store, ctx.config, full=ctx.args.full)
    for key, season in report.fetched:
        print(f"synced   {key} {season}")
    for key, season in report.skipped:
        print(f"skipped  {key} {season} (complete)")
    for key, message in report.errors:
        print(f"FAILED   {key}: {message}", file=sys.stderr)
    return 0 if report.ok else 1


def cmd_projections(ctx: Context) -> int:
    from ffapp.projections import refresh_projections

    report = refresh_projections(ctx.client, ctx.store, ctx.config.leagues, backfill=ctx.args.backfill)
    written = sum(1 for r in report.results if r.written)
    added = sum(r.added for r in report.results)
    updated = sum(r.updated for r in report.results)
    print(f"projections: {len(report.results)} weeks checked, {written} written, {added} added, {updated} updated")
    for message in report.errors:
        print(f"FAILED   {message}", file=sys.stderr)
    return 0 if report.ok else 1


def cmd_stats(ctx: Context) -> int:
    from ffapp.stats import refresh_stats

    report = refresh_stats(ctx.client, ctx.store, ctx.config.leagues, backfill=ctx.args.backfill)
    written = sum(1 for r in report.results if r.written)
    added = sum(r.added for r in report.results)
    updated = sum(r.updated for r in report.results)
    print(f"stats: {len(report.results)} weeks checked, {written} written, {added} added, {updated} updated")
    for message in report.errors:
        print(f"FAILED   {message}", file=sys.stderr)
    return 0 if report.ok else 1


def cmd_replacement(ctx: Context) -> int:
    from ffapp.replacement import write_replacement

    failed = 0
    for key in ctx.config.leagues:
        try:
            written = write_replacement(ctx.store, ctx.config, key)
        except (ValueError, FileNotFoundError) as exc:
            print(f"FAILED   {key}: {exc}", file=sys.stderr)
            failed += 1
            continue
        for path in written:
            print(f"wrote    {path}")
    return 0 if failed == 0 else 1


def cmd_verify_brackets(ctx: Context) -> int:
    from ffapp.verify import verify_all

    checks = verify_all(ctx.store, ctx.config)
    if not checks:
        print("no completed seasons stored: run `ffapp sync` first", file=sys.stderr)
        return 1
    failed = 0
    for check in checks:
        status = "OK  " if check.ok else "FAIL"
        print(f"{status} {check.league_key} {check.season}  {'; '.join(check.notes)}")
        for mismatch in check.mismatches:
            print(f"       {mismatch}")
        failed += not check.ok
    print(f"{len(checks) - failed}/{len(checks)} completed seasons reproduced")
    return 0 if failed == 0 else 1


def cmd_simulate(ctx: Context) -> int:
    from ffapp.odds import simulate_league

    failed = 0
    for key in ctx.config.leagues:
        try:
            payloads = simulate_league(
                ctx.store, ctx.config, key,
                backfill_season=ctx.args.backfill_season, runs=ctx.args.runs, seed=ctx.args.seed,
            )
        except (ValueError, FileNotFoundError) as exc:
            print(f"FAILED   {key}: {exc}", file=sys.stderr)
            failed += 1
            continue
        for payload in payloads:
            print(f"odds     {key} {payload['season']} as of week {payload['as_of_week']:2d}  ({payload['runs']} runs)")
    return 0 if failed == 0 else 1


def cmd_calibrate(ctx: Context) -> int:
    from ffapp.calibrate import calibration_dir, run_calibration

    scale = ctx.args.residual_scale
    if scale is not None and not scale > 0:
        print("FAILED   calibrate: --residual-scale must be positive", file=sys.stderr)
        return 2

    def progress(league_key: str, season: str, rows: dict) -> None:
        print(f"replayed {league_key} {season}: {len(rows['score_rows'])} team-weeks, {len(rows['game_rows'])} games, {len(rows['season_rows'])} season rows")

    try:
        report = run_calibration(
            ctx.store, ctx.config, runs=ctx.args.runs, seed=ctx.args.seed, scale=scale,
            replacement_floor=not ctx.args.no_replacement_floor, roster_drift=not ctx.args.no_roster_drift, progress=progress,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"FAILED   calibrate: {exc}", file=sys.stderr)
        return 1
    if not report["seasons"]:
        print("no completed seasons stored: run `ffapp sync` first", file=sys.stderr)
        return 1
    overall = report["overall"]
    cov = overall["score"]["coverage"]
    print(f"model    replacement floor {'on' if report['replacement_floor'] else 'off'}, roster drift {'on' if report['roster_drift'] else 'off'}")
    print(f"score    80% interval covered {cov['80'] * 100:.1f}% of {overall['score']['team_weeks']} team-weeks (95%: {cov['95'] * 100:.1f}%)")
    for outcome in ("playoffs", "title"):
        s = overall["season"][outcome]
        skill = "n/a" if s["skill"] is None else f"{s['skill']:+.3f}"
        print(f"season   {outcome}: Brier {s['brier']:.4f} vs baseline {s['baseline_brier']:.4f}, skill {skill} ({s['cases']} cases)")
    print(f"wrote    {calibration_dir(ctx.store) / 'report.json'}")
    print(f"wrote    {calibration_dir(ctx.store) / 'report.md'}")
    return 0


def cmd_export(ctx: Context) -> int:
    from ffapp.export import ExportError, export_site

    try:
        written = export_site(ctx.store, ctx.config, ctx.args.site_data)
    except ExportError as exc:
        print(f"FAILED   export: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote    {path}")
    return 0


def cmd_refresh(ctx: Context) -> int:
    """The scheduled pipeline: each step runs only if the one before succeeded."""
    steps = (
        ("sync", cmd_sync),
        ("projections", cmd_projections),
        ("stats", cmd_stats),
        ("replacement", cmd_replacement),
        ("simulate", cmd_simulate),
        ("export", cmd_export),
    )
    for name, handler in steps:
        print(f"== {name}")
        code = handler(ctx)
        if code != 0:
            print(f"refresh stopped: {name} failed (exit {code})", file=sys.stderr)
            return code
    return 0


HANDLERS = {
    "sync": cmd_sync,
    "projections": cmd_projections,
    "stats": cmd_stats,
    "replacement": cmd_replacement,
    "simulate": cmd_simulate,
    "verify-brackets": cmd_verify_brackets,
    "export": cmd_export,
    "refresh": cmd_refresh,
    "calibrate": cmd_calibrate,
}


def main(argv: Sequence[str] | None = None, client: SleeperClient | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        ctx = Context(args, client)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return HANDLERS[args.command](ctx)
