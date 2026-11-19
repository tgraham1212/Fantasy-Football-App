"""Command-line entry point: ``python -m ffapp <command>``."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from ffapp.config import DEFAULT_CONFIG_PATH, Config, ConfigError, load_config
from ffapp.sleeper import SleeperClient
from ffapp.store import DEFAULT_DATA_ROOT, Store

COMMANDS = ("should-run", "sync", "projections", "stats", "schedule", "snapshot", "ratings", "replacement", "war", "simulate", "games", "verify-brackets", "export", "refresh", "calibrate", "stamp-site", "site-copy")
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

    gate = sub.add_parser("should-run", help="Decide whether the scheduled job runs the full refresh now (prints run=true|false)")
    gate.add_argument("--mode", choices=("check", "daily", "manual"), default="check", help="daily and manual always run")
    sched = sub.add_parser("schedule", help="Store the NFL schedule (kickoffs, game states) for the current and next week into data/nfl")
    sched.add_argument("--all", action="store_true", help="Store every week of the current season")
    sub.add_parser("snapshot", help="Capture ESPN start-percentage snapshots and the player crosswalk into data/espn")
    sub.add_parser("ratings", help="Rate every manager across all stored seasons and write data/ratings")
    sub.add_parser("replacement", help="Write replacement-level values for every stored season to data/replacement")
    sub.add_parser("war", help="Compute every player's Wins Above Replacement per league-season into data/war")

    sim = sub.add_parser("simulate", help="Run the playoff odds simulation")
    sim.add_argument("--backfill-season", action="store_true", help="Also produce odds for every earlier as-of week of the current season")
    sim.add_argument("--runs", type=int, default=10_000, help="Simulation runs (default 10000)")
    sim.add_argument("--seed", type=int, default=None, help="Random seed (default: derived from league, season and as-of week)")

    games = sub.add_parser("games", help="Update this season's game logs and predictions of record in data/games")
    games.add_argument("--force-records", action="store_true", help="Recompute the record of every final week")
    sub.add_parser("verify-brackets", help="Check bracket logic against every completed season")
    cal = sub.add_parser("calibrate", help="Replay completed seasons and score the odds against what happened")
    cal.add_argument("--runs", type=int, default=10_000, help="Simulation runs per replay (default 10000)")
    cal.add_argument("--seed", type=int, default=None, help="Random seed for every replay (default: derived per league, season and week)")
    cal.add_argument("--residual-scale", type=float, default=None, help="Evaluate this residual scale instead of the configured one; the config file is not changed")
    cal.add_argument("--no-replacement-floor", action="store_true", help="Replay without the replacement-level lineup floor (evaluation only)")
    cal.add_argument("--no-roster-drift", action="store_true", help="Replay without roster drift (evaluation only)")
    sub.add_parser("export", help="Write site/data/*.json for the website")
    refresh = sub.add_parser("refresh", help="sync, projections, stats, schedule, snapshot, ratings, replacement, war, simulate, games and export in order")
    refresh.set_defaults(full=False, backfill=False, backfill_season=False, runs=10_000, seed=None)
    stamp = sub.add_parser("stamp-site", help="Before a deploy: stamp script and stylesheet URLs with the site code fingerprint and write version.json")
    stamp.add_argument("--site", type=Path, default=Path("site"), help="site directory (default site/)")
    copy = sub.add_parser("site-copy", help="Regenerate site-copy.txt from the site code; --check reports drift and pending edits; --apply writes confirmed edits into the code")
    mode = copy.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report what is out of sync and exit non-zero if anything is")
    mode.add_argument("--apply", action="store_true", help="write the pending edits in site-copy.txt into the site code (confirm with the owner first)")
    copy.add_argument("--root", type=Path, default=Path("."), help="project root holding site/ and site-copy.txt (default .)")
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


def cmd_should_run(ctx: Context) -> int:
    from datetime import datetime, timezone

    from ffapp.schedule import should_run

    decision = should_run(ctx.client, ctx.store, datetime.now(timezone.utc), ctx.args.mode)
    line = f"run={'true' if decision.run else 'false'}"
    print(f"{line}  ({decision.reason})")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return 0


def cmd_schedule(ctx: Context) -> int:
    from ffapp.schedule import refresh_schedule

    report = refresh_schedule(ctx.client, ctx.store, all_weeks=getattr(ctx.args, "all", False))
    for season, week in report.written:
        print(f"wrote    {ctx.store.nfl_week_path(season, week)}")
    for message in report.errors:
        print(f"FAILED   schedule {message}", file=sys.stderr)
    return 0 if report.ok else 1


def cmd_snapshot(ctx: Context) -> int:
    from ffapp.espn import EspnClient, capture_snapshots, match, refresh_crosswalk, teams_from_stats
    from ffapp.projections import seasons_in_scope
    from ffapp.sleeper import SleeperError

    report = capture_snapshots(EspnClient(ctx.client), ctx.client, ctx.store, ctx.config.leagues)
    for season in report.seasons_written:
        print(f"wrote    {ctx.store.espn_season_path(season)}")
    if report.week_written:
        print(f"wrote    {ctx.store.espn_week_path(*report.week_written)}")
    for message in report.errors:
        print(f"FAILED   snapshot {message}", file=sys.stderr)
    from ffapp.injuries import save_injuries

    try:
        players_payload = ctx.client.players()
        changed = refresh_crosswalk(ctx.client, ctx.store, players_payload)
        saved = save_injuries(ctx.store, ctx.client.state(), players_payload)
    except SleeperError as exc:
        print(f"FAILED   crosswalk: {exc}", file=sys.stderr)
        return 1
    print(f"crosswalk {'updated' if changed else 'unchanged'}")
    if saved:
        print(f"wrote    {ctx.store.injuries_path(*saved)}")
    crosswalk = ctx.store.read_crosswalk() or {}
    for season in seasons_in_scope(ctx.store, ctx.config.leagues):
        snapshots = [(season, ctx.store.read_espn_season(season))]
        snapshots += [(f"{season} week {w}", ctx.store.read_espn_week(season, w)) for w in ctx.store.espn_weeks(season)]
        teams = teams_from_stats(ctx.store, season)
        for label, snapshot in snapshots:
            if not snapshot:
                continue
            _, unmatched = match(snapshot.get("players") or {}, crosswalk, teams)
            for u in unmatched:
                print(f"unmatched {label}: {u.name} ({u.position}) started {u.started}%")
    return 0 if report.ok else 1


def cmd_ratings(ctx: Context) -> int:
    from ffapp.ratings import write_ratings

    failed = 0
    for key in ctx.config.leagues:
        try:
            path = write_ratings(ctx.store, ctx.config, key)
        except (ValueError, FileNotFoundError) as exc:
            print(f"FAILED   {key}: {exc}", file=sys.stderr)
            failed += 1
            continue
        print(f"wrote    {path}")
    return 0 if failed == 0 else 1


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


def cmd_war(ctx: Context) -> int:
    from ffapp.war import write_war

    failed = 0
    for key in ctx.config.leagues:
        try:
            report = write_war(ctx.store, ctx.config, key)
        except (ValueError, FileNotFoundError) as exc:
            print(f"FAILED   {key}: {exc}", file=sys.stderr)
            failed += 1
            continue
        for path in report.written:
            print(f"wrote    {path}")
        for message in report.skipped:
            print(f"skipped  {message}", file=sys.stderr)
    return 0 if failed == 0 else 1


def cmd_games(ctx: Context) -> int:
    from ffapp.games import update_games

    failed = 0
    for key in ctx.config.leagues:
        try:
            weeks = update_games(ctx.store, ctx.config, key, force_records=getattr(ctx.args, "force_records", False))
        except (ValueError, FileNotFoundError, KeyError) as exc:
            print(f"FAILED   {key}: {exc}", file=sys.stderr)
            failed += 1
            continue
        print(f"games    {key}: {len(weeks)} week files updated" + (f" ({', '.join(map(str, weeks))})" if weeks else ""))
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
            live = payload.get("live")
            where = f"live week {live['week']:2d} ({live['games_final']} of {live['games_total']} games final)" if live else f"as of week {payload['as_of_week']:2d}"
            print(f"odds     {key} {payload['season']} {where}  ({payload['runs']} runs)")
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
        # inside `refresh` the site shows this run's start time; last_run.json is only written
        # after the export (the last step) succeeds, so it would still hold the previous run's
        written = export_site(ctx.store, ctx.config, ctx.args.site_data, last_refresh=getattr(ctx.args, "refresh_started", None))
    except ExportError as exc:
        print(f"FAILED   export: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote    {path}")
    return 0


def cmd_refresh(ctx: Context) -> int:
    """The scheduled pipeline: each step runs only if the one before succeeded.

    Steps in ``OPTIONAL_STEPS`` may fail without stopping the run (the ESPN snapshot:
    WAR works from the snapshots already stored and the odds must not depend on ESPN);
    the run then ends with a warning naming them, as a workflow annotation under GitHub Actions.
    """
    from datetime import datetime, timezone

    from ffapp.schedule import write_last_run

    started = datetime.now(timezone.utc)  # stored only once the run succeeds, so a failed run changes nothing
    ctx.args.refresh_started = started  # the export step publishes it as the site's "Updated" time
    skipped: list[str] = []
    for name, handler in REFRESH_STEPS:
        print(f"== {name}")
        code = handler(ctx)
        if code != 0 and name in OPTIONAL_STEPS:
            skipped.append(f"{name} failed (exit {code}); later steps used the data already stored")
            continue
        if code != 0:
            print(f"refresh stopped: {name} failed (exit {code})", file=sys.stderr)
            return code
    write_last_run(ctx.store, started)
    for reason in skipped:
        print(warning_line("Refresh skipped a step", reason))
    return 0


def warning_line(title: str, message: str) -> str:
    """A GitHub Actions warning annotation when running there, a plain warning line otherwise."""
    if os.environ.get("GITHUB_ACTIONS"):
        return f"::warning title={title}::{message}"
    return f"WARNING  {title}: {message}"


REFRESH_STEPS = (
    ("sync", cmd_sync),
    ("projections", cmd_projections),
    ("stats", cmd_stats),
    ("schedule", cmd_schedule),
    ("snapshot", cmd_snapshot),
    ("ratings", cmd_ratings),
    ("replacement", cmd_replacement),
    ("war", cmd_war),
    ("simulate", cmd_simulate),
    ("games", cmd_games),
    ("export", cmd_export),
)
OPTIONAL_STEPS = frozenset({"schedule", "snapshot"})

HANDLERS = {
    "should-run": cmd_should_run,
    "sync": cmd_sync,
    "projections": cmd_projections,
    "stats": cmd_stats,
    "schedule": cmd_schedule,
    "snapshot": cmd_snapshot,
    "ratings": cmd_ratings,
    "replacement": cmd_replacement,
    "war": cmd_war,
    "simulate": cmd_simulate,
    "games": cmd_games,
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
    if args.command == "stamp-site":  # needs no league config
        from ffapp.stamp import stamp_site
        print(f"stamped {args.site} with {stamp_site(args.site)}")
        return 0
    if args.command == "site-copy":  # needs no league config
        return cmd_site_copy(args)
    try:
        ctx = Context(args, client)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    return HANDLERS[args.command](ctx)


def _copy_report(report) -> list[str]:
    lines = []
    for kind, what in (("stale", "code changed, file behind (regenerate)"), ("new", "new in the code (regenerate)"),
                       ("removed", "gone from the code (regenerate)"), ("pending", "edited in site-copy.txt, not yet applied"),
                       ("conflict", "changed in both the code and the file")):
        ids = report.ids(kind)
        if ids:
            lines.append(f"{kind}: {', '.join(ids)}  ({what})")
    return lines


def cmd_site_copy(args) -> int:
    from ffapp import site_copy

    root = args.root
    if args.check:
        report = site_copy.check(root)
        problems = site_copy.coverage_problems(root / "site")
        for line in _copy_report(report) + [f"uncovered: {p}" for p in problems]:
            print(line)
        if report.clean and not problems:
            print(f"{site_copy.COPY_FILE} is in sync ({len(report.statuses)} entries)")
            return 0
        if report.ids("pending", "conflict"):
            print("pending copy edits: confirm with the owner, then run python -m ffapp site-copy --apply")
        return 1
    if args.apply:
        result = site_copy.apply_edits(root)
        print(f"applied: {', '.join(result.applied) or 'none'}")
        for cid, why in result.refused:
            print(f"refused {cid}: {why}")
        for cid in result.deletions:
            print(f"deletion requested for {cid}: not applied; remove it from the code by hand")
        return 1 if result.refused else 0
    report = site_copy.regenerate(root)
    for line in _copy_report(report):
        print(line)
    print(f"wrote {site_copy.COPY_FILE} and {site_copy.LOCK_FILE} ({len(report.statuses)} entries)")
    return 0
