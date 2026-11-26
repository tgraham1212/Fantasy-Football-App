/* Managers page: one manager at a time, after Football Manager's club page. A team info bar, a
   current season info bar, then four cards (Roster, Team History, Moves, Team News). Every figure
   comes from data/<league>/managers.json (src/ffapp/managers.py); this module only renders. */

import { crest as crestHtml, escapeHtml, fitNames, headshot, nameAttrs, shortName, wireImages } from "./people.js?v=__BUILD__";

const state = {
  leagueKey: null,
  leagueName: "",
  entry: null,      // index.leagues[i].managers
  data: null,       // data/<league>/managers.json
  byId: {},         // user id -> manager
  selected: null,   // user id
  colorOf: () => null,  // user id -> css token of a current member's chart colour, or null
  onChange: () => {},   // tell app.js to rewrite the URL
  openPage: () => {},   // switch to another sub-tab (tile and news links)
  histTab: "hist",
  cardTab: "roster",
  movesSeason: null,
  movesFilter: "all",
};

const $ = (id) => document.getElementById(id);
const visible = () => !$("page-managers").hidden;
const fmt1 = (x) => (x == null ? "–" : Number(x).toFixed(1));
const fmt2 = (x) => (x == null ? "–" : Number(x).toFixed(2));
const thousands = (x) => Number(x).toLocaleString("en-US", { maximumFractionDigits: 1 });
const yy = (s) => String(s).slice(2);
const ordinal = (n) => { const s = ["th", "st", "nd", "rd"], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
const record = (r) => `${r.wins}-${r.losses}${r.ties ? `-${r.ties}` : "-0"}`;
const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);
const signed = (x, d = 1) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(d);

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading and the picker ------------------------------------------------------------------------

/* Called by app.js whenever a league loads. `wanted` is the manager named in the URL. */
export async function loadManagers(leagueKey, leagueName, entry, colorOf, wanted, onChange, openPage) {
  state.leagueKey = leagueKey;
  state.leagueName = leagueName;
  state.entry = entry || null;
  state.colorOf = colorOf || (() => null);
  state.onChange = onChange || (() => {});
  state.openPage = openPage || state.openPage;
  if (!state.entry) {
    $("mgr-unavailable").hidden = false;
    $("mgr-content").hidden = true;
    $("mgr-picker").hidden = true;
    return;
  }
  state.data = await fetchJson(`data/${state.entry.file}`);
  state.byId = Object.fromEntries(state.data.managers.map((m) => [m.user_id, m]));
  const keep = state.selected && state.byId[state.selected] ? state.selected : null;
  state.selected = findManager(wanted) || keep || (state.data.managers.find((m) => m.current) || state.data.managers[0]).user_id;
  $("mgr-unavailable").hidden = true;
  $("mgr-picker").hidden = false;
  $("mgr-content").hidden = false;
  fillPicker();
  render();
}

export async function reloadManagers() {
  if (state.entry) await loadManagers(state.leagueKey, state.leagueName, state.entry, state.colorOf, null, state.onChange, state.openPage);
}

/* The URL part naming the selected manager. */
export function managerSlug() {
  const m = state.byId[state.selected];
  return m ? encodeURIComponent(m.name) : "";
}

/* Select a manager by name or user id (from a link anywhere on the site). */
export function selectManager(nameOrId) {
  const id = findManager(nameOrId);
  if (!id) return false;
  state.selected = id;
  state.movesSeason = null;
  state.movesFilter = "all";
  if (state.data) { fillPicker(); render(); }
  state.onChange();
  return true;
}

function findManager(nameOrId) {
  if (!nameOrId || !state.data) return null;
  const text = decodeURIComponent(String(nameOrId)).toLowerCase();
  const hit = state.data.managers.find((m) => m.user_id === nameOrId || m.name.toLowerCase() === text);
  return hit ? hit.user_id : null;
}

function ordered() {
  const byName = (a, b) => a.name.localeCompare(b.name, "en", { sensitivity: "base" });
  return [...state.data.managers.filter((m) => m.current).sort(byName), ...state.data.managers.filter((m) => !m.current).sort(byName)];
}

function fillPicker() {
  const list = ordered();
  const option = (m) => `<option value="${m.user_id}"${m.user_id === state.selected ? " selected" : ""}>${escapeHtml(m.name)} · ${escapeHtml(m.team_name)}</option>`;
  const current = list.filter((m) => m.current), retired = list.filter((m) => !m.current);
  $("mgr-select").innerHTML = `<optgroup label="Managers">${current.map(option).join("")}</optgroup>` + (retired.length ? `<optgroup label="Retired">${retired.map(option).join("")}</optgroup>` : "");
}

function step(delta) {
  const list = ordered();
  const i = list.findIndex((m) => m.user_id === state.selected);
  selectManager(list[(i + delta + list.length) % list.length].user_id);
}

export function initManagers() {
  $("mgr-select").addEventListener("change", (e) => selectManager(e.target.value));
  $("mgr-prev").addEventListener("click", () => step(-1));
  $("mgr-next").addEventListener("click", () => step(1));
  $("mgr-content").addEventListener("click", (e) => {
    const goto = e.target.closest("[data-goto]");
    if (goto) { e.preventDefault(); state.openPage(goto.dataset.goto); scrollTo({ top: 0 }); return; }
    const link = e.target.closest("[data-manager]");
    if (link) { e.preventDefault(); selectManager(link.dataset.manager); scrollTo({ top: 0 }); return; }
    const tab = e.target.closest("[data-htab]");
    if (tab) { state.histTab = tab.dataset.htab; renderHistoryTabs(); fitNames($("mgr-content")); return; }
    const card = e.target.closest("[data-card-tab]");
    if (card) { state.cardTab = card.dataset.cardTab; renderCardTabs(); fitNames($("mgr-content")); return; }
    if (e.target.closest(".mgr-moves-prev, .mgr-moves-next")) { stepMovesSeason(e.target.closest(".mgr-moves-prev") ? -1 : 1); return; }
    if (e.target.closest(".mgr-showmore")) { $("mgr-content").querySelectorAll(".mgr-story.late").forEach((s) => s.classList.remove("late")); e.target.closest(".mgr-showmore").remove(); }
  });
  $("mgr-content").addEventListener("change", (e) => {
    if (e.target.id === "mgr-moves-season") { state.movesSeason = e.target.value; renderMoves(); }
    if (e.target.id === "mgr-moves-filter") { state.movesFilter = e.target.value; renderMoves(); }
  });
  addEventListener("resize", () => { if (visible()) { fitBanners(); fitNames($("mgr-content")); } });
}

export function showManagers() {
  if (state.data) { fitBanners(); fitNames($("mgr-content")); }
}

// -- shared pieces ------------------------------------------------------------------------------------

/* Team logo, else Sleeper avatar, else initials in the team colour of a current member. */
function crest(m, size) {
  return crestHtml(m, size, m && m.current ? state.colorOf(m.user_id) : null);
}

function managerLink(userId, label) {
  const m = state.byId[userId];
  if (!m) return escapeHtml(label || "–");
  return `<a class="manager-link" href="#${state.leagueKey}/managers/${encodeURIComponent(m.name)}" data-manager="${m.user_id}">${escapeHtml(label || m.name)}</a>`;
}

// -- render -------------------------------------------------------------------------------------------

function render() {
  const m = state.byId[state.selected];
  if (!m) return;
  const root = $("mgr-content");
  root.innerHTML = `
    <section class="mgr-bar" aria-label="Team">${teamBar(m)}</section>
    <section class="mgr-season" aria-label="Season">${seasonTiles(m)}</section>
    <div class="mgr-cardtabs" role="group" aria-label="Cards">${[["roster", "Roster"], ["history", "History"], ["moves", "Moves"], ["news", "News"]]
      .map(([id, label]) => `<button type="button" data-card-tab="${id}" aria-pressed="${id === state.cardTab}">${label}</button>`).join("")}</div>
    <div class="mgr-cards">
      <section class="mgr-card mgr-roster" data-card="roster" aria-label="Roster">${rosterCard(m)}</section>
      <section class="mgr-card mgr-history" data-card="history" aria-label="Team History">${historyCard(m)}</section>
      <section class="mgr-card mgr-moves" data-card="moves" aria-label="Moves" id="mgr-moves"></section>
      <section class="mgr-card mgr-news" data-card="news" aria-label="Team News">${newsCard(m)}</section>
    </div>`;
  renderMoves();
  renderHistoryTabs();
  renderCardTabs();
  wireImages(root);
  fitBanners();
  fitNames(root);
}

function renderCardTabs() {
  for (const b of $("mgr-content").querySelectorAll("[data-card-tab]")) b.setAttribute("aria-pressed", String(b.dataset.cardTab === state.cardTab));
  for (const c of $("mgr-content").querySelectorAll(".mgr-card")) c.classList.toggle("show", c.dataset.card === state.cardTab);
}

// -- team info bar ----------------------------------------------------------------------------------

const TROPHY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10v2h3v3a4 4 0 0 1-4 4h-.3A5 5 0 0 1 13 14.9V17h3v2H8v-2h3v-2.1A5 5 0 0 1 8.3 12H8a4 4 0 0 1-4-4V5h3V3zm0 4H6v1a2 2 0 0 0 1 1.7V7zm10 0v2.7A2 2 0 0 0 18 8V7h-1z"/></svg>';
const BOWL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 2h5v7h8v2a6 6 0 0 1-4 5.7V19h2v3H7v-3h2v-2.6A6 6 0 0 1 5 11V9h1V2zm2 2v5h1V4H8z"/></svg>';
const WORD = { W: "win", L: "loss", D: "draw", T: "draw" };

function formBars(results) {
  const five = [...Array(Math.max(0, 5 - results.length)).fill("D"), ...results.slice(-5)];
  const label = /*copy:MGR-03*/`Form, oldest first: ${five.map((r) => WORD[r]).join(", ")}`;
  return `<span class="mgr-form" role="img" aria-label="${label}">${five.map((r) => `<span class="${r === "W" ? "w" : r === "L" ? "l" : "d"}" title="${WORD[r]}"></span>`).join("")}</span>`;
}

function teamBar(m) {
  const flags = (years, kind) => years.length ? `<div class="mgr-rod-group"><div class="mgr-rod"></div><div class="mgr-flags">${years
    .map((y) => `<span class="mgr-flag ${kind}" title="${kind === "champ" ? "Champion" : "Toilet bowl"} ${y}">${kind === "champ" ? TROPHY : BOWL}<span>${yy(y)}</span></span>`).join("")}</div></div>` : "";
  const facts = [];
  if (m.current) facts.push(["Form", formBars(m.form || [])]);
  facts.push(m.current ? ["Founded", escapeHtml(m.first)] : ["Seasons", `${escapeHtml(m.first)}–${escapeHtml(m.last)}`]);
  facts.push(["All-Time", record(m.all_time)]);
  facts.push(["Rating", m.rating ? `${thousands(Math.round(m.rating.mu))}${m.current ? "" : ` (${m.rating.season})`}` : "–"]);
  facts.push(["Rival", m.rival ? managerLink(m.rival.user_id, m.rival.name) : "–"]);
  return `${crest(m, "lg")}<h2 class="mgr-tname">${escapeHtml(m.team_name)}</h2>
    <div class="mgr-banners" id="mgr-banners">${flags(m.banners.champion, "champ")}${flags(m.banners.toilet_bowl, "bowl")}</div>
    <dl class="mgr-facts">${facts.map(([k, v]) => `<div class="mgr-fact"><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>`;
}

/* One row of banners while it fits; out of room, champions on top and the toilet bowl below. */
function fitBanners() {
  const b = $("mgr-banners");
  if (!b) return;
  b.classList.remove("stacked");
  if (b.scrollWidth > b.clientWidth + 1) b.classList.add("stacked");
}

// -- season info bar --------------------------------------------------------------------------------

const ICON = {
  rank: '<svg viewBox="0 0 24 24"><path d="M4 20V10h4v10H4zm6 0V4h4v16h-4zm6 0v-7h4v7h-4z"/></svg>',
  ball: '<svg viewBox="0 0 24 24"><path d="M12 3c5 0 9 4 9 9s-4 9-9 9-9-4-9-9 4-9 9-9zm-3 6l-1 3 1 3h6l1-3-1-3H9z"/></svg>',
  cal: '<svg viewBox="0 0 24 24"><path d="M7 2h2v2h6V2h2v2h3v18H4V4h3V2zm-1 8v10h12V10H6z"/></svg>',
  user: '<svg viewBox="0 0 24 24"><path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-5 0-9 2.5-9 6v2h18v-2c0-3.5-4-6-9-6z"/></svg>',
  star: '<svg viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18.5 21 12 16.5 5.5 21l2-7.5L2 9h7z"/></svg>',
  up: '<svg viewBox="0 0 24 24"><path d="M4 18l6-6 4 4 6-8v4h2V4h-8v2h4l-4 6-4-4-8 8z"/></svg>',
  pct: '<svg viewBox="0 0 24 24"><path d="M7 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8zm10 10a4 4 0 1 1 0 8 4 4 0 0 1 0-8zM18 3h3L6 21H3z"/></svg>',
};

function tile(icon, label, line1, line2, opts = {}) {
  const tag = opts.href ? "a" : "div";
  const href = opts.href ? ` href="${opts.href}" data-goto="${opts.href.split("/")[1] || "predictions"}"` : "";
  return `<${tag} class="mgr-tile${opts.dim ? " dim" : ""}"${href}><span class="mgr-tile-k"><span class="lbl">${ICON[icon]}${label}</span>${opts.badge || ""}</span>
    <span class="mgr-tile-body"><span class="l1${opts.center ? " center" : ""}">${line1}</span><span class="l2${opts.center ? " center" : ""}${opts.lg ? " lg" : ""}">${line2}</span></span></${tag}>`;
}

function seasonTiles(m) {
  const t = m.tiles;
  const page = (p) => `#${state.leagueKey}${p ? `/${p}` : ""}`;
  const last = t.last_result;
  const opp = last ? state.byId[last.opp_user] : null;
  const tiles = [];
  const posLabel = m.current ? "Current League Position" : `Final League Position · ${m.last}`;
  tiles.push(tile("rank", posLabel, `<span class="big">${t.position ? ordinal(t.position) : "–"}</span>`, `${record(t.record)} · ${thousands(t.points_for)} PF`, { lg: true, href: m.current ? page("") : null }));
  tiles.push(tile("ball", last ? `Last Result · ${last.season === m.last && m.current ? `Wk ${last.week}` : last.season}` : "Last Result",
    last ? `<span class="mgr-score">${crest(m, "xs")}<b>${fmt1(last.points)} – ${fmt1(last.opp_points)}</b>${crest(opp, "xs")}</span>` : "–",
    last ? `<span class="res ${last.result.toLowerCase()}">${last.result}</span> vs ${escapeHtml(last.opp)}` : "", { center: true, href: page("games") }));
  if (m.current && t.next) {
    const nopp = state.byId[t.next.opp_user];
    const badge = t.next.rivalry ? '<span class="mgr-rivalry">Rivalry Week</span>' : "";
    tiles.push(tile("cal", `Next · Wk ${t.next.week}`, `${crest(nopp, "sm")}<span class="main">${escapeHtml(t.next.opp || "–")}</span>`,
      t.next.win_prob != null ? `${pct(t.next.win_prob)} win forecast` : "", { badge, href: page("games") }));
  } else {
    tiles.push(tile("cal", "Next", `<span class="main">${m.current ? "–" : "Retired"}</span>`, m.current ? "" : `${escapeHtml(m.first)}–${escapeHtml(m.last)}`, { dim: !m.current }));
  }
  tiles.push(tile("user", "Manager", `${crest({ ...m, logo: null }, "sm")}<span class="main">${escapeHtml(m.name)}</span>`, `${pct(m.all_time.win_rate)} Win Rate`));
  const scorer = t.top_scorer || t.top_projected;
  const scorerLabel = t.top_scorer ? (m.current ? "Top Scorer" : `Top Scorer · ${m.last}`) : "Top Scorer (Projected)";
  tiles.push(tile("star", scorerLabel, scorer ? `${headshot(scorer.player_id)}<span class="main">${shortName(scorer.name, scorer.position)}</span>` : "–",
    scorer ? `${thousands(scorer.points)} pts${t.top_scorer ? "" : " projected"} · ${escapeHtml(scorer.position || "")}` : "", { href: page("positions") }));
  const best = m.players.best;
  tiles.push(tile("up", "Best Player All-Time", best ? `${headshot(best.player_id)}<span class="main">${shortName(best.name)}</span>` : "–",
    best ? `${signed(best.war)} WAR · ${best.seasons} season${best.seasons === 1 ? "" : "s"}` : "", { href: page("war") }));
  if (m.current && t.forecast) {
    const ch = t.forecast.change;
    const change = ch == null ? "" : ch > 0 ? `<span class="up">▲ ${Math.round(ch * 100)}</span> since last week` : ch < 0 ? `<span class="down">▼ ${Math.round(-ch * 100)}</span> since last week` : "no change";
    tiles.push(tile("pct", "Playoff Forecast", `<span class="big">${pct(t.forecast.playoffs)}</span>`, change, { href: page("") }));
  } else {
    tiles.push(tile("pct", "Playoff Forecast", '<span class="big">–</span>', m.current ? "" : "Retired", { dim: !m.current }));
  }
  return tiles.join("");
}

// -- card 1: roster --------------------------------------------------------------------------------------

const POS = { QB: "qb", RB: "rb", WR: "wr", TE: "te", K: "k", DEF: "def" };
const OUT_STATUS = { Out: "O", Doubtful: "D", IR: "IR", PUP: "PUP", Sus: "Sus", NA: "NA", DNR: "DNR" };
const STATUS_LABEL = { Questionable: "Q", ...OUT_STATUS };

function tierOf(ppg, repl) {
  if (ppg == null || !repl) return "r3";
  const x = ppg / repl;
  return x >= 1.5 ? "r5" : x >= 1.2 ? "r4" : x >= 0.9 ? "r3" : x >= 0.7 ? "r2" : "r1";
}

function rosterCard(m) {
  const rows = m.roster || [];
  let lastGroup = null;
  const body = rows.map((r) => {
    const group = r.slot === "BN" ? "bn" : r.slot === "IR" ? "ir" : r.slot === "TX" ? "tx" : "st";
    const split = lastGroup && group !== lastGroup ? ' class="grp-start"' : "";
    lastGroup = group;
    const pill = r.slot === "BN" ? '<span class="mgr-pill out">BN</span>' : r.slot === "IR" ? '<span class="mgr-pill ir">IR</span>' : r.slot === "TX" ? '<span class="mgr-pill tx">Taxi</span>'
      : r.slot === "FLEX" ? '<span class="mgr-pill flex">FLEX</span>' : `<span class="mgr-pill ${POS[r.position] || "out"}">${escapeHtml(r.slot)}</span>`;
    const status = r.status && STATUS_LABEL[r.status] ? `<span class="mgr-badge ${OUT_STATUS[r.status] ? "out" : "q"}" title="${escapeHtml(r.status)}">${STATUS_LABEL[r.status]}</span>`
      : r.bye ? '<span class="mgr-badge bye">Bye</span>' : "";
    const repl = (m.replacement || {})[r.position];
    return `<tr${split}><td class="c-slot">${pill}</td><td class="c-inf">${status}</td><td class="c-name"><span class="pname">${shortName(r.name, r.position)}</span></td>
      <td class="c-pos">${escapeHtml(r.position || "")}</td><td class="c-ppg">${r.ppg == null ? "–" : `<span class="mgr-chip ${tierOf(r.ppg, repl)}">${fmt1(r.ppg)}</span>`}</td></tr>`;
  }).join("");
  const wp = m.week_points;
  const foot = wp ? `<span>Starters <b>${fmt1(wp.starters)}</b></span><span>Bench <b>${fmt1(wp.bench)}</b></span>` : "";
  const title = m.current ? "Roster" : `Roster · ${m.last}`;
  return `<div class="mgr-card-head"><h3>${title}</h3></div>
    <div class="mgr-scroll" tabindex="0" role="region" aria-label="Roster table"><table class="mgr-table">
      <thead><tr><th scope="col" class="c-slot">Slot</th><th scope="col" class="c-inf">Inf</th><th scope="col" class="c-name">Player</th><th scope="col" class="c-pos">Pos</th><th scope="col" class="c-ppg">PPG</th></tr></thead>
      <tbody>${body || `<tr><td colspan="5" class="mgr-empty">${/*copy:MGR-04*/"No roster is stored for this manager."}</td></tr>`}</tbody></table></div>
    <div class="mgr-foot">${foot}</div>`;
}

// -- card 2: team history --------------------------------------------------------------------------------

function historyCard(m) {
  const tabs = [["hist", "History"], ["h2h", "Head to Head"], ["rec", "Records"]];
  return `<div class="mgr-card-head"><h3>Team History</h3></div>
    <div class="mgr-htabs" role="tablist">${tabs.map(([id, label]) => `<button type="button" role="tab" data-htab="${id}" aria-selected="${id === state.histTab}">${label}</button>`).join("")}</div>
    <div class="mgr-scroll" tabindex="0" role="region" aria-label="Team history">
      <div class="mgr-panel" data-hpanel="hist">${historyPanel(m)}</div>
      <div class="mgr-panel" data-hpanel="h2h">${h2hPanel(m)}</div>
      <div class="mgr-panel" data-hpanel="rec">${recordsPanel(m)}</div>
    </div><div></div>`;
}

function renderHistoryTabs() {
  const root = $("mgr-content");
  for (const b of root.querySelectorAll("[data-htab]")) b.setAttribute("aria-selected", String(b.dataset.htab === state.histTab));
  for (const p of root.querySelectorAll("[data-hpanel]")) p.hidden = p.dataset.hpanel !== state.histTab;
}

const LUCK_LABEL = {
  allPlay: "All-play record",
  pace: /*copy:MGR-13*/"Wins above all-play pace",
  against: /*copy:MGR-14*/"Points against vs league average",
  bench: /*copy:MGR-15*/"Points left on bench (all-time)",
};

function historyPanel(m) {
  const h = m.history;
  const titles = (h.honours.champion || []).length;
  const trips = (h.honours.playoffs || []).length;
  const about = m.current
    ? /*copy:MGR-05*/`${escapeHtml(m.name)} founded ${escapeHtml(m.team_name)} in ${m.first}. Since then: ${titles === 1 ? "one title" : `${titles} titles`}, ${trips === 1 ? "one playoff trip" : `${trips} playoff trips`} and a ${record(m.all_time)} regular-season record.`
    : /*copy:MGR-06*/`${escapeHtml(m.name)} managed in the league from ${m.first} to ${m.last}: ${titles === 1 ? "one title" : `${titles} titles`}, ${trips === 1 ? "one playoff trip" : `${trips} playoff trips`} and a ${record(m.all_time)} regular-season record.`;
  const hon = h.honours;
  const years = (list, short) => (list && list.length ? list.map((y) => (short ? yy(y) : y)).join(", ") : "–");
  const honours = [
    ["g", "Champion", years(hon.champion)],
    ["n", "Runner-up", years(hon.runner_up)],
    ["n", "Regular-season 1st", years(hon.regular_first)],
    ["n", "Most points", years(hon.most_points)],
    ["n", "Playoff trips", years(hon.playoffs, true)],
  ];
  if (state.data.toilet_bowl) honours.push(["b", "Toilet bowl", years(hon.toilet_bowl)]);
  const lk = h.luck;
  const luckRows = lk ? [
    [LUCK_LABEL.allPlay, record(lk.all_play), ""],
    [LUCK_LABEL.pace, signed(lk.wins_above_pace), lk.wins_above_pace >= 0 ? "up" : "down"],
    [LUCK_LABEL.against, `${signed(lk.pa_vs_league)} per game`, lk.pa_vs_league <= 0 ? "up" : "down"],
    [LUCK_LABEL.bench, thousands(Math.round(lk.bench_points)), ""],
  ] : [];
  const luck = lk ? `<div class="mgr-luck">${luckRows.map(([k, v, c]) => `<span>${k}</span><span class="${c}">${v}</span>`).join("")}</div>` : "–";
  return `<p class="mgr-about">${about}</p>
    <div class="mgr-box"><h4>League History</h4>${finishChart(m)}
      <div class="mgr-key"><span>${TROPHY}Champion</span><span><i class="p"></i>Playoffs</span>${state.data.toilet_bowl ? "<span>&#128169; Toilet bowl</span>" : ""}${m.current && h.forecast_finish ? '<span><i class="f"></i>Forecast</span>' : ""}</div></div>
    <div class="mgr-box"><h4>Honours</h4><dl class="mgr-hon">${honours.map(([c, k, v]) => `<dt><span class="mark ${c}"></span>${k}</dt><dd>${v}</dd>`).join("")}</dl></div>
    <div class="mgr-box"><h4>Luck</h4>${luck}</div>`;
}

function finishChart(m) {
  const fin = m.history.finishes.filter((f) => f.place && f.final);
  const forecast = m.current ? m.history.forecast_finish : null;
  const teams = Math.max(12, ...m.history.finishes.map((f) => f.place || 0));
  const cols = fin.length + (forecast ? 1 : 0);
  if (!cols) return `<p class="mgr-empty">${/*copy:MGR-07*/"No finished season yet."}</p>`;
  const W = 262, H = 150, L = 30, R = 12, T = 12, B = 22;
  const x = (i) => (cols === 1 ? (L + W - R) / 2 : L + (i * (W - L - R)) / (cols - 1));
  const y = (r) => T + ((r - 1) * (H - T - B)) / (teams - 1);
  const champs = new Set(m.history.honours.champion || []);
  const bowls = new Set(m.history.honours.toilet_bowl || []);
  const trips = new Set(m.history.honours.playoffs || []);
  let s = `<svg class="mgr-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeHtml(/*copy:MGR-08*/`Final finish each season: ${fin.map((f) => `${f.season} ${ordinal(f.place)}`).join(", ")}`)}">`;
  s += `<rect class="zone" x="${L}" y="${y(1) - 6}" width="${W - L - R}" height="${y(6) - y(1) + 12}"/>`;
  for (const r of [1, 6, teams]) s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${y(r)}" y2="${y(r)}"/><text x="${L - 6}" y="${y(r) + 3}" text-anchor="end">${ordinal(r)}</text>`;
  if (fin.length > 1) s += `<polyline class="line" points="${fin.map((f, i) => `${x(i)},${y(f.place)}`).join(" ")}"/>`;
  if (forecast && fin.length) s += `<line class="proj" x1="${x(fin.length - 1)}" y1="${y(fin[fin.length - 1].place)}" x2="${x(fin.length)}" y2="${y(forecast)}"/>`;
  fin.forEach((f, i) => {
    const cx = x(i), cy = y(f.place);
    if (champs.has(f.season)) s += `<g transform="translate(${cx - 8} ${cy - 8})"><title>${f.season}: champion</title><circle class="halo" cx="8" cy="8" r="9"/><g transform="scale(0.667)" class="trophy">${TROPHY.replace(/<\/?svg[^>]*>/g, "")}</g></g>`;
    else if (bowls.has(f.season)) s += `<g><title>${f.season}: toilet bowl</title><circle class="halo" cx="${cx}" cy="${cy}" r="8"/><text class="emoji" x="${cx}" y="${cy + 5}" text-anchor="middle">&#128169;</text></g>`;
    else s += `<circle class="dot ${trips.has(f.season) ? "p" : ""}" cx="${cx}" cy="${cy}" r="4"><title>${f.season}: ${ordinal(f.place)}</title></circle>`;
  });
  if (forecast) s += `<circle class="fdot" cx="${x(fin.length)}" cy="${y(forecast)}" r="4.5"><title>${state.data.season}: forecast ${ordinal(forecast)}</title></circle>`;
  [...fin.map((f) => f.season), ...(forecast ? [state.data.season] : [])].forEach((season, i) => { s += `<text x="${x(i)}" y="${H - 6}" text-anchor="middle">${yy(season)}</text>`; });
  return s + "</svg>";
}

function h2hPanel(m) {
  const rows = m.head_to_head || [];
  if (!rows.length) return `<p class="mgr-empty">${/*copy:MGR-09*/"No games played yet."}</p>`;
  return `<table class="mgr-h2h"><thead><tr><th scope="col" class="c-m">Manager</th><th scope="col" class="num c-wl">W-L</th><th scope="col" class="num c-last">Last</th></tr></thead><tbody>
    ${rows.map((r) => `<tr><td class="c-m">${managerLink(r.user_id, r.name)}${r.rival ? '<span class="mgr-tag riv">Rival</span>' : ""}<span class="pf">${thousands(r.pf)}–${thousands(r.pa)} pts</span></td>
      <td class="num">${r.wins}-${r.losses}${r.ties ? `-${r.ties}` : ""}</td>
      <td class="num last">${r.last ? `<span class="res ${r.last.result.toLowerCase()}">${r.last.result}</span> ${fmt1(r.last.points)}–${fmt1(r.last.opp_points)}` : "–"}</td></tr>`).join("")}
    </tbody></table>`;
}

const RECORD_LABEL = {
  high_score: "Highest score", low_score: "Lowest score", biggest_win: "Biggest win", biggest_loss: "Biggest loss",
  closest_loss: "Closest loss", win_streak: "Longest win streak", loss_streak: "Longest losing streak", season_points: /*copy:MGR-16*/"Most points in a season",
};

function recordsPanel(m) {
  const name = (u) => state.byId[u]?.name || "";
  const where = (k, r) => {
    if (k === "win_streak" || k === "loss_streak") return `${r.season} · weeks ${r.from}–${r.to}`;
    if (k === "season_points") return `${r.season}`;
    return `${r.season} · week ${r.week} vs ${escapeHtml(name(r.opp))}`;
  };
  const value = (k, r) => (k === "biggest_win" ? signed(r.value) : k === "biggest_loss" || k === "closest_loss" ? `−${fmt1(r.value)}` : k.endsWith("streak") ? String(r.value) : thousands(r.value));
  const tag = (rank) => (rank && rank <= 3 ? `<span class="mgr-tag t${rank}">#${rank} All Time</span>` : "");
  const rows = Object.keys(RECORD_LABEL).filter((k) => m.records[k]).map((k) => {
    const r = m.records[k];
    return `<div class="mgr-rec"><span class="rk">${RECORD_LABEL[k]}${tag(r.rank)}</span><span class="rv">${value(k, r)}</span><span class="rw">${where(k, r)}</span></div>`;
  });
  if (m.rivalry && m.rival) {
    rows.push(`<div class="mgr-rec"><span class="rk">Rivalry week</span><span class="rv">${m.rivalry.wins}-${m.rivalry.losses}${m.rivalry.ties ? `-${m.rivalry.ties}` : ""}</span><span class="rw">vs ${escapeHtml(m.rival.name)}${m.rivalry.seasons.length ? `, ${m.rivalry.seasons[0]}–${m.rivalry.seasons[m.rivalry.seasons.length - 1]}` : ""}</span></div>`);
  }
  const names = m.team_names.map((t) => `<div><span>${t.from === t.to ? t.from : `${t.from}–${t.to === state.data.season && m.current ? "" : yy(t.to)}`}</span><span>${escapeHtml(t.name)}</span></div>`).join("");
  return `<div>${rows.join("") || `<p class="mgr-empty">${/*copy:MGR-12*/"No games played yet."}</p>`}</div><div class="mgr-box"><h4>Team Names</h4><div class="mgr-names">${names}</div></div>`;
}

// -- card 3: moves ---------------------------------------------------------------------------------------

function movesSeasons(m) {
  return Object.keys(m.faab || {}).sort().reverse();
}

function stepMovesSeason(delta) {
  const m = state.byId[state.selected];
  const seasons = movesSeasons(m);
  if (state.movesSeason === "all") { state.movesSeason = delta < 0 ? seasons[seasons.length - 1] : seasons[0]; renderMoves(); return; }
  const i = seasons.indexOf(state.movesSeason);
  const next = seasons[i - delta];   // the list runs newest first: "previous" is older
  if (next) { state.movesSeason = next; renderMoves(); }
}

/* WAR chip on the roster card's colours; "no games" when the move's window held no game for him,
   "no games yet" when nothing after the move has been scored. */
function moveChip(r) {
  if (r.war == null) return `<span class="mgr-chip none">${r.pending ? /*copy:MGR-19*/"no games yet" : "no games"}</span>`;
  const w = Math.round(r.war * 10) / 10 || 0;   // no "−0.0": tiny values round to 0.0
  const tier = w >= 1 ? "r5" : w >= 0.3 ? "r4" : w > -0.1 ? "r3" : w > -0.4 ? "r2" : "r1";
  return `<span class="mgr-chip ${tier}">${signed(w)}</span>`;
}

function moveWeek(r, all) {
  return all ? `week&nbsp;${r.week}, ${r.season}` : `week&nbsp;${r.week}`;
}

function moveRow(r, kind, all) {
  let how;
  if (kind === "added") {
    if (r.via === "waiver") {
      const tip = r.next != null ? `Next bid $${r.next}` : "No other bids";
      how = `Waiver · $${r.bid}${r.tied ? ` · <span title="${/*copy:MGR-20*/"Tied with the next bid and won on waiver priority"}">tied</span>` : r.over > 0 ? ` <span class="over" title="${tip}">+$${r.over}</span>` : ""}`;
    } else how = r.via === "commissioner" ? "Commissioner" : "Free agent";
  } else {
    how = r.by ? `Claimed by ${managerLink(r.by)}` : r.via === "commissioner" ? "Commissioner" : "To waivers";
  }
  return `<div class="mgr-mv"><span class="p">${shortName(r.name, r.pos)}</span><span class="how">${how} · ${moveWeek(r, all)}</span><span class="war">${moveChip(r)}</span></div>`;
}

function tradeBlock(t, all) {
  const items = (side) => [
    ...side.players.map((p) => `<span class="it">${shortName(p.name, p.pos)}${moveChip(p)}</span>`),
    ...side.picks.map((p) => `<span class="it"><span class="tag">${p.season} ${ordinal(p.round)}</span></span>`),
    ...(side.faab ? [`<span class="it"><span class="tag">$${side.faab} FAAB</span></span>`] : []),
  ].join("") || '<span class="it none">–</span>';
  const sum = (side) => side.players.reduce((a, p) => a + (p.war || 0), 0);
  const scored = [...t.got.players, ...t.gave.players].some((p) => p.war != null);
  const net = scored ? `<div class="net"><span>${/*copy:MGR-21*/"WAR since the trade"}</span><span>${moveChip({ war: sum(t.got) })} vs ${moveChip({ war: sum(t.gave) })}</span></div>` : "";
  return `<div class="mgr-trade"><div class="with"><span>with ${t.with.map((u) => managerLink(u)).join(", ")}</span><span class="wk">${moveWeek(t, all)}</span></div>
    <div class="sides"><div><span class="lbl">Got</span>${items(t.got)}</div><div><span class="lbl">Gave</span>${items(t.gave)}</div></div>${net}</div>`;
}

function renderMoves() {
  const m = state.byId[state.selected];
  const box = $("mgr-moves");
  if (!m || !box) return;
  const seasons = movesSeasons(m);
  if (!state.movesSeason || (state.movesSeason !== "all" && !seasons.includes(state.movesSeason))) state.movesSeason = seasons[0] || null;
  const all = state.movesSeason === "all";
  const picked = all ? seasons : state.movesSeason ? [state.movesSeason] : [];
  const tagged = (key) => picked.flatMap((s) => ((m.moves || {})[s] || {})[key]?.map((r) => ({ ...r, season: s })) || []);
  const filter = state.movesFilter;
  const keep = (r) => filter === "all" || r.via === filter;
  const added = filter === "trade" ? [] : tagged("added").filter(keep).reverse();
  const dropped = filter === "trade" ? [] : tagged("dropped").filter(keep).reverse();
  const trades = filter === "all" || filter === "trade" ? tagged("trades").reverse() : [];

  // FAAB meter: one season, or every season added up
  const faabs = picked.map((s) => m.faab[s]).filter(Boolean);
  const spent = faabs.reduce((a, f) => a + f.spent, 0), budget = faabs.reduce((a, f) => a + f.budget, 0);
  const overpaid = faabs.reduce((a, f) => a + (f.overpaid || 0), 0);
  const biggest = faabs.map((f, i) => f.biggest && { ...f.biggest, season: picked[i] }).filter(Boolean).sort((a, b) => b.bid - a.bid)[0];
  const meter = budget ? `<div class="mgr-meter"><div class="mt"><span>FAAB spent</span><b>$${spent} of $${budget}</b></div>
      <div class="mb"><span style="width: ${Math.min(100, Math.round((100 * spent) / budget))}%"></span></div>
      <div class="ms"><span>${biggest ? `Biggest bid: $${biggest.bid} on ${shortName(biggest.name)} (${moveWeek(biggest, all)})` : /*copy:MGR-22*/"No winning bids yet"}</span><span>Overpaid <b>$${overpaid}</b></span></div></div>` : "";

  const IN = '<svg class="ic in" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11"/><path d="M12 6v12M6 12h12"/></svg>';
  const OUT = '<svg class="ic out" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11"/><path d="M6 12h12"/></svg>';
  const TR = '<svg class="ic tr" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11"/><path d="M7 9h10l-3-3M17 15H7l3 3"/></svg>';
  const warSum = (rows) => Math.round(rows.reduce((a, r) => a + (r.war || 0), 0) * 10) / 10 || 0;
  const none = `<p class="mgr-none">None</p>`;
  const group = (icon, title, count, total, body) =>
    `<div class="mgr-grp"><h4 class="ih">${icon}${title} (${count})${total ? `<span class="tot">${total}</span>` : ""}</h4>${body || none}</div>`;
  const lists = [
    filter !== "trade" ? group(IN, "Added", added.length, added.length ? `$${added.reduce((a, r) => a + (r.bid || 0), 0)} · ${signed(warSum(added))} WAR` : "", added.map((r) => moveRow(r, "added", all)).join("")) : "",
    filter !== "trade" ? group(OUT, "Dropped", dropped.length, dropped.length ? `${signed(warSum(dropped))} WAR elsewhere` : "", dropped.map((r) => moveRow(r, "dropped", all)).join("")) : "",
    filter === "all" || filter === "trade" ? group(TR, "Trades", trades.length, "", trades.map((t) => tradeBlock(t, all)).join("")) : "",
  ].join("");

  const p = m.players || {};
  const playerRows = [
    [/*copy:MGR-17*/"Most seasons on this team", p.most_seasons ? shortName(p.most_seasons.name) : "–", p.most_seasons ? `${p.most_seasons.seasons} season${p.most_seasons.seasons === 1 ? "" : "s"}` : ""],
    [/*copy:MGR-18*/"The one that got away", p.got_away ? shortName(p.got_away.name) : "–", p.got_away ? `${signed(p.got_away.war)} WAR elsewhere` : ""],
  ];
  const players = `<div class="mgr-grp"><h4>Players</h4><div class="mgr-players">${playerRows
    .map(([k, v, n]) => `<div class="r"><span class="pk">${k}</span><span class="pv">${v}</span><span class="pn">${n}</span></div>`).join("")}</div></div>`;
  const filters = [["all", "All moves"], ["waiver", "Waivers"], ["free_agent", "Free agents"], ["trade", "Trades"]];
  box.innerHTML = `<div class="mgr-card-head"><h3>Moves</h3></div>
    <div class="mgr-controls"><button type="button" class="mgr-moves-prev" aria-label="Previous season">&#8249;</button>
      <select id="mgr-moves-season" aria-label="Season">${seasons.map((s) => `<option value="${s}"${s === state.movesSeason ? " selected" : ""}>${s}</option>`).join("")}<option value="all"${all ? " selected" : ""}>All seasons</option></select>
      <button type="button" class="mgr-moves-next" aria-label="Next season">&#8250;</button>
      <select id="mgr-moves-filter" class="filter" aria-label="Filter">${filters.map(([v, l]) => `<option value="${v}"${v === filter ? " selected" : ""}>${l}</option>`).join("")}</select></div>
    <div class="mgr-scroll" tabindex="0" role="region" aria-label="Moves"><div class="mgr-panel">
      ${meter}
      ${lists}
      ${players}
    </div></div><div></div>`;
  fitNames(box);
}

// -- card 4: team news -----------------------------------------------------------------------------------

function ago(iso) {
  const days = Math.max(0, Math.round((Date.now() - new Date(`${iso}T12:00:00Z`).getTime()) / 86_400_000));
  if (days < 1) return "today";
  if (days < 14) return `${days}d ago`;
  if (days < 60) return `${Math.round(days / 7)}w ago`;
  return `${Math.round(days / 30)}mo ago`;
}

const NEWS_ICON = {
  up: ICON.up, down: '<svg viewBox="0 0 24 24"><path d="M4 6l6 6 4-4 6 8v-4h2v8h-8v-2h4l-4-6-4 4-8-8z"/></svg>',
  inj: '<svg viewBox="0 0 24 24"><path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/></svg>',
  move: '<svg viewBox="0 0 24 24"><path d="M7 9h10l-3-3 1.4-1.4L21 10.2 15.4 16 14 14.6l3-3H7zm10 6H7l3 3-1.4 1.4L3 13.8 8.6 8 10 9.4l-3 3h10z"/></svg>',
  star: ICON.star, trophy: TROPHY,
  money: '<svg viewBox="0 0 24 24"><path d="M11 3h2v2.1c2 .3 3.5 1.6 3.5 3.4h-2c0-.9-1-1.7-2.5-1.7s-2.5.7-2.5 1.6c0 .8.7 1.3 2.8 1.8 2.6.6 4.2 1.5 4.2 3.7 0 1.8-1.5 3-3.5 3.3V19h-2v-1.8c-2.1-.3-3.6-1.6-3.6-3.5h2c0 1 1.1 1.8 2.6 1.8 1.6 0 2.5-.7 2.5-1.6 0-.9-.8-1.4-2.9-1.9-2.4-.6-4.1-1.5-4.1-3.6 0-1.7 1.4-2.9 3.5-3.3z"/></svg>',
};

/* "2027 2nd" for a pick, "$5 FAAB" for budget sent: the parts of one side of a trade, as a phrase. */
function tradeSide(players, picks, faab) {
  const parts = [...(players || []).map(escapeHtml), ...(picks || []).map((p) => `${p.season} ${ordinal(p.round)}`), ...(faab ? [`$${faab} FAAB`] : [])];
  if (parts.length <= 1) return parts[0] || "";
  return `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
}

/* One story's headline, body (feature only), category and thumbnail. Every sentence is a template
   with a copy ID, so the owner can reword any story type in site-copy.txt. */
function storyText(s, m) {
  const f = s.fields;
  const team = escapeHtml(String(m.team_name || "").trim());   // Sleeper keeps stray spaces in some team names
  const opp = escapeHtml(f.opp || "");
  const score = f.points != null ? `${fmt1(f.points)}–${fmt1(f.opp_points)}` : "";
  switch (s.type) {
    case "result": {
      const won = f.result === "W", tie = f.result === "T";
      return {
        cat: "Result", thumb: ["res", `${f.result}<br>${Math.round(f.points)}–${Math.round(f.opp_points)}`],
        head: tie ? /*copy:NEWS-01*/`${team} and ${opp} finish level at ${score}` : won ? /*copy:NEWS-02*/`${team} beat ${opp} ${score}` : /*copy:NEWS-03*/`${team} fall to ${opp} ${score}`,
        body: f.top_player ? /*copy:NEWS-04*/`${escapeHtml(f.top_player)} led the way with ${fmt1(f.top_points)} points.` : "",
      };
    }
    case "rivalry_result":
      return { cat: "Rivalry", thumb: ["res", `${f.result}<br>${Math.round(f.points)}–${Math.round(f.opp_points)}`],
        head: f.result === "W" ? /*copy:NEWS-05*/`Rivalry week goes to ${team}, ${score} over ${opp}` : /*copy:NEWS-06*/`${opp} take rivalry week from ${team}, ${score}`,
        body: f.top_player ? /*copy:NEWS-26*/`${escapeHtml(f.top_player)} led the way with ${fmt1(f.top_points)} points.` : "" };
    case "rivalry_preview":
      return { cat: "Rivalry", thumb: ["lg", NEWS_ICON.star], head: /*copy:NEWS-07*/`Rivalry week is next: ${team} face ${opp}`, body: "" };
    case "forecast": {
      const up = f.change > 0;
      return { cat: "Forecast", thumb: [up ? "up" : "down", up ? NEWS_ICON.up : NEWS_ICON.down],
        head: up ? /*copy:NEWS-08*/`Playoff forecast up ${Math.round(f.change * 100)} to ${pct(f.to)}` : /*copy:NEWS-09*/`Playoff forecast down ${Math.round(-f.change * 100)} to ${pct(f.to)}`, body: "" };
    }
    case "record":
      return { cat: "Record", thumb: ["rec", NEWS_ICON.trophy],
        head: f.rank ? /*copy:NEWS-10*/`New team high: ${fmt1(f.value)}, #${f.rank} all time in the league` : /*copy:NEWS-11*/`New team high: ${fmt1(f.value)}, beating ${fmt1(f.previous)}`, body: "" };
    case "streak":
      return { cat: "Streak", thumb: ["res", `${f.result}<br>${f.length} in a row`],
        head: f.result === "W" ? /*copy:NEWS-12*/`${f.length} straight wins for ${team}` : /*copy:NEWS-13*/`${f.length} straight losses for ${team}`, body: "" };
    case "milestone":
      return { cat: "Player", thumb: ["rec", NEWS_ICON.trophy], head: /*copy:NEWS-14*/`${escapeHtml(f.player)} passes +${f.war}.0 WAR for ${team}`, body: "" };
    case "injury":
      return { cat: "Injury", thumb: ["inj", NEWS_ICON.inj],
        head: f.body_part ? /*copy:NEWS-15*/`${escapeHtml(f.player)} listed as ${escapeHtml(f.status)} (${escapeHtml(String(f.body_part).toLowerCase())})` : /*copy:NEWS-16*/`${escapeHtml(f.player)} listed as ${escapeHtml(f.status)}`, body: "" };
    case "practice":
      return { cat: "Practice", thumb: ["inj", NEWS_ICON.inj],
        head: f.practice === "DNP" ? /*copy:NEWS-17*/`${escapeHtml(f.player)} did not practise this week` : /*copy:NEWS-18*/`${escapeHtml(f.player)} limited in practice this week`, body: "" };
    case "depth":
      return { cat: "Depth chart", thumb: ["move", NEWS_ICON.move],
        head: f.to < f.from ? /*copy:NEWS-19*/`${escapeHtml(f.player)} moves up to ${escapeHtml(f.depth_pos || "")}${f.to} on the depth chart` : /*copy:NEWS-20*/`${escapeHtml(f.player)} drops to ${escapeHtml(f.depth_pos || "")}${f.to} on the depth chart`, body: "" };
    case "trending":
      return { cat: "Trending", thumb: ["up", NEWS_ICON.up], head: /*copy:NEWS-21*/`${escapeHtml(f.player)} is the ${ordinal(f.rank)} most-added player on Sleeper today`, body: "" };
    case "totw":
      return { cat: "League", thumb: ["lg", NEWS_ICON.star],
        head: f.players.length === 1 ? /*copy:NEWS-22*/`Team of the Week: ${escapeHtml(f.players[0])} makes the cut` : /*copy:NEWS-23*/`Team of the Week: ${f.players.map(escapeHtml).join(" and ")} make the cut`, body: "" };
    case "final_season":
      return { cat: "Season", thumb: ["rec", NEWS_ICON.trophy],
        head: f.place ? /*copy:NEWS-24*/`${team} close their final season in ${ordinal(f.place)} place` : /*copy:NEWS-25*/`${team} close their final season, ${f.season}`, body: "" };
    case "trade":
      return { cat: "Trade", thumb: ["move", NEWS_ICON.move],
        head: /*copy:NEWS-27*/`${team} trade ${tradeSide(f.gave, f.gave_picks, f.gave_faab)} to ${opp} for ${tradeSide(f.got, f.got_picks, f.got_faab)}`, body: "" };
    case "big_bid":
      return { cat: "Waivers", thumb: ["lg", NEWS_ICON.money],
        head: f.next != null ? /*copy:NEWS-28*/`${team} win ${escapeHtml(f.player)} for $${f.bid}; the next bid was $${f.next}` : /*copy:NEWS-29*/`${team} win ${escapeHtml(f.player)} for $${f.bid} with no other bids`, body: "" };
    case "pays_off":
      return { cat: "Pickup", thumb: ["up", NEWS_ICON.up], head: /*copy:NEWS-30*/`${escapeHtml(f.player)}, picked up in week ${f.since}, passes +1.0 WAR for ${team}`, body: "" };
    case "got_away":
      return { cat: "Got away", thumb: ["down", NEWS_ICON.down],
        head: f.team ? /*copy:NEWS-31*/`${escapeHtml(f.player)}, dropped in week ${f.since}, passes +1.0 WAR for ${escapeHtml(f.team)}` : /*copy:NEWS-32*/`${escapeHtml(f.player)}, dropped in week ${f.since}, passes +1.0 WAR since leaving`, body: "" };
    case "outbid":
      return { cat: "Outbid", thumb: ["down", NEWS_ICON.money],
        head: f.tied ? /*copy:NEWS-33*/`Lost ${escapeHtml(f.player)} on waiver priority: ${team} and ${escapeHtml(f.winner)} both bid $${f.bid}` : /*copy:NEWS-34*/`Outbid on ${escapeHtml(f.player)}: ${team}'s $${f.bid} lost to ${escapeHtml(f.winner)}'s $${f.winning_bid}`, body: "" };
    default:
      return { cat: "News", thumb: ["lg", NEWS_ICON.star], head: "", body: "" };
  }
}

function newsCard(m) {
  const stories = m.news || [];
  const page = (p) => `#${state.leagueKey}${p === "predictions" ? "" : `/${p}`}`;
  const meta = (s, cat) => `<span class="mgr-meta"><span>${ago(s.at)}</span><span class="sep"></span><span class="cat">${cat}</span><span class="go" aria-hidden="true">&rarr;</span></span>`;
  if (!stories.length) return `<div class="mgr-card-head"><h3>Team News</h3></div><div></div><div class="mgr-scroll"><div class="mgr-panel"><p class="mgr-empty">${/*copy:MGR-11*/"No news yet this season."}</p></div></div><div></div>`;
  const [first, ...rest] = stories;
  const t = storyText(first, m);
  const isGame = first.type === "result" || first.type === "rivalry_result";
  const opp = isGame ? state.byId[first.fields.opp_user] : null;
  const art = isGame
    ? `<span class="board"><span class="side">${crest(m, "fl")}<span>${escapeHtml(m.name)}</span></span><b>${fmt1(first.fields.points)} – ${fmt1(first.fields.opp_points)}</b><span class="side">${crest(opp, "fl")}<span>${escapeHtml(first.fields.opp)}</span></span></span>`
    : `<span class="big-ic">${NEWS_ICON[t.thumb[0] === "res" ? "star" : t.thumb[0] === "rec" ? "trophy" : t.thumb[0] === "inj" ? "inj" : t.thumb[0] === "move" ? "move" : t.thumb[0] === "down" ? "down" : "up"] || NEWS_ICON.star}</span>`;
  const feature = `<a class="mgr-feat" href="${page(first.link)}"${first.link === "managers" ? "" : ` data-goto="${first.link}"`}><span class="art">${art}</span><span class="txt"><span class="h">${t.head}</span>${t.body ? `<span class="b">${t.body}</span>` : ""}${meta(first, t.cat)}</span></a>`;
  const list = rest.map((s, i) => {
    const x = storyText(s, m);
    return `<a class="mgr-story${i >= 7 ? " late" : ""}" href="${page(s.link)}"${s.link === "managers" ? "" : ` data-goto="${s.link}"`}><span class="thumb t-${x.thumb[0]}">${x.thumb[1]}</span><span class="s"><span class="h">${x.head}</span>${meta(s, x.cat)}</span></a>`;
  }).join("");
  return `<div class="mgr-card-head"><h3>Team News</h3></div><div></div>
    <div class="mgr-scroll" tabindex="0" role="region" aria-label="Team news"><div class="mgr-panel">${feature}${rest.length ? `<p class="mgr-more">More Stories</p>${list}` : ""}
      ${rest.length > 7 ? '<button type="button" class="mgr-showmore">Show more</button>' : ""}</div></div><div></div>`;
}
