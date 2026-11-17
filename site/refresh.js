/* The "Refresh" button: asks the refresh relay (a Cloudflare Worker, see relay/README.md) to start
   the data refresh. Shown only when the export carried a relay address. */

const POLL_MS = 60_000;
const box = () => document.getElementById("refresh-box");

const state = { url: null, lastRefresh: null, held: 0, message: null, busy: false, timer: null };

function minutesSince(iso) {
  if (!iso) return null;
  return Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000));
}

function agoText() {
  const m = minutesSince(state.lastRefresh);
  if (m == null) return "";
  if (m < 1) return "Updated just now";
  if (m < 60) return `Updated ${m} min ago`;
  const h = Math.floor(m / 60);
  return h < 48 ? `Updated ${h} h ago` : `Updated ${Math.floor(h / 24)} days ago`;
}

function render() {
  const btn = document.getElementById("refresh-btn");
  const note = document.getElementById("refresh-note");
  btn.disabled = state.busy || state.held > 0;
  note.textContent = state.message || (state.held > 0 ? `Available in ${state.held} min` : agoText());
}

async function call(method, path) {
  const res = await fetch(`${state.url}${path}`, { method, cache: "no-store" });
  const body = await res.json().catch(() => ({}));
  return { status: res.status, body };
}

async function poll() {
  try {
    const { status, body } = await call("GET", "/status");
    if (status === 200) state.held = body.available ? 0 : body.minutes || 0;
  } catch (e) {
    state.held = 0; // relay unreachable: keep the button usable and say when the data was refreshed
  }
  render();
}

async function refresh() {
  state.busy = true;
  state.message = "Starting a refresh…";
  render();
  try {
    const { status, body } = await call("POST", "/refresh");
    if (status === 202) {
      state.held = body.minutes || 15;
      state.message = "Refresh started. The site updates in about 5 minutes.";
    } else if (status === 429) {
      state.held = body.minutes || 1;
      state.message = null;
    } else {
      state.message = "Could not start a refresh. Try again later.";
    }
  } catch (e) {
    state.message = "Could not reach the refresh service. Try again later.";
  }
  state.busy = false;
  render();
}

/* `index` is data/index.json: { refresh_url, last_refresh, ... }. */
export function initRefresh(index) {
  const el = box();
  if (!el || !index || !index.refresh_url) return;
  state.url = index.refresh_url.replace(/\/$/, "");
  state.lastRefresh = index.last_refresh || null;
  el.hidden = false;
  document.getElementById("refresh-btn").addEventListener("click", refresh);
  render();
  poll();
  clearInterval(state.timer);
  state.timer = setInterval(() => {
    if (state.held > 0) state.held -= 1;
    if (state.held === 0 && state.message && !state.busy) state.message = null;
    render();
    poll();
  }, POLL_MS);
}
