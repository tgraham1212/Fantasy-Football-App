/* This page's code fingerprint. The deploy replaces the placeholder (see `ffapp stamp-site`);
   a local copy keeps it, which tells the update check to look for new data only. */
export const CODE = "__BUILD__";
export const STAMPED = !CODE.startsWith("__");
