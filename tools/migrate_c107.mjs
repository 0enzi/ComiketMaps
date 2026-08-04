import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { markerData } from "../src/data/newMarkerData.js";
import { calibratedC107Point, legacyPixelToOfficialPage, stablePointKey } from "./c107Geometry.mjs";

const root = path.resolve(new URL("..", import.meta.url).pathname);
const outputRoot = path.join(root, "public", "events", "c107");
const mapIds = ["east-4-6", "east-7-8", "south-1-2", "west-1-2"];
const mapLabels = ["East 4–6", "East 7–8", "South 1–2", "West 1–2"];
const mapPages = [1, 2, 3, 4];
const sourcePdf = "/private/tmp/C107Map_all_B4.pdf";
const sourcePdfSha256 = fs.existsSync(sourcePdf)
  ? crypto.createHash("sha256").update(fs.readFileSync(sourcePdf)).digest("hex")
  : "source-pdf-not-present-at-migration";

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }
function writeJson(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}
function normalizeUsername(value) { return String(value || "").replace(/^@/, "").normalize("NFKC").toLowerCase(); }

function parseBooth(raw) {
  const text = String(raw || "").normalize("NFKC");
  const match = text.match(/([東西南])\s*(?:[1-8]\s*)?([A-Za-zぁ-んァ-ヶ])\s*[-－]?\s*(\d{1,3})\s*([aAbB]{1,2})?/);
  if (!match) return { raw: text, direction: null, section: null, table: null, half: "unknown", explicitDay: null };
  const dayMatch = text.match(/([12])日目/);
  return {
    raw: text,
    direction: ({ 東: "East", 西: "West", 南: "South" })[match[1]] || null,
    section: match[2],
    table: match[3].padStart(2, "0"),
    half: match[4] ? match[4].toLowerCase() : "unknown",
    explicitDay: dayMatch ? Number(dayMatch[1]) : null,
  };
}
function canonicalBoothCode(parsed, fallback) {
  if (!parsed.section || !parsed.table) return fallback || "Unknown booth";
  return parsed.section + (parsed.table.replace(/^0+/, "") || "0") + (parsed.half === "unknown" ? "" : parsed.half);
}

function mapForIndex(index) { return mapIds[index] || `page-${index + 1}`; }
const artistByKey = new Map();
const booths = new Map();
const review = [];

for (const day of Object.keys(markerData).sort()) {
  const dayNumber = Number(day.replace(/\D/g, ""));
  for (const [indexString, markers] of Object.entries(markerData[day])) {
    const mapIndex = Number(indexString);
      const mapId = mapForIndex(mapIndex);
    for (const marker of markers) {
      const artistKey = `xhandle:${normalizeUsername(marker.id || marker.handle)}`;
      const parsed = parseBooth(marker.booth || marker.title);
      const legacyPoint = legacyPixelToOfficialPage(marker.x, marker.y);
      const point = calibratedC107Point(mapId, parsed.section, parsed.table, legacyPoint);
      const boothId = `${mapId}:${stablePointKey(point.x, point.y)}`;
      const reasons = [];
      if (!parsed.direction || !parsed.section || !parsed.table) reasons.push("legacy-booth-unparsed");
      if (parsed.half === "unknown") reasons.push("unknown-half");
      if (parsed.explicitDay && parsed.explicitDay !== dayNumber) reasons.push("explicit-day-conflict");
      if (reasons.length) review.push({ artist_key: artistKey, day: dayNumber, map_id: mapId, source: marker.booth, reason: reasons.join(",") });

      if (!booths.has(boothId)) booths.set(boothId, {
        booth_id: boothId, map_id: mapId, direction: parsed.direction, hall: null,
        section: parsed.section, table: parsed.table, half: parsed.half,
        booth_code: canonicalBoothCode(parsed, marker.booth), x: point.x, y: point.y,
        bounds: null, confidence: "needs_review", source: "legacy-marker-seed", artist_keys: [],
      });
      booths.get(boothId).artist_keys.push(artistKey);
      if (!artistByKey.has(artistKey)) {
        artistByKey.set(artistKey, {
          artist_key: artistKey,
          user_id: "",
          username: normalizeUsername(marker.handle || marker.id),
          display_name: marker.title || marker.id,
          description: marker.description || "",
          profile_url: "",
          avatar_url: marker.pfp || "",
          banner_url: marker.banner || "",
          locations: [],
        });
      }
      artistByKey.get(artistKey).locations.push({
        day: dayNumber, map_id: mapId, booth_id: boothId,
        booth_code: canonicalBoothCode(parsed, marker.booth), x: point.x, y: point.y,
        status: reasons.length ? "needs_review" : "accepted",
        source: "legacy-marker-seed", source_text: marker.booth || marker.title || "",
      });
    }
  }
}

ensureDir(path.join(outputRoot, "maps"));
const stalePublicReview = path.join(outputRoot, "review-queue.json");
if (fs.existsSync(stalePublicReview)) fs.rmSync(stalePublicReview);
for (let i = 0; i < mapIds.length; i += 1) {
  const input = `/private/tmp/c107-map-render/page-${i + 1}.png`;
  const output = path.join(outputRoot, "maps", `${mapIds[i]}.webp`);
  if (!fs.existsSync(input)) throw new Error(`Missing rendered PDF page: ${input}`);
  // cwebp is used by the migration command so the repository stores compact,
  // browser-friendly derived assets rather than the source PDF.
  const { spawnSync } = await import("node:child_process");
  const conversion = spawnSync("cwebp", ["-quiet", "-q", "88", input, "-o", output], { encoding: "utf8" });
  if (conversion.status !== 0) throw new Error(conversion.stderr || "cwebp failed");
}

const manifests = mapIds.map((mapId, i) => ({
  map_id: mapId, label: mapLabels[i], page: mapPages[i], asset: `maps/${mapId}.webp`,
  width: 1720, height: 1215,
}));
const manifest = {
  schema_version: "1.0.0", event_id: "C107", name: "Comic Market 107",
  attribution: "Map source: Comic Market official C107 map (https://www.comiket.co.jp/info-a/C107/C107Map_all_B4.pdf). Redistribution of derived map images must be confirmed before deployment.",
  source_pdf: "https://www.comiket.co.jp/info-a/C107/C107Map_all_B4.pdf",
  source_pdf_sha256: sourcePdfSha256,
  maps: manifests,
  days: [{ id: "day-1", label: "Day 1", number: 1 }, { id: "day-2", label: "Day 2", number: 2 }],
  generated_at: "2026-08-01T00:00:00Z",
};

writeJson(path.join(outputRoot, "manifest.json"), manifest);
const artists = [...artistByKey.values()].sort((a, b) => a.artist_key.localeCompare(b.artist_key));
const publicArtists = artists
  .map(({ artist_key, user_id, username, display_name, description, profile_url, avatar_url, banner_url, locations }) => ({
    artist_key, user_id, username, display_name, description, profile_url, avatar_url, banner_url,
    locations: locations
      .filter((location) => location.status === "accepted")
      .map(({ day, map_id, booth_id, booth_code }) => ({ day, map_id, booth_id, booth_code })),
  }))
  .filter((artist) => artist.locations.length > 0);
const publicBooths = [...booths.values()].map(({ booth_id, map_id, direction, hall, section, table, half, booth_code, x, y, bounds }) => ({
  booth_id, map_id, direction, hall, section, table, half, booth_code, x, y, bounds,
}));
writeJson(path.join(outputRoot, "booths.json"), publicBooths.sort((a, b) => a.booth_id.localeCompare(b.booth_id)));
writeJson(path.join(outputRoot, "artists.json"), publicArtists);
ensureDir(path.join(root, "work", "events", "c107"));
writeJson(path.join(root, "work", "events", "c107", "review-queue.json"), { schema_version: "1.0.0", event_id: "C107", records: review });
writeJson(path.join(root, "public", "events", "index.json"), {
  schema_version: "1.0.0", events: [{ event_id: "C107", name: "Comic Market 107", manifest: "events/c107/manifest.json" }],
});
console.log(`Migrated ${artists.length} markers and ${booths.size} legacy booth locations`);
console.log(`Review queue: ${review.length} record(s)`);
