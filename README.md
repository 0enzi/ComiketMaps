# Comiket Maps

Reusable Comiket map importer, localhost review tool, and static mobile/PWA viewer.

## Viewer

The frontend reads `public/events/index.json`, then discovers each event’s manifest, days, semantic maps, booths, and reviewed artists. It does not contain event-specific map URLs or marker coordinates. The C107 migration maps PDF pages to:

| PDF page | Semantic map |
| --- | --- |
| 1 | `east-4-6` |
| 2 | `east-7-8` |
| 3 | `south-1-2` |
| 4 | `west-1-2` |

Run it with Node 20.19+:

```sh
npm ci
npm run dev
```

The viewer keeps PIXI available for GPU rendering, but local development uses the resilient HTML map layer by default because some embedded browsers expose a broken WebGL context. It still supports drag, scroll/pinch-style zoom, numbered markers, and the same selection flow. Set `VITE_ENABLE_PIXI=true` when testing the PIXI renderer explicitly.

The Vite base path is `/ComiketMaps/` for GitHub Pages. `npm run build` produces one Vite PWA service worker and base-safe assets. Raw importer inputs are never copied into `dist`.

## Importer

The importer requires Python 3.10+ and Poppler (`pdfinfo`, `pdftoppm`). Pillow/OpenCV, Japanese Tesseract data, and FastAPI/Uvicorn are optional extras for richer calibration/OCR and can be installed with `pip install -e '.[pdf,ocr,review,validation]'`. The dependency-free core still renders complete PDF pages and serves the review UI on `127.0.0.1`. When `config/events/<event>.json` exists, `init` loads it automatically.

```sh
python -m comiket_import init --event C108 --pdf /path/to/C108Map_all_B4.pdf
python -m comiket_import import-artists --event C108 --csv /path/to/following.csv
python -m comiket_import review --event C108 --open
python -m comiket_import build --event C108
```

The checked-in C107 and C108 configs map each official PDF page to a semantic map ID. The downloaded C108 PDF and rendered pages currently live only in the gitignored `work/` directory while calibration, artist review, and map-image redistribution permission are pending.

Open the review URL after `review`. Orange rectangles are computer-vision suggestions only. Click a booth cell to capture its normalized point, enter direction, hall, section, table, and half, then save the calibrated booth. Edit artist candidates in the table and accept, reject, exclude, or merge them. Corrections are stored in private `work/events/<event>/review_overrides.json` and are reapplied after a fresh CSV import. `build` stays blocked until unresolved artist records and accepted locations without geometry are cleared.

Private source PDFs, CSVs, rendered work pages, OCR, and review state live under `work/` and are gitignored. Only reviewed public records and derived assets are written under `public/events/<event-id>/`.

Manual corrections use CSV columns such as `user_id,username,display_name,day,direction,hall,section,table,half,action`. Use `action=replace` when a correction replaces all parsed locations for that artist; ordinary rows replace only the same day. Missing halves remain `unknown` and block publication until reviewed.

An eventual Chrome extension should export the same normalized artist CSV/manual-correction columns consumed here. It can gather profile text in the browser, but it must not publish directly or contain map coordinates; calibration and publication remain in this local review pipeline. Extension development is intentionally outside v1.

## C107 migration

`node tools/migrate_c107.mjs` converts the prototype’s 58 records into the public event contract and renders the official PDF pages as WebP assets. It intentionally emits a review queue for legacy contradictions and marks those coordinates as `legacy-marker-seed` until calibration/permission review is complete. The official source PDF is attributed in the manifest; redistribution of derived official map images must be confirmed before deployment.

## Checks

```sh
./venv/bin/python -m pytest -q
npm run test:viewer
npm run lint
npm run build
```

GitHub Pages: https://0enzi.github.io/ComiketMaps/
