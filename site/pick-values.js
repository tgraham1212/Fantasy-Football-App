/* How Pick Values Work: the rookie pick value model from data/pick-values.json. Plain JS + Chart.js. */

import { initRefresh } from "./refresh.js?v=__BUILD__";
import { initUpdates } from "./updates.js?v=__BUILD__";

const THIRDS = ["Early", "Middle", "Late"];
const ROUND_NAMES = { 1: "1st", 2: "2nd", 3: "3rd" };
const SERIES_TOKENS = ["--team-1", "--team-2", "--team-3"];
const FIRST_SLOT = { Early: 1, Middle: 5, Late: 9 };

const state = { index: null, model: null, round: 1, charts: {} };
const $ = (id) => document.getElementById(id);

// -- formatting -----------------------------------------------------------------------------------

function signed(v, digits = 2) {
  if (v == null) return "–";
  const s = Math.abs(v).toFixed(digits);
  if (Number(s) === 0) return s;
  return v > 0 ? `+${s}` : `−${s}`;
}

function cls(v) {
  if (v == null || Math.abs(v) < 0.005) return "";
  return v > 0 ? "war-pos" : "war-neg";
}

function slotLabel(slot) {
  return `${Math.ceil(slot / 12)}.${String(((slot - 1) % 12) + 1).padStart(2, "0")}`;
}

function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function groupName(rnd, third) {
  return `${ROUND_NAMES[rnd]} ${third}`;
}

// -- theme ------------------------------------------------------------------------------------------

function initTheme() {
  let stored = null;
  try { stored = localStorage.getItem("theme"); } catch (e) { /* private mode */ }
  const fromUrl = new URLSearchParams(location.search).get("theme");
  const theme = fromUrl === "dark" || fromUrl === "light" ? fromUrl : stored;
  if (theme === "dark" || theme === "light") document.documentElement.dataset.theme = theme;
  $("theme-toggle").addEventListener("click", () => {
    const isDark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
    renderCharts();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderCharts);
}

// -- summary and group table --------------------------------------------------------------------------

function renderMeta() {
  const M = state.model;
  const classes = Object.keys(M.classes);
  const picks = Object.values(M.classes).reduce((a, c) => a + c.picks, 0);
  $("pv-meta").textContent = /*copy:PV-22*/`${picks} picks from the ${classes[0]}–${classes[classes.length - 1]} rookie classes · WAR through the ${M.through_season} season · built ${formatDate(M.built_at)}`;
}

function renderGroups() {
  const M = state.model;
  const rows = [];
  for (const rnd of [1, 2, 3]) {
    for (const third of THIRDS) {
      const g = M.groups[`${rnd}-${third}`];
      const first = (rnd - 1) * 12 + FIRST_SLOT[third];
      const full = g.seasons.length ? g.seasons[g.seasons.length - 1].picks : 0;
      rows.push(`<tr data-group="${rnd}-${third}"><th scope="row">${groupName(rnd, third)}</th><td>${slotLabel(first)}–${slotLabel(first + 3)}</td>
        <td class="num"><span class="${cls(g.measured)}">${signed(g.measured)}</span> <span class="pv-range">${signed(g.range[0])} to ${signed(g.range[1])}</span></td>
        <td class="num">${g.picks} / ${full}</td><td class="num"><strong class="${cls(g.value)}">${signed(g.value)}</strong></td></tr>`);
    }
  }
  $("pv-groups").innerHTML = `<thead><tr><th scope="col">Pick</th><th scope="col">Slots</th><th scope="col">Measured, 8 seasons</th><th scope="col">Picks (season 1 / 8)</th><th scope="col">Model value</th></tr></thead><tbody>${rows.join("")}</tbody>`;
}

function renderRoundSwitcher() {
  const wrap = $("pv-round-switcher");
  wrap.innerHTML = "";
  for (const rnd of [1, 2, 3]) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = `${ROUND_NAMES[rnd]} round`;
    btn.setAttribute("aria-pressed", String(rnd === state.round));
    btn.addEventListener("click", () => {
      state.round = rnd;
      renderRoundSwitcher();
      renderTotalChart();
      renderTotalTable();
    });
    wrap.appendChild(btn);
  }
}

// -- tables (the charts' table views) --------------------------------------------------------------------

function renderTotalTable() {
  const M = state.model;
  const groups = THIRDS.map((t) => [t, M.groups[`${state.round}-${t}`]]);
  const seasons = Math.max(...groups.map(([, g]) => g.seasons.length));
  const head = `<tr><th scope="col">Through season</th>${groups.map(([t]) => `<th scope="col">${groupName(state.round, t)}</th>`).join("")}</tr>`;
  const body = Array.from({ length: seasons }, (_, k) => `<tr><th scope="row">${k + 1}</th>${groups.map(([, g]) => {
    const s = g.seasons[k];
    return `<td class="num">${s ? `<span class="${cls(s.total)}">${signed(s.total)}</span> <span class="pv-range">${s.picks} picks</span>` : "–"}</td>`;
  }).join("")}</tr>`).join("");
  $("pv-total-table").innerHTML = `<thead>${head}</thead><tbody>${body}</tbody>`;
}

function renderSeasonTable() {
  const R = state.model.rounds;
  const seasons = Math.max(...[1, 2, 3].map((r) => R[r].seasons.length));
  const head = `<tr><th scope="col">Season</th>${[1, 2, 3].map((r) => `<th scope="col">${ROUND_NAMES[r]} round</th>`).join("")}</tr>`;
  const body = Array.from({ length: seasons }, (_, k) => `<tr><th scope="row">${k + 1}</th>${[1, 2, 3].map((r) => {
    const s = R[r].seasons[k];
    return `<td class="num">${s ? `<span class="${cls(s.mean)}">${signed(s.mean)}</span> <span class="pv-range">${s.picks} picks</span>` : "–"}</td>`;
  }).join("")}</tr>`).join("");
  $("pv-season-table").innerHTML = `<thead>${head}</thead><tbody>${body}</tbody>`;
}

function renderSlotTable() {
  const rows = state.model.slots.map((s) => `<tr><th scope="row">${s.label}</th>
    <td class="num"><span class="${cls(s.total3)}">${signed(s.total3)}</span></td><td class="num">${s.picks3}</td>
    <td class="num"><span class="${cls(s.total8)}">${signed(s.total8)}</span></td><td class="num">${s.picks8}</td>
    <td>${s.best ? `${escapeHtml(s.best.name)} (${s.best.class}) ${signed(s.best.war)}` : "–"}</td></tr>`).join("");
  $("pv-slot-table").innerHTML = `<thead><tr><th scope="col">Pick</th><th scope="col">Through 3 seasons</th><th scope="col">Picks</th><th scope="col">Through 8 seasons</th><th scope="col">Picks</th><th scope="col">Best pick so far</th></tr></thead><tbody>${rows}</tbody>`;
}

// -- charts ---------------------------------------------------------------------------------------------

function baseOptions(yTitle, xTitle) {
  const muted = cssVar("--muted");
  const grid = cssVar("--grid");
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 12, left: 4 } },
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: true, position: "top", align: "end", labels: { color: cssVar("--ink-2"), usePointStyle: true, boxWidth: 8, boxHeight: 8 } },
      tooltip: {
        backgroundColor: cssVar("--surface"),
        titleColor: cssVar("--ink"),
        bodyColor: cssVar("--ink-2"),
        borderColor: cssVar("--border"),
        borderWidth: 1,
        padding: 10,
      },
    },
    scales: {
      x: { title: { display: true, text: xTitle, color: muted }, grid: { display: false }, border: { color: cssVar("--axis") }, ticks: { color: muted, maxRotation: 0, autoSkip: true } },
      y: {
        title: { display: true, text: yTitle, color: muted },
        grid: { color: (ctx) => (ctx.tick && ctx.tick.value === 0 ? cssVar("--axis") : grid), drawTicks: false },
        border: { display: false },
        ticks: { color: muted, callback: (v) => signed(v, 1) },
      },
    },
  };
}

function line(label, data, token, extra = {}) {
  const color = cssVar(token);
  return { label, data, borderColor: color, backgroundColor: color, borderWidth: 2, pointRadius: 4, pointHoverRadius: 6,
           pointBorderColor: cssVar("--surface"), pointBorderWidth: 2, tension: 0, ...extra };
}

function draw(key, canvasId, config) {
  if (state.charts[key]) state.charts[key].destroy();
  state.charts[key] = new Chart($(canvasId), config);
}

function renderTotalChart() {
  const M = state.model;
  const groups = THIRDS.map((t) => M.groups[`${state.round}-${t}`]);
  const seasons = Math.max(...groups.map((g) => g.seasons.length));
  const options = baseOptions("Total WAR", "Seasons since the draft");
  options.plugins.tooltip.callbacks = {
    title: (items) => (items.length ? `Through season ${items[0].label}` : ""),
    label: (item) => {
      const s = groups[item.datasetIndex].seasons[item.dataIndex];
      return s ? `${item.dataset.label}: ${signed(s.total)} (${s.picks} picks)` : "";
    },
  };
  draw("total", "pv-total-chart", {
    type: "line",
    data: {
      labels: Array.from({ length: seasons }, (_, k) => String(k + 1)),
      datasets: THIRDS.map((t, i) => line(groupName(state.round, t), groups[i].seasons.map((s) => s.total), SERIES_TOKENS[i])),
    },
    options,
  });
}

function renderSeasonChart() {
  const R = state.model.rounds;
  const seasons = Math.max(...[1, 2, 3].map((r) => R[r].seasons.length));
  const options = baseOptions("WAR in the season", "Season since the draft");
  options.plugins.tooltip.callbacks = {
    title: (items) => (items.length ? `Season ${items[0].label}` : ""),
    label: (item) => {
      const s = R[item.datasetIndex + 1].seasons[item.dataIndex];
      return s ? `${item.dataset.label}: ${signed(s.mean)} (${s.picks} picks)` : "";
    },
  };
  draw("season", "pv-season-chart", {
    type: "line",
    data: {
      labels: Array.from({ length: seasons }, (_, k) => String(k + 1)),
      datasets: [1, 2, 3].map((r, i) => line(`${ROUND_NAMES[r]} round`, R[r].seasons.map((s) => s.mean), SERIES_TOKENS[i])),
    },
    options,
  });
}

function renderSlotChart() {
  const S = state.model.slots;
  const narrow = $("pv-slot-chart").parentElement.clientWidth < 560;
  const options = baseOptions("Average WAR", "Rookie draft slot");
  options.scales.x.ticks.maxTicksLimit = narrow ? 6 : 12;
  options.plugins.tooltip.callbacks = {
    title: (items) => (items.length ? `Pick ${items[0].label}` : ""),
    label: (item) => {
      const s = S[item.dataIndex];
      return item.datasetIndex === 0 ? `Through 3 seasons: ${signed(s.total3)} (${s.picks3} picks)` : `Through 8 seasons: ${signed(s.total8)} (${s.picks8} picks)`;
    },
    afterBody: (items) => {
      const s = items.length ? S[items[0].dataIndex] : null;
      return s && s.best ? `Best: ${s.best.name} (${s.best.class}), ${signed(s.best.war)}` : "";
    },
  };
  const bar = (label, key, token) => ({ label, data: S.map((s) => s[key]), backgroundColor: cssVar(token), borderRadius: 3, maxBarThickness: 14, categoryPercentage: 0.8, barPercentage: 0.9 });
  draw("slot", "pv-slot-chart", {
    type: "bar",
    data: { labels: S.map((s) => s.label), datasets: [bar("Through 3 seasons", "total3", SERIES_TOKENS[0]), bar("Through 8 seasons", "total8", SERIES_TOKENS[1])] },
    options,
  });
}

function renderCharts() {
  if (!state.model) return;
  renderTotalChart();
  renderSeasonChart();
  renderSlotChart();
}

// -- loading -----------------------------------------------------------------------------------------------

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function loadModel() {
  const status = $("status");
  if (!state.index.pick_values || !state.index.pick_values.file) {
    $("not-run").hidden = false;
    $("main").hidden = true;
    status.hidden = true;
    return;
  }
  state.model = await fetchJson(`data/${state.index.pick_values.file}`);
  renderMeta();
  renderGroups();
  renderRoundSwitcher();
  renderTotalTable();
  renderSeasonTable();
  renderSlotTable();
  $("main").hidden = false;
  $("not-run").hidden = true;
  status.hidden = true;
  renderCharts();
}

async function main() {
  initTheme();
  const status = $("status");
  try {
    state.index = await fetchJson("data/index.json");
    initRefresh(state.index);
    initUpdates(state.index.last_refresh, async (index) => {
      state.index = index;
      await loadModel();
    });
    await loadModel();
  } catch (err) {
    status.textContent = `Could not load the pick values (${err.message}).`;
    status.classList.add("error");
    status.hidden = false;
  }
  let resizeTimer = null;
  addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderCharts, 150);
  });
}

main();
