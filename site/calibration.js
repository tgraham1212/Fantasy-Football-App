/* Calibration page: reliability chart, PIT histogram and tables from data/calibration.json. Plain JS + Chart.js. */

import { initRefresh } from "./refresh.js?v=__BUILD__";
import { initUpdates } from "./updates.js?v=__BUILD__";

const OUTCOME_LABELS = {
  playoffs: { label: "Make playoffs", noun: /*copy:CAL-44*/"made the playoffs" },
  bye: { label: "First-round bye", noun: /*copy:CAL-45*/"earned a bye" },
  final: { label: "Reach final", noun: /*copy:CAL-46*/"reached the final" },
  title: { label: "Win championship", noun: /*copy:CAL-47*/"won the title" },
  losers_bracket: { label: "Losers bracket", noun: /*copy:CAL-48*/"landed in the losers bracket" },
  last: { label: "Finish last", noun: /*copy:CAL-49*/"finished last" },
  avoid_losers_bye: { label: "Avoid bottom two", noun: /*copy:CAL-50*/"stayed out of the bottom two" },
};
const HEADLINE_OUTCOMES = ["playoffs", "bye", "title"];
const SERIES_TOKENS = ["--team-1", "--team-2", "--team-3", "--team-4"];

const state = { index: null, report: null, names: {}, leagues: {}, outcome: "playoffs", charts: {} };
const POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"];
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
  const floor = R.replacement_floor === false ? "replacement floor off" : `replacement floor on${R.replacement_top_n ? ` (best ${R.replacement_top_n} free agents)` : ""}`;
  const drift = R.roster_drift === false ? "roster drift off" : "roster drift on";
  $("meta").textContent = /*copy:CAL-33*/`${seasons} league-seasons (${leagues} leagues, ${span}) · ${R.runs.toLocaleString()} simulations per replay · ${scale} · ${floor} · ${drift} · computed ${formatDate(R.generated_at)}`;
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
    const skill = s.skill == null ? "" : /*copy:CAL-36*/` Skill vs the standings: ${signed(s.skill, 2)}.`;
    items.push(
      mid
        ? /*copy:CAL-34*/`<strong>${escapeHtml(outcomeLabel(key))}:</strong> teams shown at about ${pct(mid.predicted)} ${noun} ${pct(mid.observed)} of the time (${mid.count} cases).${skill}`
        : /*copy:CAL-35*/`<strong>${escapeHtml(outcomeLabel(key))}:</strong> ${s.cases} cases.${skill}`,
    );
  }
  const sc = O.score;
  items.push(
    /*copy:CAL-37*/`<strong>Score noise:</strong> real scores fell inside the simulated 80% range ${pct(sc.coverage["80"], 1)} of the time and inside the 95% range ${pct(sc.coverage["95"], 1)} of the time, over ${sc.team_weeks.toLocaleString()} team-weeks.`,
  );
  $("headlines").innerHTML = items.map((t) => `<li>${t}</li>`).join("");
}

// -- how the odds are made ----------------------------------------------------------

function keepOf(model, k) {
  const slopes = model && model.drift && model.drift.slopes;
  if (!slopes || !slopes.length) return null;
  return slopes[Math.min(Math.max(k, 1), slopes.length) - 1];
}

function sdOf(model, k) {
  const sds = model && model.drift && model.drift.sds;
  if (!sds || !sds.length) return null;
  return sds[Math.min(Math.max(k, 1), sds.length) - 1];
}

function renderHow() {
  const R = state.report;
  const cov = R.overall && R.overall.score && R.overall.score.coverage;
  if (cov && cov["80"] != null) {
    $("how-noise").textContent = /*copy:CAL-24*/`Checked against ${R.seasons.length} past seasons, the real score fell inside the simulated 80% range ${pct(cov["80"], 1)} of the time, so the noise is about the right width.`;
  }
  const keys = leagueKeys();
  const withData = keys.filter((k) => state.leagues[k] && (state.leagues[k].replacement || state.leagues[k].model));
  const n = R.replacement_top_n || (withData.length && state.leagues[withData[0]].replacement && state.leagues[withData[0]].replacement.top_n);
  if (n) $("how-floor").textContent = /*copy:CAL-25*/`Here that means the best ${n} free agents at each position, averaged, using this week's projections.`;

  const driftBits = [];
  const tables = [];
  for (const key of keys) {
    const L = state.leagues[key];
    if (!L) continue;
    const name = escapeHtml(leagueName(key));
    const rep = L.replacement;
    if (rep && rep.levels) {
      const cells = (obj, digits) => POSITIONS.map((p) => `<td class="num">${obj && obj[p] != null ? obj[p].toFixed(digits) : "–"}</td>`).join("");
      tables.push(`<div><h3>${/*copy:CAL-26*/`${name}: what a replacement-level player scores`}</h3>
        <div class="table-wrap" tabindex="0" role="region" aria-label="${name} replacement levels"><table class="plain"><thead><tr><th scope="col"></th>${POSITIONS.map((p) => `<th scope="col" class="num">${p}</th>`).join("")}</tr></thead>
        <tbody><tr><th scope="row">Week ${rep.week} (projected)</th>${cells(rep.levels, 1)}</tr>
        <tr><th scope="row">Season value (actual, shrunk)</th>${cells(rep.season, 1)}</tr></tbody></table></div>
        <p class="hint">${/*copy:CAL-27*/"Points per week under this league's scoring. The season value is what those pickups have really scored so far, blended with earlier seasons early in the year."}</p></div>`);
    }
    const m = L.model;
    if (m && m.roster_drift && keepOf(m, 2) != null) {
      const two = Math.round(20 * keepOf(m, 2));
      const twelve = Math.round(20 * keepOf(m, 12));
      const sd = sdOf(m, 12);
      const spread = sd ? /*copy:CAL-28*/` and allows about ${sd.toFixed(1)} points of random roster change either way by twelve weeks out` : "";
      if (twelve >= 20) {
        driftBits.push(/*copy:CAL-29*/`In ${leagueName(key)}, past seasons show a team's edge holding up once its lineup holes are filled, so the model keeps the full edge${spread}.`);
      } else {
        driftBits.push(/*copy:CAL-30*/`In ${leagueName(key)}, a team 20 points a week better than average is expected to keep about ${two} of those points two weeks out and ${twelve} twelve weeks out${spread}.`);
      }
    } else if (m && m.roster_drift === false) {
      driftBits.push(/*copy:CAL-31*/`${leagueName(key)}: drift is currently switched off.`);
    }
  }
  $("how-drift").textContent = driftBits.join(" ");
  $("how-tables").innerHTML = tables.join("");
  $("how-fallback").hidden = tables.length > 0 && driftBits.length > 0;
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
                /*copy:CAL-39*/`Shown at ${Math.round(r.lo * 100)}–${Math.round(r.hi * 100)}% (average ${Math.round(r.x)}%)`,
                /*copy:CAL-40*/`Happened ${Math.round(r.y)}% of the time`,
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
            title: (items) => (items.length ? /*copy:CAL-41*/`Real score in the ${items[0].label}th percentile of its simulation` : ""),
            label: (item) => `${item.raw} team-weeks (${pct(item.raw / Math.max(1, total), 1)})`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: /*copy:CAL-42*/"Percentile of the real score within its simulated range", color: muted },
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
  $("bias-note").textContent = /*copy:CAL-32*/`On average the simulation expected ${signed(sc.mean_bias, 1)} points more than teams actually scored (${signed(sc.mean_bias_sim_lineup, 1)} against the simulated lineup's own actual points). Typical simulated spread for one team-week: ±${num(sc.mean_sim_sd, 1)} points.`;
}

function renderGames() {
  const g = state.report.overall.game;
  $("game-summary").textContent = /*copy:CAL-43*/`${g.games.toLocaleString()} regular-season games · Brier ${num(g.brier, 4)} (0.25 = coin flip)`;
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
    initRefresh(state.index);
    // New data deployed while the page is open: redraw in place, keeping the outcome shown.
    initUpdates(state.index.last_refresh, async (index) => {
      state.index = index;
      await loadReport();
    });
    await loadReport();
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

async function loadReport() {
  const status = $("status");
  for (const l of state.index.leagues || []) state.names[l.key] = l.name;
  if (!state.index.calibration || !state.index.calibration.file) {
    $("not-run").hidden = false;
    status.hidden = true;
    return;
  }
  state.report = await fetchJson(`data/${state.index.calibration.file}`);
  const leagueFiles = await Promise.all((state.index.leagues || []).map((l) => fetchJson(`data/${l.file}`).catch(() => null)));
  (state.index.leagues || []).forEach((l, i) => { if (leagueFiles[i]) state.leagues[l.key] = leagueFiles[i]; });
  const wanted = new URLSearchParams(location.search).get("outcome");
  if (state.report.outcomes.includes(wanted)) state.outcome = wanted;
  else if (!state.report.outcomes.includes(state.outcome)) state.outcome = "playoffs";
  renderMeta();
  renderHeadlines();
  renderHow();
  renderSwitcher();
  renderSeasonTable();
  renderCoverage();
  renderGames();
  renderLineup();
  renderCaveats();
  $("main").hidden = false;
  status.hidden = true;
  renderCharts();
}

main();
