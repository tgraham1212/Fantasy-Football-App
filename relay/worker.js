/*
 * Refresh relay: a Cloudflare Worker that is the refresh clock, stores the live bundle, and lets the
 * published site's Refresh Data button start a refresh (docs/refresh-modes.md).
 *
 * Every minute (cron trigger) it works out the refresh mode from the schedule summary the cold run
 * uploads and the game states in the latest live bundle, then starts the runs that mode makes due:
 *   Live       hot run back to back (whenever none is queued or running); cold run every 15 minutes
 *   Quiet      hot run and cold run every 15 minutes
 *   Off-season nothing (GitHub's daily schedule runs the cold run)
 * and a cold run in "slate" mode when a slate (games sharing a kickoff) has gone final.
 *
 * GET  /status   -> { available, minutes, last_start, mode, reason }   reason: live | running | cooldown | null
 * POST /refresh  -> 202 { started }  |  409 { reason: "live" }  |  429 { minutes, reason }
 * GET  /live     -> the latest bundle (200), or 204 when there is none or none newer than ?since=
 * PUT  /live     -> store a bundle (hot run only: Authorization: Bearer HOT_TOKEN, X-Bundle-Meta)
 * PUT  /schedule -> store the schedule summary (cold run only, same token)
 *
 * Browser requests are answered for SITE_ORIGIN only. GitHub is the source of truth for runs; the
 * Worker also remembers its own last dispatches for a minute, since a new run takes a few seconds
 * to show up in GitHub's list. KV writes stay within the free plan's 1,000 a day: one per hot run
 * (skipped when nothing changed, stopped at WRITE_CAP), one per changed schedule summary, one per
 * slate and one per button press.
 *
 * Settings (Cloudflare dashboard -> the Worker -> Settings, or wrangler.toml):
 *   GITHUB_TOKEN  secret: fine-grained token, this repository only, "Actions: Read and write"
 *   HOT_TOKEN     secret: any long random string, also stored as the repository secret HOT_TOKEN
 *   LIVE          KV namespace binding
 *   REPO          e.g. "tgraham1212/Fantasy-Football-App"
 *   SITE_ORIGIN   e.g. "https://fantasyfoosball.net"
 *   WORKFLOW      optional, default "refresh.yml" (cold);  HOT_WORKFLOW  optional, default "hot.yml";
 *   REF           optional, default "main"
 */

export const COOLDOWN_MINUTES = 5; // between button presses
export const EVERY_MINUTES = 15; // hot runs in Quiet; cold runs in Quiet and Live
export const STALE_HOURS = 6; // a game not seen final this long after kickoff counts as final
export const SLATE_HOURS = 8; // a slate that kicked off longer ago than this no longer gets its run
export const WRITE_CAP = 950; // hot bundle writes per UTC day (the free plan allows 1,000 KV writes)
export const BUNDLE_TTL_DAYS = 7;
const API = "https://api.github.com";
const MINUTE = 60_000;
const ACTIVE = new Set(["queued", "in_progress", "waiting", "requested", "pending"]);
const RANK = { scheduled: 0, s: 0, in_progress: 1, i: 1, final: 2, f: 2 };

const memory = { hot: 0, cold: 0, button: 0 };

export function resetMemory() {
  memory.hot = 0;
  memory.cold = 0;
  memory.button = 0;
}

function json(body, status, origin) {
  const headers = { "Content-Type": "application/json", "Cache-Control": "no-store" };
  if (origin) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
    headers["Access-Control-Allow-Headers"] = "Content-Type";
    headers["Vary"] = "Origin";
  }
  return new Response(body == null ? null : JSON.stringify(body), { status, headers });
}

function github(env, fetchImpl) {
  return async (path, init = {}) => {
    const res = await fetchImpl(`${API}${path}`, {
      ...init,
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ffapp-refresh-relay",
        ...(init.body ? { "Content-Type": "application/json" } : {}),
      },
    });
    if (!res.ok) throw new Error(`GitHub ${res.status} for ${path}`);
    return res.status === 204 ? null : res.json();
  };
}

const coldWorkflow = (env) => env.WORKFLOW || "refresh.yml";
const hotWorkflow = (env) => env.HOT_WORKFLOW || "hot.yml";

async function recentRuns(gh, env, workflow) {
  return (await gh(`/repos/${env.REPO}/actions/workflows/${workflow}/runs?per_page=5`)).workflow_runs || [];
}

const anyActive = (runs) => runs.some((r) => ACTIVE.has(r.status));
const lastCreated = (runs) => runs.reduce((ms, r) => Math.max(ms, Date.parse(r.created_at) || 0), 0);

async function dispatch(gh, env, workflow, inputs) {
  await gh(`/repos/${env.REPO}/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    body: JSON.stringify(inputs ? { ref: env.REF || "main", inputs } : { ref: env.REF || "main" }),
  });
}

/* -- refresh mode ------------------------------------------------------------------------------ */

/* A game's state: the furthest along of the summary's and the latest bundle's, and final once it
   is STALE_HOURS past kickoff. */
function gameState(game, bundleGames, nowMs) {
  const seen = Math.max(RANK[game.state] ?? 0, RANK[(bundleGames || {})[game.id]] ?? 0);
  if (seen < 2 && nowMs - game.kickoff >= STALE_HOURS * 60 * MINUTE) return 2;
  return seen;
}

/* "offseason" | "live" | "quiet". Without a summary yet, Quiet: the first cold run uploads one. */
export function mode(nowMs, summary, bundleGames) {
  if (!summary) return "quiet";
  if (summary.offseason) return "offseason";
  for (const game of summary.games || []) {
    if (game.kickoff <= nowMs && gameState(game, bundleGames, nowMs) < 2) return "live";
  }
  return "quiet";
}

/* Slates whose games are all final: [{ key, kickoff }], oldest first. */
export function finalSlates(nowMs, summary, bundleGames) {
  const slates = new Map();
  for (const game of (summary && summary.games) || []) {
    const s = slates.get(game.slate) || { key: game.slate, kickoff: game.kickoff, final: true };
    s.final = s.final && gameState(game, bundleGames, nowMs) === 2;
    slates.set(game.slate, s);
  }
  return [...slates.values()].filter((s) => s.final).sort((a, b) => a.kickoff - b.kickoff);
}

/* -- KV ---------------------------------------------------------------------------------------- */

async function bundleMeta(env) {
  if (!env.LIVE) return null;
  const { value, metadata } = await env.LIVE.getWithMetadata("live", { type: "stream" });
  if (value && value.cancel) await value.cancel();
  return metadata || null;
}

async function readState(env, nowMs) {
  const summary = env.LIVE ? await env.LIVE.get("schedule", { type: "json" }) : null;
  const meta = await bundleMeta(env);
  return { summary, meta, mode: mode(nowMs, summary, meta && meta.g) };
}

const utcDay = (ms) => new Date(ms).toISOString().slice(0, 10);

/* -- the clock --------------------------------------------------------------------------------- */

/* One tick of the refresh clock; returns what it did, for the log and the tests. */
export async function tick(env, fetchImpl, nowMs) {
  const { summary, meta, mode: m } = await readState(env, nowMs);
  const did = [`mode ${m}`];
  if (m === "offseason") return did;
  const gh = github(env, fetchImpl);

  const hotRuns = await recentRuns(gh, env, hotWorkflow(env));
  const hotBusy = anyActive(hotRuns) || nowMs - memory.hot < MINUTE;
  const capped = meta && meta.day === utcDay(nowMs) && meta.n >= WRITE_CAP;
  const hotDue = m === "live" || nowMs - Math.max(lastCreated(hotRuns), memory.hot) >= EVERY_MINUTES * MINUTE;
  if (capped) did.push("hot capped");
  else if (!hotBusy && hotDue) {
    memory.hot = nowMs;
    await dispatch(gh, env, hotWorkflow(env));
    did.push("hot");
  }

  const coldRuns = await recentRuns(gh, env, coldWorkflow(env));
  const coldBusy = anyActive(coldRuns) || nowMs - memory.cold < MINUTE;
  const done = (env.LIVE && (await env.LIVE.get("slates", { type: "json" }))) || [];
  const slate = finalSlates(nowMs, summary, meta && meta.g).find(
    (s) => !done.includes(s.key) && nowMs - s.kickoff <= SLATE_HOURS * 60 * MINUTE,
  );
  if (slate) {
    // Queues behind a running cold run; the 15-minute runs wait while one is queued, so it is
    // never replaced in the queue.
    memory.cold = nowMs;
    await dispatch(gh, env, coldWorkflow(env), { mode: "slate" });
    await env.LIVE.put("slates", JSON.stringify([...done, slate.key].slice(-40)));
    did.push(`cold slate ${slate.key}`);
  } else if (!coldBusy && nowMs - Math.max(lastCreated(coldRuns), memory.cold) >= EVERY_MINUTES * MINUTE) {
    memory.cold = nowMs;
    await dispatch(gh, env, coldWorkflow(env), { mode: m });
    did.push(`cold ${m}`);
  }
  return did;
}

/* -- the button -------------------------------------------------------------------------------- */

async function lastButton(env, includeMemory = true) {
  const stored = env.LIVE ? Number(await env.LIVE.get("button")) || 0 : 0;
  return includeMemory ? Math.max(stored, memory.button) : stored;
}

/* { available, minutes, last_start, mode, reason } */
export async function buttonStatus(env, fetchImpl, nowMs, includeMemory = true) {
  const { mode: m } = await readState(env, nowMs);
  const last = await lastButton(env, includeMemory);
  const out = { available: false, minutes: 0, last_start: last ? new Date(last).toISOString() : null, mode: m, reason: null };
  if (m === "live") return { ...out, reason: "live" };
  const left = last ? last + COOLDOWN_MINUTES * MINUTE - nowMs : 0;
  if (left > 0) return { ...out, minutes: Math.ceil(left / MINUTE), reason: "cooldown" };
  const gh = github(env, fetchImpl);
  const runs = await recentRuns(gh, env, m === "offseason" ? coldWorkflow(env) : hotWorkflow(env));
  if (anyActive(runs)) return { ...out, minutes: 1, reason: "running" };
  return { ...out, available: true };
}

async function startRefresh(env, fetchImpl, nowMs, origin) {
  // Claim the button before the first await, so a second click during the calls is refused.
  const held = memory.button + COOLDOWN_MINUTES * MINUTE - nowMs;
  if (memory.button && held > 0) return json({ available: false, minutes: Math.ceil(held / MINUTE), reason: "cooldown" }, 429, origin);
  const previous = memory.button;
  memory.button = nowMs;
  let status;
  try {
    status = await buttonStatus(env, fetchImpl, nowMs, false);
  } catch (err) {
    memory.button = previous;
    throw err;
  }
  if (!status.available) {
    memory.button = previous;
    if (status.reason === "live") return json({ available: false, minutes: 0, reason: "live" }, 409, origin);
    return json({ available: false, minutes: status.minutes, reason: status.reason }, 429, origin);
  }
  const gh = github(env, fetchImpl);
  try {
    if (status.mode !== "offseason") {
      memory.hot = nowMs;
      await dispatch(gh, env, hotWorkflow(env));
    }
    memory.cold = nowMs;
    await dispatch(gh, env, coldWorkflow(env), { mode: "manual" });
  } catch (err) {
    memory.button = previous;
    throw err;
  }
  if (env.LIVE) await env.LIVE.put("button", String(nowMs));
  return json({ started: true, available: false, minutes: COOLDOWN_MINUTES, mode: status.mode }, 202, origin);
}

/* -- the bundle -------------------------------------------------------------------------------- */

function authorised(request, env) {
  return Boolean(env.HOT_TOKEN) && request.headers.get("Authorization") === `Bearer ${env.HOT_TOKEN}`;
}

function decodeMeta(header) {
  try {
    return JSON.parse(atob(header || ""));
  } catch {
    return null;
  }
}

async function putLive(request, env, nowMs) {
  const meta = decodeMeta(request.headers.get("X-Bundle-Meta"));
  if (!meta || !meta.h || !meta.t) return json({ error: "X-Bundle-Meta with h and t required" }, 400, null);
  const old = await bundleMeta(env);
  if (old && old.h === meta.h) return json({ stored: false, reason: "unchanged" }, 200, null);
  const day = utcDay(nowMs);
  const n = old && old.day === day ? (old.n || 0) + 1 : 1;
  if (n > WRITE_CAP) return json({ stored: false, reason: "daily write cap" }, 429, null);
  await env.LIVE.put("live", request.body, {
    metadata: { h: meta.h, t: meta.t, g: meta.g || {}, day, n },
    expirationTtl: BUNDLE_TTL_DAYS * 24 * 3600,
  });
  return json({ stored: true, n }, 200, null);
}

async function getLive(request, env, origin) {
  if (!env.LIVE) return json(null, 204, origin);
  const since = Date.parse(new URL(request.url).searchParams.get("since") || "") || 0;
  const { value, metadata } = await env.LIVE.getWithMetadata("live", { type: "stream" });
  if (!value || !metadata || Date.parse(metadata.t) <= since) {
    if (value && value.cancel) await value.cancel();
    return json(null, 204, origin);
  }
  const res = json(null, 200, origin);
  return new Response(value, { status: 200, headers: res.headers });
}

/* -- routing ----------------------------------------------------------------------------------- */

export async function handle(request, env, fetchImpl = fetch, nowMs = Date.now()) {
  const path = new URL(request.url).pathname;
  try {
    if (request.method === "PUT" && (path === "/live" || path === "/schedule")) {
      if (!authorised(request, env)) return json({ error: "not allowed" }, 403, null);
      if (!env.LIVE) return json({ error: "no KV namespace bound as LIVE" }, 500, null);
      if (path === "/live") return await putLive(request, env, nowMs);
      await env.LIVE.put("schedule", await request.text());
      return json({ stored: true }, 200, null);
    }
    const origin = request.headers.get("Origin");
    if (origin !== env.SITE_ORIGIN) return json({ error: "origin not allowed" }, 403, null);
    if (request.method === "OPTIONS") return json(null, 204, origin);
    if (request.method === "GET" && path === "/status") return json(await buttonStatus(env, fetchImpl, nowMs), 200, origin);
    if (request.method === "POST" && path === "/refresh") return await startRefresh(env, fetchImpl, nowMs, origin);
    if (request.method === "GET" && path === "/live") return await getLive(request, env, origin);
    return json({ error: "not found" }, 404, origin);
  } catch (err) {
    return json({ error: String(err.message || err) }, 502, request.headers.get("Origin") === env.SITE_ORIGIN ? env.SITE_ORIGIN : null);
  }
}

export default {
  fetch(request, env) {
    return handle(request, env);
  },
  scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env, fetch, Date.now()).then((did) => console.log(did.join("; "))));
  },
};
