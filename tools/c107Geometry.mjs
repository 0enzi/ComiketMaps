// C107's prototype coordinates were recorded against the legacy Cloudinary
// render rather than the official PDF page render. Keep the conversion in a
// small, testable module so a future calibrated event can replace it cleanly.
export const LEGACY_MAP_SIZE = Object.freeze({ width: 2306, height: 1244 });
export const OFFICIAL_PAGE_SIZE = Object.freeze({ width: 1720, height: 1215 });

// These are booth calibration points on the official C107 East 4–6 page.
// They are keyed by semantic booth identity so artist records never own map
// coordinates and future imports can reuse the same calibration layer.
export const C107_CALIBRATED_BOOTHS = Object.freeze({
  // East 4–6 outer wall and top-wall cells.
  "east-4-6|ア|60": Object.freeze({ x: 508, y: 286 }),
  "east-4-6|ア|64": Object.freeze({ x: 420, y: 269 }),
  "east-4-6|ア|80": Object.freeze({ x: 66, y: 450 }),
  "east-4-6|ア|84": Object.freeze({ x: 58, y: 525 }),
  "east-4-6|ア|85": Object.freeze({ x: 58, y: 608 }),

  // East 4 section cells. These are the centers of the printed table cells,
  // not the midpoint of the adjacent two-cell booth pair.
  "east-4-6|ヨ|49": Object.freeze({ x: 129, y: 719 }),
  "east-4-6|ユ|37": Object.freeze({ x: 169, y: 392 }),
  "east-4-6|ユ|40": Object.freeze({ x: 169, y: 441 }),
  "east-4-6|ユ|43": Object.freeze({ x: 169, y: 480 }),
  "east-4-6|ユ|49": Object.freeze({ x: 169, y: 594 }),
  "east-4-6|ユ|52": Object.freeze({ x: 169, y: 633 }),

  // East 4 メ/マ/ホ/ヒ blocks.
  "east-4-6|メ|16": Object.freeze({ x: 324, y: 581 }),
  "east-4-6|メ|25": Object.freeze({ x: 324, y: 419 }),
  "east-4-6|メ|34": Object.freeze({ x: 308, y: 365 }),
  "east-4-6|メ|36": Object.freeze({ x: 308, y: 392 }),
  "east-4-6|メ|38": Object.freeze({ x: 308, y: 419 }),
  "east-4-6|メ|39": Object.freeze({ x: 308, y: 441 }),
  "east-4-6|メ|40": Object.freeze({ x: 308, y: 454 }),
  "east-4-6|メ|42": Object.freeze({ x: 308, y: 480 }),
  "east-4-6|メ|44": Object.freeze({ x: 308, y: 506 }),
  "east-4-6|マ|18": Object.freeze({ x: 438, y: 532 }),
  "east-4-6|ホ|09": Object.freeze({ x: 475, y: 693 }),
  "east-4-6|ヒ|09": Object.freeze({ x: 586, y: 632 }),

  // East 5 ノ block.
  "east-4-6|ノ|09": Object.freeze({ x: 685, y: 672 }),
});

export function calibratedC107Point(mapId, section, table, fallback) {
  return C107_CALIBRATED_BOOTHS[`${mapId}|${section}|${table}`] || fallback;
}

export function legacyPixelToOfficialPage(x, y) {
  return {
    x: Math.round(Number(x) * (OFFICIAL_PAGE_SIZE.width / LEGACY_MAP_SIZE.width) + 45),
    y: Math.round(Number(y) * 0.844 + 100),
  };
}

export function stablePointKey(x, y) {
  return `${Math.round(Number(x) / 8)}:${Math.round(Number(y) / 8)}`;
}
