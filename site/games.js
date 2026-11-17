/* Games page: this season's matchups week by week with the model's forecast per game. */

const state = {
  leagueKey: null,
  leagueName: "",
  entry: null, // index.leagues[i].games, or null
  index: null, // data/<league>/games/index.json
  weeks: {}, // week -> payload (cached per league)
  week: null,
  colorOf: () => "--accent", // roster_id -> css token name, from the Predictions page
  charts: [],
};

const PLACE_LABEL = { 1: "Championship", 3: "3rd place", 5: "5th place" };
const $ = (id) => document.getElementById(id);
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function withAlpha(hex, alpha) {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h.slice(0, 6);
  return `#${full}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;
}

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading ----------------------------------------------------------------------------------

/* Called by app.js whenever a league loads. `colorOf(rid)` gives the team's colour token. */
export async function loadGames(leagueKey, leagueName, entry, colorOf) {
  if (state.leagueKey !== leagueKey) {
    state.weeks = {};
    state.index = null;
    state.week = null;
  }
  state.leagueKey = leagueKey;
  state.leagueName = leagueName;
  state.entry = entry || null;
  state.colorOf = colorOf || state.colorOf;
  $("games-title").textContent = `${leagueName} · Games`;
  if (!state.entry) {
    $("games-unavailable").hidden = false;
    $("games-content").hidden = true;
    $("games-controls").hidden = true;
    return;
  }
  state.index = await fetchJson(`data/${state.entry.file}`);
  const weeks = state.index.weeks.map((w) => w.week);
  if (!weeks.includes(state.week)) state.week = weeks.includes(state.index.current) ? state.index.current : weeks[weeks.length - 1];
  await showWeek(state.week);
}

async function showWeek(week) {
  state.week = week;
  if (!state.weeks[week]) {
    const info = state.index.weeks.find((w) => w.week === week);
    state.weeks[week] = await fetchJson(`data/${state.leagueKey}/games/${info.file}`);
  }
  render();
}

/* Re-draw with the current theme's colours (called by app.js on theme changes). */
export function rerenderGames() {
  if (state.index && state.weeks[state.week]) render();
}

// -- rendering ----------------------------------------------------------------------------------

function render() {
  $("games-unavailable").hidden = true;
  $("games-content").hidden = false;
  $("games-controls").hidden = false;
  renderControls();
  renderNote();
  renderCards();
}

function renderControls() {
  const select = $("games-week");
  select.innerHTML = "";
  for (const w of state.index.weeks) {
    const opt = document.createElement("option");
    opt.value = String(w.week);
    opt.textContent = w.week === state.index.current ? `${w.label} (this week)` : w.label;
    select.appendChild(opt);
  }
  select.value = String(state.week);
  const weeks = state.index.weeks.map((w) => w.week);
  const i = weeks.indexOf(state.week);
  $("games-prev").disabled = i <= 0;
  $("games-next").disabled = i >= weeks.length - 1;
}

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function renderNote() {
  const W = state.weeks[state.week];
  let text;
  if (W.kind === "final") {
    text = W.source === "pre-week"
      ? `Final. Shown against the forecast made before the week (after week ${W.forecast_as_of}), from before the projection log began. A check marks the winner; the lines on each chart are the actual scores.`
      : "Final. Shown against the prediction of record: the lineups the managers started, each player at his last projection before kickoff. A check marks the winner; the lines on each chart are the actual scores.";
  } else {
    text = `Forecast from the simulation run ${formatTime(W.generated_at)} (after week ${W.forecast_as_of}), 10,000 simulations per game. Each chart shows the spread of simulated scores.`;
    if (W.games.some((g) => g.projected)) {
      text += " Playoff pairings are projected: teams seeded by expected finish, the favourite advancing; each game says how often that pairing happened in the simulations.";
    }
    text += " Lineups are the model's best projected lineup; players listed as out can still appear in it until their projection drops.";
  }
  $("games-note").textContent = text;
}

function winFill(p) {
  const t = Math.round(Math.abs(p - 0.5) * 200);
  const pole = p >= 0.5 ? "var(--win-hi)" : "var(--win-lo)";
  return `background: color-mix(in oklab, var(--win-mid) ${100 - t}%, ${pole}); color: var(--win-ink);`;
}

function gameLabel(g) {
  if (g.bracket === "regular") return "";
  const bracket = g.bracket === "losers" ? "Toilet bowl" : "";
  let name = PLACE_LABEL[g.place] || (g.round === 1 ? "Quarterfinal" : g.round === 2 ? "Semifinal" : "Playoffs");
  if (g.bracket === "losers") name = g.place === 1 ? "Toilet bowl final" : g.place ? `Toilet bowl, ${PLACE_LABEL[g.place].toLowerCase()}` : `Toilet bowl ${name.toLowerCase()}`;
  const seeds = g.seeds && g.seeds.every((s) => s) ? ` · #${g.seeds[0]} v #${g.seeds[1]}` : "";
  const projected = g.projected ? ` · projected, happens in ${Math.round((g.frequency || 0) * 100)}% of simulations` : "";
  return `${bracket && !name.startsWith("Toilet") ? bracket + " " : ""}${name}${seeds}${projected}`;
}

function teamRow(g, t) {
  const color = cssVar(state.colorOf(t.roster_id));
  const won = g.winner != null && g.winner === t.roster_id;
  const actual = t.actual != null ? `<span class="actual">${t.actual.toFixed(1)} actual</span>` : "";
  return `
    <div class="game-team">
      <span class="swatch" style="--team: ${color}" aria-hidden="true"></span>
      <span class="who"><span class="owner-name">${escapeHtml(t.display_name || `Roster ${t.roster_id}`)}</span><span class="team">${escapeHtml(t.team_name || "")}</span></span>
      <span class="mean"><span class="num">${t.mean.toFixed(1)}</span><span class="unit">avg pts</span>${actual}</span>
      <span class="win" style="${winFill(t.win_prob)}" title="Win probability">${won ? '<span class="check" aria-label="won">&#10003;</span>' : ""}${Math.round(t.win_prob * 100)}%</span>
    </div>`;
}

function playerList(rows) {
  return rows.map((r) => `<li${r.replacement ? ' class="fill"' : ""}><span class="pos">${escapeHtml(r.position)}</span><span class="pname">${escapeHtml(r.name)}</span><span class="pts">${Number(r.projected).toFixed(1)}</span></li>`).join("");
}

function teamPlayers(t) {
  const out = t.not_playing.length
    ? `<p class="out-label">Not playing</p><ul class="out">${t.not_playing.map((o) => `<li><span class="pname">${escapeHtml(o.name)}</span><span class="reason">${escapeHtml(o.reason)}</span></li>`).join("")}</ul>`
    : "";
  return `
    <div class="team-players">
      <p class="tp-name">${escapeHtml(t.display_name || "")}</p>
      <ul class="key">${playerList(t.key_players)}</ul>
      <details class="lineup"><summary>Full lineup</summary><ul>${t.lineup.map((r) => `<li${r.replacement ? ' class="fill"' : ""}><span class="pos">${escapeHtml(r.slot)}</span><span class="pname">${escapeHtml(r.name)}</span><span class="pts">${Number(r.projected).toFixed(1)}</span></li>`).join("")}</ul></details>
      ${out}
    </div>`;
}

function cardHtml(g, idx) {
  const label = gameLabel(g);
  return `
    <section class="game-card${g.projected ? " projected" : ""}">
      ${label ? `<p class="game-label">${escapeHtml(label)}</p>` : ""}
      <div class="game-body">
        <div class="game-rows">${g.teams.map((t) => teamRow(g, t)).join("")}</div>
        <div class="game-chart"><canvas id="game-chart-${idx}" role="img" aria-label="Simulated score distributions for ${escapeHtml(g.teams.map((t) => t.display_name).join(" and "))}"></canvas></div>
      </div>
      <div class="game-players">${g.teams.map(teamPlayers).join("")}</div>
    </section>`;
}

function byeHtml(b) {
  const color = cssVar(state.colorOf(b.roster_id));
  const where = b.bracket === "losers" ? "toilet bowl" : "playoffs";
  return `
    <section class="game-card bye">
      <p class="game-label">First-round bye · #${b.seed} seed in the ${where}</p>
      <div class="game-team"><span class="swatch" style="--team: ${color}" aria-hidden="true"></span>
        <span class="who"><span class="owner-name">${escapeHtml(b.display_name || `Roster ${b.roster_id}`)}</span><span class="team">${escapeHtml(b.team_name || "")}</span></span>
        <span class="bye-tag">Bye</span></div>
    </section>`;
}

/* Cards in display order: regular weeks as stored; playoff weeks per bracket, the 1 seed's side first. */
function layout(W) {
  if (!W.playoffs) return [{ heading: null, items: W.games.map((g) => ({ game: g })) }];
  const sections = [];
  for (const bracket of ["winners", "losers"]) {
    const games = W.games.filter((g) => g.bracket === bracket);
    const byes = W.byes.filter((b) => b.bracket === bracket).sort((a, b) => a.seed - b.seed);
    if (!games.length && !byes.length) continue;
    let items = games.map((g) => ({ game: g }));
    if (byes.length === 2 && games.length === 2) {
      // round 1: the 1 seed and the 4v5 game on top, the 3v6 game and the 2 seed below
      items = [{ bye: byes[0] }, { game: games[0] }, { game: games[1] }, { bye: byes[1] }];
    }
    sections.push({ heading: bracket === "losers" ? "Toilet bowl" : "Playoffs", items });
  }
  return sections;
}

function destroyCharts() {
  for (const c of state.charts) c.destroy();
  state.charts = [];
}

function renderCards() {
  destroyCharts();
  const W = state.weeks[state.week];
  const grid = $("games-grid");
  let html = "";
  let idx = 0;
  const games = [];
  for (const section of layout(W)) {
    if (section.heading) html += `<h3 class="games-section">${escapeHtml(section.heading)}</h3>`;
    html += `<div class="games-cards">`;
    for (const item of section.items) {
      if (item.bye) html += byeHtml(item.bye);
      else {
        html += cardHtml(item.game, idx);
        games.push([idx, item.game]);
        idx += 1;
      }
    }
    html += `</div>`;
  }
  grid.innerHTML = html || `<p class="hint">No games stored for this week.</p>`;
  for (const [i, g] of games) drawChart($(`game-chart-${i}`), g);
}

/* Vertical lines at the actual scores, in each team's colour. */
const actualLines = {
  id: "actualLines",
  afterDatasetsDraw(chart) {
    const lines = chart.options.plugins.actualLines?.lines || [];
    const { ctx, chartArea, scales } = chart;
    for (const line of lines) {
      const x = scales.x.getPixelForValue(line.value);
      if (x < chartArea.left || x > chartArea.right) continue;
      ctx.save();
      ctx.strokeStyle = line.color;
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 3]);
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.stroke();
      ctx.restore();
    }
  },
};

function drawChart(canvas, g) {
  if (!canvas || typeof Chart === "undefined") return;
  const { start, width, shares } = g.hist;
  const n = shares[0].length;
  const xs = Array.from({ length: n }, (_, i) => start + width * (i + 0.5));
  const ink2 = cssVar("--ink-2");
  const datasets = g.teams.map((t, k) => {
    const color = cssVar(state.colorOf(t.roster_id));
    return {
      label: t.display_name,
      data: xs.map((x, i) => ({ x, y: shares[k][i] / 10 })),
      borderColor: color,
      backgroundColor: withAlpha(color, 0.28),
      fill: "origin",
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.35,
    };
  });
  const lo = start;
  let hi = start + width * n;
  const lines = g.teams.filter((t) => t.actual != null).map((t) => ({ value: t.actual, color: cssVar(state.colorOf(t.roster_id)) }));
  for (const l of lines) hi = Math.max(hi, l.value + width);
  state.charts.push(new Chart(canvas, {
    type: "line",
    data: { datasets },
    plugins: [actualLines],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      parsing: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { type: "linear", min: Math.min(lo, ...lines.map((l) => l.value - width)), max: hi, grid: { display: false }, ticks: { color: ink2, maxTicksLimit: 5 }, title: { display: true, text: "points", color: ink2, font: { size: 11 } } },
        y: { display: false, beginAtZero: true },
      },
      plugins: {
        legend: { display: false },
        actualLines: { lines },
        tooltip: {
          callbacks: {
            title: (items) => `${Math.round(items[0].parsed.x - width / 2)}-${Math.round(items[0].parsed.x + width / 2)} points`,
            label: (item) => `${item.dataset.label}: ${item.parsed.y.toFixed(1)}% of simulations`,
          },
        },
      },
    },
  }));
}

// -- wiring ---------------------------------------------------------------------------------------

export function initGames() {
  $("games-week").addEventListener("change", (e) => showWeek(Number(e.target.value)));
  const step = (delta) => {
    const weeks = state.index.weeks.map((w) => w.week);
    const i = weeks.indexOf(state.week) + delta;
    if (i >= 0 && i < weeks.length) showWeek(weeks[i]);
  };
  $("games-prev").addEventListener("click", () => step(-1));
  $("games-next").addEventListener("click", () => step(1));
}

/* Charts have no size while the page is hidden; redraw when it is shown. */
export function showGames() {
  rerenderGames();
}
