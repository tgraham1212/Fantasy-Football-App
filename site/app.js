/* Playoff odds site: league switcher, sortable odds table, odds-over-time chart. Plain JS + Chart.js. */

const DEFAULT_BOTTOM = { key: "avoid_losers_bye", label: "Avoid Loser's Bye", description: "" };

const state = {
  index: null,
  league: null, // current league payload
  metric: "playoffs",
  selected: null, // roster_id of the highlighted current team
  selectedFormer: null, // manager id of a highlighted former member (rating chart only)
  sort: null, // null = standings order, else { key, dir: "desc" | "asc" }
  chart: null,
  ratingChart: null,
  ratingMetric: "mu", // "mu" | "career_z"
  ratingRange: "all", // "season" | "3" | "all"
  colors: {}, // roster_id -> css token name, fixed per league load
};

const RATING_METRICS = [
  { key: "mu", label: "Rating", title: "Manager rating over time", note: "Openskill rating of each manager's weekly points rank; 1000 is average" },
  { key: "career_z", label: "Z-score", title: "Career z-score over time", note: "Career mean of weekly z-scores: standard deviations above or below that week's league average" },
];
const RATING_RANGES = [
  { key: "season", label: "This season" },
  { key: "3", label: "Last 3 seasons" },
  { key: "all", label: "All time" },
];

const $ = (id) => document.getElementById(id);

// -- formatting ---------------------------------------------------------------

function pct(v) {
  if (v == null) return "–";
  if (v >= 0.9995) return "100%";
  if (v >= 0.995) return ">99%";
  if (v > 0 && v < 0.005) return "<1%";
  return `${Math.round(v * 100)}%`;
}

/* Fill strength 0..100: nothing below 1%, full from 99% up. */
function fillPercent(v) {
  if (v == null) return 0;
  const p = v * 100;
  if (p < 1) return 0;
  if (p > 99) return 100;
  return p;
}

function record(t) {
  return `${t.wins}-${t.losses}${t.ties ? `-${t.ties}` : ""}`;
}

function projRecord(t) {
  return `${t.proj_wins.toFixed(1)} - ${t.proj_losses.toFixed(1)}`;
}

function eloDelta(d) {
  if (d == null || Math.round(d) === 0) return "";
  const cls = d > 0 ? "up" : "down";
  return `<span class="elo-delta ${cls}">${d > 0 ? "+" : "−"}${Math.abs(Math.round(d))}</span>`;
}

function changeTooltip(L, t, key) {
  if (L.previous_as_of_week == null || !t.change || t.change[key] == null) return "";
  const since = L.previous_as_of_week === 0 ? "since preseason" : `since week ${L.previous_as_of_week}`;
  const pts = Math.abs(t.change[key] * 100);
  if (pts < 0.05) return `No change ${since}`;
  return `${t.change[key] > 0 ? "Up" : "Down"} ${pts.toFixed(1)} points ${since}`;
}

function weekLabel(w) {
  return w === 0 ? "Pre" : `Wk ${w}`;
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

function withAlpha(hex, alpha) {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h.slice(0, 6);
  return `#${full}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;
}

// -- league-dependent definitions ------------------------------------------------

function bottomColumn(L) {
  return L.bottom_column && L.bottom_column.key ? L.bottom_column : DEFAULT_BOTTOM;
}

/* Chart metrics: the table's four chance columns, in the table's order. */
function metricsFor(L) {
  const bottom = bottomColumn(L);
  return [
    { key: bottom.key, label: bottom.label, title: `${bottom.label} chances by week` },
    { key: "playoffs", label: "Make playoffs", title: "Playoff chances by week" },
    { key: "bye", label: "First-round bye", title: "First-round bye chances by week" },
    { key: "title", label: "Win championship", title: "Championship chances by week" },
  ];
}

/* Standings order: wins (ties count half), then points scored. Matches Sleeper's standings page. */
function standingsCompare(a, b) {
  const wa = a.wins + 0.5 * a.ties;
  const wb = b.wins + 0.5 * b.ties;
  if (wb !== wa) return wb - wa;
  if (b.points_for !== a.points_for) return b.points_for - a.points_for;
  return a.roster_id - b.roster_id;
}

/* Sortable columns. `value` gives the natural "first click" ordering: highest first
   for numbers; for Owner the natural order is A to Z, so its value is negated rank. */
function columnsFor(L) {
  const bottom = bottomColumn(L);
  return {
    elo: { value: (t) => t.elo },
    elo_change: { value: (t) => t.elo_change },
    owner: { text: (t) => (t.display_name ?? "").toLowerCase() },
    proj: { value: (t) => t.proj_wins },
    bottom: { value: (t) => t[bottom.key] },
    playoffs: { value: (t) => t.playoffs },
    bye: { value: (t) => t.bye },
    title: { value: (t) => t.title },
  };
}

function sortedTeams(L) {
  const teams = [...L.teams].sort(standingsCompare);
  if (!state.sort) return teams;
  const col = columnsFor(L)[state.sort.key];
  if (!col) return teams;
  const sign = state.sort.dir === "asc" ? -1 : 1;
  const cmp = col.text
    ? (a, b) => col.text(a).localeCompare(col.text(b)) // A to Z is the natural ("desc") order
    : (a, b) => (col.value(b) ?? -Infinity) - (col.value(a) ?? -Infinity);
  return teams.sort((a, b) => sign * cmp(a, b) || standingsCompare(a, b));
}

/* One fixed colour per team for the whole season: tokens assigned by ascending roster_id. */
function assignColors(L) {
  const ids = L.teams.map((t) => t.roster_id).sort((a, b) => a - b);
  state.colors = {};
  ids.forEach((rid, i) => { state.colors[rid] = `--team-${(i % 12) + 1}`; });
}

function teamColor(rid) {
  return cssVar(state.colors[rid] || "--accent");
}

// -- theme ----------------------------------------------------------------------

function initTheme() {
  let stored = null;
  try { stored = localStorage.getItem("theme"); } catch (e) { /* private mode etc. */ }
  const fromUrl = new URLSearchParams(location.search).get("theme"); // ?theme=dark|light forces a theme
  const theme = fromUrl === "dark" || fromUrl === "light" ? fromUrl : stored;
  if (theme === "dark" || theme === "light") document.documentElement.dataset.theme = theme;
  $("theme-toggle").addEventListener("click", () => {
    const isDark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
    renderTable();
    renderChart();
    renderRatingChart();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { renderTable(); renderChart(); renderRatingChart(); });
}

// -- league switcher --------------------------------------------------------------

function renderSwitcher() {
  const nav = $("league-switcher");
  nav.innerHTML = "";
  for (const league of state.index.leagues) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = league.name;
    btn.setAttribute("aria-pressed", String(state.league && state.league.league_key === league.key));
    btn.addEventListener("click", () => loadLeague(league.key));
    nav.appendChild(btn);
  }
}

// -- summary ----------------------------------------------------------------------

function renderSummary() {
  const L = state.league;
  $("league-title").textContent = `${L.league_name} · ${L.season}`;
  const asOf = L.as_of_week === 0 ? "Preseason" : `After week ${L.as_of_week} of ${L.regular_season_weeks}`;
  $("freshness").textContent = `${asOf} · updated ${formatDate(L.generated_at)} · ${L.runs.toLocaleString()} simulations`;
  document.title = `${L.league_name} – Playoff Odds`;
}

// -- table ---------------------------------------------------------------------------

function initTableHead() {
  for (const th of document.querySelectorAll("#odds-table thead th[data-col]")) {
    const btn = th.querySelector("button.sort");
    if (!btn) continue;
    btn.addEventListener("click", () => {
      const key = th.dataset.col;
      if (state.sort && state.sort.key === key) {
        state.sort = { key, dir: state.sort.dir === "desc" ? "asc" : "desc" };
      } else {
        state.sort = { key, dir: "desc" };
      }
      renderTable();
    });
  }
}

function renderHead() {
  const L = state.league;
  const bottom = bottomColumn(L);
  const bottomBtn = $("bottom-head");
  bottomBtn.innerHTML = bottom.key === "last" ? "#1 Pick" : "Avoid<br>Loser's Bye";
  bottomBtn.title = bottom.description || "";
  for (const th of document.querySelectorAll("#odds-table thead th[data-col]")) {
    if (state.sort && th.dataset.col === state.sort.key) {
      th.setAttribute("aria-sort", state.sort.dir === "asc" ? "ascending" : "descending");
    } else {
      th.removeAttribute("aria-sort");
    }
  }
}

function chanceCell(L, t, key) {
  const v = t[key];
  const p = fillPercent(v);
  const fillSwitch = Number(cssVar("--fill-switch")) || 101;
  const classes = ["num", "chance"];
  if (p >= fillSwitch) classes.push("fill-dark");
  if (v != null && v < 0.01) classes.push("chance-low");
  const tip = changeTooltip(L, t, key);
  return `<td class="${classes.join(" ")}" style="--p: ${p.toFixed(1)}"${tip ? ` title="${escapeHtml(tip)}"` : ""}>${pct(v)}</td>`;
}

function renderTable() {
  const L = state.league;
  if (!L) return;
  renderHead();
  const bottom = bottomColumn(L);
  const body = $("odds-body");
  body.innerHTML = "";
  for (const t of sortedTeams(L)) {
    const tr = document.createElement("tr");
    tr.dataset.roster = String(t.roster_id);
    tr.tabIndex = 0;
    tr.setAttribute("aria-selected", String(state.selected === t.roster_id));
    tr.innerHTML = `
      <td class="num col-elo">${t.elo == null ? "" : Math.round(t.elo)}</td>
      <td class="num col-elo-change">${eloDelta(t.elo_change)}</td>
      <td class="col-owner">
        <span class="owner-name"><span class="swatch" style="--team: var(${state.colors[t.roster_id] || "--accent"})" aria-hidden="true"></span>${escapeHtml(t.display_name ?? "")}<span class="record">${record(t)}</span></span>
        <span class="team">${escapeHtml(t.team_name)}</span>
      </td>
      <td class="num col-proj">${projRecord(t)}</td>
      ${chanceCell(L, t, bottom.key)}
      ${chanceCell(L, t, "playoffs")}
      ${chanceCell(L, t, "bye")}
      ${chanceCell(L, t, "title")}`;
    const toggle = () => selectTeam(state.selected === t.roster_id ? null : t.roster_id);
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    body.appendChild(tr);
  }
}

function selectTeam(rosterId) {
  state.selected = rosterId;
  state.selectedFormer = null;
  for (const tr of $("odds-body").querySelectorAll("tr")) {
    tr.setAttribute("aria-selected", String(Number(tr.dataset.roster) === rosterId));
  }
  renderChart();
  renderRatingChart();
}

/* A former member has no table row or odds line; highlighting one dims everything else. */
function selectFormer(managerId) {
  state.selected = null;
  state.selectedFormer = managerId;
  for (const tr of $("odds-body").querySelectorAll("tr")) tr.setAttribute("aria-selected", "false");
  renderChart();
  renderRatingChart();
}

function anySelected() {
  return state.selected != null || state.selectedFormer != null;
}

// -- metric switcher -------------------------------------------------------------------

function renderMetrics() {
  const box = $("metric-switcher");
  box.innerHTML = "";
  for (const m of metricsFor(state.league)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = m.label;
    btn.setAttribute("aria-pressed", String(state.metric === m.key));
    btn.addEventListener("click", () => {
      state.metric = m.key;
      renderMetrics();
      renderChart();
    });
    box.appendChild(btn);
  }
}

// -- chart ---------------------------------------------------------------------------------

/* Direct labels at each line's end: a dot in the team colour, then the name in ink.
   On narrow screens only the selected team is labeled. */
const endLabels = {
  id: "endLabels",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea } = chart;
    const narrow = chart.width < 560;
    const items = [];
    chart.data.datasets.forEach((ds, i) => {
      if (!chart.isDatasetVisible(i)) return;
      const selected = ds.isSelected;
      if (narrow && !selected) return;
      const meta = chart.getDatasetMeta(i);
      let last = null;
      for (let k = meta.data.length - 1; k >= 0; k--) {
        if (ds.data[k] != null) { last = meta.data[k]; break; }
      }
      if (!last) return;
      items.push({ y: last.y, x: last.x, text: ds.shortLabel, selected, color: ds.teamColor });
    });
    // push overlapping labels apart, keeping them inside the plot
    items.sort((a, b) => a.y - b.y);
    const gap = 13;
    for (let i = 1; i < items.length; i++) {
      if (items[i].y - items[i - 1].y < gap) items[i].y = items[i - 1].y + gap;
    }
    for (let i = items.length - 1; i >= 0; i--) {
      const maxY = chartArea.bottom - 2;
      if (items[i].y > maxY) items[i].y = maxY;
      if (i < items.length - 1 && items[i + 1].y - items[i].y < gap) items[i].y = items[i + 1].y - gap;
    }
    ctx.save();
    ctx.font = `${narrow ? 600 : 500} 11.5px system-ui, -apple-system, "Segoe UI", sans-serif`;
    ctx.textBaseline = "middle";
    const dimmed = anySelected();
    for (const it of items) {
      const faded = dimmed && !it.selected;
      ctx.globalAlpha = faded ? 0.45 : 1;
      ctx.fillStyle = it.color;
      ctx.beginPath();
      ctx.arc(it.x + 9, it.y, 3.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = it.selected ? cssVar("--ink") : cssVar("--ink-2");
      ctx.fillText(it.text, it.x + 16, it.y);
    }
    ctx.restore();
  },
};

function shortName(name, max) {
  return name.length > max ? `${name.slice(0, max - 1).trimEnd()}…` : name;
}

/* Axis top: the next multiple of 10 at least 5 points above the highest plotted value, capped at 100. */
function axisMax(datasets) {
  let max = 0;
  for (const ds of datasets) for (const v of ds.data) if (v != null && v > max) max = v;
  return Math.min(100, Math.max(10, Math.ceil((max + 5) / 10) * 10));
}

function renderChart() {
  if (!state.league) return;
  const L = state.league;
  const metrics = metricsFor(L);
  const metric = metrics.find((m) => m.key === state.metric) || metrics[1];
  $("chart-title").textContent = metric.title;
  const weeks = L.history.weeks;
  const canvas = $("odds-chart");
  const narrow = canvas.parentElement.clientWidth < 560;
  const selectedAny = anySelected();

  const datasets = L.teams.map((t) => {
    const selected = t.roster_id === state.selected;
    const color = teamColor(t.roster_id);
    const faded = selectedAny && !selected;
    return {
      label: t.display_name || t.team_name,
      shortLabel: shortName(t.display_name || t.team_name, narrow ? 14 : 22),
      rosterId: t.roster_id,
      isSelected: selected,
      teamColor: color,
      data: (L.history.teams[String(t.roster_id)] || {})[metric.key]?.map((v) => (v == null ? null : v * 100)) ?? [],
      borderColor: faded ? withAlpha(color, 0.25) : color,
      borderWidth: selected ? 3 : 2,
      pointRadius: 0,
      pointHoverRadius: selected ? 5 : 4,
      pointHoverBackgroundColor: color,
      pointHoverBorderColor: cssVar("--surface"),
      pointHoverBorderWidth: 2,
      pointHitRadius: 14,
      tension: 0.25,
      spanGaps: true,
      order: selected ? 0 : 1,
    };
  });

  const top = axisMax(datasets);
  const step = top <= 40 ? 5 : (top <= 60 ? 10 : 25);
  const ink2 = cssVar("--ink-2");
  const muted = cssVar("--muted");
  const grid = cssVar("--grid");
  const axis = cssVar("--axis");
  const config = {
    type: "line",
    data: { labels: weeks.map(weekLabel), datasets },
    plugins: [endLabels],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { right: narrow ? 104 : 160, top: 8 } },
      interaction: { mode: "index", intersect: false },
      onClick(evt, elements, chart) {
        const hits = chart.getElementsAtEventForMode(evt, "nearest", { intersect: false }, true);
        if (!hits.length) { selectTeam(null); return; }
        const rid = chart.data.datasets[hits[0].datasetIndex].rosterId;
        selectTeam(state.selected === rid ? null : rid);
      },
      plugins: {
        legend: { display: false }, // the table doubles as the legend (swatches); lines are labeled directly
        tooltip: {
          backgroundColor: cssVar("--surface"),
          titleColor: cssVar("--ink"),
          bodyColor: ink2,
          borderColor: cssVar("--border"),
          borderWidth: 1,
          padding: 10,
          usePointStyle: true,
          boxWidth: 8,
          boxHeight: 8,
          boxPadding: 4,
          itemSort: (a, b) => (b.raw ?? -1) - (a.raw ?? -1),
          callbacks: {
            title: (items) => (items.length ? (weeks[items[0].dataIndex] === 0 ? "Preseason" : `After week ${weeks[items[0].dataIndex]}`) : ""),
            label: (item) => `${item.dataset.label}: ${item.raw == null ? "–" : `${Math.round(item.raw)}%`}`,
            labelPointStyle: () => ({ pointStyle: "circle", rotation: 0 }),
            labelColor: (item) => ({ borderColor: item.dataset.teamColor, backgroundColor: item.dataset.teamColor }),
          },
        },
      },
      scales: {
        x: {
          grid: { color: grid, drawTicks: false },
          border: { color: axis },
          ticks: { color: muted, maxRotation: 0, autoSkip: true, maxTicksLimit: narrow ? 6 : 15 },
        },
        y: {
          min: 0,
          max: top,
          grid: { color: grid, drawTicks: false },
          border: { display: false },
          ticks: { color: muted, stepSize: step, callback: (v) => `${v}%` },
        },
      },
    },
  };

  if (state.chart) {
    state.chart.destroy();
  }
  state.chart = new Chart(canvas, config);
  const sel = L.teams.find((t) => t.roster_id === state.selected);
  $("chart-note").textContent = sel
    ? `${sel.display_name || sel.team_name} is highlighted. Click the team again to clear.`
    : "Each line is a team, in the colour shown beside its name in the table. Hover for every team's chance after a given week; click a line or a table row to highlight one team.";
}

// -- rating chart -----------------------------------------------------------------------------------

function renderPills(boxId, items, currentKey, onPick) {
  const box = $(boxId);
  box.innerHTML = "";
  for (const item of items) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = item.label;
    btn.setAttribute("aria-pressed", String(currentKey === item.key));
    btn.addEventListener("click", () => onPick(item.key));
    box.appendChild(btn);
  }
}

function renderRatingPills() {
  renderPills("rating-metric", RATING_METRICS, state.ratingMetric, (key) => {
    state.ratingMetric = key;
    renderRatingPills();
    renderRatingChart();
  });
  renderPills("rating-range", RATING_RANGES, state.ratingRange, (key) => {
    state.ratingRange = key;
    renderRatingPills();
    renderRatingChart();
  });
}

/* Index of the first plotted week for the chosen range. */
function rangeStart(R) {
  const seasons = R.seasons || [];
  if (state.ratingRange === "all" || !seasons.length) return 0;
  const keep = state.ratingRange === "season" ? seasons.slice(-1) : seasons.slice(-3);
  const i = R.weeks.findIndex((w) => keep.includes(w.season));
  return i < 0 ? 0 : i;
}

/* Former members: three validated greys, then the same greys dashed, then dotted. */
function formerStyle(index) {
  const token = `--former-${(index % 3) + 1}`;
  const pattern = Math.floor(index / 3) % 3;
  return { color: cssVar(token), dash: pattern === 0 ? [] : pattern === 1 ? [7, 4] : [2, 4] };
}

/* Zero line for the z-score metric. */
const zeroLine = {
  id: "zeroLine",
  beforeDatasetsDraw(chart) {
    if (state.ratingMetric !== "career_z") return;
    const y = chart.scales.y;
    if (y.min > 0 || y.max < 0) return;
    const { ctx, chartArea } = chart;
    const py = y.getPixelForValue(0);
    ctx.save();
    ctx.strokeStyle = cssVar("--axis");
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartArea.left, py);
    ctx.lineTo(chartArea.right, py);
    ctx.stroke();
    ctx.restore();
  },
};

function renderRatingChart() {
  if (!state.league) return;
  const L = state.league;
  const R = L.ratings;
  const metric = RATING_METRICS.find((m) => m.key === state.ratingMetric) || RATING_METRICS[0];
  $("rating-title").textContent = metric.title;
  if (!R || !R.weeks?.length) {
    $("rating-wrap").hidden = true;
    $("rating-metric").hidden = true;
    $("rating-range").hidden = true;
    $("rating-note").textContent = "Manager ratings are not yet available for this league.";
    if (state.ratingChart) { state.ratingChart.destroy(); state.ratingChart = null; }
    return;
  }
  $("rating-wrap").hidden = false;
  $("rating-metric").hidden = false;
  $("rating-range").hidden = false;

  const start = rangeStart(R);
  const weeks = R.weeks.slice(start);
  const seasonStarts = new Set();
  weeks.forEach((w, i) => { if (i === 0 || weeks[i - 1].season !== w.season) seasonStarts.add(i); });
  const singleSeason = seasonStarts.size === 1;
  const canvas = $("rating-chart");
  const narrow = canvas.parentElement.clientWidth < 560;
  const selectedAny = anySelected();
  const managers = Object.entries(R.managers);
  const current = managers.filter(([, m]) => m.current);
  const former = managers.filter(([, m]) => !m.current).sort((a, b) => (a[1].display_name || "").localeCompare(b[1].display_name || ""));

  const datasets = [];
  const push = (id, m, color, dash, selected) => {
    const data = m[metric.key].slice(start);
    if (!data.some((v) => v != null)) return; // nothing in this range
    const faded = selectedAny && !selected;
    datasets.push({
      label: m.display_name || id,
      shortLabel: shortName(m.display_name || id, narrow ? 14 : 22),
      managerId: id,
      rosterId: m.roster_id,
      isSelected: selected,
      teamColor: color,
      data,
      borderColor: faded ? withAlpha(color, 0.25) : color,
      borderDash: dash,
      borderWidth: selected ? 3 : 2,
      pointRadius: 0,
      pointHoverRadius: selected ? 5 : 4,
      pointHoverBackgroundColor: color,
      pointHoverBorderColor: cssVar("--surface"),
      pointHoverBorderWidth: 2,
      pointHitRadius: 14,
      tension: 0.2,
      spanGaps: false,
      order: selected ? 0 : (m.current ? 1 : 2),
    });
  };
  for (const [id, m] of current) push(id, m, teamColor(m.roster_id), [], m.roster_id === state.selected);
  former.forEach(([id, m], i) => { const st = formerStyle(i); push(id, m, st.color, st.dash, id === state.selectedFormer); });

  const labels = weeks.map((w) => (singleSeason ? `Wk ${w.week}` : `${w.season} wk ${w.week}`));
  const ink2 = cssVar("--ink-2");
  const muted = cssVar("--muted");
  const grid = cssVar("--grid");
  const axis = cssVar("--axis");
  const isZ = metric.key === "career_z";
  const fmt = (v) => (v == null ? "–" : isZ ? (v > 0 ? "+" : "") + v.toFixed(2) : String(Math.round(v)));
  const config = {
    type: "line",
    data: { labels, datasets },
    plugins: [zeroLine, endLabels],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { right: narrow ? 104 : 160, top: 8 } },
      interaction: { mode: "index", intersect: false },
      onClick(evt, elements, chart) {
        const hits = chart.getElementsAtEventForMode(evt, "nearest", { intersect: false }, true);
        if (!hits.length) { selectTeam(null); return; }
        const ds = chart.data.datasets[hits[0].datasetIndex];
        if (ds.rosterId != null) selectTeam(state.selected === ds.rosterId ? null : ds.rosterId);
        else selectFormer(state.selectedFormer === ds.managerId ? null : ds.managerId);
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: cssVar("--surface"),
          titleColor: cssVar("--ink"),
          bodyColor: ink2,
          borderColor: cssVar("--border"),
          borderWidth: 1,
          padding: 10,
          usePointStyle: true,
          boxWidth: 8,
          boxHeight: 8,
          boxPadding: 4,
          itemSort: (a, b) => (b.raw ?? -Infinity) - (a.raw ?? -Infinity),
          callbacks: {
            title: (items) => (items.length ? `${weeks[items[0].dataIndex].season}, after week ${weeks[items[0].dataIndex].week}` : ""),
            label: (item) => `${item.dataset.label}: ${fmt(item.raw)}`,
            labelPointStyle: () => ({ pointStyle: "circle", rotation: 0 }),
            labelColor: (item) => ({ borderColor: item.dataset.teamColor, backgroundColor: item.dataset.teamColor }),
          },
        },
      },
      scales: {
        x: {
          grid: {
            drawTicks: false,
            color: (ctx) => (singleSeason ? grid : (seasonStarts.has(ctx.index) ? axis : "transparent")),
          },
          border: { color: axis },
          ticks: singleSeason
            ? { color: muted, maxRotation: 0, autoSkip: true, maxTicksLimit: narrow ? 6 : 15 }
            : {
                color: muted,
                maxRotation: 0,
                autoSkip: false,
                callback: (value, index) => (seasonStarts.has(index) ? weeks[index].season : null),
              },
        },
        y: {
          grid: { color: grid, drawTicks: false },
          border: { display: false },
          ticks: { color: muted, callback: (v) => (isZ ? v.toFixed(1) : v) },
          ...(isZ ? {} : { suggestedMin: 600, suggestedMax: 1400 }),
        },
      },
    },
  };

  if (state.ratingChart) state.ratingChart.destroy();
  state.ratingChart = new Chart(canvas, config);
  const sel = datasets.find((d) => d.isSelected);
  $("rating-note").textContent = sel
    ? `${sel.label} is highlighted. Click the line again to clear.`
    : `${metric.note}. Regular-season weeks only; each season's end-of-year owner is credited with that roster's weeks. Current members keep their table colour; former members are grey (dashed when a grey repeats).`;
}

// -- loading ------------------------------------------------------------------------------------

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function loadLeague(key) {
  const entry = state.index.leagues.find((l) => l.key === key) || state.index.leagues[0];
  const payload = await fetchJson(`data/${entry.file}`);
  state.league = payload;
  state.sort = null; // sorting is view state and resets on league switch
  assignColors(payload);
  // ?team=<roster_id> preselects a team and ?metric=<key> picks the chart metric (shareable links)
  const params = new URLSearchParams(location.search);
  const wantedTeam = Number(params.get("team"));
  state.selected = payload.teams.some((t) => t.roster_id === wantedTeam) ? wantedTeam : null;
  state.selectedFormer = null;
  const metrics = metricsFor(payload);
  const wantedMetric = params.get("metric");
  if (metrics.some((m) => m.key === wantedMetric)) state.metric = wantedMetric;
  else if (!metrics.some((m) => m.key === state.metric)) state.metric = "playoffs";
  try { history.replaceState(null, "", `#${entry.key}`); } catch (e) { /* ignore */ }
  renderSwitcher();
  renderSummary();
  renderTable();
  renderMetrics();
  renderChart();
  renderRatingPills();
  renderRatingChart();
  $("main").hidden = false;
  $("status").hidden = true;
}

async function main() {
  initTheme();
  initTableHead();
  try {
    state.index = await fetchJson("data/index.json");
    if (!state.index.leagues?.length) throw new Error("no leagues exported");
    const wanted = location.hash.replace("#", "");
    await loadLeague(wanted);
  } catch (err) {
    const status = $("status");
    status.textContent = `Could not load the odds data (${err.message}).`;
    status.classList.add("error");
    status.hidden = false;
  }
  let resizeTimer = null;
  addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderChart, 150);
  });
}

main();
