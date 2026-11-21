"""The hot run: this week's live scores, forecast and game cards as one bundle (docs/refresh-modes.md).

It works on a scratch copy of the data folder (the committed records plus the cold run's build
cache) so the data folder itself is never changed:

1. current-week league data from Sleeper (league settings, rosters, this week's matchups);
2. the NFL scoreboard for the current and next week;
3. the simulation (same model and runs as the cold run) and this week's game cards;
4. the site export, from which the bundle takes, per league, the forecast file, the games index
   and the current week's game file, keyed by their paths under ``site/data``.

The bundle also carries each current-week game's state (for the relay's clock), the commit the
inputs came from and the run's time. Uploading it is the workflow's job (``PUT /live``).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ffapp.config import Config
from ffapp.sleeper import SleeperClient, SleeperError
from ffapp.store import Store, read_json

BUNDLE_VERSION = 1


class HotError(RuntimeError):
    """A hot run could not produce a bundle; nothing is uploaded and the previous bundle stays."""


@dataclass
class HotResult:
    bundle: dict
    notes: list[str] = field(default_factory=list)


def base_commit() -> str | None:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def sync_current_week(client: SleeperClient, store: Store, config: Config, week: int) -> list[str]:
    """Refresh each league's settings, rosters and this week's matchups (about 3 calls a league)."""
    notes = []
    for key in config.leagues:
        seasons = store.seasons(key)
        if not seasons:
            raise HotError(f"{key}: no stored season (the cold run has not synced yet)")
        stored = store.read_league(key, seasons[-1]) or {}
        league_id = str(stored.get("league_id") or "")
        if not league_id:
            raise HotError(f"{key}: stored league has no id")
        data = store.read_season(key, seasons[-1])
        data.league = client.league(league_id)
        data.rosters = client.rosters(league_id)
        data.matchups[week] = client.matchups(league_id, week) or []
        store.write_season(key, data)
        notes.append(f"synced   {key} week {week}")
    return notes


def game_states(store: Store, season: str, week: int) -> dict[str, str]:
    games = (store.read_nfl_week(season, week) or {}).get("games") or []
    return {f"{season}-{week:02d}-{g['away']}@{g['home']}": g.get("state") or "scheduled" for g in games}


def bundle_files(site_data: Path, league_keys) -> dict[str, dict]:
    """Per league: the forecast file, the games index and the current week's game file."""
    index = read_json(site_data / "index.json")
    files: dict[str, dict] = {}
    for entry in index.get("leagues") or []:
        if entry.get("key") not in league_keys:
            continue
        files[entry["file"]] = read_json(site_data / entry["file"])
        games = entry.get("games")
        if games:
            games_index = read_json(site_data / games["file"])
            files[games["file"]] = games_index
            week = next((w for w in games_index.get("weeks") or [] if w.get("week") == games.get("current")), None)
            if week:
                rel = f"{Path(games['file']).parent.as_posix()}/{week['file']}"
                files[rel] = read_json(site_data / rel)
    return files


def content_hash(bundle: dict) -> str:
    """Hash of what the page shows: the files and game states, without times."""
    def strip(value):
        if isinstance(value, dict):
            return {k: strip(v) for k, v in value.items() if k not in ("generated_at", "last_refresh", "at")}
        if isinstance(value, list):
            return [strip(v) for v in value]
        return value
    body = {"files": strip(bundle.get("files")), "games": bundle.get("games")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()[:16]


STATE_CODES = {"scheduled": "s", "in_progress": "i", "final": "f"}


def bundle_meta(bundle: dict) -> str:
    """What the relay keeps beside the bundle without parsing it (KV metadata, at most 1 KB), as
    base64 JSON for the X-Bundle-Meta header: the content hash, the run's time and each game's
    state as one letter."""
    import base64

    meta = {"h": bundle["hash"], "t": bundle["generated_at"],
            "g": {gid: STATE_CODES.get(state, "s") for gid, state in (bundle.get("games") or {}).items()}}
    return base64.b64encode(json.dumps(meta, separators=(",", ":")).encode("utf-8")).decode("ascii")


def run_hot(client: SleeperClient, config: Config, data_root: Path, *, runs: int = 10_000, now: datetime | None = None) -> HotResult:
    from ffapp.export import export_site
    from ffapp.games import update_games
    from ffapp.odds import simulate_league
    from ffapp.schedule import refresh_schedule

    now = now or datetime.now(timezone.utc)
    try:
        state = client.state()
    except SleeperError as exc:
        raise HotError(f"NFL state: {exc}") from exc
    season, week = str(state.get("season") or ""), int(state.get("week") or 0)
    if state.get("season_type") not in ("regular", "post") or not week:
        raise HotError("no current NFL week (off-season): nothing to update")

    with tempfile.TemporaryDirectory(prefix="ffapp-hot-") as tmp:
        scratch = Path(tmp) / "data"
        shutil.copytree(data_root, scratch)
        store = Store(scratch)
        try:
            notes = sync_current_week(client, store, config, week)
        except SleeperError as exc:
            raise HotError(f"sync: {exc}") from exc
        report = refresh_schedule(client, store)
        if not report.ok:
            raise HotError("scoreboard: " + "; ".join(report.errors))
        for key in config.leagues:
            for payload in simulate_league(store, config, key, runs=runs):
                live = payload.get("live")
                notes.append(f"odds     {key} " + (f"live week {live['week']}" if live else f"as of week {payload['as_of_week']}"))
            update_games(store, config, key, now=now)
        site_data = Path(tmp) / "site-data"
        export_site(store, config, site_data, last_refresh=now)
        bundle = {
            "version": BUNDLE_VERSION,
            "generated_at": now.isoformat(timespec="seconds"),
            "base_commit": base_commit(),
            "season": season,
            "week": week,
            "games": game_states(store, season, week),
            "files": bundle_files(site_data, set(config.leagues)),
        }
    bundle["hash"] = content_hash(bundle)
    return HotResult(bundle=bundle, notes=notes)
