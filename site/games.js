/* Games page: this season's matchups week by week with the model's forecast per game. */

const state = {
  leagueKey: null,
  leagueName: "",
  entry: null, // index.leagues[i].games, or null
  index: null, // data/<league>/games/index.json
  weeks: {}, // week -> payload (cached per league)
  week: null,
  colorOf: () => "--accent", // roster_id -> css token name, from the Predictions page
  charts: {}, // game key -> Chart
  viewOf: {}, // `${week}:${game key}` -> "model" | "actual"
  openOf: {}, // `${week}:${game key}` -> true while that card's Full Lineup is open
  cards: [], // card index -> game (for re-rendering one card)
  onWeek: () => {}, // told when the shown week changes (app.js keeps it in the URL)
};

const PLACE_LABEL = { 1: "Championship", 3: "3rd place", 5: "5th place" };
const LIVE_BADGE = `<span class="live-badge" role="img" aria-label="Live">
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path class="arc arc-out" d="M5.3 5.3a9.5 9.5 0 0 0 0 13.4"/><path class="arc arc-in" d="M8.2 8.2a5.4 5.4 0 0 0 0 7.6"/>
    <circle class="dot" cx="12" cy="12" r="2.6"/>
    <path class="arc arc-in" d="M15.8 8.2a5.4 5.4 0 0 1 0 7.6"/><path class="arc arc-out" d="M18.7 5.3a9.5 9.5 0 0 1 0 13.4"/>
  </svg><span class="live-text">LIVE</span></span>`;
const $ = (id) => document.getElementById(id);
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/* A manager's name as a link to their Managers page (app.js opens it). */
function managerLink(name) {
  if (!name) return "";
  return `<a class="manager-link" href="#${state.leagueKey || ""}/managers/${encodeURIComponent(name)}" data-manager-link="${escapeHtml(name)}">${escapeHtml(name)}</a>`;
}

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

/* Called by app.js whenever a league loads. `colorOf(rid)` gives the team's colour token;
   `wantedWeek` (from the URL) is shown when the league has it. */
export async function loadGames(leagueKey, leagueName, entry, colorOf, wantedWeek = null) {
  if (state.leagueKey !== leagueKey) {
    state.weeks = {};
    state.index = null;
    state.week = null;
    state.viewOf = {};
    state.openOf = {};
  }
  if (wantedWeek != null) state.week = wantedWeek;
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
  if (!weeks.includes(state.week)) state.week = defaultWeek();
  await showWeek(state.week);
}

function defaultWeek() {
  const weeks = state.index.weeks.map((w) => w.week);
  return weeks.includes(state.index.current) ? state.index.current : weeks[weeks.length - 1];
}

/* New data deployed: drop the cached weeks and redraw the same week (the default week if it is
   gone), keeping each card's view and open lineups. */
export async function reloadGames() {
  if (!state.entry) return;
  state.index = await fetchJson(`data/${state.entry.file}`);
  state.weeks = {};
  if (!state.index.weeks.some((w) => w.week === state.week)) state.week = defaultWeek();
  await showWeek(state.week);
}

export function currentWeek() {
  return state.week;
}

async function showWeek(week) {
  state.week = week;
  state.onWeek(week);
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
      ? /*copy:GAME-02*/`Final. Shown against the forecast made before the week (after week ${W.forecast_as_of}), from before the Sleeper projection log began. A check marks the winner; the lines on each chart are the actual scores.`
      : /*copy:GAME-03*/"Final. Shown against the forecast of record: the lineups the managers started, each player at his last projection before kickoff. A check marks the winner; the lines on each chart are the actual scores.";
  } else {
    text = /*copy:GAME-04*/`Forecast from the simulation run ${formatTime(W.generated_at)} (after week ${W.forecast_as_of}), 10,000 simulations per game. Each chart shows the spread of simulated scores.`;
    if (W.games.some((g) => g.projected)) {
      text += /*copy:GAME-05*/"Playoff pairings are forecast: teams seeded by expected finish, the favourite advancing; each game says how often that pairing happened in the simulations.";
    }
    text += /*copy:GAME-06*/" Lineups are the model's best projected lineup; players listed as out can still appear in it until their projection drops.";
    if (W.live) {
      text = /*copy:GAME-07*/`Live, from the run ${formatTime(W.generated_at)}. Players whose games have started are locked in the slot their manager started them in: final scores count as they are, games in progress count points so far plus the projection for the time left. Injuries or benchings during a game only show once it is final. The site refreshes before and after each slate of games.`;
    }
  }
  if (W.games.some((g) => g.teams.some((t) => t.lineup.some((r) => r.wpa != null)))) {
    text += " " + /*copy:GAME-08*/"Percentages beside scored players are win probability added: how much that score moved the team's win probability against the pre-kickoff forecast, everyone else at their Sleeper projections. They show the size of each swing and do not add up to the team's total.";
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
  const projected = g.projected ? /*copy:GAME-10*/`· forecast, happens in ${Math.round((g.frequency || 0) * 100)}% of simulations` : "";
  return `${bracket && !name.startsWith("Toilet") ? bracket + " " : ""}${name}${seeds}${projected}`;
}

function choicesLine(t) {
  if (t.lineup_choices == null) return "";
  const v = Number(t.lineup_choices);
  const cls = v > 0 ? "up" : v < 0 ? "down" : "";
  return /*copy:GAME-09*/`<span class="choices ${cls}" title="Points vs the model lineup: what the manager's starters scored minus what the model's picks scored">Lineup choices: ${v > 0 ? "+" : ""}${v.toFixed(1)}</span>`;
}

function teamRow(g, t) {
  const color = cssVar(state.colorOf(t.roster_id));
  const won = g.winner != null && g.winner === t.roster_id;
  const live = t.points_so_far != null;
  const scored = live ? t.points_so_far : t.actual;
  const score = scored != null
    ? `<span class="num">${scored.toFixed(1)}</span><span class="unit">${t.mean.toFixed(1)} ${/*copy:GAME-14*/"forecasted"}</span>`
      + (live ? `<span class="unit">${t.to_play} to play</span>` : "") + choicesLine(t)
    : `<span class="num">${t.mean.toFixed(1)}</span><span class="unit">${/*copy:GAME-13*/"forecast"}</span>`;
  return `
    <div class="game-team">
      <span class="swatch" style="--team: ${color}" aria-hidden="true"></span>
      <span class="who"><span class="owner-name">${t.display_name ? managerLink(t.display_name) : `Roster ${t.roster_id}`}</span><span class="team">${escapeHtml(t.team_name || "")}</span></span>
      <span class="mean">${score}</span>
      <span class="win" style="${winFill(t.win_prob)}" title="Win probability">${won ? '<span class="check" aria-label="won">&#10003;</span>' : ""}${Math.round(t.win_prob * 100)}%</span>
    </div>`;
}

function kickoffLabel(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const day = d.toLocaleDateString(undefined, { weekday: "short" });
  const h = d.getHours() % 12 || 12;
  return `${day} ${h}:${String(d.getMinutes()).padStart(2, "0")}`; // compact: "Sun 1:00"
}

/* Beside the name: "F" for a final game on the live week, plus "BN" for a benched model pick. The
   clock of a game in progress sits in the right-hand column (kickTag), so the name keeps its room. */
function statusTag(r) {
  let tags = "";
  if (r.status === "final" && state.weeks[state.week]?.live) tags += `<span class="st st-final" title="Final">F</span>`;
  if (r.benched) tags += `<span class="st st-bench" title="The manager did not start him">BN</span>`;
  return tags;
}

/* Win probability added for a scored starter, shown right after his points. */
function wpaTag(r) {
  if (r.wpa == null) return "";
  const pts = Math.round(r.wpa * 100);
  const cls = pts > 0 ? "up" : pts < 0 ? "down" : "";
  return `<span class="aside wpa ${cls}" title="Win probability added">${pts > 0 ? "+" : ""}${pts}%</span>`;
}

/* The right-hand column: the kickoff time for a player yet to play, or the clock of his game in progress. */
function kickTag(r) {
  if (r.status === "in_progress") return `<span class="aside kick st-live"><span class="st-dot" aria-hidden="true"></span>${escapeHtml(r.clock || "Live")}</span>`;
  return r.kickoff && !r.status ? `<span class="aside kick">${escapeHtml(kickoffLabel(r.kickoff))}</span>` : "";
}

function hasAside(teams) {
  return teams.some((t) => [...t.lineup, ...t.key_players].some((r) => r.wpa != null || r.status === "in_progress" || (r.kickoff && !r.status)));
}

/* A card is live only while one of its managers' real starters is in a game in progress (bench
   players and starters still to kick off don't count). */
function cardIsLive(g) {
  if (!state.weeks[state.week]?.live) return false;
  const actual = (g.views && g.views.actual) || g;
  return (actual.teams || []).some((t) => (t.lineup || []).some((r) => r.status === "in_progress"));
}

/* The site's name standard: a player's full name, or "A. St. Brown" (a defense: its nickname) only
   when the full name does not fit its space; the full name stays in the tooltip. */
function shortPlayerName(name, position) {
  const parts = String(name || "").trim().split(/\s+/);
  if (position === "DEF") return parts[parts.length - 1];
  return parts.length > 1 ? `${parts[0][0]}. ${parts.slice(1).join(" ")}` : name;
}

function nameAttrs(name, position) {
  const short = shortPlayerName(name, position);
  return short && short !== name ? ` title="${escapeHtml(name)}" data-full="${escapeHtml(name)}" data-short="${escapeHtml(short)}"` : "";
}

/* After rendering (and on resize): shorten only the names that overflow. Hidden elements measure 0
   wide and are left full; they are fitted again when shown. */
/* Text wider than its box, measured to the fraction of a pixel (scrollWidth rounds, and a name
   over by under a pixel still gets an ellipsis). */
function overflows(el) {
  const box = el.getBoundingClientRect().width;
  if (!box) return false;
  const r = document.createRange();
  r.selectNodeContents(el);
  return r.getBoundingClientRect().width > box + 0.01;
}

function fitNames(root) {
  for (const el of (root || document).querySelectorAll("[data-short]")) {
    el.textContent = el.dataset.full;
    if (overflows(el)) el.textContent = el.dataset.short;
  }
  // a replacement fill drops its "(replacement level)" bracket the same way
  for (const more of (root || document).querySelectorAll(".fa-more")) {
    const nm = more.parentElement;
    more.hidden = false;
    if (nm.clientWidth && nm.scrollWidth > nm.clientWidth + 1) more.hidden = true;
  }
}

/* A replacement fill reads "Free agent (replacement level)"; the bracket hides on phones. */
const FILL_PREFIX = "Free agent (";
function playerName(r) {
  if (r.replacement && String(r.name).startsWith(FILL_PREFIX)) {
    return `Free agent<span class="fa-more"> ${escapeHtml(r.name.slice("Free agent ".length))}</span>`;
  }
  return escapeHtml(r.name);
}

/* One player line: label (position or slot), name with status, points (or projection), aside. */
function playerLine(r, label, aside) {
  const scored = r.points != null;
  const value = scored ? `<span class="pts scored" title="Projected ${Number(r.projected).toFixed(1)}">${Number(r.points).toFixed(1)}</span>`
    : `<span class="pts">${Number(r.projected).toFixed(1)}</span>`;
  const cls = [r.replacement ? "fill" : "", r.status ? `is-${r.status}` : ""].filter(Boolean).join(" ");
  return `<li${cls ? ` class="${cls}"` : ""}><span class="pos">${escapeHtml(label)}</span><span class="pname"><span class="nm"${r.replacement ? "" : nameAttrs(r.name, r.position)}>${playerName(r)}</span>${statusTag(r)}</span>${value}${aside ? wpaTag(r) + kickTag(r) : ""}</li>`;
}

function teamPlayers(t, aside, open) {
  const out = t.not_playing.length
    ? `<p class="out-label">Not playing</p><ul class="out">${t.not_playing.map((o) => `<li><span class="pname">${escapeHtml(o.name)}</span><span class="reason">${escapeHtml(o.reason)}</span></li>`).join("")}</ul>`
    : "";
  return `
    <div class="team-players">
      <p class="tp-name">${managerLink(t.display_name)}</p>
      <ul class="key">${t.key_players.map((r) => playerLine(r, r.position, aside)).join("")}</ul>
      <details class="lineup"${open ? " open" : ""}><summary>Full Lineup</summary><ul>${t.lineup.map((r) => playerLine(r, r.slot, aside)).join("")}</ul></details>
      ${out}
    </div>`;
}

function viewKey(g) {
  return `${state.week}:${g.key}`;
}

/* The game as the selected view shows it: that view's teams and histogram. */
function viewed(g) {
  const views = g.views || { [g.default_view || "model"]: { teams: g.teams, hist: g.hist } };
  const name = views[state.viewOf[viewKey(g)]] ? state.viewOf[viewKey(g)] : g.default_view || Object.keys(views)[0];
  return { ...g, view: name, source: views[name].source, teams: views[name].teams, hist: views[name].hist, both: Boolean(views.model && views.actual) };
}

function viewToggle(v) {
  if (!v.both) return "";
  const btn = (name, label) => `<button type="button" data-view="${name}" aria-pressed="${v.view === name}">${label}</button>`;
  return `<span class="view-toggle" role="group" aria-label="Lineup view">${btn("model", "Model")}${btn("actual", "Actual")}</span>`;
}

function cardHtml(g, idx) {
  const v = viewed(g);
  const label = gameLabel(g);
  const live = cardIsLive(g);
  const rebuilt = v.view === "actual" && v.source === "rebuilt" ? `<span class="rebuilt" title="Rebuilt from the managers' starters at their stored projections (before the projection log began)">rebuilt</span>` : "";
  const toggle = viewToggle(v);
  const head = live || label || toggle ? `<div class="game-label">${live ? LIVE_BADGE : ""}${label ? `<span>${escapeHtml(label)}</span>` : ""}${rebuilt}${toggle}</div>` : "";
  const aside = hasAside(v.teams);
  return `
    <section class="game-card${g.projected ? " projected" : ""}${live ? " live" : ""}${aside ? "" : " no-aside"}" data-card="${idx}">
      ${head}
      <div class="game-body">
        <div class="game-rows">${v.teams.map((t) => teamRow(v, t)).join("")}</div>
        <div class="game-chart"><canvas id="game-chart-${idx}" role="img" aria-label="Simulated score distributions for ${escapeHtml(v.teams.map((t) => t.display_name).join(" and "))}"></canvas></div>
      </div>
      <div class="game-players">${v.teams.map((t) => teamPlayers(t, aside, state.openOf[viewKey(g)])).join("")}</div>
    </section>`;
}

/* Wire a rendered card: the view toggle re-renders just this card; the two Full Lineup expanders move together. */
function wireCard(idx) {
  const card = document.querySelector(`.game-card[data-card="${idx}"]`);
  if (!card) return;
  for (const btn of card.querySelectorAll(".view-toggle button")) {
    btn.addEventListener("click", () => {
      const g = state.cards[idx];
      state.viewOf[viewKey(g)] = btn.dataset.view;
      card.outerHTML = cardHtml(g, idx);
      if (state.charts[g.key]) state.charts[g.key].destroy();
      drawChart($(`game-chart-${idx}`), viewed(g), g.key);
      wireCard(idx);
      fitNames(document.querySelector(`.game-card[data-card="${idx}"]`));
    });
  }
  const details = [...card.querySelectorAll("details.lineup")];
  for (const d of details) {
    d.addEventListener("toggle", () => {
      fitNames(d);  // names in a list that was closed were measured at zero width
      state.openOf[viewKey(state.cards[idx])] = d.open;
      for (const other of details) if (other !== d && other.open !== d.open) other.open = d.open;
    });
  }
}

function byeHtml(b) {
  const color = cssVar(state.colorOf(b.roster_id));
  const where = b.bracket === "losers" ? "toilet bowl" : "playoffs";
  return `
    <section class="game-card bye">
      <p class="game-label">${/*copy:GAME-11*/`First-round bye · #${b.seed} seed in the ${where}`}</p>
      <div class="game-team"><span class="swatch" style="--team: ${color}" aria-hidden="true"></span>
        <span class="who"><span class="owner-name">${b.display_name ? managerLink(b.display_name) : `Roster ${b.roster_id}`}</span><span class="team">${escapeHtml(b.team_name || "")}</span></span>
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
  for (const c of Object.values(state.charts)) c.destroy();
  state.charts = {};
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
        state.cards[idx] = item.game;
        idx += 1;
      }
    }
    html += `</div>`;
  }
  grid.innerHTML = html || `<p class="hint">${/*copy:GAME-12*/"No games stored for this week."}</p>`;
  for (const [i, g] of games) {
    drawChart($(`game-chart-${i}`), viewed(g), g.key);
    wireCard(i);
  }
  fitNames(grid);
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

function drawChart(canvas, g, key) {
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
  state.charts[key] = (new Chart(canvas, {
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

export function initGames(onWeek) {
  if (onWeek) state.onWeek = onWeek;
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

let fitTimer = null;
addEventListener("resize", () => {
  clearTimeout(fitTimer);
  fitTimer = setTimeout(() => fitNames(document.getElementById("games-grid")), 150);
});
