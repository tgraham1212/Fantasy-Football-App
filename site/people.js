/* Shared pieces for drawing Managers and Players: team logos and Sleeper avatars, Player photos, and
   the site's Player name standard (full name, or "A. St. Brown" only when it does not fit). Used by the
   Managers page (managers.js) and the League page (league.js), so both fall back the same way. */

export const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const AVATAR = (id) => `https://sleepercdn.com/avatars/thumbs/${encodeURIComponent(id)}`;
export const HEADSHOT = (pid) => (/^[A-Z]{2,3}$/.test(pid) ? `https://sleepercdn.com/images/team_logos/nfl/${pid.toLowerCase()}.png` : `https://sleepercdn.com/content/nfl/players/thumb/${encodeURIComponent(pid)}.jpg`);

export function initials(name) {
  const parts = String(name).replace(/[^A-Za-z0-9 ]/g, " ").trim().split(/\s+/);
  return (parts.length > 1 ? parts[0][0] + parts[1][0] : String(name).slice(0, 2)).toUpperCase();
}

/* Team logo, else Sleeper avatar, else initials in the team colour (`token`, a css variable name). A
   failed image falls back to the initials in place, so the crest keeps its size. */
export function crest(m, size, token = null) {
  if (!m) return `<span class="mgr-crest ${size} initials"><span>?</span></span>`;
  const style = `--crest: var(${token || "--former-3"})`;
  const text = `<span>${escapeHtml(initials(m.name))}</span>`;
  const src = m.logo || (m.avatar ? AVATAR(m.avatar) : null);
  if (!src) return `<span class="mgr-crest ${size} initials" style="${style}" aria-hidden="true">${text}</span>`;
  return `<span class="mgr-crest ${size}" style="${style}" aria-hidden="true"><img src="${escapeHtml(src)}" alt="" loading="lazy" referrerpolicy="no-referrer" data-fallback="crest">${text}</span>`;
}

export function headshot(pid) {
  return `<span class="mgr-head" aria-hidden="true">${pid ? `<img src="${escapeHtml(HEADSHOT(pid))}" alt="" loading="lazy" referrerpolicy="no-referrer" data-fallback="head">` : ""}</span>`;
}

/* The site's name standard: a player's full name, or "A. St. Brown" (a defense: its nickname) only
   when the full name does not fit its space; the full name stays in the tooltip. */
export function shortPlayerName(name, position) {
  const parts = String(name || "").trim().split(/\s+/);
  if (position === "DEF") return parts[parts.length - 1];
  return parts.length > 1 ? `${parts[0][0]}. ${parts.slice(1).join(" ")}` : name;
}

export function nameAttrs(name, position) {
  const short = shortPlayerName(name, position);
  return short && short !== name ? ` title="${escapeHtml(name)}" data-full="${escapeHtml(name)}" data-short="${escapeHtml(short)}"` : "";
}

/* A player's name in a tile, card or row, fitted after rendering (the name standard above). */
export function shortName(name, position) {
  return `<span class="fitname"${nameAttrs(name, position)}>${escapeHtml(name)}</span>`;
}

/* Text wider than its box, measured to the fraction of a pixel (scrollWidth rounds, and a name
   over by under a pixel still gets an ellipsis). */
export function overflows(el) {
  const box = el.getBoundingClientRect().width;
  if (!box) return false;
  const r = document.createRange();
  r.selectNodeContents(el);
  return r.getBoundingClientRect().width > box + 0.01;
}

/* After rendering (and on resize): shorten only the names that overflow. Hidden elements measure 0
   wide and are left full; they are fitted again when shown. */
export function fitNames(root) {
  for (const el of (root || document).querySelectorAll("[data-short], .fitname")) {
    el.classList.remove("fit-wrap");
    if (el.dataset.short) {
      el.textContent = el.dataset.full;
      if (overflows(el)) el.textContent = el.dataset.short;
    }
    if (overflows(el)) el.classList.add("fit-wrap");   // even the short form is too wide: wrap it, never cut it
  }
}

/* A broken Sleeper image leaves the initials or silhouette underneath. */
export function wireImages(root) {
  for (const img of root.querySelectorAll("img[data-fallback]")) {
    img.addEventListener("error", () => img.remove(), { once: true });
  }
}
