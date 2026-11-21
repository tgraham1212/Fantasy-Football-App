/* Keeps an open page current (docs/refresh-modes.md). While the tab is visible it checks every
   60 seconds - every 30 while a game is in progress - and once when the tab becomes visible again:
   - new site code (the deployed fingerprint differs from this page's): pin a note to the bottom
     of the screen asking for a reload, and stop - new data is never swapped under old code;
   - newer deployed data (data/index.json) with the same code: drop any older live bundle and hand
     the new index to the page's reload hook, which redraws in place keeping the visitor's place;
   - a newer live bundle from the refresh relay (the hot runs' forecast and this week's game cards):
     lay its files over the deployed ones (data.js) and redraw the same way.
   Either way the refresh button is told the data arrived, with the newer of the two times.
   A local copy has no fingerprint (version.js keeps its placeholder): it checks deployed data
   only and never reads the live bundle. */

import { CODE, STAMPED } from "./version.js?v=__BUILD__";
import { dataArrived } from "./refresh.js?v=__BUILD__";
import { clearOverlay, setOverlay } from "./data.js?v=__BUILD__";

const CHECK_MS = 60_000;
const LIVE_CHECK_MS = 30_000;
const state = { index: null, loaded: null, bundleAt: null, live: false, reload: null, relay: null, timer: null, busy: false, outdated: false };

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

const ms = (iso) => (iso ? new Date(iso).getTime() : 0);
const newer = (a, b) => Boolean(a) && ms(a) > ms(b);
const latest = () => (newer(state.bundleAt, state.loaded) ? state.bundleAt : state.loaded);

function showVersionNote() {
  if (document.getElementById("version-note")) return;
  const note = document.createElement("div");
  note.id = "version-note";
  note.className = "version-note";
  note.setAttribute("role", "status");
  note.innerHTML = `<span>${/*copy:MSG-07*/"A new version of the site is available."}</span><button type="button" class="nav-link">Refresh</button>`;
  note.querySelector("button").addEventListener("click", () => location.reload());
  document.body.appendChild(note);
}

/* The latest bundle when it is newer than what the page shows, else null. Never throws. */
async function fetchBundle() {
  if (!state.relay) return null;
  try {
    const since = latest();
    const res = await fetch(`${state.relay}/live${since ? `?since=${encodeURIComponent(since)}` : ""}`, { cache: "no-store" });
    if (res.status !== 200) return null;
    const bundle = await res.json();
    return bundle && bundle.files && newer(bundle.generated_at, latest()) ? bundle : null;
  } catch (e) {
    return null; // relay unreachable: keep what the page shows
  }
}

async function check() {
  if (state.busy || state.outdated || document.visibilityState !== "visible") return;
  state.busy = true;
  try {
    if (STAMPED) {
      const version = await fetchJson("version.json").catch(() => null);
      if (version && version.code && version.code !== CODE) {
        state.outdated = true;
        clearTimeout(state.timer);
        showVersionNote();
        return;
      }
    }
    const index = await fetchJson("data/index.json");
    if (newer(index.last_refresh, state.loaded)) {
      state.index = index;
      state.loaded = index.last_refresh;
      if (!newer(state.bundleAt, state.loaded)) {
        clearOverlay(); // the deployed data is newer than the bundle
        state.bundleAt = null;
      }
      await state.reload(index);
      dataArrived(latest());
    }
    const bundle = STAMPED ? await fetchBundle() : null;
    if (bundle) {
      setOverlay(bundle.files);
      state.bundleAt = bundle.generated_at;
      state.live = Object.values(bundle.games || {}).includes("in_progress");
      await state.reload(state.index);
      dataArrived(latest());
    }
  } catch (e) {
    /* offline or mid-deploy: try again at the next check */
  } finally {
    state.busy = false;
    schedule();
  }
}

function schedule() {
  clearTimeout(state.timer);
  if (!state.outdated) state.timer = setTimeout(check, state.live ? LIVE_CHECK_MS : CHECK_MS);
}

/* `index` is the loaded data/index.json; `reload(index)` redraws the page from new data. */
export function initUpdates(index, reload) {
  state.index = index;
  state.loaded = (index && index.last_refresh) || null;
  state.relay = index && index.refresh_url ? index.refresh_url.replace(/\/$/, "") : null;
  state.reload = reload;
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") check(); });
  if (STAMPED && state.relay) check(); // a newer bundle than the deployed data shows straight away
  else schedule();
}
