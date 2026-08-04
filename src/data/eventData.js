const BASE_URL = import.meta.env.BASE_URL || "/";
import { groupMarkers } from "./markerGrouping";

const withBase = (value) => {
  if (!value) return value;
  if (/^https?:\/\//i.test(value)) return value;
  return `${BASE_URL.replace(/\/$/, "")}/${String(value).replace(/^\//, "")}`;
};

async function fetchJson(path) {
  const response = await fetch(withBase(path));
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status})`);
  return response.json();
}

export async function loadEventIndex() {
  return fetchJson("events/index.json");
}

function dayId(day) {
  return String(day?.id ?? day?.number ?? day?.day ?? "day-1");
}

function dayNumber(day) {
  const value = Number(day?.number ?? String(dayId(day)).replace(/\D/g, ""));
  return Number.isFinite(value) && value > 0 ? value : 1;
}

export async function loadEvent(eventEntry) {
  const manifest = await fetchJson(eventEntry.manifest);
  const eventBase = eventEntry.manifest.replace(/[^/]+$/, "");
  const [booths, artists] = await Promise.all([
    fetchJson(`${eventBase}booths.json`),
    fetchJson(`${eventBase}artists.json`),
  ]);
  const maps = (manifest.maps || []).map((map) => ({
    ...map,
    asset: withBase(`${eventBase}${map.asset}`),
  }));
  const days = (manifest.days || []).map((day) => ({ ...day, id: dayId(day), number: dayNumber(day) }));
  const markers = groupMarkers({ manifest, days, booths, artists });
  return {
    ...manifest,
    eventEntry,
    maps,
    days,
    booths,
    artists,
    markers,
  };
}

export function markersFor(event, dayIdValue, mapId) {
  return (event?.markers || []).filter((marker) => marker.dayId === dayIdValue && marker.mapId === mapId);
}
