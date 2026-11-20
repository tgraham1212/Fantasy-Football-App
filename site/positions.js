/* Positional Rankings page: one dot chart per position, a row per manager, a dot per rostered
   player at his regular-season points per game, and the WAR replacement level as a dotted line. */

const ORDER = ["QB", "RB", "WR", "TE", "K", "DEF"];
const LABEL = { QB: "Quarterbacks", RB: "Running backs", WR: "Wide receivers", TE: "Tight ends", K: "Kickers", DEF: "Defenses" };
const ROW = 38; // px per manager row, the minimum (two-line labels): rows grow to fit the widest lane spread
const TOP = 40; // px above the first row: replacement label and axis ticks
const BOTTOM = 10;
const NARROW = 300; // plot width (px) below which dots shrink
const PAD_RIGHT = 14; // room for edge arrows and a dot sitting on the axis end

/* Dot radius and lane offsets for a plot width: smaller dots on narrow (phone) charts. */
function dotGeometry(width) {
  const r = width < NARROW ? 5.5 : 7;
  const step = width < NARROW ? 5.5 : 6;
  return { r, minGap: 2 * r - 1, lanes: [0, -step, step, -2 * step, 2 * step, -3 * step, 3 * step, -4 * step, 4 * step] };
}

const state = {
  leagueKey: null,
  entry: null, // index.leagues[i].positions
  index: null, // data/<league>/positions/index.json
  seasons: {}, // season -> payload
  selection: null,
  colorOf: () => null, // owner user id -> css token of a current member, or null
  dirty: true, // redraw needed once the page is visible
};

const $ = (id) => document.getElementById(id);
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const visible = () => !$("page-positions").hidden;

/* A manager's name as a link to their Managers page (app.js opens it). */
function managerLink(name) {
  if (!name) return "";
  return `<a class="manager-link" href="#${state.leagueKey || ""}/managers/${encodeURIComponent(name)}" data-manager-link="${escapeHtml(name)}">${escapeHtml(name)}</a>`;
}

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading ------------------------------------------------------------------------------------

/* Called by app.js whenever a league loads. `entry` is index.leagues[i].positions (may be null);
   `colorOf(userId)` gives a current member's colour token, or null for a former member. */
export async function loadPositions(leagueKey, entry, colorOf) {
  if (state.leagueKey !== leagueKey) {
    state.seasons = {};
    state.index = null;
    state.selection = null;
  }
  state.leagueKey = leagueKey;
  state.entry = entry || null;
  state.colorOf = colorOf || (() => null);
  if (!state.entry) {
    $("positions-unavailable").hidden = false;
    $("positions-content").hidden = true;
    $("positions-controls").hidden = true;
    $("positions-note").textContent = "";
    return;
  }
  state.index = await fetchJson(`data/${state.entry.file}`);
  if (!state.selection || !state.index.seasons.some((s) => s.season === state.selection)) state.selection = state.index.current;
  await ensureSeason(state.selection);
  render();
}

/* New data deployed: drop the cached seasons and redraw the same season. */
export async function reloadPositions() {
  if (!state.entry) return;
  state.index = await fetchJson(`data/${state.entry.file}`);
  state.seasons = {};
  if (!state.index.seasons.some((s) => s.season === state.selection)) state.selection = state.index.current;
  await ensureSeason(state.selection);
  render();
}

/* The sub-tab became visible: charts are measured, so draw them now if they are stale. */
export function showPositions() {
  if (state.dirty) drawCharts();
}

async function ensureSeason(season) {
  if (!state.seasons[season]) state.seasons[season] = await fetchJson(`data/${state.leagueKey}/positions/${season}.json`);
}

// -- page ---------------------------------------------------------------------------------------

function render() {
  $("positions-unavailable").hidden = true;
  $("positions-controls").hidden = false;
  $("positions-content").hidden = false;
  const select = $("positions-season");
  select.innerHTML = [...state.index.seasons].reverse().map((s) => `<option value="${s.season}">${s.season}</option>`).join("");
  select.value = state.selection;
  const payload = state.seasons[state.selection];
  const weeks = payload.weeks || [];
  const last = weeks[weeks.length - 1];
  $("positions-note").textContent = payload.status === "complete"
    ? /*copy:POS-04*/`Regular-season points per game (weeks ${weeks[0]} to ${last}) for each team's final roster.`
    : payload.final_through
      ? /*copy:POS-05*/`Points per game: actual points through week ${payload.final_through} plus Sleeper's projected points for weeks ${payload.final_through + 1} to ${last}, for each team's current roster.`
      : /*copy:POS-06*/`Points per game from Sleeper's projected points for weeks ${weeks[0]} to ${last}, for each team's current roster.`;
  drawCharts();
}

function teamColors(payload) {
  const colors = {};
  let former = 0;
  for (const team of payload.teams) {
    const token = state.colorOf(team.owner_id);
    colors[team.roster_id] = token || `--former-${(former++ % 3) + 1}`;
  }
  return colors;
}

function drawCharts() {
  const grid = $("positions-grid");
  if (!state.index || !visible()) {
    state.dirty = true;
    return;
  }
  state.dirty = false;
  const payload = state.seasons[state.selection];
  const positions = ORDER.filter((p) => payload.positions[p]);
  const colors = teamColors(payload);
  grid.innerHTML = positions.map((pos) => `
    <section class="card pos-card" data-pos="${pos}">
      <div class="card-head"><h3>${LABEL[pos]}</h3></div>
      <div class="pos-chart">
        <div class="pos-labels"></div>
        <div class="pos-plot"></div>
      </div>
      <div class="pos-pop" role="tooltip" hidden></div>
    </section>`).join("");
  const cards = positions.map((pos) => grid.querySelector(`.pos-card[data-pos="${pos}"]`));
  const layouts = positions.map((pos, i) => layoutChart(cards[i], pos, payload));
  // two columns: the charts sharing a grid row use one row height so both fill their cards
  const twoColumns = getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).length > 1;
  const rowHeights = layouts.map((l) => l.rowH);
  if (twoColumns) {
    for (let i = 0; i + 1 < layouts.length; i += 2) {
      const h = Math.max(rowHeights[i], rowHeights[i + 1]);
      rowHeights[i] = h;
      rowHeights[i + 1] = h;
    }
  }
  layouts.forEach((l, i) => renderChart(cards[i], l, rowHeights[i], colors));
}

// -- one chart ----------------------------------------------------------------------------------

function rowsFor(pos, payload) {
  const rows = payload.teams.map((team) => ({
    team,
    players: team.players.filter((p) => p.position === pos).sort((a, b) => b.ppg - a.ppg || a.id.localeCompare(b.id)),
  }));
  const name = (r) => r.team.team_name || r.team.display_name || "";
  rows.sort((a, b) => {
    if (!a.players.length || !b.players.length) return (b.players.length ? 1 : 0) - (a.players.length ? 1 : 0) || name(a).localeCompare(name(b));
    for (let i = 0; i < Math.max(a.players.length, b.players.length); i += 1) {
      const d = (b.players[i]?.ppg ?? -Infinity) - (a.players[i]?.ppg ?? -Infinity);
      if (d) return d;
    }
    return name(a).localeCompare(name(b));
  });
  return rows;
}

/* Lane offsets so close dots step above and below the row line, deterministically. */
function placeDots(xs, geo) {
  const placed = [];
  return xs.map((x) => {
    let best = geo.lanes[0];
    let bestGap = -1;
    for (const lane of geo.lanes) {
      const gap = placed.reduce((m, p) => Math.min(m, Math.hypot(p.x - x, p.y - lane)), Infinity);
      if (gap >= geo.minGap) { best = lane; bestGap = gap; break; }
      if (gap > bestGap) { best = lane; bestGap = gap; }
    }
    placed.push({ x, y: best });
    return best;
  });
}

function lastName(name) {
  const parts = String(name).split(" ").filter((w) => !/^(Jr\.?|Sr\.?|II|III|IV|V)$/.test(w));
  return parts.length > 1 ? parts.slice(1).join(" ") : parts[0] || "";
}

/* Measure a chart: its rows, scale and dot lanes, and the row height its widest lane spread needs. */
function layoutChart(card, pos, payload) {
  const rows = rowsFor(pos, payload);
  const info = payload.positions[pos];
  const [lo, hi] = info.axis;
  const plot = card.querySelector(".pos-plot");
  const width = Math.max(120, plot.clientWidth);
  const geo = dotGeometry(width);
  const x0 = geo.r + 2;
  const x1 = width - PAD_RIGHT;
  const sx = (v) => x0 + ((Math.min(Math.max(v, lo), hi) - lo) / (hi - lo)) * (x1 - x0);
  const placed = rows.map((r) => {
    const xs = r.players.map((p) => sx(p.ppg));
    return { xs, lanes: placeDots(xs, geo) };
  });
  const spread = Math.max(0, ...placed.flatMap((p) => p.lanes.map(Math.abs)));
  const rowH = Math.max(ROW, Math.ceil(2 * (spread + geo.r) + 6));
  return { pos, rows, info, lo, hi, width, geo, x0, x1, sx, placed, rowH };
}

function renderChart(card, layout, rowH, colors) {
  const { pos, rows, info, lo, hi, width, geo, x0, x1, sx, placed } = layout;
  const R = geo.r;
  const plot = card.querySelector(".pos-plot");
  const height = TOP + rows.length * rowH + BOTTOM;
  card.querySelector(".pos-chart").style.setProperty("--pos-row", `${rowH}px`);

  card.querySelector(".pos-labels").innerHTML = `<div class="pos-label-top"></div>` + rows.map((r) => {
    const manager = r.team.display_name || r.team.team_name || `Roster ${r.team.roster_id}`;
    const team = r.team.display_name ? r.team.team_name || "" : "";
    return `<div class="pos-label" title="${escapeHtml(team ? `${manager} (${team})` : manager)}">
      <span class="owner-name">${r.team.display_name ? managerLink(manager) : escapeHtml(manager)}</span>${team ? `<span class="team">${escapeHtml(team)}</span>` : ""}
    </div>`;
  }).join("");

  const parts = [];
  for (let t = lo; t <= hi + 1e-9; t += 5) {
    const x = sx(t);
    parts.push(`<line class="pos-grid-line" x1="${x}" x2="${x}" y1="${TOP - 4}" y2="${height - BOTTOM}"/>`);
    parts.push(`<text class="pos-tick" x="${x}" y="${TOP - 10}" text-anchor="middle">${t}</text>`);
  }
  rows.forEach((_, i) => {
    const y = TOP + i * rowH + rowH / 2;
    parts.push(`<line class="pos-row-line" x1="${x0}" x2="${x1}" y1="${y}" y2="${y}"/>`);
  });
  if (info.replacement != null) {
    const x = sx(info.replacement);
    const anchor = x > width - 60 ? "end" : x < 60 ? "start" : "middle";
    parts.push(`<line class="pos-rep" x1="${x}" x2="${x}" y1="${TOP - 2}" y2="${height - BOTTOM}"/>`);
    parts.push(`<text class="pos-rep-label" x="${x}" y="11" text-anchor="${anchor}">Replacement Level</text>`);
  }

  let top = null; // the chart's highest points per game
  rows.forEach((r) => r.players.forEach((p) => { if (!top || p.ppg > top.ppg) top = p; }));

  rows.forEach((r, i) => {
    const y = TOP + i * rowH + rowH / 2;
    const token = colors[r.team.roster_id];
    const { xs, lanes } = placed[i];
    r.players.forEach((p, j) => {
      const x = xs[j];
      const cy = y + lanes[j];
      const style = `fill: color-mix(in srgb, var(${token}) 38%, var(--surface)); stroke: var(${token});`;
      const extra = [p.status, p.taxi ? "taxi squad" : null].filter(Boolean).join(", ");
      const label = `${p.name}, ${p.ppg.toFixed(1)} points per game${extra ? `, ${extra}` : ""}`;
      if (p.ppg > hi) parts.push(`<path class="pos-arrow" d="M${x + R + 2} ${cy - 4} L${x + R + 6} ${cy} L${x + R + 2} ${cy + 4}" style="stroke: var(${token});"/>`);
      if (p.ppg < lo) parts.push(`<path class="pos-arrow" d="M${x - R - 2} ${cy - 4} L${x - R - 6} ${cy} L${x - R - 2} ${cy + 4}" style="stroke: var(${token});"/>`);
      parts.push(`<circle class="pos-dot${p.taxi ? " taxi" : ""}" cx="${x}" cy="${cy}" r="${R}" style="${style}" tabindex="0" role="img" aria-label="${escapeHtml(label)}" data-name="${escapeHtml(p.name)}" data-ppg="${p.ppg.toFixed(1)}"${p.status ? ` data-status="${escapeHtml(p.status)}"` : ""}${p.taxi ? ' data-taxi="1"' : ""}/>`);
      const arm = R - 3;
      if (p.injured) parts.push(`<g class="pos-hurt" aria-hidden="true"><line x1="${x - arm}" x2="${x + arm}" y1="${cy}" y2="${cy}"/><line x1="${x}" x2="${x}" y1="${cy - arm}" y2="${cy + arm}"/></g>`);
      if (top && p === top) parts.push(`<text class="pos-top-name" x="${x}" y="${cy - R - 4}" text-anchor="middle">${escapeHtml(lastName(p.name))}</text>`);
    });
  });

  plot.innerHTML = `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="group" aria-label="${LABEL[pos]} by points per game">${parts.join("")}</svg>`;
  keepNameInCard(card, plot);
  wirePopup(card);
}

/* The top name sits centred on its dot and may overhang the plot; shift it only as far as
   needed to stay inside the card. */
function keepNameInCard(card, plot) {
  const name = plot.querySelector(".pos-top-name");
  if (!name) return;
  const c = card.getBoundingClientRect();
  const b = name.getBoundingClientRect();
  const margin = 6;
  let shift = 0;
  if (b.right > c.right - margin) shift = c.right - margin - b.right;
  if (b.left + shift < c.left + margin) shift = c.left + margin - b.left;
  if (shift) name.setAttribute("x", String(Number(name.getAttribute("x")) + shift));
}

// -- popup --------------------------------------------------------------------------------------

function wirePopup(card) {
  const pop = card.querySelector(".pos-pop");
  const show = (dot) => {
    pop.innerHTML = `<strong>${escapeHtml(dot.dataset.name)}</strong><span>${dot.dataset.ppg} PPG</span>`
      + (dot.dataset.status ? `<span class="pos-status">${escapeHtml(dot.dataset.status)}</span>` : "")
      + (dot.dataset.taxi ? `<span class="pos-taxi">Taxi</span>` : "");
    pop.hidden = false;
    const c = card.getBoundingClientRect();
    const d = dot.getBoundingClientRect();
    const w = pop.offsetWidth;
    const h = pop.offsetHeight;
    let left = d.left - c.left + d.width / 2 - w / 2;
    left = Math.max(4, Math.min(left, c.width - w - 4));
    let topPx = d.top - c.top - h - 8;
    if (topPx < 4) topPx = d.bottom - c.top + 8;
    pop.style.left = `${left}px`;
    pop.style.top = `${topPx}px`;
  };
  const hide = () => { pop.hidden = true; };
  for (const dot of card.querySelectorAll(".pos-dot")) {
    dot.addEventListener("mouseenter", () => show(dot));
    dot.addEventListener("mouseleave", hide);
    dot.addEventListener("focus", () => show(dot));
    dot.addEventListener("blur", hide);
    dot.addEventListener("click", () => show(dot)); // a tap on a touch screen
  }
}

// -- wiring -------------------------------------------------------------------------------------

export function initPositions() {
  $("positions-season").addEventListener("change", async (e) => {
    state.selection = e.target.value;
    await ensureSeason(state.selection);
    render();
  });
  let timer = null;
  let lastWidth = innerWidth;
  addEventListener("resize", () => {
    if (innerWidth === lastWidth) return; // phones fire resize on scroll when the address bar moves
    lastWidth = innerWidth;
    clearTimeout(timer);
    timer = setTimeout(() => (visible() ? drawCharts() : (state.dirty = true)), 150);
  });
}
