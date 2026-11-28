/* League page, Preseason tab: each season's preseason Forecast, made once when the draft was complete:
   every team's grade (A+ to F), title, playoff and last-place shares with bars, forecast record, points
   per week, the wins its bench saves and, for a finished season, where it actually finished; redraft
   seasons add each team's Draft Strength rank. Every figure comes from data/<league>/preseason.json
   (src/ffapp/preseason.py); this module only renders. A table on wide screens, a list on phones. */

import { crest, escapeHtml, wireImages } from "./people.js?v=__BUILD__";
import { comparator, markSorted, wireHeaders } from "./sorting.js?v=__BUILD__";

const state = {
  leagueKey: null,
  entry: null,     // index.leagues[i].preseason
  data: null,      // data/<league>/preseason.json
  season: null,
  sort: { key: "title", dir: "desc" },
  onChange: () => {},
};

const $ = (id) => document.getElementById(id);
const GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"];
const FIRST_DIR = { grade: "desc", manager: "desc", title: "desc", playoffs: "desc", last: "desc", record: "desc", ppg: "desc", strength: "asc", saved: "desc", finish: "asc" };
const COLUMNS = {
  grade: { value: (t) => GRADE_ORDER.length - GRADE_ORDER.indexOf(t.grade) },
  manager: { text: (t) => mgr(t.user)?.name || "" },
  title: { value: (t) => t.title },
  playoffs: { value: (t) => t.playoffs },
  last: { value: (t) => t.last },
  record: { value: (t) => t.wins },
  ppg: { value: (t) => t.ppg },
  strength: { value: (t) => t.draft_strength },
  saved: { value: (t) => t.wins_saved },
  finish: { value: (t) => t.finish },
};

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading and URL ---------------------------------------------------------------------------------

/* `route` is the URL path after /league/preseason: an optional season. */
export async function loadPreseason(leagueKey, entry, route, onChange) {
  const sameLeague = state.leagueKey === leagueKey;
  state.leagueKey = leagueKey;
  state.entry = entry || null;
  state.onChange = onChange || state.onChange;
  if (!sameLeague) state.season = null;
  state.data = state.entry ? await fetchJson(`data/${state.entry.file}`) : null;
  for (const part of route || []) if (/^\d{4}$/.test(part)) state.season = part;
  if (state.data && !state.data.seasons[state.season]) state.season = state.data.latest;
  render();
}

/* The URL part after /league/preseason. */
export function preseasonSlug() {
  return state.season ? `/${state.season}` : "";
}

export function initPreseason() {
  $("ps-season").addEventListener("change", (e) => {
    state.season = e.target.value;
    render();
    state.onChange();
  });
}

// -- rendering --------------------------------------------------------------------------------------

const mgr = (id) => state.data.managers[id];
const pct = (x) => (x > 0 && x < 0.005 ? "<1%" : `${Math.round(x * 100)}%`);
const ordinal = (n) => (n == null ? "–" : `${n}${n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" }[n % 10] || "th")}`);
const gradeClass = (g) => `g-${g.toLowerCase().replace("+", "p").replace("-", "m")}`;
const signed = (x) => `${x < 0 ? "−" : "+"}${Math.abs(x).toFixed(2)}`;
const badge = (g) => `<span class="ps-grade ${gradeClass(g)}">${escapeHtml(g)}</span>`;

function managerCell(id) {
  const m = mgr(id);
  if (!m) return `<span class="lg-who muted">–</span>`;
  const link = `<a class="manager-link" href="#${state.leagueKey}/managers/${encodeURIComponent(m.name)}" data-manager-link="${escapeHtml(m.name)}">${escapeHtml(m.name)}</a>`;
  return `<span class="lg-who">${crest({ ...m, user_id: id }, "xs")}<span class="lg-who-col">${link}</span></span>`;
}

function shareCell(x, kind) {
  return `<span class="ps-share"><span class="ps-num">${pct(x)}</span><span class="ps-track" aria-hidden="true"><span class="ps-fill ${kind}" style="width: ${Math.max(0, Math.min(100, x * 100)).toFixed(1)}%"></span></span></span>`;
}

function finishCell(n, total) {
  if (n == null) return `<span class="muted">–</span>`;
  const tag = n === 1 ? `<span class="ps-tag champ">${/*copy:LG-114*/"Champion"}</span>` : n === total ? `<span class="ps-tag last">${/*copy:LG-115*/"Last"}</span>` : "";
  return `<b>${ordinal(n)}</b>${tag}`;
}

function sortHead(key, label, cls = "") {
  return `<th scope="col" class="${cls}" data-col="${key}"><button type="button" class="sort">${label}</button></th>`;
}

function render() {
  const has = !!(state.data && state.season);
  $("ps-unavailable").hidden = has;
  $("ps-card").hidden = !has;
  const select = $("ps-season");
  const seasons = has ? Object.keys(state.data.seasons).sort().reverse() : [];
  select.innerHTML = seasons.map((s) => `<option value="${s}"${s === state.season ? " selected" : ""}>${s}</option>`).join("");
  select.disabled = !has;
  if (!has) return;
  const season = state.data.seasons[state.season];
  const redraft = season.teams.some((t) => t.draft_strength != null);
  $("ps-h").textContent = `${state.season} ${/*copy:LG-116*/"Preseason Forecast"}`;
  $("ps-redraft-note").hidden = !redraft;
  const total = season.teams.length;
  const col = COLUMNS[state.sort.key] || COLUMNS.title;
  const teams = [...season.teams].sort(comparator(col, state.sort.dir, (a, b) => b.title - a.title));
  const wide = $("ps-card").querySelector(".ps-wide");
  wide.innerHTML = `<table class="plain ps-table"><thead><tr>
      ${sortHead("grade", "Grade", "ps-gcol")}${sortHead("manager", "Manager")}${sortHead("title", "Title", "num")}${sortHead("playoffs", "Playoffs", "num")}
      ${sortHead("last", "Last", "num")}${sortHead("record", "Forecast", "num")}${sortHead("ppg", "Pts/Wk", "num")}${redraft ? sortHead("strength", "Draft Strength", "num") : ""}
      ${sortHead("saved", "Wins Saved", "num")}${sortHead("finish", "Finished")}</tr></thead>
    <tbody>${teams.map((t) => `<tr>
      <td class="ps-gcol">${badge(t.grade)}</td><td>${managerCell(t.user)}</td>
      <td class="num">${shareCell(t.title, "title")}</td><td class="num">${shareCell(t.playoffs, "playoffs")}</td><td class="num">${shareCell(t.last, "last")}</td>
      <td class="num">${t.wins.toFixed(1)}–${t.losses.toFixed(1)}</td><td class="num muted">${t.ppg.toFixed(1)}</td>
      ${redraft ? `<td class="num">${ordinal(t.draft_strength)}</td>` : ""}
      <td class="num ps-saved">${signed(t.wins_saved)}</td><td class="ps-finish">${finishCell(t.finish, total)}</td></tr>`).join("")}</tbody></table>`;
  const table = wide.querySelector("table");
  markSorted(table.querySelectorAll("thead th[data-col]"), state.sort);
  wireHeaders(table, (key) => {
    state.sort = state.sort.key === key ? { key, dir: state.sort.dir === "asc" ? "desc" : "asc" } : { key, dir: FIRST_DIR[key] };
    render();
  });
  $("ps-card").querySelector(".ps-list").innerHTML = teams.map((t) => `<li>
      ${badge(t.grade)}
      <span class="ps-row">
        <span class="ps-line">${managerCell(t.user)}<span class="ps-finish">${finishCell(t.finish, total)}</span></span>
        <span class="ps-shares"><span>${/*copy:LG-117*/"Title"} <b>${pct(t.title)}</b></span><span>${/*copy:LG-118*/"Playoffs"} <b>${pct(t.playoffs)}</b></span><span>${/*copy:LG-119*/"Last"} <b>${pct(t.last)}</b></span></span>
        <span class="dr-meta">${/*copy:LG-120*/"Forecast"} ${t.wins.toFixed(1)}–${t.losses.toFixed(1)} · ${t.ppg.toFixed(1)} ${/*copy:LG-121*/"pts/wk"}${redraft ? ` · ${/*copy:LG-122*/"Draft Strength"} ${ordinal(t.draft_strength)}` : ""} · ${/*copy:LG-123*/"bench saves"} <b class="ps-saved">${signed(t.wins_saved)} ${/*copy:LG-124*/"wins"}</b></span>
      </span></li>`).join("");
  wireImages($("ps-card"));
}
