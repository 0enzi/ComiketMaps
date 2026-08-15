# Comiket Maps

**A fast, mobile-first archive for Comiket booth maps and reviewed artist locations.**

[Open the live map](https://0enzi.github.io/ComiketMaps/)

The current public archive is **Comic Market 108 (C108)**. It is designed for quick booth lookup on desktop and mobile, with priority-colored markers, artist profiles, pinch/scroll zoom, and offline iPhone support.

## Use it on an iPhone

1. Open the live map in **Safari** while online.
2. Wait until the download button says **Saved**.
3. Tap **Share → Add to Home Screen**.
4. Launch Comiket Maps from the new home-screen icon.

The reviewed C108 maps and event data are cached for offline use. Profile images hosted by social networks may still need a connection.

## Run locally

Requirements: Node.js **20.19+**.

```sh
npm ci
npm run dev
```

Then open `http://localhost:5173/ComiketMaps/`.

Useful checks:

```sh
npm run test:viewer
npm run lint
npm run build
```

The normal development build uses the resilient HTML map layer. To explicitly test the PIXI renderer:

```sh
VITE_ENABLE_PIXI=true npm run dev
```

## Priority markers

Markers use the same priority system as the Discord link list:

| Priority | Map color |
| ---: | --- |
| 0 points | Green |
| 5 points (`!`) | Yellow |
| 10 points (`!!`) | Red |

If multiple artists share a booth, the marker uses the highest priority at that booth.

## Import and review data

The importer keeps raw following exports and review state private under `work/`. Only reviewed, derived records are published under `public/events/`.

The normal C108 workflow is:

```sh
python -m comiket_import init --event C108 --pdf /path/to/C108Map_all_B4.pdf
python -m comiket_import import-bot --event C108 --db /path/to/nyaa.db
python -m comiket_import review --event C108 --open
python -m comiket_import build --event C108
```

`import-bot` reads SQLite in read-only mode and imports only C108 rows already
marked as exhibitors. It also carries over any saved avatar/banner metadata and
seeds calibrated map cells, so rerunning it safely updates priorities and new
booth additions without duplicating artists.

The review page is the authority for accepted booth locations. Unresolved artist locations and accepted locations without calibrated geometry block a normal publish build. The automatic bot sync uses `--allow-missing-calibration` so calibrated booths can publish while uncalibrated booths are omitted until their map points are reviewed.

Python 3.10+ and Poppler (`pdfinfo`, `pdftoppm`) are required. Optional OCR, PDF, review, and validation extras are documented in `pyproject.toml`.

## Publish to GitHub Pages

This repository uses the `gh-pages` package rather than an Actions workflow:

```sh
npm run deploy
```

The command builds `dist/` and publishes it to the `gh-pages` branch. In GitHub repository settings, Pages should use **Deploy from a branch → `gh-pages` → `/ (root)`**.

The Vite base path is `/ComiketMaps/`, so the same build works at the project-page URL.

## Repository layout

```text
src/                  React viewer and map interactions
public/events/        Published event manifests, artists, booths, and map assets
comiket_import/       Python importer, review server, and public builder
config/events/        Event-specific PDF/map configuration
tools/                One-off migration and geometry utilities
work/                 Private local PDFs, renders, CSVs, and review state (ignored)
```

## Archive and source notes

C107 is no longer in the live event picker, but its reviewed map files and username list remain under `public/events/c107/` for reference and rollback.

Official Comiket map images are attributed in each event manifest. Confirm redistribution permission before publishing a new event’s derived map assets.
