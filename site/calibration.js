/* Calibration page: reliability chart, PIT histogram and tables from data/calibration.json. Plain JS + Chart.js. */

const OUTCOME_LABELS = {
  playoffs: { label: "Make playoffs", noun: "made the playoffs" },
  bye: { label: "First-round bye", noun: "earned a bye" },
  final: { label: "Reach final", noun: "reached the final" },
  title: { label: "Win championship", noun: "won the title" },
  losers_bracket: { label: "Losers bracket", noun: "landed in the losers bracket" },
  last: { label: "Finish last", noun: "finished last" },
  avoid_losers_bye: { label: "Avoid bottom two", noun: "stayed out of the bottom two" },
};
const HEADLINE_OUTCOMES = ["playoffs", "bye", "title"];
const SERIES_TOKENS = ["--team-1", "--team-2", "--team-3", "--team-4"];

const state = { index: null, report: null, names: {}, outcome: "playoffs", charts: {} };
const $ = (id) => document.getElementById(id);

// -- formatting ---------------------------------------------------------------

function pct(v, digits = 0) {
  return v == null ? "–" : `${(v * 100).toFixed(digits)}%`;
}

function num(v, digits = 3) {
  return v == null ? "–" : v.toFixed(digits);
}

function signed(v, digits = 1) {
  if (v == null) return "–";
  const s = v.toFixed(digits);
  return v > 0 ? `+${s}` : s;
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

function leagueName(key) {
  return state.names[key] || key;
}

function leagueKeys() {
  return Object.keys(state.report.leagues);
}

function outcomeLabel(key) {
  return OUTCOME_LABELS[key]?.label ?? key;
}

// -- theme --------------------------------------------------------------------

function initTheme() {
  let stored = null;
  try { stored = localStorage.getItem("theme"); } catch (e) { /* private mode etc. */ }
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

// -- summary --------------------------------------------------------------------

function renderMeta() {
  const R = state.report;
  const seasons = R.seasons.length;
  const leagues = new Set(R.seasons.map((s) => s.league_key)).size;
  const years = R.seasons.map((s) => Number(s.season));
  const span = years.length ? `${Math.min(...years)}–${Math.max(...years)}` : "";
  const scale = R.residual_scale === 1 ? "no residual scaling" : `residual scale ${R.residual_scale}`;
  $("meta").textContent = `${seasons} league-seasons (${leagues} leagues, ${span}) · ${R.runs.toLocaleString()} simulations per replay · ${scale} · computed ${formatDate(R.generated_at)}`;
}

function renderHeadlines() {
  const O = state.report.overall;
  const items = [];
  for (const key of HEADLINE_OUTCOMES) {
    const s = O.season[key];
    if (!s) continue;
    const bins = s.bins.filter((b) => b.count >= 25 && b.lo >= 0.1 && b.hi <= 0.9);
    const mid = bins.length ? bins.reduce((best, b) => (Math.abs(b.predicted - 0.3) < Math.abs(best.predicted - 0.3) ? b : best), bins[0]) : null;
    const noun = OUTCOME_LABELS[key].noun;
    const skill = s.skill == null ? "" : ` Skill vs the standings: ${signed(s.skill, 2)}.`;
    items.push(
      mid
        ? `<strong>${escapeHtml(outcomeLabel(key))}:</strong> teams shown at about ${pct(mid.predicted)} ${noun} ${pct(mid.observed)} of the time (${mid.count} cases).${skill}`
        : `<strong>${escapeHtml(outcomeLabel(key))}:</strong> ${s.cases} cases.${skill}`,
    );
  }
  const sc = O.score;
  items.push(
    `<strong>Score noise:</strong> real scores fell inside the simulated 80% range ${pct(sc.coverage["80"], 1)} of the time and inside the 95% range ${pct(sc.coverage["95"], 1)} of the time, over ${sc.team_weeks.toLocaleString()} team-weeks.`,
  );
  $("headlines").innerHTML = items.map((t) => `<li>${t}</li>`).join("");
}

// -- outcome switcher and reliability chart ------------------------------------------

function renderSwitcher() {
  const wrap = $("outcome-switcher");
  wrap.innerHTML = "";
  for (const key of state.report.outcomes) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = outcomeLabel(key);
    btn.setAttribute("aria-pressed", String(key === state.outcome));
    btn.addEventListener("click", () => {
      state.outcome = key;
      try { history.replaceState(null, "", `?outcome=${key}`); } catch (e) { /* ignore */ }
      renderSwitcher();
      renderReliability();
      renderSeasonTable();
    });
    wrap.appendChild(btn);
  }
}

function radiusFor(count, maxCount) {
  if (!count) return 0;
  return 4 + 10 * Math.sqrt(count / Math.max(1, maxCount));
}

function renderReliability() {
  const R = state.report;
  const key = state.outcome;
  $("reliability-title").textContent = `${outcomeLabel(key)}: predicted vs observed`;
  const canvas = $("reliability-chart");
  const narrow = canvas.parentElement.clientWidth < 560;
  const surface = cssVar("--surface");
  const keys = leagueKeys();
  const maxCount = Math.max(1, ...keys.flatMap((k) => R.leagues[k].season[key].bins.map((b) => b.count)));
  const datasets = keys.map((k, i) => {
    const color = cssVar(SERIES_TOKENS[i % SERIES_TOKENS.length]);
    const bins = R.leagues[k].season[key].bins.filter((b) => b.count > 0);
    return {
      type: "scatter",
      label: leagueName(k),
      data: bins.map((b) => ({ x: b.predicted * 100, y: b.observed * 100, count: b.count, lo: b.lo, hi: b.hi })),
      backgroundColor: color,
      borderColor: surface,
      borderWidth: 2,
      pointRadius: (ctx) => radiusFor(ctx.raw?.count, maxCount),
      pointHoverRadius: (ctx) => radiusFor(ctx.raw?.count, maxCount) + 2,
      pointHitRadius: 10,
      order: 1,
    };
  });
  datasets.push({
    type: "line",
    label: "Perfect calibration",
    data: [{ x: 0, y: 0 }, { x: 100, y: 100 }],
    borderColor: cssVar("--axis"),
    borderWidth: 1,
    pointRadius: 0,
    pointHitRadius: 0,
    order: 2,
    legendHidden: true,
  });
  const muted = cssVar("--muted");
  const grid = cssVar("--grid");
  const ink2 = cssVar("--ink-2");
  const config = {
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { top: 8, right: 16, left: 4 } },
      interaction: { mode: "nearest", intersect: true },
      plugins: {
        legend: {
          display: true,
          position: "top",
          align: "end",
          labels: {
            color: ink2,
            usePointStyle: true,
            boxWidth: 8,
            boxHeight: 8,
            filter: (item, data) => !data.datasets[item.datasetIndex].legendHidden,
          },
        },
        tooltip: {
          backgroundColor: surface,
          titleColor: cssVar("--ink"),
          bodyColor: ink2,
          borderColor: cssVar("--border"),
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            title: (items) => (items.length ? items[0].dataset.label : ""),
            label: (item) => {
              const r = item.raw;
              if (r.count == null) return "";
              return [
                `Shown at ${Math.round(r.lo * 100)}–${Math.round(r.hi * 100)}% (average ${Math.round(r.x)}%)`,
                `Happened ${Math.round(r.y)}% of the time`,
                `${r.count} cases`,
              ];
            },
          },
        },
      },
      scales: {
        x: {
          type: "linear",
          min: 0,
          max: 100,
          title: { display: true, text: "Predicted chance", color: muted },
          grid: { color: grid, drawTicks: false },
          border: { color: cssVar("--axis") },
          ticks: { color: muted, stepSize: narrow ? 25 : 10, callback: (v) => `${v}%` },
        },
        y: {
          type: "linear",
          min: 0,
          max: 100,
          title: { display: true, text: "Observed rate", color: muted },
          grid: { color: grid, drawTicks: false },
          border: { display: false },
          ticks: { color: muted, stepSize: narrow ? 25 : 10, callback: (v) => `${v}%` },
        },
      },
    },
  };
  if (state.charts.reliability) state.charts.reliability.destroy();
  state.charts.reliability = new Chart(canvas, config);
}

// -- PIT histogram ------------------------------------------------------------------------

function renderPit() {
  const sc = state.report.overall.score;
  const counts = sc.pit_histogram || [];
  const total = counts.reduce((a, b) => a + b, 0);
  const expected = total / Math.max(1, counts.length);
  const canvas = $("pit-chart");
  const labels = counts.map((_, i) => `${i * 10}–${(i + 1) * 10}`);
  const muted = cssVar("--muted");
  const grid = cssVar("--grid");
  const config = {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Team-weeks",
          data: counts,
          backgroundColor: cssVar("--accent"),
          borderRadius: { topLeft: 4, topRight: 4 },
          borderSkipped: "bottom",
          maxBarThickness: 24,
          categoryPercentage: 0.8,
          barPercentage: 0.9,
        },
      ],
    },
    plugins: [
      {
        id: "expectedLine",
        afterDatasetsDraw(chart) {
          const y = chart.scales.y.getPixelForValue(expected);
          const { ctx, chartArea } = chart;
          ctx.save();
          ctx.strokeStyle = cssVar("--ink-2");
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(chartArea.left, y);
          ctx.lineTo(chartArea.right, y);
          ctx.stroke();
          ctx.fillStyle = cssVar("--ink-2");
          ctx.font = "11px system-ui, -apple-system, \"Segoe UI\", sans-serif";
          ctx.textBaseline = "bottom";
          ctx.textAlign = "right";
          ctx.fillText(`flat = ${Math.round(expected)} per tenth`, chartArea.right - 4, y - 3);
          ctx.restore();
        },
      },
    ],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: cssVar("--surface"),
          titleColor: cssVar("--ink"),
          bodyColor: cssVar("--ink-2"),
          borderColor: cssVar("--border"),
          borderWidth: 1,
          padding: 10,
          displayColors: false,
          callbacks: {
            title: (items) => (items.length ? `Real score in the ${items[0].label}th percentile of its simulation` : ""),
            label: (item) => `${item.raw} team-weeks (${pct(item.raw / Math.max(1, total), 1)})`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Percentile of the real score within its simulated range", color: muted },
          grid: { display: false },
          border: { color: cssVar("--axis") },
          ticks: { color: muted, maxRotation: 0, autoSkip: true, maxTicksLimit: canvas.parentElement.clientWidth < 420 ? 5 : 10, font: { size: 10 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: grid, drawTicks: false },
          border: { display: false },
          ticks: { color: muted, precision: 0 },
        },
      },
    },
  };
  if (state.charts.pit) state.charts.pit.destroy();
  state.charts.pit = new Chart(canvas, config);
}

// -- tables ---------------------------------------------------------------------------------

function table(id, head, rows) {
  const th = head.map((h, i) => `<th scope="col"${i ? ' class="num"' : ""}>${h}</th>`).join("");
  const body = rows
    .map((r) => `<tr>${r.map((c, i) => (i ? `<td class="num">${c}</td>` : `<th scope="row">${c}</th>`)).join("")}</tr>`)
    .join("");
  $(id).innerHTML = `<thead><tr>${th}</tr></thead><tbody>${body}</tbody>`;
}

function renderSeasonTable() {
  const R = state.report;
  const key = state.outcome;
  const scopes = [["overall", "All seasons"], ...leagueKeys().map((k) => [k, leagueName(k)])];
  const rows = scopes.map(([k, name]) => {
    const s = k === "overall" ? R.overall.season[key] : R.leagues[k].season[key];
    return [escapeHtml(name), s.cases.toLocaleString(), s.team_seasons, pct(s.observed_rate, 1), num(s.brier, 4), num(s.baseline_brier, 4), signed(s.skill, 3)];
  });
  table("season-table", [escapeHtml(outcomeLabel(key)), "Cases", "Team-seasons", "Happened", "Brier", "Baseline", "Skill"], rows);
}

function renderCoverage() {
  const R = state.report;
  const scopes = [["overall", "All"], ...leagueKeys().map((k) => [k, leagueName(k)])];
  const head = ["Simulated range", "Should contain", ...scopes.map(([, n]) => escapeHtml(n)), "Simulated lineup (all)"];
  const rows = ["50", "80", "95"].map((lvl) => [
    `${lvl}% range`,
    `${lvl}%`,
    ...scopes.map(([k]) => pct((k === "overall" ? R.overall : R.leagues[k]).score.coverage[lvl], 1)),
    pct(R.overall.score.coverage_sim_lineup[lvl], 1),
  ]);
  table("coverage-table", head, rows);
  const sc = R.overall.score;
  $("bias-note").textContent = `On average the simulation expected ${signed(sc.mean_bias, 1)} points more than teams actually scored (${signed(sc.mean_bias_sim_lineup, 1)} against the simulated lineup's own actual points). Typical simulated spread for one team-week: ±${num(sc.mean_sim_sd, 1)} points.`;
}

function renderGames() {
  const g = state.report.overall.game;
  $("game-summary").textContent = `${g.games.toLocaleString()} regular-season games · Brier ${num(g.brier, 4)} (0.25 = coin flip)`;
  const rows = g.bins.filter((b) => b.count > 0).map((b) => [
    `Favourite at ${Math.round(b.lo * 100)}–${Math.round(b.hi * 100)}%`,
    pct(b.predicted, 1),
    pct(b.observed, 1),
    b.count,
  ]);
  table("game-table", ["Simulated chance", "Average predicted", "Favourite won", "Games"], rows);
}

function renderLineup() {
  const R = state.report;
  const rows = [...leagueKeys().map((k) => [k, leagueName(k)]), ["overall", "All"]].map(([k, name]) => {
    const l = k === "overall" ? R.overall.lineup : R.leagues[k].lineup;
    return [escapeHtml(name), l.team_weeks.toLocaleString(), signed(l.projected_gap, 1), signed(l.actual_gap, 1)];
  });
  table("lineup-table", ["League", "Team-weeks", "Projected points left on the bench", "Actual points left on the bench"], rows);
}

function renderCaveats() {
  $("caveats").innerHTML = (state.report.caveats || []).map((c) => `<li>${escapeHtml(c)}</li>`).join("");
}

function renderCharts() {
  if (!state.report) return;
  renderReliability();
  renderPit();
}

// -- loading ----------------------------------------------------------------------------------

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function main() {
  initTheme();
  const status = $("status");
  try {
    state.index = await fetchJson("data/index.json");
    for (const l of state.index.leagues || []) state.names[l.key] = l.name;
    if (!state.index.calibration || !state.index.calibration.file) {
      $("not-run").hidden = false;
      status.hidden = true;
      return;
    }
    state.report = await fetchJson(`data/${state.index.calibration.file}`);
    const wanted = new URLSearchParams(location.search).get("outcome");
    if (state.report.outcomes.includes(wanted)) state.outcome = wanted;
    renderMeta();
    renderHeadlines();
    renderSwitcher();
    renderSeasonTable();
    renderCoverage();
    renderGames();
    renderLineup();
    renderCaveats();
    $("main").hidden = false;
    status.hidden = true;
    renderCharts();
  } catch (err) {
    status.textContent = `Could not load the calibration data (${err.message}).`;
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
