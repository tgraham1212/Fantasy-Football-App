/* Player WAR page: season control, per-position leaderboards, expanded sortable list, worked example. */

import { comparator, markSorted, nextSort, wireHeaders } from "./sorting.js?v=__BUILD__";

const POSITIONS = ["QB", "RB", "WR", "TE", "DEF", "K"];
const POSITION_LABEL = { QB: "Quarterbacks", RB: "Running backs", WR: "Wide receivers", TE: "Tight ends", DEF: "Defenses", K: "Kickers" };
const STAT_COLUMNS = {
  QB: [["pass_yd", "Pass yds"], ["pass_td", "Pass TD"], ["pass_int", "INT"], ["rush_yd", "Rush yds"], ["rush_td", "Rush TD"]],
  RB: [["rush_yd", "Rush yds"], ["rush_td", "Rush TD"], ["rec", "Rec"], ["rec_yd", "Rec yds"], ["rec_td", "Rec TD"]],
  WR: [["rec", "Rec"], ["rec_yd", "Rec yds"], ["rec_td", "Rec TD"], ["rush_yd", "Rush yds"]],
  TE: [["rec", "Rec"], ["rec_yd", "Rec yds"], ["rec_td", "Rec TD"], ["rush_yd", "Rush yds"]],
  K: [["fgm", "FG made"], ["fga", "FG att"], ["xpm", "XP made"]],
  DEF: [["sack", "Sacks"], ["int", "INT"], ["fum_rec", "Fum rec"], ["def_td", "TD"], ["pts_allow", "Pts allowed / game"]],
};
const PER_GAME = new Set(["pts_allow"]);
const TOP_N = 10;
const WALKTHROUGH_SEASON = "2024";
const WALKTHROUGH = [["4217", "Kittle"], ["11604", "Bowers"]];

const state = {
  leagueKey: null,
  leagueName: "",
  entry: null, // the league's `war` entry from data/index.json, or null
  index: null, // data/<league>/war/index.json
  seasons: {}, // season -> payload (cached per league)
  selection: null, // season string or "all"
  mode: "seasons", // All-Time only: "seasons" | "career"
  dialogPos: null,
  sort: null,
};

const $ = (id) => document.getElementById(id);
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtWar = (v) => (v == null ? "" : (v >= 0 ? "+" : "") + v.toFixed(2));
const fmtStat = (key, v) => (v == null ? "" : PER_GAME.has(key) ? Number(v).toFixed(1) : String(Math.round(v)));

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading ------------------------------------------------------------------------------------

/* Called by app.js whenever a league loads. `entry` is index.leagues[i].war (may be null). */
export async function loadWar(leagueKey, leagueName, entry) {
  if (state.leagueKey !== leagueKey) {
    state.seasons = {};
    state.index = null;
    state.selection = null;
    state.mode = "seasons";
  }
  state.leagueKey = leagueKey;
  state.leagueName = leagueName;
  state.entry = entry || null;
  closeDialog();
  if (!state.entry) {
    renderUnavailable();
    return;
  }
  state.index = await fetchJson(`data/${state.entry.file}`);
  if (!state.selection || (state.selection !== "all" && !state.index.seasons.some((s) => s.season === state.selection))) {
    state.selection = state.index.current;
  }
  await ensureSeason(state.selection);
  render();
}

/* New data deployed: drop the cached seasons and redraw the same selection, mode and an open
   full list with its sort. */
export async function reloadWar() {
  if (!state.entry) return;
  state.index = await fetchJson(`data/${state.entry.file}`);
  state.seasons = {};
  if (state.selection !== "all" && !state.index.seasons.some((s) => s.season === state.selection)) {
    state.selection = state.index.current;
  }
  await ensureSeason(state.selection);
  render();
  if (state.dialogPos && $("war-dialog").open) {
    const scroller = document.querySelector("#war-dialog .dialog-table");
    const top = scroller ? scroller.scrollTop : 0;
    renderDialogBody();
    if (scroller) scroller.scrollTop = top;
  }
}

async function ensureSeason(selection) {
  const wanted = selection === "all" ? state.index.seasons.map((s) => s.season) : [selection];
  await Promise.all(wanted.filter((s) => !state.seasons[s]).map(async (s) => {
    state.seasons[s] = await fetchJson(`data/${state.leagueKey}/war/${s}.json`);
  }));
}

// -- rows ---------------------------------------------------------------------------------------

function seasonRows(season) {
  return (state.seasons[season]?.players || []).map((p) => ({ ...p, season }));
}

function allSeasonRows() {
  return state.index.seasons.flatMap((s) => seasonRows(s.season));
}

/* One row per player: WAR summed across their seasons; owner, team and name from the latest season. */
function careerRows() {
  const byId = new Map();
  for (const row of allSeasonRows()) {
    const c = byId.get(row.id) || { id: row.id, position: row.position, name: row.name, team: row.team, owner: row.owner, others: [], seasons: 0, games: 0, points: 0, exp_wins: 0, war: 0, stats: {}, _statGames: {}, season: row.season };
    c.seasons += 1;
    c.games += row.games;
    c.points += row.points;
    c.exp_wins += row.exp_wins;
    c.war += row.war;
    for (const [key, value] of Object.entries(row.stats || {})) {
      if (PER_GAME.has(key)) { // per-game figures combine weighted by games
        c.stats[key] = ((c.stats[key] || 0) * (c._statGames[key] || 0) + value * row.games) / ((c._statGames[key] || 0) + row.games);
        c._statGames[key] = (c._statGames[key] || 0) + row.games;
      } else {
        c.stats[key] = (c.stats[key] || 0) + value;
      }
    }
    const holders = [row.owner, ...(row.others || [])].filter(Boolean);
    for (const h of holders) if (!c.others.includes(h)) c.others.push(h);
    if (row.season >= c.season) { // latest season wins for name, team, owner
      c.season = row.season;
      c.name = row.name;
      c.team = row.team;
      c.owner = row.owner;
      c.position = row.position;
    }
    byId.set(row.id, c);
  }
  return [...byId.values()].map((c) => ({ ...c, others: c.others.filter((h) => h !== c.owner), points: Math.round(c.points * 100) / 100, war: Math.round(c.war * 10000) / 10000 }));
}

function currentRows() {
  if (state.selection === "all") return state.mode === "career" ? careerRows() : allSeasonRows();
  return seasonRows(state.selection);
}

const byWar = (a, b) => b.war - a.war || b.points - a.points || a.name.localeCompare(b.name);

function rowsFor(position) {
  return currentRows().filter((r) => r.position === position).sort(byWar).map((r, i) => ({ ...r, rank: i + 1 }));
}

function positionsPresent() {
  const present = new Set(currentRows().map((r) => r.position));
  return POSITIONS.filter((p) => present.has(p));
}

// -- rendering ------------------------------------------------------------------------------------

function render() {
  renderControls();
  renderGrid();
  renderWalkthrough();
  $("war-controls").hidden = false;
  $("war-note").hidden = false;
  $("war-unavailable").hidden = true;
  $("war-content").hidden = false;
}

function renderUnavailable() {
  $("war-title").textContent = `${state.leagueName} · Player WAR`;
  $("war-controls").hidden = true;
  $("war-note").hidden = true;
  $("war-unavailable").hidden = false;
  $("war-content").hidden = true;
}

function seasonLabel(s) {
  const current = s.season === state.index.current && s.through_week < 14 ? ` (through week ${s.through_week})` : "";
  return `${s.season}${current}`;
}

function renderControls() {
  $("war-title").textContent = `${state.leagueName} · Player WAR`;
  const select = $("war-season");
  select.innerHTML = "";
  for (const s of [...state.index.seasons].reverse()) {
    const opt = document.createElement("option");
    opt.value = s.season;
    opt.textContent = seasonLabel(s);
    select.appendChild(opt);
  }
  const all = document.createElement("option");
  all.value = "all";
  all.textContent = "All-Time";
  select.appendChild(all);
  select.value = state.selection;
  const modeBox = $("war-mode");
  modeBox.hidden = state.selection !== "all";
  for (const btn of modeBox.querySelectorAll("button")) btn.setAttribute("aria-pressed", String(btn.dataset.mode === state.mode));
  $("war-note").textContent = noteText();
}

const MERGED_NOTE = "This season is only partly captured by weekly start-percentage snapshots, so it uses a merged replacement cut: weeks with their own snapshot use it, and the rest rank each player by his highest start percentage from weeks he played (or his ownership if he is injured and was never seen active). It settles as more weeks are captured.";
const YEARLY_NOTE = "This season uses a yearly replacement cut: one start-percentage snapshot picks the consensus lineups and the replacement players for every week.";

function cutOf(season) {
  const s = state.index.seasons.find((x) => x.season === season);
  if (s && s.cut) return s.cut;
  const first = state.index.first_weekly;
  return first && season >= first ? "weekly" : "yearly";
}

function noteText() {
  const first = state.index.first_weekly;
  const parts = [];
  if (state.selection === "all") {
    parts.push(state.mode === "career" ? "Career: each player's WAR summed over their seasons in this league; owner and team from their latest season." : "Every player-season in this league ranked together.");
    const yearly = state.index.seasons.filter((s) => cutOf(s.season) === "yearly");
    const merged = state.index.seasons.filter((s) => cutOf(s.season) === "merged");
    if (yearly.length) parts.push(first ? `Seasons before ${first} use a yearly replacement cut (one start-percentage snapshot per season) instead of a weekly one.` : "Completed seasons so far use a yearly replacement cut (one start-percentage snapshot per season); weekly cuts begin once a full season of weekly snapshots exists.");
    if (merged.length) parts.push(`${merged.map((s) => s.season).join(", ")} ${merged.length > 1 ? "use" : "uses"} a merged cut from the weekly snapshots captured so far.`);
  } else {
    const s = state.index.seasons.find((x) => x.season === state.selection);
    if (s && s.season === state.index.current && s.through_week < 14) parts.push(`Regular-season weeks 1 to ${s.through_week} so far; values settle as the season's averages fill in.`);
    if (s && cutOf(s.season) === "yearly") parts.push(YEARLY_NOTE);
    if (s && cutOf(s.season) === "merged") parts.push(MERGED_NOTE);
  }
  parts.push("WAR is wins above a replacement-level player over the regular season. Hover an owner to see who else held the player that season.");
  return parts.join(" ");
}

function ownerCell(row) {
  if (!row.owner) return `<td class="war-owner"><span class="muted">—</span></td>`;
  const others = row.others || [];
  const title = others.length ? `Also held by: ${others.join(", ")}` : "";
  const marker = others.length ? ` <span class="also" aria-hidden="true">+${others.length}</span>` : "";
  const sr = others.length ? `<span class="sr-only">, also held by ${escapeHtml(others.join(", "))}</span>` : "";
  return `<td class="war-owner"><span${title ? ` title="${escapeHtml(title)}"` : ""}>${escapeHtml(row.owner)}${marker}${sr}</span></td>`;
}

function extraHeader() {
  if (state.selection !== "all") return "";
  return state.mode === "career" ? `<th scope="col" class="num">Szns</th>` : `<th scope="col" class="num">Year</th>`;
}

function extraCell(row) {
  if (state.selection !== "all") return "";
  return state.mode === "career" ? `<td class="num">${row.seasons}</td>` : `<td class="num">${escapeHtml(row.season)}</td>`;
}

function renderGrid() {
  const grid = $("war-grid");
  grid.innerHTML = "";
  for (const pos of positionsPresent()) {
    const rows = rowsFor(pos).slice(0, TOP_N);
    const box = document.createElement("section");
    box.className = "war-table";
    box.innerHTML = `
      <div class="war-table-head"><h3>${POSITION_LABEL[pos]}</h3><span class="hint">Top ${TOP_N} by WAR</span></div>
      <div class="war-scroll"><table class="plain war">
        <thead><tr><th scope="col" class="num rank">#</th><th scope="col">Name</th><th scope="col">NFL</th><th scope="col">Owner</th>${extraHeader()}<th scope="col" class="num">WAR</th></tr></thead>
        <tbody>${rows.map((r) => `<tr><td class="num rank">${r.rank}</td><td class="name">${escapeHtml(r.name)}</td><td class="muted">${escapeHtml(r.team || "")}</td>${ownerCell(r)}${extraCell(r)}<td class="num war-value">${fmtWar(r.war)}</td></tr>`).join("")}</tbody>
      </table></div>
      <button type="button" class="expand" data-pos="${pos}" aria-label="Show every ${POSITION_LABEL[pos].toLowerCase()} with a WAR"><span aria-hidden="true">&#x2922;</span> Full list</button>`;
    box.querySelector(".expand").addEventListener("click", () => openDialog(pos));
    grid.appendChild(box);
  }
}

// -- expanded list ------------------------------------------------------------------------------

function dialogColumns(pos) {
  const cols = [
    { key: "rank", label: "#", num: true, value: (r) => -r.rank, cell: (r) => r.rank },
    { key: "name", label: "Name", text: (r) => r.name.toLowerCase(), cell: (r) => escapeHtml(r.name) },
    { key: "team", label: "NFL", text: (r) => (r.team || "").toLowerCase(), cell: (r) => escapeHtml(r.team || "") },
    { key: "owner", label: "Owner", text: (r) => (r.owner || "￿").toLowerCase(), cell: null },
  ];
  if (state.selection === "all") {
    cols.push(state.mode === "career"
      ? { key: "seasons", label: "Szns", num: true, value: (r) => r.seasons, cell: (r) => r.seasons }
      : { key: "season", label: "Year", num: true, value: (r) => Number(r.season), cell: (r) => escapeHtml(r.season) });
  }
  cols.push({ key: "games", label: "GP", num: true, value: (r) => r.games, cell: (r) => r.games });
  cols.push({ key: "points", label: "PS", num: true, value: (r) => r.points, cell: (r) => r.points.toFixed(1) });
  for (const [key, label] of STAT_COLUMNS[pos] || []) {
    cols.push({ key: `stat:${key}`, label, num: true, value: (r) => r.stats?.[key], cell: (r) => fmtStat(key, r.stats?.[key]) });
  }
  cols.push({ key: "war", label: "WAR", num: true, value: (r) => r.war, cell: (r) => fmtWar(r.war) });
  return cols;
}

function openDialog(pos) {
  state.dialogPos = pos;
  state.sort = null;
  const dialog = $("war-dialog");
  renderDialog();
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function closeDialog() {
  const dialog = $("war-dialog");
  if (dialog.open) dialog.close();
  state.dialogPos = null;
}

function renderDialog() {
  const pos = state.dialogPos;
  if (!pos) return;
  const cols = dialogColumns(pos);
  const scope = state.selection === "all" ? (state.mode === "career" ? "all-time careers" : "all player-seasons") : state.selection;
  $("war-dialog-title").textContent = `${POSITION_LABEL[pos]} · ${scope}`;
  const table = $("war-full");
  table.innerHTML = `
    <thead><tr>${cols.map((c) => `<th scope="col" class="${c.num ? "num" : ""}" data-col="${c.key}"><button type="button" class="sort">${escapeHtml(c.label)}</button></th>`).join("")}</tr></thead>
    <tbody></tbody>`;
  wireHeaders(table, (key) => { state.sort = nextSort(state.sort, key); renderDialogBody(); });
  renderDialogBody();
}

function renderDialogBody() {
  const pos = state.dialogPos;
  const cols = dialogColumns(pos);
  const table = $("war-full");
  markSorted(table.querySelectorAll("thead th[data-col]"), state.sort);
  let rows = rowsFor(pos);
  if (state.sort) {
    const col = cols.find((c) => c.key === state.sort.key);
    if (col) rows = [...rows].sort(comparator(col, state.sort.dir, (a, b) => a.rank - b.rank));
  }
  table.querySelector("tbody").innerHTML = rows.map((r) => `<tr>${cols.map((c) => (c.key === "owner" ? ownerCell(r) : `<td class="${c.num ? "num" : ""}${c.key === "name" ? " name" : ""}">${c.cell(r)}</td>`)).join("")}</tr>`).join("");
}

// -- worked example ----------------------------------------------------------------------------------

async function renderWalkthrough() {
  const box = $("war-walkthrough");
  const has2024 = state.index.seasons.some((s) => s.season === WALKTHROUGH_SEASON);
  if (has2024) await ensureSeason(WALKTHROUGH_SEASON);
  const payload = state.seasons[WALKTHROUGH_SEASON];
  const wt = payload?.walkthrough;
  if (!wt || !WALKTHROUGH.every(([id]) => wt[id])) {
    box.hidden = true;
    return;
  }
  const [kittle, bowers] = WALKTHROUGH.map(([id]) => wt[id]);
  const te = payload.constants.slot_mean.TE;
  const sd = payload.constants.opponent_sd;
  const repl = payload.replacement.TE;
  const weeks = kittle.weekly.map((w) => w.week);
  const cell = (w) => (w.played ? `<td class="num">${w.score.toFixed(1)}</td>` : `<td class="num fill" title="No game: replacement level used">${w.score.toFixed(1)}<span class="fill-mark" aria-hidden="true">*</span><span class="sr-only"> (replacement fill)</span></td>`) + `<td class="num p">${(w.p * 100).toFixed(0)}%</td>`;
  box.hidden = false;
  box.innerHTML = `
    <h3>Worked example: Kittle and Bowers, 2024</h3>
    <p class="hint">${escapeHtml(state.leagueName)}, 2024 constants: TE slot mean ${te.toFixed(1)}, opponent spread ${sd.toFixed(1)}, TE replacement level ${repl.level.toFixed(1)} (a replacement tight end earns ${repl.baseline_wins.toFixed(2)} expected wins over ${weeks.length} weeks). Each week's win chance is the share of the opponent distribution below the league mean plus (score − ${te.toFixed(1)}).</p>
    <div class="table-wrap"><table class="plain walkthrough">
      <thead><tr><th scope="col">Week</th><th scope="col" class="num" colspan="2">Kittle: score, win chance</th><th scope="col" class="num" colspan="2">Bowers: score, win chance</th></tr></thead>
      <tbody>${weeks.map((week, i) => `<tr><th scope="row">${week}</th>${cell(kittle.weekly[i])}${cell(bowers.weekly[i])}</tr>`).join("")}</tbody>
      <tfoot>
        <tr><th scope="row">Expected wins</th><td class="num" colspan="2">${kittle.exp_wins.toFixed(2)}</td><td class="num" colspan="2">${bowers.exp_wins.toFixed(2)}</td></tr>
        <tr><th scope="row">Minus replacement</th><td class="num" colspan="2">−${repl.baseline_wins.toFixed(2)}</td><td class="num" colspan="2">−${repl.baseline_wins.toFixed(2)}</td></tr>
        <tr class="total"><th scope="row">WAR</th><td class="num" colspan="2">${fmtWar(kittle.war)}</td><td class="num" colspan="2">${fmtWar(bowers.war)}</td></tr>
      </tfoot>
    </table></div>
    <p class="hint">* a week with no game played, filled at the replacement level. Kittle missed ${kittle.weekly.filter((w) => !w.played).length} of ${weeks.length} weeks and still finished ahead of Bowers (${bowers.games} games) on the strength of his per-game scoring; the replacement fill keeps a missed week from counting as a zero.</p>`;
}

// -- wiring ----------------------------------------------------------------------------------------

export function initWar() {
  $("war-season").addEventListener("change", async (e) => {
    state.selection = e.target.value;
    state.sort = null;
    await ensureSeason(state.selection);
    render();
  });
  for (const btn of $("war-mode").querySelectorAll("button")) {
    btn.addEventListener("click", () => {
      state.mode = btn.dataset.mode;
      render();
    });
  }
  $("war-dialog-close").addEventListener("click", closeDialog);
  $("war-dialog").addEventListener("click", (e) => { if (e.target === e.currentTarget) closeDialog(); });
}
