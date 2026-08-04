function compareLocation(a, b) {
  const section = String(a.section ?? "").localeCompare(String(b.section ?? ""), "ja");
  if (section) return section;
  const table = Number(a.table) - Number(b.table);
  if (Number.isFinite(table) && table) return table;
  return String(a.half ?? "").localeCompare(String(b.half ?? ""));
}

export function groupMarkers({ manifest, days, booths, artists }) {
  const boothById = new Map(booths.map((booth) => [booth.booth_id, booth]));
  const markersByKey = new Map();
  for (const artist of artists || []) {
    for (const location of artist.locations || []) {
      const booth = boothById.get(location.booth_id);
      if (!booth) continue;
      const day = days.find((candidate) => candidate.number === Number(location.day)) || days[0];
      if (!day) continue;
      const key = `${day.id}:${location.booth_id}`;
      if (!markersByKey.has(key)) {
        markersByKey.set(key, {
          id: `${manifest.event_id}:${key}`,
          booth_id: location.booth_id,
          booth_code: location.booth_code || booth.booth_code || "Unknown booth",
          label: location.booth_code || booth.booth_code || "Unknown booth",
          mapId: booth.map_id,
          dayId: day.id,
          x: booth.x,
          y: booth.y,
          section: booth.section,
          table: booth.table,
          half: booth.half,
          artists: [],
        });
      }
      markersByKey.get(key).artists.push(artist);
    }
  }
  return [...markersByKey.values()].sort((a, b) => compareLocation(a, b));
}
