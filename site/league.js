/* League page, Records tab: the league's bests and worsts in two views. Managers: Champions, All-Time
   Standings, Weekly Records and Season Records. Players: Best Games, Best Bench Games, Career Scoring
   and Championships. Selecting a record opens its top 25. Every figure comes from
   data/<league>/records.json (src/ffapp/league_records.py); this module only renders. Each table is
   drawn twice, a table for wide screens and a list for phones; CSS shows one. */

import { crest, escapeHtml, fitNames, headshot, shortName, wireImages } from "./people.js?v=__BUILD__";

const state = {
  leagueKey: null,
  leagueName: "",
  entry: null,      // index.leagues[i].records
  data: null,       // data/<league>/records.json
  view: "managers", // "managers" | "players"
  filters: { best_games: "ALL", bench_games: "ALL", career: "ALL", championships: "ALL" },
  onChange: () => {},
  opener: null,     // the control that opened the pop-up, focused again on close
};

const $ = (id) => document.getElementById(id);
const visible = () => !$("page-league").hidden;
const fmt2 = (x) => Number(x).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const signed = (x, d = 1) => (x > 0 ? "+" : x < 0 ? "−" : "") + Math.abs(x).toFixed(d);
const record = (r) => `${r.wins}-${r.losses}${r.ties ? `-${r.ties}` : ""}`;
const pct3 = (x) => x.toFixed(3).replace(/^0/, "");

/* The luck explanation lives once, in the pop-up note (LG-47); the luck rows show it on hover and focus. */
const luckText = () => $("lg-dialog-note").textContent.trim();

const WEEKLY = [
  ["high_team", /*copy:LG-12*/"Highest Team Score"], ["low_team", /*copy:LG-13*/"Lowest Team Score"],
  ["high_matchup", /*copy:LG-14*/"Highest Matchup Score"], ["low_matchup", /*copy:LG-15*/"Lowest Matchup Score"],
  ["blowout", /*copy:LG-16*/"Biggest Blowout"], ["closest", /*copy:LG-17*/"Closest Game"],
  ["high_loss", /*copy:LG-18*/"Highest Score in a Loss"], ["low_win", /*copy:LG-19*/"Lowest Score in a Win"],
];
const SEASON = [
  ["most_points", /*copy:LG-20*/"Most Points", "points"], ["fewest_points", /*copy:LG-21*/"Fewest Points", "points"],
  ["most_against", /*copy:LG-22*/"Most Points Against", "points"], ["best_record", /*copy:LG-23*/"Best Record", "record"],
  ["worst_record", /*copy:LG-24*/"Worst Record", "record"], ["best_missed", /*copy:LG-25*/"Best Team to Miss Playoffs", "points"],
  ["worst_made", /*copy:LG-26*/"Worst Team to Make Playoffs", "points"], ["luckiest", /*copy:LG-27*/"Luckiest Season", "luck"],
  ["unluckiest", /*copy:LG-28*/"Unluckiest Season", "luck"], ["win_streak", /*copy:LG-29*/"Longest Winning Streak", "streak"],
  ["loss_streak", /*copy:LG-30*/"Longest Losing Streak", "streak"], ["bench", /*copy:LG-31*/"Most Bench Points", "points"],
  ["lineup_gained", /*copy:LG-32*/"Most Points Gained by Lineup Choices", "lineup"],
  ["lineup_lost", /*copy:LG-33*/"Most Points Lost by Lineup Choices", "lineup"],
];
const PLAYER_CARDS = ["best_games", "bench_games", "career", "championships"];  // titles: the cards' headings (LG-07 to LG-10)
const cardTitle = (card) => $("lg-players").querySelector(`[data-card="${card}"] h2`).textContent;
const POSITIONS = ["ALL", "QB", "RB", "WR", "TE", "DEF", "K"];
const RESULT = {
  first: ["1st", "res-first"], second: ["2nd", "res-second"], third: ["3rd", "res-third"], playoffs: ["Playoffs", "res-playoffs"],
  missed: ["Missed Playoffs", "res-missed"], toilet_bowl: ["Toilet Bowl Champ", "res-bowl"], last: ["Last", "res-bowl"],
  in_progress: ["In progress", "res-now"],
};
const KIND_TAG = { Playoffs: "tag-playoffs", Championship: "tag-champ", "3rd Place": "tag-third", "Toilet Bowl": "tag-bowl", "Toilet Bowl Final": "tag-bowl" };

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

// -- loading, view and URL -------------------------------------------------------------------------

/* Called by app.js whenever a league loads. `view` is the Records view named in the URL. */
export async function loadRecords(leagueKey, leagueName, entry, view, onChange) {
  state.leagueKey = leagueKey;
  state.leagueName = leagueName;
  state.entry = entry || null;
  state.onChange = onChange || state.onChange;
  if (view) state.view = view === "players" ? "players" : "managers";
  $("lg-unavailable").hidden = !!state.entry;
  if (!state.entry) {
    $("lg-managers").hidden = $("lg-players").hidden = true;
    return;
  }
  state.data = await fetchJson(`data/${state.entry.file}`);
  render();
}

export async function reloadRecords() {
  if (state.entry) await loadRecords(state.leagueKey, state.leagueName, state.entry, null, state.onChange);
}

/* The URL part after /league: the tab and, for the Players view, the view. */
export function leagueSlug() {
  return `records${state.view === "players" ? "/players" : ""}`;
}

export function showLeague() {
  if (state.data) fitNames($("page-league"));
}

function setView(view) {
  state.view = view;
  renderView();
  state.onChange();
}

export function initLeague() {
  $("lg-views").addEventListener("click", (e) => {
    const b = e.target.closest("[data-lg-view]");
    if (b) setView(b.dataset.lgView);
  });
  $("page-league").addEventListener("click", (e) => {
    if (e.target.closest("a")) return;
    const pos = e.target.closest("[data-lg-pos]");
    if (pos) { state.filters[pos.dataset.card] = pos.dataset.lgPos; renderPlayerCard(pos.dataset.card); return; }
    const open = e.target.closest("[data-record]");
    if (open) { state.opener = open.matches("button") ? open : open.querySelector("button") || open; openDialog(open.dataset.record); }
  });
  $("lg-dialog-close").addEventListener("click", closeDialog);
  $("lg-dialog").addEventListener("click", (e) => { if (e.target === e.currentTarget) closeDialog(); });
  $("lg-dialog").addEventListener("close", () => { if (state.opener && document.contains(state.opener)) state.opener.focus(); });
  addEventListener("resize", () => { if (visible()) fitNames($("page-league")); });
}

// -- shared pieces ------------------------------------------------------------------------------------

const mgr = (id) => state.data.managers[id];

function nameLink(id) {
  const m = mgr(id);
  return m ? `<a class="manager-link" href="#${state.leagueKey}/managers/${encodeURIComponent(m.name)}" data-manager-link="${escapeHtml(m.name)}">${escapeHtml(m.name)}</a>` : "–";
}

function managerCell(id, size = "xs") {
  const m = mgr(id);
  if (!id || !m) return `<span class="lg-who muted">–</span>`;
  return `<span class="lg-who">${crest({ ...m, user_id: id }, size)}${nameLink(id)}</span>`;
}

function plainManager(id) {
  const m = mgr(id);
  return m ? `<span class="lg-who">${crest({ ...m, user_id: id }, "xs")}<span class="lg-name">${escapeHtml(m.name)}</span></span>` : "";
}

function posPill(pos) {
  return pos ? `<span class="mgr-pill lg-pos ${pos.toLowerCase()}">${escapeHtml(pos)}</span>` : "";
}

function rankPill(rank) {
  return `<span class="lg-rank${rank <= 3 ? ` r${rank}` : ""}">${rank}</span>`;
}

function tags(e) {
  const out = [];
  if (e.kind && KIND_TAG[e.kind]) out.push(`<span class="lg-tag ${KIND_TAG[e.kind]}">${escapeHtml(e.kind)}</span>`);
  if (e.current) out.push(`<span class="lg-tag tag-now">${/*copy:LG-34*/"This season"}</span>`);
  return out.join("");
}

function resultPill(result) {
  const [label, cls] = RESULT[result] || ["", ""];
  return label ? `<span class="lg-result ${cls}">${label}</span>` : "";
}

const year = (e) => `${e.season}${e.current ? "*" : ""}`;
const when = (e) => `${e.season} / Wk ${e.week}`;
const scoreLine = (e) => `${fmt2(e.score[0])}–${fmt2(e.score[1])}`;

function seasonValue(kind, e) {
  if (kind === "record") return record(e.record);
  if (kind === "luck") return `${signed(e.value, 2)} wins`;
  if (kind === "streak") return `${e.value} games`;
  if (kind === "lineup") return signed(e.value, 1);
  return fmt2(e.value);
}

function wideNarrow(wide, narrow) {
  return `<div class="lg-wide">${wide}</div><div class="lg-narrow">${narrow}</div>`;
}

function moreButton(id, label) {
  return `<button type="button" class="lg-more" data-record="${id}" aria-label="${escapeHtml(label)}: top 25">${/*copy:LG-35*/"Top 25"} <span aria-hidden="true">›</span></button>`;
}

// -- render -------------------------------------------------------------------------------------------

function render() {
  renderChampions();
  renderStandings();
  renderWeekly();
  renderSeason();
  for (const key of PLAYER_CARDS) renderPlayerCard(key);
  renderView();
  wireImages($("page-league"));
}

function renderView() {
  for (const b of $("lg-views").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.lgView === state.view));
  $("lg-managers").hidden = state.view !== "managers";
  $("lg-players").hidden = state.view !== "players";
  fitNames($("page-league"));
}

function renderChampions() {
  const rows = state.data.champions;
  const lastLabel = state.data.toilet_bowl ? /*copy:LG-36*/"Toilet Bowl Champion" : /*copy:LG-37*/"Last Place";
  const best = (b) => b ? `<span class="lg-player">${headshot(b.player_id)}<span class="lg-player-text">${shortName(b.name, b.position)}<span class="lg-sub">${posPill(b.position)}${escapeHtml([b.team, `${b.war.toFixed(1)} WAR`].filter(Boolean).join(" · "))}</span></span></span>` : "–";
  const champ = (c) => `<span class="lg-champ">${crest({ ...mgr(c.champion), user_id: c.champion }, "sm")}<span class="lg-player-text">${nameLink(c.champion)}${c.team_name ? `<span class="lg-sub">${escapeHtml(c.team_name)}</span>` : ""}</span></span>`;
  const wide = `<div class="table-wrap"><table class="plain lg-table lg-champions">
    <thead><tr><th scope="col">Year</th><th scope="col">Champion</th><th scope="col">Runner-up</th><th scope="col">${lastLabel}</th>
      <th scope="col" class="num">Record</th><th scope="col" class="num">Points Scored</th><th scope="col">Best Player</th></tr></thead>
    <tbody>${rows.map((c) => `<tr><td class="lg-year">${c.season}</td><td>${champ(c)}</td><td>${managerCell(c.runner_up)}</td><td>${managerCell(c.last)}</td>
      <td class="num">${record(c.record)}</td><td class="num">${fmt2(c.points)}</td><td>${best(c.best_player)}</td></tr>`).join("")}</tbody></table></div>`;
  const narrow = `<ol class="lg-list">${rows.map((c) => `<li class="lg-item"><span class="lg-year">${c.season}</span><div class="lg-item-body">${champ(c)}
      <dl class="lg-facts"><dt>Runner-up</dt><dd>${managerCell(c.runner_up)}</dd><dt>${lastLabel}</dt><dd>${managerCell(c.last)}</dd>
      <dt>Season</dt><dd>${record(c.record)} · ${fmt2(c.points)} pts</dd><dt>Best Player</dt><dd>${best(c.best_player)}</dd></dl></div></li>`).join("")}</ol>`;
  $("lg-champions").querySelector(".lg-body").innerHTML = rows.length ? wideNarrow(wide, narrow) : `<p class="hint">${/*copy:LG-38*/"No season has finished yet."}</p>`;
}

function renderStandings() {
  const rows = state.data.standings;
  const lastLabel = state.data.toilet_bowl ? /*copy:LG-39*/"Toilet" : /*copy:LG-40*/"Last";
  const count = (n, cls) => n ? `<span class="lg-count ${cls}">${n}</span>` : `<span class="lg-count none">–</span>`;
  const diff = (d) => `<span class="${d >= 0 ? "up" : "down"}">${signed(d, 1)}</span>`;
  const span = (r) => `${r.seasons} season${r.seasons === 1 ? "" : "s"} · ${r.first}${r.last_season !== r.first ? `–${r.current ? "" : r.last_season}` : ""}`;
  const current = rows.filter((r) => r.current), former = rows.filter((r) => !r.current);
  const tr = (r) => `<tr class="${r.current ? "" : "former"}"><td class="lg-rankcell">${r.rank ?? ""}</td>
    <td><span class="lg-who-col">${managerCell(r.user, "sm")}<span class="lg-sub">${span(r)}</span></span></td>
    <td class="num grp">${record(r.record)}</td><td class="num strong">${pct3(r.pct)}</td><td class="num">${diff(r.diff)}</td>
    <td class="num grp">${r.playoffs}</td><td class="num">${record(r.playoff_record)}</td>
    <td class="ctr grp">${count(r.first_place, "r1")}</td><td class="ctr">${count(r.second_place, "r2")}</td><td class="ctr">${count(r.third_place, "r3")}</td><td class="ctr">${count(r.last_place, "bowl")}</td></tr>`;
  const groupRow = `<tr class="lg-group"><th scope="rowgroup" colspan="11">${/*copy:LG-41*/"Former Managers"}</th></tr>`;
  const wide = `<div class="table-wrap"><table class="plain lg-table lg-standings">
    <thead><tr class="group-row"><td colspan="2"></td><th scope="colgroup" colspan="3" class="grp">Overall</th><th scope="colgroup" colspan="2" class="grp">Playoffs</th><th scope="colgroup" colspan="4" class="grp">Titles</th></tr>
    <tr><th scope="col">#</th><th scope="col">Manager</th><th scope="col" class="num grp">Record</th><th scope="col" class="num">Win %</th><th scope="col" class="num">Point Diff</th>
      <th scope="col" class="num grp">App</th><th scope="col" class="num">Record</th><th scope="col" class="ctr grp">1st</th><th scope="col" class="ctr">2nd</th><th scope="col" class="ctr">3rd</th><th scope="col" class="ctr">${lastLabel}</th></tr></thead>
    <tbody>${current.map(tr).join("")}${former.length ? groupRow + former.map(tr).join("") : ""}</tbody></table></div>`;
  const chips = (r) => [[r.first_place, "1st", "r1"], [r.second_place, "2nd", "r2"], [r.third_place, "3rd", "r3"], [r.last_place, lastLabel === "Toilet" ? "Toilet Bowl" : "Last", "bowl"]]
    .filter(([n]) => n).map(([n, label, cls]) => `<span class="lg-count ${cls}">${n > 1 ? `${n}× ` : ""}${label}</span>`).join("");
  const li = (r) => `<li class="lg-item ${r.current ? "" : "former"}"><span class="lg-rankcell">${r.rank ?? ""}</span><div class="lg-item-body">
      <div class="lg-line">${managerCell(r.user, "sm")}<span class="strong">${pct3(r.pct)}</span></div>
      <div class="lg-line lg-sub"><span>${record(r.record)} · ${diff(r.diff)}</span><span>${span(r)}</span></div>
      <div class="lg-line lg-sub lg-chips"><span>${r.playoffs ? `${/*copy:LG-42*/"Playoffs"} ${r.playoffs} · ${record(r.playoff_record)}` : /*copy:LG-43*/"No playoffs"}</span>${chips(r)}</div></div></li>`;
  const narrow = `<ol class="lg-list">${current.map(li).join("")}</ol>${former.length ? `<h3 class="lg-group-h">${/*copy:LG-44*/"Former Managers"}</h3><ol class="lg-list">${former.map(li).join("")}</ol>` : ""}`;
  $("lg-standings").querySelector(".lg-body").innerHTML = wideNarrow(wide, narrow);
}

function renderWeekly() {
  const rows = WEEKLY.map(([key, label]) => ({ key, label, e: (state.data.weekly[key] || [])[0] })).filter((r) => r.e);
  const wide = `<div class="table-wrap"><table class="plain lg-table lg-records">
    <thead><tr><th scope="col">Record</th><th scope="col" class="num">Value</th><th scope="col">Manager</th><th scope="col">Opponent</th><th scope="col">Year / Wk</th><th scope="col"><span class="sr-only">Top 25</span></th></tr></thead>
    <tbody>${rows.map(({ key, label, e }) => `<tr class="lg-click" data-record="weekly:${key}"><td class="strong">${label}</td>
      <td class="num"><span class="lg-value">${fmt2(e.value)}</span><span class="lg-sub">${scoreLine(e)}</span></td>
      <td>${managerCell(e.user, "sm")}</td><td class="muted">${managerCell(e.opp)}</td><td>${when(e)}${tags(e)}</td>
      <td class="num">${moreButton(`weekly:${key}`, label)}</td></tr>`).join("")}</tbody></table></div>`;
  const narrow = `<div class="lg-list">${rows.map(({ key, label, e }) => `<button type="button" class="lg-rowbtn" data-record="weekly:${key}" aria-label="${escapeHtml(`${label}: ${fmt2(e.value)}, ${mgr(e.user)?.name || ""} vs ${mgr(e.opp)?.name || ""}. Top 25`)}">
      <span class="lg-line"><span class="lg-label">${label}</span><span class="lg-value">${fmt2(e.value)}</span></span>
      <span class="lg-line">${plainManager(e.user)}<span class="muted">vs ${escapeHtml(mgr(e.opp)?.name || "")}</span></span>
      <span class="lg-line lg-sub"><span>${e.season} · Week ${e.week}${tags(e)}</span></span><span class="lg-chev" aria-hidden="true">›</span></button>`).join("")}</div>`;
  $("lg-weekly").querySelector(".lg-body").innerHTML = wideNarrow(wide, narrow);
}

function renderSeason() {
  const rows = SEASON.map(([key, label, kind]) => ({ key, label, kind, e: (state.data.season[key] || [])[0] })).filter((r) => r.e);
  const label = (r) => r.kind === "luck" ? `<span class="lg-tip" tabindex="0" title="${escapeHtml(luckText())}">${r.label}</span>` : r.label;
  const wide = `<div class="table-wrap"><table class="plain lg-table lg-records">
    <thead><tr><th scope="col">Record</th><th scope="col">Manager</th><th scope="col">Year</th><th scope="col" class="num">Value</th><th scope="col">Season Result</th><th scope="col"><span class="sr-only">Top 25</span></th></tr></thead>
    <tbody>${rows.map((r) => `<tr class="lg-click" data-record="season:${r.key}"><td class="strong">${label(r)}</td><td>${managerCell(r.e.user, "sm")}</td><td>${year(r.e)}</td>
      <td class="num"><span class="lg-value">${seasonValue(r.kind, r.e)}</span></td><td>${resultPill(r.e.result)}</td><td class="num">${moreButton(`season:${r.key}`, r.label)}</td></tr>`).join("")}</tbody></table></div>`;
  const narrow = `<div class="lg-list">${rows.map((r) => `<button type="button" class="lg-rowbtn" data-record="season:${r.key}" aria-label="${escapeHtml(`${r.label}: ${seasonValue(r.kind, r.e)}, ${mgr(r.e.user)?.name || ""} ${year(r.e)}. Top 25`)}">
      <span class="lg-line"><span class="lg-label">${r.label}</span><span class="lg-value">${seasonValue(r.kind, r.e)}</span></span>
      <span class="lg-line">${plainManager(r.e.user)}<span class="muted">${year(r.e)}</span>${resultPill(r.e.result)}</span><span class="lg-chev" aria-hidden="true">›</span></button>`).join("")}</div>`;
  $("lg-season").querySelector(".lg-body").innerHTML = wideNarrow(wide, narrow);
  $("lg-season").querySelector(".lg-star").hidden = !rows.some((r) => r.e.current);
}

// -- players ------------------------------------------------------------------------------------------

function playerColumns(card) {
  const mgrName = (e) => e.user ? managerCell(e.user) : `<span class="muted">${/*copy:LG-45*/"Free agent"}</span>`;
  if (card === "career") return { heads: ["Games", "Points", "PPG"], cells: (e) => [e.games, fmt2(e.points), e.ppg.toFixed(2)], detail: (e) => `${e.games} games · ${e.ppg.toFixed(2)} PPG`, value: (e) => fmt2(e.points) };
  if (card === "championships") return {
    heads: ["Managers", "Seasons", "Titles"],
    cells: (e) => [e.users.map((u) => escapeHtml(mgr(u)?.name || "")).join(", "), e.seasons.join(", "), e.value],
    detail: (e) => `${e.seasons.join(", ")} · ${e.users.map((u) => mgr(u)?.name || "").join(", ")}`, value: (e) => e.value,
  };
  return {
    heads: ["Manager", "Year / Wk", "Points"], cells: (e) => [mgrName(e), `${when(e)}${tags(e)}`, fmt2(e.value)],
    detail: (e) => `${e.user ? mgr(e.user)?.name || "" : "Free agent"} · ${e.season} Wk ${e.week}`, value: (e) => fmt2(e.value),
  };
}

function playerRow(e, cols) {
  return `<span class="lg-player">${headshot(e.player_id)}<span class="lg-player-text">${shortName(e.name, e.position)}${posPill(e.position)}</span></span>`;
}

function renderPlayerCard(card) {
  const section = $("lg-players").querySelector(`[data-card="${card}"]`);
  const pos = state.filters[card];
  const list = ((state.data.players[card] || {})[pos] || []);
  const top = list.slice(0, 5);
  const cols = playerColumns(card);
  const label = cardTitle(card);
  const filters = `<div class="lg-filters" role="group" aria-label="Position">${POSITIONS.map((p) => `<button type="button" class="lg-pos-btn ${p.toLowerCase()}" data-card="${card}" data-lg-pos="${p}" aria-pressed="${p === pos}">${p === "ALL" ? "All" : p}</button>`).join("")}</div>`;
  const wide = `<table class="plain lg-table lg-ptable"><thead><tr><th scope="col">#</th><th scope="col">Player</th>${cols.heads.map((h, i) => `<th scope="col"${i === 2 ? ' class="num"' : ""}>${h}</th>`).join("")}</tr></thead>
    <tbody>${top.map((e) => `<tr><td>${rankPill(e.rank)}</td><td>${playerRow(e, cols)}</td>${cols.cells(e).map((c, i) => `<td${i === 2 ? ' class="num strong"' : ' class="muted"'}>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  const narrow = `<ol class="lg-list">${top.map((e) => `<li class="lg-item">${rankPill(e.rank)}<div class="lg-item-body"><div class="lg-line">${playerRow(e, cols)}<span class="lg-value">${cols.value(e)}</span></div>
      <div class="lg-line lg-sub"><span>${escapeHtml(cols.detail(e))}${e.current ? tags({ current: true }) : ""}</span></div></div></li>`).join("")}</ol>`;
  section.querySelector(".lg-body").innerHTML = `${filters}${top.length ? wideNarrow(wide, narrow) : `<p class="hint">${/*copy:LG-46*/"No Players at this position yet."}</p>`}${top.length ? moreButton(`players:${card}`, label) : ""}`;
  wireImages(section);
  fitNames(section);
}

// -- the pop-up -----------------------------------------------------------------------------------------

function openDialog(id) {
  const [group, key] = id.split(":");
  const dialog = $("lg-dialog");
  let title, rows, wide, narrow;
  if (group === "weekly") {
    title = WEEKLY.find(([k]) => k === key)[1];
    rows = state.data.weekly[key] || [];
    wide = `<table class="plain lg-table lg-dtable"><thead><tr><th scope="col">#</th><th scope="col" class="num">Value</th><th scope="col">Manager</th><th scope="col">Opponent</th><th scope="col">Year / Wk</th></tr></thead>
      <tbody>${rows.map((e) => `<tr><td>${rankPill(e.rank)}</td><td class="num"><span class="lg-value">${fmt2(e.value)}</span><span class="lg-sub">${scoreLine(e)}</span></td><td>${managerCell(e.user)}</td><td class="muted">${managerCell(e.opp)}</td><td>${when(e)}${tags(e)}</td></tr>`).join("")}</tbody></table>`;
    narrow = `<ol class="lg-list">${rows.map((e) => `<li class="lg-item">${rankPill(e.rank)}<div class="lg-item-body"><div class="lg-line">${managerCell(e.user, "sm")}<span class="lg-value">${fmt2(e.value)}</span></div>
      <div class="lg-line lg-sub"><span>vs ${escapeHtml(mgr(e.opp)?.name || "")} · ${e.season} Wk ${e.week}</span></div>${tags(e) ? `<div class="lg-line">${tags(e)}</div>` : ""}</div></li>`).join("")}</ol>`;
  } else if (group === "season") {
    const [, label, kind] = SEASON.find(([k]) => k === key);
    title = label;
    rows = state.data.season[key] || [];
    wide = `<table class="plain lg-table lg-dtable"><thead><tr><th scope="col">#</th><th scope="col" class="num">Value</th><th scope="col">Manager</th><th scope="col">Year</th><th scope="col">Season Result</th></tr></thead>
      <tbody>${rows.map((e) => `<tr><td>${rankPill(e.rank)}</td><td class="num"><span class="lg-value">${seasonValue(kind, e)}</span></td><td>${managerCell(e.user)}</td><td>${year(e)}</td><td>${resultPill(e.result)}</td></tr>`).join("")}</tbody></table>`;
    narrow = `<ol class="lg-list">${rows.map((e) => `<li class="lg-item">${rankPill(e.rank)}<div class="lg-item-body"><div class="lg-line">${managerCell(e.user, "sm")}<span class="lg-value">${seasonValue(kind, e)}</span></div>
      <div class="lg-line lg-sub"><span>${year(e)}</span>${resultPill(e.result)}</div></div></li>`).join("")}</ol>`;
    $("lg-dialog-note").hidden = kind !== "luck";
  } else {
    title = cardTitle(key);
    const pos = state.filters[key];
    if (pos !== "ALL") title += ` · ${pos}`;
    rows = (state.data.players[key] || {})[pos] || [];
    const cols = playerColumns(key);
    wide = `<table class="plain lg-table lg-dtable"><thead><tr><th scope="col">#</th><th scope="col">Player</th>${cols.heads.map((h, i) => `<th scope="col"${i === 2 ? ' class="num"' : ""}>${h}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((e) => `<tr><td>${rankPill(e.rank)}</td><td>${playerRow(e, cols)}</td>${cols.cells(e).map((c, i) => `<td${i === 2 ? ' class="num strong"' : ' class="muted"'}>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    narrow = `<ol class="lg-list">${rows.map((e) => `<li class="lg-item">${rankPill(e.rank)}<div class="lg-item-body"><div class="lg-line">${playerRow(e, cols)}<span class="lg-value">${cols.value(e)}</span></div>
      <div class="lg-line lg-sub"><span>${escapeHtml(cols.detail(e))}</span></div></div></li>`).join("")}</ol>`;
  }
  if (group !== "season") $("lg-dialog-note").hidden = true;
  const seasons = [...new Set(state.data.standings.flatMap((r) => [r.first, r.last_season]))].sort();
  $("lg-dialog-title").textContent = title;
  $("lg-dialog-sub").textContent = `Top 25 · ${state.leagueName}, ${seasons[0]}–${seasons[seasons.length - 1]}`;
  $("lg-dialog-body").innerHTML = wideNarrow(wide, narrow);
  wireImages($("lg-dialog-body"));
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
  fitNames($("lg-dialog-body"));
}

function closeDialog() {
  const dialog = $("lg-dialog");
  if (dialog.open) dialog.close();
}
