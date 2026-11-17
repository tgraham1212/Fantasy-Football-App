/* Shared sortable-header rules: first click sorts descending (text columns A to Z),
   second click flips, the sorted header shows a fill and an arrow, untouched tables show none. */

export function nextSort(current, key) {
  if (current && current.key === key) return { key, dir: current.dir === "desc" ? "asc" : "desc" };
  return { key, dir: "desc" };
}

/* Mark the sorted header with aria-sort and clear the rest. `ths` are <th data-col> elements. */
export function markSorted(ths, sort) {
  for (const th of ths) {
    if (sort && th.dataset.col === sort.key) th.setAttribute("aria-sort", sort.dir === "asc" ? "ascending" : "descending");
    else th.removeAttribute("aria-sort");
  }
}

/* A comparator for `col` ({ value } numeric, highest first; or { text }, A to Z first) in direction `dir`.
   Missing numbers sort last in either direction; `tiebreak` orders equal rows. */
export function comparator(col, dir, tiebreak = () => 0) {
  const sign = dir === "asc" ? -1 : 1;
  if (col.text) return (a, b) => sign * col.text(a).localeCompare(col.text(b)) || tiebreak(a, b);
  return (a, b) => {
    const va = col.value(a);
    const vb = col.value(b);
    if (va == null && vb == null) return tiebreak(a, b);
    if (va == null) return 1;
    if (vb == null) return -1;
    return sign * (vb - va) || tiebreak(a, b);
  };
}

/* Wire every sortable header button in `table` to `onSort(key)`. */
export function wireHeaders(table, onSort) {
  for (const th of table.querySelectorAll("thead th[data-col]")) {
    const btn = th.querySelector("button.sort");
    if (btn) btn.addEventListener("click", () => onSort(th.dataset.col));
  }
}
