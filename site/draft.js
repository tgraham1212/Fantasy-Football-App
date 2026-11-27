/* League page, Draft tab: one stored draft as a board (rounds by draft slots) or a table, each pick
   graded on draft day against ADP (Steal/Reach) and in retrospect against the WAR its slot usually
   produces in this league (Hit/Bust, or Unlucky), with the Managers summary for this draft or all
   drafts. Every grade comes from data/<league>/draft.json (src/ffapp/draft.py); this module only
   renders. The board scrolls inside its card with the round column pinned; the table and the Managers
   summary are drawn twice, a table for wide screens and a list for phones, and CSS shows one. */

import { crest, escapeHtml, fitNames, shortName, wireImages } from "./people.js?v=__BUILD__";
import { comparator, markSorted, wireHeaders } from "./sorting.js?v=__BUILD__";

const state = {
  leagueKey: null,
  entry: null,     // index.leagues[i].draft
  data: null,      // data/<league>/draft.json
  view: "board",   // "board" | "table"
  grade: "day",    // board badges: "day" (Steal/Reach) | "results" (Hit/Bust/Unlucky)
  span: "draft",   // Managers card: "draft" | "all"
  season: null,
  sort: { key: "no", dir: "asc" },
  onChange: () => {},
};

const $ = (id) => document.getElementById(id);
const PHONE = matchMedia("(max-width: 599.98px)");

/* The direction a column sorts on its first pick: most WAR and the biggest gains first, else pick order. */
const FIRST_DIR = { no: "asc", manager: "desc", player: "desc", adp: "asc", adp_rank: "asc", war: "desc", war_rank: "asc", slot_war: "desc", war_gap: "desc", games: "desc" };
const COLUMNS = {
  no: { value: (p) => p.no },
  manager: { text: (p) => mgr(p.user)?.name || "" },
  player: { text: (p) => `${p.player.last} ${p.player.first}` },
  adp: { value: (p) => p.adp },
  adp_rank: { value: (p) => p.adp_rank },
  war: { value: (p) => p.war },
  war_rank: { value: (p) => p.war_rank },
  slot_war: { value: (p) => p.slot_war },
  war_gap: { value: (p) => p.war_gap },
  games: { value: (p) => p.games },
};

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading and URL ---------------------------------------------------------------------------------

/* `route` is the URL path after /league/draft: an optional "table" and an optional season. */
export async function loadDraft(leagueKey, entry, route, onChange) {
  const sameLeague = state.leagueKey === leagueKey;
  state.leagueKey = leagueKey;
  state.entry = entry || null;
  state.onChange = onChange || state.onChange;
  if (!sameLeague) state.season = null;
  state.data = state.entry ? await fetchJson(`data/${state.entry.file}`) : null;
  applyRoute(route || []);
  render();
}

export function applyRoute(parts) {
  for (const part of parts) {
    if (part === "table" || part === "board") state.view = part;
    else if (/^\d{4}$/.test(part)) state.season = part;
  }
  if (state.data && !state.data.seasons[state.season]) state.season = state.data.latest;
}

/* The URL part after /league/draft. */
export function draftSlug() {
  return `${state.view === "table" ? "/table" : ""}${state.season ? `/${state.season}` : ""}`;
}

export function showDraft() {
  if (state.data && !$("dr-page").hidden) fitNames($("dr-page"));
}

export function initDraft() {
  $("dr-views").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dr-view]");
    if (!b) return;
    state.view = b.dataset.drView;
    render();
    state.onChange();
  });
  $("dr-grades").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dr-grade]");
    if (!b) return;
    state.grade = b.dataset.drGrade;
    render();
  });
  $("dr-span").addEventListener("click", (e) => {
    const b = e.target.closest("[data-dr-span]");
    if (!b) return;
    state.span = b.dataset.drSpan;
    renderManagers();
  });
  $("dr-season").addEventListener("change", (e) => {
    state.season = e.target.value;
    render();
    state.onChange();
  });
  PHONE.addEventListener("change", () => showDraft());
  addEventListener("resize", () => showDraft());
}

// -- shared pieces -------------------------------------------------------------------------------------

const mgr = (id) => state.data.managers[id];
const rookie = () => state.data.rules.kind === "rookie";
const num = (x) => (Number.isInteger(x) ? String(Math.abs(x)) : Math.abs(x).toFixed(1));
const sign = (x) => (x > 0 ? "+" : x < 0 ? "−" : "");
const war = (x, d = 2) => (x == null ? `<span class="muted">–</span>` : `<span class="${x > 0 ? "war-pos" : x < 0 ? "war-neg" : ""}">${sign(x)}${Math.abs(x).toFixed(d)}</span>`);
const TRADED = `<svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true"><path d="M1 3h6M5 1l2 2-2 2M9 7H3M5 5L3 7l2 2" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>`;
const CROSS = `<svg width="9" height="9" viewBox="0 0 10 10" aria-hidden="true"><path d="M3.5 0.5h3v3h3v3h-3v3h-3v-3h-3v-3h3z" fill="currentColor"/></svg>`;
const fullName = (p) => `${p.player.first} ${p.player.last}`.trim();

function managerLink(id) {
  const m = mgr(id);
  return m ? `<a class="manager-link" href="#${state.leagueKey}/managers/${encodeURIComponent(m.name)}" data-manager-link="${escapeHtml(m.name)}">${escapeHtml(m.name)}</a>` : "–";
}

function managerCell(id, sub) {
  const m = mgr(id);
  if (!m) return `<span class="lg-who muted">–</span>`;
  return `<span class="lg-who">${crest({ ...m, user_id: id }, "xs")}<span class="lg-who-col">${managerLink(id)}${sub ? `<span class="lg-sub">${sub}</span>` : ""}</span></span>`;
}

function stealBadge(p) {
  if (p.steal_reach === "steal") return `<span class="dr-badge steal">${/*copy:LG-81*/"Steal"} +${num(p.adp_diff)}</span>`;
  if (p.steal_reach === "reach") return `<span class="dr-badge reach">${/*copy:LG-82*/"Reach"} −${num(p.adp_diff)}</span>`;
  return "";
}

function hitBadge(p) {
  if (p.hit_bust === "unlucky") {
    const tip = `Played ${p.games} of his team's ${p.games_possible} games`;
    return `<span class="dr-badge unlucky" title="${escapeHtml(tip)}">${CROSS}${/*copy:LG-83*/"Unlucky"} ${p.games}/${p.games_possible}</span>`;
  }
  if (p.hit_bust === "hit") return `<span class="dr-badge hit">${/*copy:LG-84*/"Hit"} +${p.war_gap.toFixed(2)}</span>`;
  if (p.hit_bust === "bust") return `<span class="dr-badge bust">${/*copy:LG-85*/"Bust"} −${Math.abs(p.war_gap).toFixed(2)}</span>`;
  return "";
}

const keeperBadge = (p) => (p.keeper ? `<span class="dr-badge keeper">${/*copy:LG-86*/"Keeper"}</span>` : "");
const posPill = (pos, rank) => `<span class="mgr-pill dr-pos ${String(pos).toLowerCase()}">${escapeHtml(pos)}${rank || ""}</span>`;

// -- rendering --------------------------------------------------------------------------------------

function render() {
  const has = !!(state.data && state.season);
  $("dr-unavailable").hidden = has;
  $("dr-draft").hidden = $("dr-managers").hidden = !has;
  for (const b of $("dr-views").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.drView === state.view));
  for (const b of $("dr-grades").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.drGrade === state.grade));
  for (const b of $("dr-span").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.drSpan === state.span));
  $("dr-grades").classList.toggle("dr-off", state.view !== "board");  // keeps its space, so the controls never move
  const select = $("dr-season");
  const seasons = has ? Object.keys(state.data.seasons).sort().reverse() : [];
  select.innerHTML = seasons.map((s) => `<option value="${s}"${s === state.season ? " selected" : ""}>${s}</option>`).join("");
  select.disabled = !has;
  if (!has) return;
  $("dr-draft-h").textContent = `${state.season} ${rookie() ? /*copy:LG-87*/"Rookie Draft" : /*copy:LG-88*/"Draft"}`;
  $("dr-note-redraft").hidden = rookie();
  $("dr-note-rookie").hidden = !rookie();
  $("dr-board").hidden = state.view !== "board";
  $("dr-table").hidden = state.view !== "table";
  for (const key of $("dr-legend").querySelectorAll("[data-grade]")) {
    key.hidden = state.view === "board" && !key.dataset.grade.split(" ").includes(state.grade);
  }
  if (state.view === "board") renderBoard();
  else renderTable();
  renderManagers();
  renderKeepers();
  showDraft();
}

/* Keeper Eligible (redraft, the latest draft only): Managers by price round, Players as position chips. */
function renderKeepers() {
  const ke = state.data.seasons[state.season].keepers;
  $("dr-keepers").hidden = !ke;
  if (!ke) return;
  $("dr-keepers-h").textContent = `${/*copy:LG-98*/"Keeper Eligible for"} ${ke.for_season}`;
  $("dr-keepers-provisional").hidden = ke.final;
  const rounds = Math.max(1, ...ke.rows.flatMap((r) => r.players.map((pl) => pl.price_round)));
  const cols = Array.from({ length: rounds }, (_, i) => i + 1);
  const chip = (pl) => {
    const name = `${pl.player.first} ${pl.player.last}`.trim();
    const kept = pl.second_year ? ` ${/*copy:LG-102*/"(kept this season)"}` : "";
    const tip = `${name}, ${pl.player.pos} ${pl.player.team}. ${/*copy:LG-103*/"Drafted in round"} ${pl.drafted_round}${kept}. ${/*copy:LG-104*/"Price: a pick in round"} ${pl.price_round}.`;
    return `<span class="dr-ke-chip ${pl.player.pos.toLowerCase()}" title="${escapeHtml(tip)}">${shortName(name, pl.player.pos)}${pl.second_year ? `<span class="dr-ke-2" aria-label="kept this season">K</span>` : ""}</span>`;
  };
  $("dr-keepers").querySelector(".dr-ke-table").innerHTML = `<table class="plain dr-ke-matrix"><thead><tr>
      <th scope="col" class="dr-ke-mgr">Manager</th>${cols.map((r) => `<th scope="col" class="dr-ke-rd">${/*copy:LG-99*/"Rd"} ${r}</th>`).join("")}</tr></thead>
    <tbody>${ke.rows.map((row) => `<tr><th scope="row" class="dr-ke-mgr">${managerCell(row.user)}</th>${cols.map((r) => {
      const here = row.players.filter((pl) => pl.price_round === r);
      return `<td>${here.map(chip).join("")}</td>`;
    }).join("")}</tr>`).join("")}</tbody></table>`;
  $("dr-keepers").querySelector(".dr-ke-list").innerHTML = ke.rows.map((row) => `<li>
      <span class="dr-line">${managerCell(row.user)}</span>
      <span class="dr-ke-items">${row.players.length ? row.players.map((pl) => `<span class="dr-ke-item"><b>${/*copy:LG-100*/"Rd"} ${pl.price_round}</b>${chip(pl)}</span>`).join("") : `<span class="muted">${/*copy:LG-101*/"None eligible"}</span>`}</span></li>`).join("");
  wireImages($("dr-keepers"));
}

function renderBoard() {
  const season = state.data.seasons[state.season];
  const bySpot = new Map(season.picks.map((p) => [`${p.round}.${p.slot}`, p]));
  const rounds = season.rounds || Math.max(...season.picks.map((p) => p.round));
  const head = season.slots.map((s) => `<th scope="col" class="dr-slot">${s.user && mgr(s.user) ? crest({ ...mgr(s.user), user_id: s.user }, "xs") : ""}${managerLink(s.user)}</th>`).join("");
  const cell = (p) => {
    if (!p) return `<td></td>`;
    const pos = p.player.pos;
    const by = p.user !== p.slot_user && mgr(p.user) ? `<span class="dr-by">${TRADED}${escapeHtml(mgr(p.user).name)}</span>` : "";
    const badge = p.keeper ? keeperBadge(p) : state.grade === "day" ? stealBadge(p) : hitBadge(p);
    const tip = `${p.label} (${p.no}) ${fullName(p)}, ${pos} ${p.player.team}; picked by ${mgr(p.user)?.name || "–"}`
      + (p.user !== p.slot_user ? ` via ${mgr(p.slot_user)?.name || "–"}` : "")
      + (p.adp_rank ? `; ADP rank ${p.adp_rank}` : "") + `; WAR ${p.war.toFixed(2)}, WAR rank ${p.war_rank}`;
    return `<td><div class="dr-cell ${pos.toLowerCase()}" title="${escapeHtml(tip)}" data-pick="${p.no}">`
      + `<span class="dr-cell-top"><span>${p.label}</span><span>${escapeHtml(pos)} ${escapeHtml(p.player.team)}</span></span>`
      + `<span class="dr-name">${shortName(fullName(p), pos)}</span><span class="dr-by-slot">${by}</span><span class="dr-badge-slot">${badge}</span></div></td>`;
  };
  const rows = Array.from({ length: rounds }, (_, i) => i + 1).map((r) =>
    `<tr><th scope="row" class="dr-rd">${/*copy:LG-89*/"Rd"} ${r}</th>${season.slots.map((s) => cell(bySpot.get(`${r}.${s.slot}`))).join("")}</tr>`).join("");
  const width = 48 + season.slots.length * 96;  // fixed columns: the round label, then 92 px cells plus padding
  $("dr-board").innerHTML = `<table class="plain dr-board" style="width: ${width}px"><thead><tr><th scope="col" class="dr-rd"><span class="sr-only">Round</span></th>${head}</tr></thead><tbody>${rows}</tbody></table>`;
  wireImages($("dr-board"));
}

function sortHead(key, label, cls = "") {
  return `<th scope="col" class="${cls}" data-col="${key}"><button type="button" class="sort">${label}</button></th>`;
}

function renderTable() {
  const season = state.data.seasons[state.season];
  const col = COLUMNS[state.sort.key];
  const picks = [...season.picks].sort(comparator(col, state.sort.dir, (a, b) => a.no - b.no));
  const row = (p) => {
    const pos = p.player.pos;
    const via = p.user !== p.slot_user && mgr(p.slot_user) ? `via ${escapeHtml(mgr(p.slot_user).name)}` : "";
    const fa = rookie() && p.player.exp > 0 ? `<span class="dr-badge fa">${/*copy:LG-90*/"Free agent"}</span>` : "";
    const games = `${p.games} ${/*copy:LG-91*/"of"} ${p.games_possible}`;
    return `<tr>
      <td class="dr-pick"><b>${p.label}</b> <span>(${p.no})</span></td>
      <td>${managerCell(p.user, via)}</td>
      <td><span class="dr-player">${shortName(fullName(p), pos)}${posPill(pos)}<span class="dr-sub">${escapeHtml(p.player.team)}</span>${fa}${keeperBadge(p)}${stealBadge(p)}</span></td>
      <td class="num muted">${p.adp == null ? "–" : p.adp.toFixed(1)}</td>
      <td>${p.adp_rank ? `<span class="dr-rank"><span>${p.adp_rank}</span>${posPill(pos, p.adp_pos_rank)}</span>` : `<span class="muted">–</span>`}</td>
      <td class="num strong">${war(p.war)}</td>
      <td><span class="dr-rank"><span>${p.war_rank}</span>${posPill(pos, p.war_pos_rank)}</span></td>
      <td class="num muted">${p.slot_war == null ? "–" : `${sign(p.slot_war)}${Math.abs(p.slot_war).toFixed(2)}`}</td>
      <td>${hitBadge(p)}</td>
      <td class="num dr-games${p.hit_bust === "unlucky" ? " unlucky" : ""}">${games}</td></tr>`;
  };
  const wide = $("dr-table").querySelector(".dr-wide");
  wide.innerHTML = `<table class="plain dr-table"><thead><tr>
      ${sortHead("no", "Pick")}${sortHead("manager", "Manager")}${sortHead("player", "Player")}${sortHead("adp", "ADP", "num")}
      ${sortHead("adp_rank", "ADP Rank")}${sortHead("war", "WAR", "num")}${sortHead("war_rank", "WAR Rank")}${sortHead("slot_war", "Slot WAR", "num")}
      ${sortHead("war_gap", "Hit/Bust")}${sortHead("games", "Games Played", "num")}</tr></thead>
    <tbody>${picks.map(row).join("")}</tbody></table>`;
  const table = wide.querySelector("table");
  markSorted(table.querySelectorAll("thead th[data-col]"), state.sort);
  wireHeaders(table, (key) => {
    state.sort = state.sort.key === key ? { key, dir: state.sort.dir === "asc" ? "desc" : "asc" } : { key, dir: FIRST_DIR[key] };
    renderTable();
    showDraft();
  });
  $("dr-table").querySelector(".dr-list").innerHTML = season.picks.map((p) => {
    const via = p.user !== p.slot_user && mgr(p.slot_user) ? ` · via ${escapeHtml(mgr(p.slot_user).name)}` : "";
    return `<li><span class="dr-pick"><b>${p.label}</b><span class="dr-sub">(${p.no})</span></span>
      <span><span class="dr-line">${shortName(fullName(p), p.player.pos)}${posPill(p.player.pos)}${keeperBadge(p)}${stealBadge(p)}</span>
        <span class="dr-meta">${escapeHtml(mgr(p.user)?.name || "–")}${via} · WAR ${war(p.war)}</span></span>
      <span class="dr-grade">${hitBadge(p)}</span></li>`;
  }).join("");
  wireImages($("dr-table"));
}

function avgBadge(x, kind) {
  if (x == null) return `<span class="muted">–</span>`;
  const cls = kind === "adp" ? (x >= 1 ? "steal" : x <= -1 ? "reach" : "") : x >= 0.25 ? "hit" : x <= -0.25 ? "bust" : "";
  return `<span class="dr-avg ${cls}">${sign(x)}${Math.abs(x).toFixed(kind === "adp" ? 1 : 2)}</span>`;
}

function bestPick(b) {
  if (!b) return `<span class="muted">–</span>`;
  const season = state.span === "all" && b.season ? `${b.season} ` : "";
  return `<span class="dr-player"><b>${season}${b.label}</b> ${shortName(`${b.player.first} ${b.player.last}`.trim(), b.player.pos)}${posPill(b.player.pos)} ${war(b.war_gap)}</span>`;
}

function renderManagers() {
  if (!state.data || !state.season) return;
  for (const b of $("dr-span").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.drSpan === state.span));
  const rows = state.span === "all" ? state.data.all_drafts : state.data.seasons[state.season].summary;
  $("dr-managers").querySelector(".dr-mgr-table").innerHTML = `<table class="plain dr-table"><thead><tr>
      <th scope="col">Manager</th><th scope="col" class="num">Picks</th><th scope="col">Steal/Reach</th><th scope="col">Hit/Bust</th>
      <th scope="col" class="num">WAR</th><th scope="col">Best Pick</th><th scope="col" class="num">Unlucky</th></tr></thead>
    <tbody>${rows.map((r) => `<tr><td>${managerCell(r.user)}</td><td class="num">${r.picks}</td><td>${avgBadge(r.adp_diff, "adp")}</td>
      <td>${avgBadge(r.war_gap, "war")}</td><td class="num strong">${war(r.war)}</td><td>${bestPick(r.best)}</td>
      <td class="num muted">${r.unlucky || "–"}</td></tr>`).join("")}</tbody></table>`;
  $("dr-managers").querySelector(".dr-mgr-list").innerHTML = rows.map((r) => `<li>
      <span class="dr-line">${managerCell(r.user)}<span class="dr-meta">${r.picks} ${r.picks === 1 ? /*copy:LG-95*/"pick" : /*copy:LG-92*/"picks"}</span></span>
      <span class="dr-meta">Steal/Reach ${avgBadge(r.adp_diff, "adp")} · Hit/Bust ${avgBadge(r.war_gap, "war")} · WAR ${war(r.war)}${r.unlucky ? ` · ${r.unlucky} ${/*copy:LG-93*/"unlucky"}` : ""}</span>
      <span class="dr-meta">${/*copy:LG-94*/"Best pick:"} ${bestPick(r.best)}</span></li>`).join("");
  wireImages($("dr-managers"));
  showDraft();
}
