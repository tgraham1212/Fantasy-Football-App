/* Keeps an open page current. Once a minute while the tab is visible (and once when it becomes
   visible again) it checks version.json and data/index.json:
   - new site code (the deployed fingerprint differs from this page's): pin a note to the bottom
     of the screen asking for a reload, and stop - new data is never swapped under old code;
   - new data with the same code: hand the new index to the page's reload hook, which redraws in
     place keeping the visitor's place, then tell the refresh button the data arrived.
   A local copy has no fingerprint (version.js keeps its placeholder) and checks data only. */

import { CODE, STAMPED } from "./version.js?v=__BUILD__";
import { dataArrived } from "./refresh.js?v=__BUILD__";

const CHECK_MS = 60_000;
const state = { loaded: null, reload: null, timer: null, busy: false, outdated: false };

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

const newer = (a, b) => Boolean(a) && (!b || new Date(a).getTime() > new Date(b).getTime());

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

async function check() {
  if (state.busy || state.outdated || document.visibilityState !== "visible") return;
  state.busy = true;
  try {
    if (STAMPED) {
      const version = await fetchJson("version.json").catch(() => null);
      if (version && version.code && version.code !== CODE) {
        state.outdated = true;
        clearInterval(state.timer);
        showVersionNote();
        return;
      }
    }
    const index = await fetchJson("data/index.json");
    if (newer(index.last_refresh, state.loaded)) {
      await state.reload(index);
      state.loaded = index.last_refresh;
      dataArrived(index.last_refresh);
    }
  } catch (e) {
    /* offline or mid-deploy: try again next minute */
  } finally {
    state.busy = false;
  }
}

/* `lastRefresh` is the loaded index's last_refresh; `reload(index)` redraws the page from new data. */
export function initUpdates(lastRefresh, reload) {
  state.loaded = lastRefresh || null;
  state.reload = reload;
  clearInterval(state.timer);
  state.timer = setInterval(check, CHECK_MS);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") check(); });
}
