import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";

import { COOLDOWN_MINUTES, WRITE_CAP, finalSlates, handle, mode, resetMemory, tick } from "./worker.js";

const NOW = Date.parse("2026-11-22T18:30:00Z");
const MIN = 60_000;
const ago = (m) => new Date(NOW - m * MIN).toISOString();

/* An in-memory KV namespace with metadata, counting writes. */
function fakeKV(initial = {}) {
  const store = new Map(Object.entries(initial).map(([k, v]) => [k, typeof v === "object" && v.value !== undefined ? v : { value: v }]));
  return {
    store,
    writes: 0,
    async get(key, opts) {
      const e = store.get(key);
      if (!e) return null;
      return opts && opts.type === "json" ? JSON.parse(e.value) : e.value;
    },
    async getWithMetadata(key) {
      const e = store.get(key);
      if (!e) return { value: null, metadata: null };
      return { value: { cancel() {}, text: e.value }, metadata: e.metadata || null };
    },
    async put(key, value, opts = {}) {
      this.writes += 1;
      const text = typeof value === "string" ? value : await new Response(value).text();
      store.set(key, { value: text, metadata: opts.metadata, ttl: opts.expirationTtl });
    },
  };
}

/* A fake GitHub: recent runs per workflow file; records every call. */
function fakeGitHub({ hot = [], cold = [], dispatchStatus = 204 } = {}) {
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url, method: init.method || "GET", body: init.body ? JSON.parse(init.body) : null, auth: init.headers?.Authorization });
    if (url.includes("/dispatches")) return new Response(null, { status: dispatchStatus });
    if (url.includes("/workflows/hot.yml/runs")) return Response.json({ workflow_runs: hot });
    if (url.includes("/workflows/refresh.yml/runs")) return Response.json({ workflow_runs: cold });
    return new Response("nope", { status: 404 });
  };
  const dispatched = () => calls.filter((c) => c.url.includes("/dispatches")).map((c) => `${c.url.match(/workflows\/([^/]+)/)[1]}${c.body.inputs ? ":" + c.body.inputs.mode : ""}`);
  return { fetchImpl, calls, dispatched };
}

const run = (createdMinutesAgo, status = "completed") => ({ created_at: ago(createdMinutesAgo), status });

const kick = (iso) => Date.parse(iso);
const EARLY = "2026-11-22T18:00:00+00:00";
const LATE = "2026-11-22T21:05:00+00:00";
const SUMMARY = {
  season: "2026", week: 11, offseason: false,
  games: [
    { id: "2026-11-NYJ@NE", week: 11, kickoff: kick(EARLY), slate: EARLY, state: "scheduled" },
    { id: "2026-11-KC@BUF", week: 11, kickoff: kick(EARLY), slate: EARLY, state: "scheduled" },
    { id: "2026-11-SF@SEA", week: 11, kickoff: kick(LATE), slate: LATE, state: "scheduled" },
  ],
};

const SITE = "https://site.example";
function env(kv = fakeKV({ schedule: JSON.stringify(SUMMARY) })) {
  return { GITHUB_TOKEN: "t", HOT_TOKEN: "hot-secret", REPO: "o/r", SITE_ORIGIN: SITE, LIVE: kv };
}

const req = (method, path, { origin = SITE, headers = {}, body } = {}) =>
  new Request(`https://relay.example${path}`, { method, body, headers: { ...(origin ? { Origin: origin } : {}), ...headers } });

const bundleEntry = (g, extra = {}) => ({ value: "{}", metadata: { h: "h0", t: ago(2), g, day: "2026-11-22", n: 10, ...extra } });

beforeEach(() => resetMemory());

/* -- modes and transitions --------------------------------------------------------------------- */

test("modes: off-season, quiet before kickoff, live after kickoff, quiet when all final", () => {
  assert.equal(mode(NOW, { ...SUMMARY, offseason: true }, {}), "offseason"); // 4: championship weeks scored
  assert.equal(mode(kick(EARLY) - MIN, SUMMARY, {}), "quiet"); // 1: in season, nothing kicked off
  assert.equal(mode(NOW, SUMMARY, {}), "live"); // 2: a kickoff time passed
  const allFinal = { "2026-11-NYJ@NE": "f", "2026-11-KC@BUF": "f", "2026-11-SF@SEA": "f" };
  assert.equal(mode(kick(LATE) + 200 * MIN, SUMMARY, allFinal), "quiet"); // 3: every game that kicked off is final
  assert.equal(mode(NOW, null, null), "quiet", "no summary yet: Quiet, so a cold run uploads one");
});

test("live stays live while the late slate plays, after the early slate is final", () => {
  const early = { "2026-11-NYJ@NE": "f", "2026-11-KC@BUF": "f", "2026-11-SF@SEA": "i" };
  assert.equal(mode(kick(LATE) + 30 * MIN, SUMMARY, early), "live");
  assert.deepEqual(finalSlates(kick(LATE) + 30 * MIN, SUMMARY, early).map((s) => s.key), [EARLY]); // 5
});

test("a game not seen final 6 hours after kickoff counts as final", () => {
  assert.equal(mode(kick(LATE) + 6 * 60 * MIN, SUMMARY, {}), "quiet");
  assert.equal(mode(kick(LATE) + 6 * 60 * MIN - MIN, SUMMARY, { "2026-11-NYJ@NE": "f", "2026-11-KC@BUF": "f" }), "live");
});

/* -- the clock --------------------------------------------------------------------------------- */

test("live: starts a hot run when none is going, and a cold run every 15 minutes in live mode", async () => {
  const gh = fakeGitHub({ hot: [run(2)], cold: [run(16)] });
  assert.deepEqual(await tick(env(), gh.fetchImpl, NOW), ["mode live", "hot", "cold live"]);
  assert.deepEqual(gh.dispatched(), ["hot.yml", "refresh.yml:live"]);
});

test("live: no second hot run while one is queued or running, and none twice in a minute", async () => {
  const busy = fakeGitHub({ hot: [run(1, "in_progress")], cold: [run(3)] });
  assert.deepEqual(await tick(env(), busy.fetchImpl, NOW), ["mode live"]);
  const idle = fakeGitHub({ hot: [run(3)], cold: [run(3)] });
  await tick(env(), idle.fetchImpl, NOW);
  await tick(env(), idle.fetchImpl, NOW + 20_000); // GitHub has not listed the new run yet
  assert.deepEqual(idle.dispatched(), ["hot.yml"]);
});

test("quiet: hot and cold runs every 15 minutes", async () => {
  const before = kick(EARLY) - 120 * MIN;
  const recent = fakeGitHub({ hot: [{ created_at: new Date(before - 10 * MIN).toISOString(), status: "completed" }], cold: [{ created_at: new Date(before - 10 * MIN).toISOString(), status: "completed" }] });
  assert.deepEqual(await tick(env(), recent.fetchImpl, before), ["mode quiet"]);
  const due = fakeGitHub({ hot: [{ created_at: new Date(before - 15 * MIN).toISOString(), status: "completed" }], cold: [] });
  assert.deepEqual(await tick(env(), due.fetchImpl, before), ["mode quiet", "hot", "cold quiet"]);
});

test("off-season: the clock starts nothing", async () => {
  const gh = fakeGitHub();
  const kv = fakeKV({ schedule: JSON.stringify({ ...SUMMARY, offseason: true, games: [] }) });
  assert.deepEqual(await tick(env(kv), gh.fetchImpl, NOW), ["mode offseason"]);
  assert.equal(gh.calls.length, 0);
});

test("a final slate starts one cold run in slate mode, once", async () => {
  const at = kick(LATE) + 20 * MIN;
  const kv = fakeKV({ schedule: JSON.stringify(SUMMARY), live: bundleEntry({ "2026-11-NYJ@NE": "f", "2026-11-KC@BUF": "f", "2026-11-SF@SEA": "i" }) });
  const gh = fakeGitHub({ hot: [run(0, "in_progress")], cold: [{ created_at: new Date(at - 5 * MIN).toISOString(), status: "in_progress" }] });
  assert.deepEqual(await tick(env(kv), gh.fetchImpl, at), ["mode live", `cold slate ${EARLY}`]);
  assert.deepEqual(JSON.parse(kv.store.get("slates").value), [EARLY]);
  resetMemory();
  const later = fakeGitHub({ hot: [run(0, "in_progress")], cold: [{ created_at: new Date(at).toISOString(), status: "in_progress" }] });
  assert.deepEqual(await tick(env(kv), later.fetchImpl, at + 2 * MIN), ["mode live"]);
});

test("hot runs stop at the daily write cap; cold runs carry on", async () => {
  const kv = fakeKV({ schedule: JSON.stringify(SUMMARY), live: bundleEntry({}, { n: WRITE_CAP }) });
  const gh = fakeGitHub({ hot: [run(3)], cold: [run(20)] });
  assert.deepEqual(await tick(env(kv), gh.fetchImpl, NOW), ["mode live", "hot capped", "cold live"]);
});

/* -- the button -------------------------------------------------------------------------------- */

const QUIET_AT = kick(EARLY) - 120 * MIN;

test("quiet: the button starts a hot run and a manual cold run, then holds for 5 minutes", async () => {
  const gh = fakeGitHub({ hot: [run(300)], cold: [run(300)] });
  const e = env();
  const res = await handle(req("POST", "/refresh"), e, gh.fetchImpl, QUIET_AT);
  assert.equal(res.status, 202);
  assert.deepEqual(gh.dispatched(), ["hot.yml", "refresh.yml:manual"]);
  assert.equal(e.LIVE.store.get("button").value, String(QUIET_AT));
  const again = await handle(req("POST", "/refresh"), e, gh.fetchImpl, QUIET_AT + 2 * MIN);
  assert.equal(again.status, 429);
  assert.deepEqual(await again.json(), { available: false, minutes: 3, reason: "cooldown" });
  const status = await (await handle(req("GET", "/status"), e, gh.fetchImpl, QUIET_AT + 2 * MIN)).json();
  assert.equal(status.reason, "cooldown");
  assert.equal(status.minutes, COOLDOWN_MINUTES - 2);
});

test("two clicks at once start one refresh", async () => {
  const gh = fakeGitHub({ hot: [run(300)], cold: [run(300)] });
  const e = env();
  const [a, b] = await Promise.all([handle(req("POST", "/refresh"), e, gh.fetchImpl, QUIET_AT), handle(req("POST", "/refresh"), e, gh.fetchImpl, QUIET_AT + 3000)]);
  assert.deepEqual([a.status, b.status].sort(), [202, 429]);
  assert.equal(gh.dispatched().filter((d) => d === "hot.yml").length, 1);
});

test("the button is held while a hot run is going", async () => {
  const gh = fakeGitHub({ hot: [run(1, "in_progress")] });
  const body = await (await handle(req("GET", "/status"), env(), gh.fetchImpl, QUIET_AT)).json();
  assert.deepEqual({ available: body.available, reason: body.reason, mode: body.mode }, { available: false, reason: "running", mode: "quiet" });
});

test("live: the button is held and a refresh is refused", async () => {
  const gh = fakeGitHub();
  const status = await (await handle(req("GET", "/status"), env(), gh.fetchImpl, NOW)).json();
  assert.deepEqual({ available: status.available, reason: status.reason, mode: status.mode }, { available: false, reason: "live", mode: "live" });
  const res = await handle(req("POST", "/refresh"), env(), gh.fetchImpl, NOW);
  assert.equal(res.status, 409);
  assert.equal(gh.dispatched().length, 0);
});

test("off-season: the button starts a cold run only", async () => {
  const gh = fakeGitHub({ cold: [run(300)] });
  const kv = fakeKV({ schedule: JSON.stringify({ ...SUMMARY, offseason: true, games: [] }) });
  assert.equal((await handle(req("POST", "/refresh"), env(kv), gh.fetchImpl, NOW)).status, 202);
  assert.deepEqual(gh.dispatched(), ["refresh.yml:manual"]);
});

test("a failed dispatch does not hold the button", async () => {
  const gh = fakeGitHub({ dispatchStatus: 500 });
  const e = env();
  assert.equal((await handle(req("POST", "/refresh"), e, gh.fetchImpl, QUIET_AT)).status, 502);
  const status = await (await handle(req("GET", "/status"), e, fakeGitHub().fetchImpl, QUIET_AT)).json();
  assert.equal(status.available, true);
});

test("browser requests from another origin are refused without calling GitHub", async () => {
  const gh = fakeGitHub();
  for (const [m, p] of [["GET", "/status"], ["POST", "/refresh"], ["GET", "/live"]]) {
    const res = await handle(req(m, p, { origin: "https://evil.example" }), env(), gh.fetchImpl, NOW);
    assert.equal(res.status, 403);
  }
  assert.equal(gh.calls.length, 0);
});

test("preflight and unknown paths", async () => {
  assert.equal((await handle(req("OPTIONS", "/refresh"), env(), fakeGitHub().fetchImpl, NOW)).status, 204);
  assert.equal((await handle(req("GET", "/nope"), env(), fakeGitHub().fetchImpl, NOW)).status, 404);
});

/* -- the bundle -------------------------------------------------------------------------------- */

const meta = (h, t = ago(0), g = { "2026-11-NYJ@NE": "i" }) => btoa(JSON.stringify({ h, t, g }));
const put = (path, body, headers) => req("PUT", path, { origin: null, body, headers: { Authorization: "Bearer hot-secret", ...headers } });

test("the hot run stores one bundle with its game states; an unchanged bundle is not written", async () => {
  const e = env();
  const res = await handle(put("/live", '{"files":{}}', { "X-Bundle-Meta": meta("h1") }), e, fetch, NOW);
  assert.deepEqual(await res.json(), { stored: true, n: 1 });
  const entry = e.LIVE.store.get("live");
  assert.equal(entry.value, '{"files":{}}');
  assert.deepEqual(entry.metadata.g, { "2026-11-NYJ@NE": "i" });
  assert.equal(entry.ttl, 7 * 24 * 3600);
  const same = await handle(put("/live", '{"files":{}}', { "X-Bundle-Meta": meta("h1") }), e, fetch, NOW + MIN);
  assert.deepEqual(await same.json(), { stored: false, reason: "unchanged" });
  assert.equal(e.LIVE.writes, 1);
});

test("bundle writes are counted per UTC day and stop at the cap", async () => {
  const kv = fakeKV({ schedule: JSON.stringify(SUMMARY), live: bundleEntry({}, { n: WRITE_CAP }) });
  const res = await handle(put("/live", "{}", { "X-Bundle-Meta": meta("new") }), env(kv), fetch, NOW);
  assert.equal(res.status, 429);
  const nextDay = await handle(put("/live", "{}", { "X-Bundle-Meta": meta("new") }), env(kv), fetch, NOW + 24 * 60 * MIN);
  assert.deepEqual(await nextDay.json(), { stored: true, n: 1 });
});

test("writes need the hot run's secret", async () => {
  const e = env();
  const res = await handle(req("PUT", "/live", { origin: null, body: "{}", headers: { "X-Bundle-Meta": meta("x") } }), e, fetch, NOW);
  assert.equal(res.status, 403);
  const wrong = await handle(req("PUT", "/schedule", { origin: null, body: "{}", headers: { Authorization: "Bearer guess" } }), e, fetch, NOW);
  assert.equal(wrong.status, 403);
  assert.equal(e.LIVE.writes, 0);
});

test("the schedule summary is stored for the clock", async () => {
  const e = env(fakeKV());
  const res = await handle(put("/schedule", JSON.stringify(SUMMARY), {}), e, fetch, NOW);
  assert.equal(res.status, 200);
  assert.equal(mode(NOW, await e.LIVE.get("schedule", { type: "json" }), {}), "live");
});

test("the page gets the bundle, or 204 when none is newer than it has", async () => {
  const t = ago(1);
  const kv = fakeKV({ schedule: JSON.stringify(SUMMARY), live: { value: '{"b":1}', metadata: { h: "h", t, g: {} } } });
  kv.getWithMetadata = async (key) => {
    const e = kv.store.get(key);
    return e ? { value: new Response(e.value).body, metadata: e.metadata } : { value: null, metadata: null };
  };
  const res = await handle(req("GET", "/live"), env(kv), fetch, NOW);
  assert.equal(res.status, 200);
  assert.equal(await res.text(), '{"b":1}');
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), SITE);
  const none = await handle(req("GET", `/live?since=${encodeURIComponent(t)}`), env(kv), fetch, NOW);
  assert.equal(none.status, 204);
  assert.equal((await handle(req("GET", "/live"), env(fakeKV()), fetch, NOW)).status, 204);
});
