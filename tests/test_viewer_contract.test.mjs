import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { calibratedC107Point, legacyPixelToOfficialPage, stablePointKey } from "../tools/c107Geometry.mjs";
import { groupMarkers } from "../src/data/markerGrouping.js";
import { clampMapScale, clampMapView, fitMapScale, MAP_MAX_SCALE } from "../src/data/mapViewport.js";
import { markerTableLabel } from "../src/data/markerLabel.js";
import { MAP_MARKER_SIZE, priorityCssColor, priorityLabel } from "../src/data/markerStyle.js";
import { latestEventEntry } from "../src/data/eventSelection.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const viewerSource = fs.readFileSync(path.join(root, "src/components/PIXIViewer.jsx"), "utf8");
const viewerCss = fs.readFileSync(path.join(root, "src/index.css"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "public/events/c107/manifest.json"), "utf8"));
const booths = JSON.parse(fs.readFileSync(path.join(root, "public/events/c107/booths.json"), "utf8"));
const artists = JSON.parse(fs.readFileSync(path.join(root, "public/events/c107/artists.json"), "utf8"));

test("viewer renders compact numbered boxes without booth-code labels", () => {
  assert.match(viewerSource, /<span>\{markerTableLabel\(marker\)}<\/span>/);
  assert.doesNotMatch(viewerSource, /<em>\{marker\.label\}<\/em>/);
  assert.doesNotMatch(viewerSource, /map-fallback-marker-layer/);
  assert.match(viewerSource, /left: imageCoordinate\(marker\.x, imageWidth\)/);
  assert.match(viewerCss, new RegExp(`\\.map-fallback-marker\\s*\\{[^}]*width:\\s*${MAP_MARKER_SIZE}px[^}]*height:\\s*${MAP_MARKER_SIZE}px`, "s"));
  assert.doesNotMatch(viewerCss, /\.map-fallback-marker em\s*\{/);
  assert.doesNotMatch(viewerSource, /--marker-scale/);
});

test("marker labels use the printed booth table number", () => {
  assert.equal(markerTableLabel({ table: "09", label: "ヒ9ab" }), "9");
  assert.equal(markerTableLabel({ table: "36", label: "メ36ab" }), "36");
  assert.equal(markerTableLabel({ table: "", label: "unknown" }), "unknown");
});

test("viewer opens the newest discovered event without hardcoding its ID", () => {
  assert.equal(latestEventEntry([
    { event_id: "C107", name: "Comic Market 107" },
    { event_id: "C108", name: "Comic Market 108" },
  ]).event_id, "C108");
});

test("map annotations scale with the image and zoom-out stops at fit", () => {
  const fitted = fitMapScale(900, 900, 1720, 1215);
  assert.equal(fitted, 900 / 1720);
  assert.equal(clampMapScale(0.08, fitted), fitted);
  assert.equal(clampMapScale(fitted * 2, fitted), fitted * 2);
  assert.equal(clampMapScale(99, fitted), MAP_MAX_SCALE);
  assert.equal(MAP_MARKER_SIZE * fitted, MAP_MARKER_SIZE * (900 / 1720));
});

test("map panning stays inside the visible image bounds", () => {
  const clamped = clampMapView({ scale: 8, x: 100, y: 576 }, 900, 900, 2867, 2024);
  assert.equal(clamped.x, 0);
  assert.equal(clamped.y, 0);

  const centered = clampMapView({ scale: 0.2, x: -50, y: 999 }, 900, 900, 2867, 2024);
  assert.equal(centered.x, (900 - 2867 * 0.2) / 2);
  assert.equal(centered.y, (900 - 2024 * 0.2) / 2);
});

test("C107 legacy coordinates go through the explicit page transform", () => {
  assert.deepEqual(legacyPixelToOfficialPage(539, 131), { x: 447, y: 211 });
  assert.deepEqual(legacyPixelToOfficialPage(388, 298), { x: 334, y: 352 });
  assert.equal(stablePointKey(447, 211), "56:26");
});

test("C107 semantic calibration overrides bad legacy points", () => {
  assert.deepEqual(calibratedC107Point("east-4-6", "ア", "64", { x: 447, y: 211 }), { x: 420, y: 269 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ア", "80", { x: 88, y: 419 }), { x: 66, y: 450 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ア", "84", { x: 78, y: 505 }), { x: 58, y: 525 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ア", "85", { x: 79, y: 602 }), { x: 58, y: 608 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ヒ", "09", { x: 720, y: 676 }), { x: 586, y: 632 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ノ", "09", { x: 720, y: 676 }), { x: 685, y: 672 });
  assert.deepEqual(calibratedC107Point("east-4-6", "メ", "36", { x: 334, y: 352 }), { x: 308, y: 392 });
  assert.deepEqual(calibratedC107Point("east-4-6", "ユ", "37", { x: 193, y: 352 }), { x: 169, y: 392 });
});

test("every generated C107 booth coordinate belongs to its map", () => {
  const dimensions = new Map(manifest.maps.map((map) => [map.map_id, map]));
  assert.ok(booths.length > 0);
  for (const booth of booths) {
    const map = dimensions.get(booth.map_id);
    assert.ok(map, `missing map for ${booth.booth_id}`);
    assert.ok(Number.isFinite(booth.x) && booth.x >= 0 && booth.x <= map.width, booth.booth_id);
    assert.ok(Number.isFinite(booth.y) && booth.y >= 0 && booth.y <= map.height, booth.booth_id);
  }
});

test("public output preserves stable identities and strips private fields", () => {
  const appearances = new Set();
  for (const artist of artists) {
    assert.match(artist.artist_key, /^x(?::|handle:)/);
    for (const location of artist.locations) {
      const appearance = `${artist.artist_key}:${location.day}:${location.map_id}:${location.booth_id}`;
      assert.ok(!appearances.has(appearance), `duplicate appearance ${appearance}`);
      appearances.add(appearance);
      assert.equal("status" in location, false);
      assert.equal("source_text" in location, false);
    }
  }
});

test("viewer groups valid co-located artists by day and booth", () => {
  const booth = { booth_id: "east-4-6:artist-booth", map_id: "east-4-6", section: "メ", table: "36", half: "ab", booth_code: "メ36ab", x: 334, y: 352 };
  const grouped = groupMarkers({
    manifest: { event_id: "C107" },
    days: [{ id: "day-1", number: 1 }],
    booths: [booth],
    artists: [
      { artist_key: "x:1", username: "one", locations: [{ day: 1, booth_id: booth.booth_id, booth_code: booth.booth_code }] },
      { artist_key: "x:2", username: "two", locations: [{ day: 1, booth_id: booth.booth_id, booth_code: booth.booth_code }] },
    ],
  });
  assert.equal(grouped.length, 1);
  assert.equal(grouped[0].artists.length, 2);
  assert.equal(grouped[0].id, "C107:day-1:east-4-6:artist-booth");
});

test("map markers use the highest priority at a shared booth", () => {
  const booth = { booth_id: "east-4-6:priority-booth", map_id: "east-4-6", section: "ア", table: "1", half: "ab", booth_code: "ア1ab", x: 100, y: 100 };
  const grouped = groupMarkers({
    manifest: { event_id: "C107" },
    days: [{ id: "day-1", number: 1 }],
    booths: [booth],
    artists: [
      { artist_key: "x:green", username: "green", priority: 0, locations: [{ day: 1, booth_id: booth.booth_id }] },
      { artist_key: "x:yellow", username: "yellow", priority: 5, locations: [{ day: 1, booth_id: booth.booth_id }] },
      { artist_key: "x:red", username: "red", priority: 10, locations: [{ day: 1, booth_id: booth.booth_id }] },
    ],
  });
  assert.equal(grouped[0].priority, 10);
  assert.equal(priorityCssColor(grouped[0].priority), "#ef5964");
  assert.equal(priorityLabel(0), "0 points");
  assert.match(viewerCss, /\.priority-0\s*\{[^}]*--priority-color:\s*var\(--priority-green\)/s);
  assert.match(viewerCss, /\.priority-5\s*\{[^}]*--priority-color:\s*var\(--priority-yellow\)/s);
  assert.match(viewerCss, /\.priority-10\s*\{[^}]*--priority-color:\s*var\(--priority-red\)/s);
});
