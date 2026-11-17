/*
 * Refresh relay: a Cloudflare Worker that lets the published site start the "Refresh odds" workflow.
 *
 * GET  /status   -> { available, minutes, last_start }   (minutes until a refresh is allowed; 0 when available)
 * POST /refresh  -> 202 { started: true }  or 429 { available: false, minutes }
 *
 * Only requests from SITE_ORIGIN are answered. A refresh is refused within 15 minutes of the start of
 * the last refresh run, scheduled or manual, queued or running. GitHub is the source of truth: the
 * workflow's runs from the last 15 minutes are listed and a run counts when it is a manual dispatch or
 * when its `refresh` job was not skipped (hourly checks that decided not to refresh do not count). A
 * dispatch can take a few seconds to show up in that list, so the Worker also remembers its own last
 * dispatch.
 *
 * Settings (Cloudflare dashboard -> the Worker -> Settings -> Variables and secrets):
 *   GITHUB_TOKEN  secret: fine-grained token, this repository only, "Actions: Read and write"
 *   REPO          e.g. "tgraham1212/Fantasy-Football-App"
 *   SITE_ORIGIN   e.g. "https://tgraham1212.github.io"
 *   WORKFLOW      optional, default "refresh.yml";  REF  optional, default "main"
 */

export const COOLDOWN_MINUTES = 15;
const API = "https://api.github.com";

let lastDispatchMs = 0; // per Worker instance; GitHub's own run list covers the rest

export function resetMemory() {
  lastDispatchMs = 0;
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

/* Start time (ms) of the latest refresh run in the cooldown window, or 0. */
export async function lastRefreshStart(env, fetchImpl, nowMs) {
  const gh = github(env, fetchImpl);
  const workflow = env.WORKFLOW || "refresh.yml";
  const since = new Date(nowMs - COOLDOWN_MINUTES * 60_000).toISOString();
  const runs = (await gh(`/repos/${env.REPO}/actions/workflows/${workflow}/runs?per_page=20&created=%3E%3D${encodeURIComponent(since)}`)).workflow_runs || [];
  let latest = 0;
  for (const run of runs) {
    let start = null;
    if (run.event === "workflow_dispatch") {
      start = Date.parse(run.created_at);
    } else {
      const jobs = (await gh(`/repos/${env.REPO}/actions/runs/${run.id}/jobs`)).jobs || [];
      const refresh = jobs.find((j) => j.name === "refresh");
      if (refresh && refresh.conclusion !== "skipped") start = Date.parse(refresh.started_at || run.created_at);
    }
    if (start && start > latest) latest = start;
  }
  return Math.max(latest, lastDispatchMs);
}

function minutesLeft(lastMs, nowMs) {
  if (!lastMs) return 0;
  const left = lastMs + COOLDOWN_MINUTES * 60_000 - nowMs;
  return left > 0 ? Math.ceil(left / 60_000) : 0;
}

export async function handle(request, env, fetchImpl = fetch, nowMs = Date.now()) {
  const origin = request.headers.get("Origin");
  if (origin !== env.SITE_ORIGIN) return json({ error: "origin not allowed" }, 403, null);
  if (request.method === "OPTIONS") return json(null, 204, origin);
  const path = new URL(request.url).pathname;
  try {
    if (request.method === "GET" && path === "/status") {
      const last = await lastRefreshStart(env, fetchImpl, nowMs);
      const minutes = minutesLeft(last, nowMs);
      return json({ available: minutes === 0, minutes, last_start: last ? new Date(last).toISOString() : null }, 200, origin);
    }
    if (request.method === "POST" && path === "/refresh") {
      const last = await lastRefreshStart(env, fetchImpl, nowMs);
      const minutes = minutesLeft(last, nowMs);
      if (minutes > 0) return json({ available: false, minutes }, 429, origin);
      lastDispatchMs = nowMs; // claim before the call, so a second click during it is refused
      try {
        await github(env, fetchImpl)(`/repos/${env.REPO}/actions/workflows/${env.WORKFLOW || "refresh.yml"}/dispatches`, {
          method: "POST",
          body: JSON.stringify({ ref: env.REF || "main" }),
        });
      } catch (err) {
        lastDispatchMs = 0;
        throw err;
      }
      return json({ started: true, available: false, minutes: COOLDOWN_MINUTES }, 202, origin);
    }
    return json({ error: "not found" }, 404, origin);
  } catch (err) {
    return json({ error: String(err.message || err) }, 502, origin);
  }
}

export default {
  fetch(request, env) {
    return handle(request, env);
  },
};
