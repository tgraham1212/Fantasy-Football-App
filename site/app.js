/* Playoff odds site: league switcher, odds table, odds-over-time chart. Plain JS + Chart.js. */

const METRICS = [
  { key: "playoffs", label: "Playoffs", title: "Playoff chances by week" },
  { key: "bye", label: "Bye", title: "First-round bye chances by week" },
  { key: "final", label: "Final", title: "Chances of reaching the final by week" },
  { key: "title", label: "Title", title: "Title chances by week" },
];

const state = {
  index: null,
  league: null, // current league payload
  metric: "playoffs",
  selected: null, // roster_id
  chart: null,
};

const $ = (id) => document.getElementById(id);

// -- formatting ---------------------------------------------------------------

function pct(v) {
  if (v == null) return "–";
  if (v >= 0.9995) return "100%";
  if (v >= 0.995) return ">99%";
  if (v > 0 && v < 0.005) return "<1%";
  return `${Math.round(v * 100)}%`;
}

function delta(d) {
  if (d == null) return "";
  const p = Math.round(d * 100);
  if (p === 0) return `<span class="delta flat" title="No change">—</span>`;
  const cls = p > 0 ? "up" : "down";
  const arrow = p > 0 ? "▲" : "▼";
  return `<span class="delta ${cls}">${arrow}${Math.abs(p)}</span>`;
}

function record(t) {
  return `${t.wins}-${t.losses}${t.ties ? `-${t.ties}` : ""}`;
}

function projRecord(t) {
  return `${t.proj_wins.toFixed(1)}-${t.proj_losses.toFixed(1)}`;
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
    renderChart();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderChart);
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

function renderTable() {
  const body = $("odds-body");
  body.innerHTML = "";
  for (const t of state.league.teams) {
    const tr = document.createElement("tr");
    tr.dataset.roster = String(t.roster_id);
    tr.tabIndex = 0;
    tr.setAttribute("aria-selected", String(state.selected === t.roster_id));
    tr.innerHTML = `
      <td class="team-col"><span class="team-name"><span class="sel-dot" aria-hidden="true"></span>${escapeHtml(t.team_name)}</span><span class="owner">${escapeHtml(t.display_name ?? "")}</span></td>
      <td class="num">${record(t)}</td>
      <td class="num">${t.points_for.toFixed(1)}</td>
      <td class="num">${projRecord(t)}</td>
      <td class="num pct-main">${pct(t.playoffs)}</td>
      <td class="num">${delta(t.change.playoffs)}</td>
      <td class="num">${pct(t.bye)}</td>
      <td class="num">${pct(t.final)}</td>
      <td class="num">${pct(t.title)}</td>
      <td class="num">${pct(t.losers_bracket)}</td>
      <td class="num">${pct(t.last)}</td>`;
    const toggle = () => selectTeam(state.selected === t.roster_id ? null : t.roster_id);
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
    body.appendChild(tr);
  }
}

function selectTeam(rosterId) {
  state.selected = rosterId;
  for (const tr of $("odds-body").querySelectorAll("tr")) {
    tr.setAttribute("aria-selected", String(Number(tr.dataset.roster) === rosterId));
  }
  renderChart();
}

// -- metric switcher -------------------------------------------------------------------

function renderMetrics() {
  const box = $("metric-switcher");
  box.innerHTML = "";
  for (const m of METRICS) {
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

/* Direct labels at each line's end. On narrow screens only the selected team is labeled. */
const endLabels = {
  id: "endLabels",
  afterDatasetsDraw(chart) {
    const { ctx, chartArea } = chart;
    const narrow = chart.width < 560;
    const items = [];
    chart.data.datasets.forEach((ds, i) => {
      if (!chart.isDatasetVisible(i)) return;
      const selected = ds.rosterId === state.selected;
      if (narrow && !selected) return;
      const meta = chart.getDatasetMeta(i);
      let last = null;
      for (let k = meta.data.length - 1; k >= 0; k--) {
        if (ds.data[k] != null) { last = meta.data[k]; break; }
      }
      if (!last) return;
      items.push({ y: last.y, x: last.x, text: ds.shortLabel, selected });
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
    const dimmed = state.selected != null;
    for (const it of items) {
      ctx.fillStyle = it.selected ? cssVar("--accent") : (dimmed ? cssVar("--muted") : cssVar("--ink-2"));
      ctx.globalAlpha = it.selected || !dimmed ? 1 : 0.7;
      ctx.fillText(it.text, it.x + 7, it.y);
    }
    ctx.restore();
  },
};

function shortName(name, max) {
  return name.length > max ? `${name.slice(0, max - 1).trimEnd()}…` : name;
}

function renderChart() {
  if (!state.league) return;
  const L = state.league;
  const metric = METRICS.find((m) => m.key === state.metric);
  $("chart-title").textContent = metric.title;
  const weeks = L.history.weeks;
  const canvas = $("odds-chart");
  const narrow = canvas.parentElement.clientWidth < 560;
  const selectedAny = state.selected != null;

  const datasets = L.teams.map((t) => {
    const selected = t.roster_id === state.selected;
    return {
      label: t.team_name,
      shortLabel: shortName(t.team_name, narrow ? 14 : 22),
      rosterId: t.roster_id,
      data: (L.history.teams[String(t.roster_id)] || {})[state.metric]?.map((v) => (v == null ? null : v * 100)) ?? [],
      borderColor: selected ? cssVar("--accent") : (selectedAny ? cssVar("--line-dim") : cssVar("--line")),
      borderWidth: selected ? 3 : 2,
      pointRadius: 0,
      pointHoverRadius: selected ? 5 : 4,
      pointHoverBackgroundColor: selected ? cssVar("--accent") : cssVar("--muted"),
      pointHoverBorderColor: cssVar("--surface"),
      pointHoverBorderWidth: 2,
      pointHitRadius: 14,
      tension: 0.25,
      spanGaps: true,
      order: selected ? 0 : 1,
    };
  });

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
      layout: { padding: { right: narrow ? 96 : 150, top: 8 } },
      interaction: { mode: "index", intersect: false },
      onClick(evt, elements, chart) {
        const hits = chart.getElementsAtEventForMode(evt, "nearest", { intersect: false }, true);
        if (!hits.length) { selectTeam(null); return; }
        const rid = chart.data.datasets[hits[0].datasetIndex].rosterId;
        selectTeam(state.selected === rid ? null : rid);
      },
      plugins: {
        legend: { display: false }, // the table doubles as the legend; lines are labeled directly
        tooltip: {
          backgroundColor: cssVar("--surface"),
          titleColor: cssVar("--ink"),
          bodyColor: ink2,
          borderColor: cssVar("--border"),
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          itemSort: (a, b) => (b.raw ?? -1) - (a.raw ?? -1),
          callbacks: {
            title: (items) => (items.length ? (weeks[items[0].dataIndex] === 0 ? "Preseason" : `After week ${weeks[items[0].dataIndex]}`) : ""),
            label: (item) => `${item.dataset.label}: ${item.raw == null ? "–" : `${Math.round(item.raw)}%`}`,
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
          max: 100,
          grid: { color: grid, drawTicks: false },
          border: { display: false },
          ticks: { color: muted, stepSize: 25, callback: (v) => `${v}%` },
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
    ? `${sel.team_name} is highlighted. Click the team again to clear.`
    : "Each line is a team. Hover for every team's chance after a given week; click a line or a table row to highlight one team.";
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
  // ?team=<roster_id> preselects a team and ?metric=bye|final|title picks the chart metric (shareable links)
  const params = new URLSearchParams(location.search);
  const wantedTeam = Number(params.get("team"));
  state.selected = payload.teams.some((t) => t.roster_id === wantedTeam) ? wantedTeam : null;
  if (METRICS.some((m) => m.key === params.get("metric"))) state.metric = params.get("metric");
  try { history.replaceState(null, "", `#${entry.key}`); } catch (e) { /* ignore */ }
  renderSwitcher();
  renderSummary();
  renderTable();
  renderMetrics();
  renderChart();
  $("main").hidden = false;
  $("status").hidden = true;
}

async function main() {
  initTheme();
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
