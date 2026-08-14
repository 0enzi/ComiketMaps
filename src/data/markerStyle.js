export const MAP_MARKER_SIZE = 18;

// Priority is shared by the Discord link list and the map viewer. Keep the
// palette deliberately high-contrast so the same marker remains recognizable
// on both the map image and the dark details panel.
export const PRIORITY_STYLES = {
  0: { css: "#2bd17f", pixi: 0x2bd17f, label: "0 points" },
  5: { css: "#f4c84b", pixi: 0xf4c84b, label: "5 points" },
  10: { css: "#ef5964", pixi: 0xef5964, label: "10 points" },
};

export function normalizePriority(value) {
  const number = Number(value);
  return number === 10 || number === 5 ? number : 0;
}

export function priorityCssColor(value) {
  return PRIORITY_STYLES[normalizePriority(value)].css;
}

export function priorityPixiColor(value) {
  return PRIORITY_STYLES[normalizePriority(value)].pixi;
}

export function priorityLabel(value) {
  return PRIORITY_STYLES[normalizePriority(value)].label;
}
