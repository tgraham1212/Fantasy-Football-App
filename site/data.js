/* Data loading with the live bundle laid over the deployed files (docs/refresh-modes.md).

   The hot runs put this week's league forecast and game cards in one bundle on the refresh relay;
   updates.js fetches it and calls setOverlay() with its files, keyed by their paths under data/.
   While a bundle is newer than the deployed data, fetchData() answers those paths from it, so every
   view - including switching weeks - shows the newest numbers; every other path is fetched. */

const overlay = new Map();

export function setOverlay(files) {
  overlay.clear();
  for (const [path, payload] of Object.entries(files || {})) overlay.set(`data/${path}`, payload);
}

export function clearOverlay() {
  overlay.clear();
}

export async function fetchData(path) {
  if (overlay.has(path)) return structuredClone(overlay.get(path));
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}
