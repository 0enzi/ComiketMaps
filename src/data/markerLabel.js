export function markerTableLabel(marker) {
  const table = String(marker?.table ?? "").trim();
  if (/^\d+$/.test(table)) return String(Number(table));
  return table || marker?.label || "?";
}
