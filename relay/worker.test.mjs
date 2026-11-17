import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";

import { COOLDOWN_MINUTES, handle, resetMemory } from "./worker.js";

const ENV = { GITHUB_TOKEN: "t", REPO: "o/r", SITE_ORIGIN: "https://site.example" };
const NOW = Date.parse("2026-11-22T18:00:00Z");
const minutesAgo = (m) => new Date(NOW - m * 60_000).toISOString();

/* A fake GitHub: `runs` for the run list, `jobs[id]` per run; records every call. */
function fakeGitHub({ runs = [], jobs = {}, dispatchStatus = 204 } = {}) {
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url, method: init.method || "GET", body: init.body, auth: init.headers?.Authorization });
    if (url.includes("/dispatches")) return new Response(null, { status: dispatchStatus });
    const m = url.match(/\/runs\/(\d+)\/jobs/);
    if (m) return Response.json({ jobs: jobs[m[1]] || [] });
    if (url.includes("/runs?")) return Response.json({ workflow_runs: runs });
    return new Response("nope", { status: 404 });
  };
  return { fetchImpl, calls };
}

const req = (method, path, origin = ENV.SITE_ORIGIN) =>
  new Request(`https://relay.example${path}`, { method, headers: origin ? { Origin: origin } : {} });

beforeEach(() => resetMemory());

test("available when no refresh started in the window", async () => {
  const { fetchImpl } = fakeGitHub();
  const res = await handle(req("GET", "/status"), ENV, fetchImpl, NOW);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { available: true, minutes: 0, last_start: null });
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), ENV.SITE_ORIGIN);
});

test("held with the minutes left after a scheduled refresh started 6 minutes ago", async () => {
  const { fetchImpl } = fakeGitHub({
    runs: [{ id: 1, event: "schedule", created_at: minutesAgo(7) }],
    jobs: { 1: [{ name: "gate", conclusion: "success" }, { name: "refresh", status: "in_progress", started_at: minutesAgo(6) }] },
  });
  const body = await (await handle(req("GET", "/status"), ENV, fetchImpl, NOW)).json();
  assert.equal(body.available, false);
  assert.equal(body.minutes, 9);
  const refused = await handle(req("POST", "/refresh"), ENV, fetchImpl, NOW);
  assert.equal(refused.status, 429);
  assert.deepEqual(await refused.json(), { available: false, minutes: 9 });
});

test("a queued manual run counts from when it was created", async () => {
  const { fetchImpl } = fakeGitHub({ runs: [{ id: 2, event: "workflow_dispatch", created_at: minutesAgo(1), status: "queued" }] });
  const body = await (await handle(req("GET", "/status"), ENV, fetchImpl, NOW)).json();
  assert.deepEqual([body.available, body.minutes], [false, 14]);
});

test("an hourly check that skipped the refresh does not count", async () => {
  const { fetchImpl } = fakeGitHub({
    runs: [{ id: 3, event: "schedule", created_at: minutesAgo(2) }],
    jobs: { 3: [{ name: "gate", conclusion: "success" }, { name: "refresh", status: "completed", conclusion: "skipped" }] },
  });
  const body = await (await handle(req("GET", "/status"), ENV, fetchImpl, NOW)).json();
  assert.equal(body.available, true);
});

test("a refresh starts the workflow on main, and a second click seconds later is refused", async () => {
  const { fetchImpl, calls } = fakeGitHub();
  const first = await handle(req("POST", "/refresh"), ENV, fetchImpl, NOW);
  assert.equal(first.status, 202);
  assert.deepEqual(await first.json(), { started: true, available: false, minutes: COOLDOWN_MINUTES });
  const dispatch = calls.find((c) => c.url.includes("/dispatches"));
  assert.equal(dispatch.method, "POST");
  assert.match(dispatch.url, /\/repos\/o\/r\/actions\/workflows\/refresh\.yml\/dispatches$/);
  assert.deepEqual(JSON.parse(dispatch.body), { ref: "main" });
  assert.equal(dispatch.auth, "Bearer t");
  // GitHub has not listed the new run yet; the Worker's own memory still refuses the second click
  const second = await handle(req("POST", "/refresh"), ENV, fetchImpl, NOW + 5_000);
  assert.equal(second.status, 429);
  assert.equal(calls.filter((c) => c.url.includes("/dispatches")).length, 1);
});

test("a failed dispatch does not hold the button", async () => {
  const { fetchImpl } = fakeGitHub({ dispatchStatus: 500 });
  const res = await handle(req("POST", "/refresh"), ENV, fetchImpl, NOW);
  assert.equal(res.status, 502);
  const after = await (await handle(req("GET", "/status"), ENV, fakeGitHub().fetchImpl, NOW)).json();
  assert.equal(after.available, true);
});

test("requests from another origin are refused without calling GitHub", async () => {
  const { fetchImpl, calls } = fakeGitHub();
  const res = await handle(req("POST", "/refresh", "https://evil.example"), ENV, fetchImpl, NOW);
  assert.equal(res.status, 403);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), null);
  assert.equal(calls.length, 0);
  assert.equal((await handle(req("GET", "/status", null), ENV, fetchImpl, NOW)).status, 403);
});

test("preflight and unknown paths", async () => {
  const { fetchImpl } = fakeGitHub();
  assert.equal((await handle(req("OPTIONS", "/refresh"), ENV, fetchImpl, NOW)).status, 204);
  assert.equal((await handle(req("GET", "/nope"), ENV, fetchImpl, NOW)).status, 404);
});

test("the window ends 15 minutes after the last start", async () => {
  const { fetchImpl } = fakeGitHub({ runs: [{ id: 4, event: "workflow_dispatch", created_at: minutesAgo(15) }] });
  const body = await (await handle(req("GET", "/status"), ENV, fetchImpl, NOW)).json();
  assert.equal(body.available, true);
});
