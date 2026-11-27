/* League page, Strength of Schedule tab: two heat-grid tables for one season. Weekly Ranks credits each
   Manager with their opponent's rank by points each week; Schedule Swap gives each Manager's wins under
   every Manager's schedule. Every figure comes from data/<league>/schedule.json
   (src/ffapp/schedule_strength.py); this module only renders. One table per view at every width: it
   scrolls inside its card with the Manager column pinned. Below 600 px the summary columns are cut to
   Rank and Season (Weekly Ranks) or Rank and Index (Schedule Swap, Index moved forward) so the ranking
   reads without scrolling. */

import { crest, escapeHtml, wireImages } from "./people.js?v=__BUILD__";
import { comparator, markSorted, wireHeaders } from "./sorting.js?v=__BUILD__";

const state = {
  leagueKey: null,
  entry: null,    // index.leagues[i].schedule
  data: null,     // data/<league>/schedule.json
  view: "ranks",  // "ranks" | "swap"
  season: null,
  sort: { ranks: { key: "rank", dir: "asc" }, swap: { key: "rank", dir: "asc" } },
  onChange: () => {},
};

const $ = (id) => document.getElementById(id);
const PHONE = matchMedia("(max-width: 599.98px)");

/* The direction a column sorts on its first pick: the hardest schedule first. */
const FIRST_DIR = { rank: "asc", season: "asc", played: "asc", upcoming: "asc", own: "desc", avg: "desc", index: "desc" };

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading and URL ---------------------------------------------------------------------------------

/* `route` is the URL path after /league/schedule: an optional "swap" and an optional season. */
export async function loadSchedule(leagueKey, entry, route, onChange) {
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
    if (part === "swap" || part === "ranks") state.view = part;
    else if (/^\d{4}$/.test(part)) state.season = part;
  }
  if (state.data && !state.data.seasons[state.season]) state.season = state.data.current_season;
}

/* The URL part after /league/schedule. */
export function scheduleSlug() {
  return `${state.view === "swap" ? "/swap" : ""}${state.season ? `/${state.season}` : ""}`;
}

export function initSchedule() {
  $("sos-views").addEventListener("click", (e) => {
    const b = e.target.closest("[data-sos-view]");
    if (!b) return;
    state.view = b.dataset.sosView;
    render();
    state.onChange();
  });
  $("sos-season").addEventListener("change", (e) => {
    state.season = e.target.value;
    render();
    state.onChange();
  });
  PHONE.addEventListener("change", () => { if (state.data && state.season) render(); });
}

// -- shared pieces -------------------------------------------------------------------------------------

const mgr = (id) => state.data.managers[id];
const ordinal = (n) => `${n}${n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th")}`;
const fixed = (x, d) => (x == null ? "–" : Number(x).toFixed(d));
const signed = (x) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const record = (r) => `${r[0]}-${r[1]}${r[2] ? `-${r[2]}` : ""}`;

function managerCell(id, sub) {
  const m = mgr(id);
  if (!m) return `<span class="lg-who muted">–</span>`;
  const link = `<a class="manager-link" href="#${state.leagueKey}/managers/${encodeURIComponent(m.name)}" data-manager-link="${escapeHtml(m.name)}">${escapeHtml(m.name)}</a>`;
  return `<span class="lg-who">${crest({ ...m, user_id: id }, "xs")}<span class="lg-who-col">${link}${sub ? `<span class="lg-sub">${sub}</span>` : ""}</span></span>`;
}

function rankCell(rank) {
  return `<td class="sos-rank"><b>${ordinal(rank)}</b><span>${/*copy:LG-61*/"Hardest"}</span></td>`;
}

function sortHead(key, label, cls = "num") {
  return `<th scope="col" class="${cls}" data-col="${key}"><button type="button" class="sort">${label}</button></th>`;
}

function sorted(rows, view, columns) {
  const sort = state.sort[view];
  const col = columns[sort.key];
  return col ? [...rows].sort(comparator(col, sort.dir, (a, b) => a.rank - b.rank)) : rows;
}

function onSort(view, key) {
  const cur = state.sort[view];
  state.sort[view] = cur.key === key ? { key, dir: cur.dir === "asc" ? "desc" : "asc" } : { key, dir: FIRST_DIR[key] };
  view === "ranks" ? renderRanks() : renderSwap();
}

function finish(card, view) {
  const table = card.querySelector("table");
  markSorted(table.querySelectorAll("thead th[data-col]"), state.sort[view]);
  wireHeaders(table, (key) => onSort(view, key));
  wireImages(card);
}

// -- rendering --------------------------------------------------------------------------------------

function render() {
  const has = !!(state.data && state.season);
  $("sos-unavailable").hidden = has;
  $("sos-ranks").hidden = !has || state.view !== "ranks";
  $("sos-swap").hidden = !has || state.view !== "swap";
  for (const b of $("sos-views").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.sosView === state.view));
  const select = $("sos-season");
  const seasons = has ? Object.keys(state.data.seasons).sort().reverse() : [];
  select.innerHTML = seasons.map((s) => `<option value="${s}"${s === state.season ? " selected" : ""}>${s}</option>`).join("");
  select.disabled = !has;
  if (!has) return;
  if (state.view === "ranks") renderRanks();
  else renderSwap();
}

/* Opponent-rank quarter, 1 (ranks 1-3 in a 12-team league) to 4. */
const quarter = (rank, teams) => Math.min(4, Math.floor(((rank - 1) * 4) / teams) + 1);

function renderRanks() {
  const season = state.data.seasons[state.season];
  const card = $("sos-ranks");
  const teams = season.ranks.length;
  const cells0 = season.ranks[0].cells;
  const played = cells0.filter((c) => !c.upcoming).length;
  const ahead = cells0.length - played;
  const wide = !PHONE.matches;  // Played and Upcoming only above 600 px
  const extra = wide ? 1 + (ahead ? 1 : 0) : 0;
  const columns = { rank: { value: (r) => r.rank }, season: { value: (r) => r.season }, played: { value: (r) => r.played }, upcoming: { value: (r) => r.upcoming } };
  const rows = sorted(season.ranks, "ranks", columns);
  const edge = (c, i) => (c.upcoming && (i === 0 || !cells0[i - 1].upcoming) ? " sos-edge" : "");
  const weekHead = cells0.map((c, i) => `<th scope="col" class="sos-wk${edge(c, i)}">${c.week}</th>`).join("");
  const cell = (c, i) => {
    const m = mgr(c.opp);
    const name = m ? m.name : "–";
    const tip = `Week ${c.week}: ${name}, ${c.points.toFixed(1)} points${c.upcoming ? " forecast" : ""}, ranked ${c.opp_rank} of ${teams}`;
    return `<td class="sos-c r${quarter(c.opp_rank, teams)}${c.upcoming ? " sos-up" : ""}${edge(c, i)}" title="${escapeHtml(tip)}">`
      + `<span class="sos-pts">${c.points.toFixed(1)}</span><span class="sos-rk">${c.opp_rank}</span>`
      + `${m ? crest({ ...m, user_id: c.opp }, "xxs") : ""}<span class="sr-only">${escapeHtml(name)}</span></td>`;
  };
  card.querySelector(".sos-wrap").innerHTML = `<table class="plain sos-table sos-ranks-table">
    <thead>
      <tr class="sos-group"><th scope="colgroup" colspan="${3 + extra}"></th>
        <th scope="colgroup" colspan="${played}">${/*copy:LG-62*/"Played"}</th>${ahead ? `<th scope="colgroup" colspan="${ahead}" class="sos-edge">${/*copy:LG-63*/"Forecast"}</th>` : ""}</tr>
      <tr><th scope="col" class="sos-mgr">Manager</th>${sortHead("rank", "Rank", "sos-rank")}${sortHead("season", "Season")}${wide ? sortHead("played", "Played") : ""}${wide && ahead ? sortHead("upcoming", "Upcoming") : ""}${weekHead}</tr>
    </thead>
    <tbody>${rows.map((r) => `<tr><th scope="row" class="sos-mgr">${managerCell(r.user, record(r.record))}</th>${rankCell(r.rank)}
      <td class="num strong">${fixed(r.season, 2)}</td>${wide ? `<td class="num muted">${fixed(r.played, 2)}</td>` : ""}${wide && ahead ? `<td class="num muted">${fixed(r.upcoming, 2)}</td>` : ""}
      ${r.cells.map(cell).join("")}</tr>`).join("")}</tbody></table>`;
  finish(card, "ranks");
}

/* Wins against the Manager's own-schedule wins: s1 two or more fewer ... s4 two or more more, s0 within 0.05. */
function bucket(d) {
  if (Math.abs(d) < 0.05) return "s0";
  if (d <= -2) return "s1";
  return d < 0 ? "s2" : d < 2 ? "s3" : "s4";
}

function renderSwap() {
  const season = state.data.seasons[state.season];
  const card = $("sos-swap");
  const order = season.swap.order;
  const columns = { rank: { value: (r) => r.rank }, own: { value: (r) => r.own }, avg: { value: (r) => r.avg }, index: { value: (r) => r.index } };
  const rows = sorted(season.swap.rows, "swap", columns);
  const phone = PHONE.matches;
  const indexHead = sortHead("index", "Index");
  const indexCell = (r) => `<td class="num strong ${r.index > 0 ? "sos-hard" : "sos-easy"}">${signed(r.index)}</td>`;
  const heads = order.map((id, j) => {
    const m = mgr(id);
    const name = m ? m.name : "–";
    return `<th scope="col" class="sos-sched${j === 0 ? " sos-first" : ""}" title="${escapeHtml(name)}">${m ? crest({ ...m, user_id: id }, "xs") : ""}<span class="sr-only">${escapeHtml(name)}</span></th>`;
  }).join("");
  const cells = (r) => r.wins.map((v, j) => {
    const own = order[j] === r.user;
    const m = mgr(order[j]);
    const tip = own ? `${mgr(r.user)?.name}'s own schedule: ${v.toFixed(1)} wins` : `${mgr(r.user)?.name} with ${m ? m.name : "–"}'s schedule: ${v.toFixed(1)} wins`;
    return `<td class="sos-w ${own ? "own" : bucket(v - r.own)}" title="${escapeHtml(tip)}">${v.toFixed(1)}</td>`;
  }).join("");
  card.querySelector(".sos-wrap").innerHTML = `<table class="plain sos-table sos-swap-table">
    <thead>
      <tr class="sos-group"><th scope="colgroup" colspan="${phone ? 3 : 2}"></th>
        <th scope="colgroup" colspan="${order.length}">${/*copy:LG-64*/"Wins with this Manager's schedule"}</th>
        <th scope="colgroup" colspan="${phone ? 3 : 4}" class="sos-edge">${/*copy:LG-65*/"Difficulty"}</th></tr>
      <tr><th scope="col" class="sos-mgr">Manager</th>${sortHead("rank", "Rank", "sos-rank")}${phone ? indexHead : ""}${heads}
        ${sortHead("own", "Own", "num sos-edge")}${sortHead("avg", "Avg")}${phone ? "" : indexHead}<th scope="col" class="num">Range</th></tr>
    </thead>
    <tbody>${rows.map((r) => `<tr><th scope="row" class="sos-mgr">${managerCell(r.user)}</th>${rankCell(r.rank)}${phone ? indexCell(r) : ""}${cells(r)}
      <td class="num sos-edge">${r.own.toFixed(1)}</td><td class="num muted">${r.avg.toFixed(1)}</td>${phone ? "" : indexCell(r)}
      <td class="num muted sos-range">${r.lo.toFixed(1)} – ${r.hi.toFixed(1)}</td></tr>`).join("")}</tbody></table>`;
  finish(card, "swap");
}
