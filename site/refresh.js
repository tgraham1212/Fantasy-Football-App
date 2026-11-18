/* The "Refresh Data" button: asks the refresh relay (a Cloudflare Worker, see relay/README.md) to
   start the data refresh. Shown only when the export carried a relay address. The note under it
   stays short (at most 22 characters) so it never moves the layout; the full sentence is its
   tooltip. The update check (updates.js) calls dataArrived() when new data is swapped in. */

const POLL_MS = 60_000;
const GIVE_UP_MS = 20 * 60_000; // a started refresh that has not landed by then did not finish
const box = () => document.getElementById("refresh-box");

const state = { url: null, lastRefresh: null, held: 0, note: null, busy: false, timer: null, waitTimer: null };

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

/* A transient message: short text for the note, the full sentence for the tooltip. */
function say(short, full, sticky = false) {
  state.note = { short, full: full || short, sticky };
}

function render() {
  const btn = document.getElementById("refresh-btn");
  const note = document.getElementById("refresh-note");
  if (!btn || !note) return;
  btn.disabled = state.busy || state.held > 0;
  let short, full;
  if (state.note) ({ short, full } = state.note);
  else if (state.held > 0) {
    short = `Available in ${state.held} min`;
    full = /*copy:MSG-01*/`A refresh ran recently. The next one can start in ${state.held} min.`;
  } else {
    short = agoText();
    full = state.lastRefresh ? /*copy:MSG-02*/`Data last refreshed ${new Date(state.lastRefresh).toLocaleString()}.` : "";
  }
  note.textContent = short;
  if (full) note.title = full; else note.removeAttribute("title");
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

function waitForData() {
  clearTimeout(state.waitTimer);
  state.waitTimer = setTimeout(() => {
    state.waitTimer = null;
    say("Refresh didn't finish", /*copy:MSG-03*/"No new data arrived within 20 minutes of the refresh starting. Try again later.", true);
    render();
  }, GIVE_UP_MS);
}

async function refresh() {
  state.busy = true;
  say("Starting…", /*copy:MSG-10*/"Asking for a data refresh…");
  render();
  try {
    const { status, body } = await call("POST", "/refresh");
    if (status === 202) {
      state.held = body.minutes || 15;
      say(/*copy:MSG-11*/"Started, back in ~5 min", /*copy:MSG-04*/"Refresh started. The new data shows here by itself in about 5 minutes.");
      waitForData();
    } else if (status === 429) {
      state.held = body.minutes || 1;
      state.note = null;
    } else {
      say(/*copy:MSG-12*/"Couldn't start, try later", /*copy:MSG-05*/"Could not start a refresh. Try again later.");
    }
  } catch (e) {
    say(/*copy:MSG-13*/"Couldn't start, try later", /*copy:MSG-06*/"Could not reach the refresh service. Try again later.");
  }
  state.busy = false;
  render();
}

/* Called by the update check when newer data has been swapped into the page. */
export function dataArrived(lastRefresh) {
  state.lastRefresh = lastRefresh || state.lastRefresh;
  clearTimeout(state.waitTimer);
  state.waitTimer = null;
  state.note = null;
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
    if (state.held === 0 && state.note && !state.busy && !state.waitTimer && !state.note.sticky) state.note = null;
    render();
    poll();
  }, POLL_MS);
}
