"""Command-line pipeline and local review application.

The default implementation deliberately has a zero-dependency core.  Pillow,
OpenCV, Tesseract, FastAPI, and Uvicorn can be layered on later, but a
maintainer can already render, inspect, review, validate, and build without
putting raw following exports into the public bundle.
"""

from __future__ import annotations

import argparse
import csv
import http.server
import json
import math
import shutil
import threading
import subprocess
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artists import event_config_from_dict, merge_records, read_artist_csv, read_manual_csv
from .bot_database import read_bot_database
from .carryover import build_carry_over, c108_anchor, carry_over_map_id
from .models import SCHEMA_VERSION, read_json, write_json
from .normalize import (
    format_booth_code,
    normalize_direction,
    normalize_half,
    normalize_section,
    normalize_table,
    normalize_text,
)
from .pdf_import import init_event, load_calibration, load_event
from .validate import validate_public_event


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "work"
PUBLIC_ROOT = ROOT / "public" / "events"
EVENT_CONFIG_ROOT = ROOT / "config" / "events"


def event_dir(event_id: str) -> Path:
    return WORK_ROOT / "events" / event_id.lower()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_event_config(event_id: str) -> Dict[str, Any]:
    path = event_dir(event_id) / "event.json"
    if not path.exists():
        raise FileNotFoundError(f"Run init first: {path}")
    return read_json(path)


def command_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config) if args.config else EVENT_CONFIG_ROOT / f"{args.event.lower()}.json"
    config = read_json(config_path) if config_path.exists() else {}
    event = init_event(args.event, Path(args.pdf).resolve(), WORK_ROOT, config, args.dpi)
    event["generated_at"] = event.get("generated_at", _now())
    write_json(event_dir(args.event) / "event.json", event)
    if config_path.exists():
        print(f"Loaded event config: {config_path}")
    print(f"Initialized {args.event}: {event['pdf']['pages']} rendered page(s)")
    print(f"Private work state: {event_dir(args.event)}")
    return 0


def _manual_path(event_id: str) -> Path:
    return event_dir(event_id) / "manual_corrections.csv"


def _overrides_path(event_id: str) -> Path:
    return event_dir(event_id) / "review_overrides.json"


def _apply_review_overrides(records: List[Any], overrides: Dict[str, Any]) -> List[Any]:
    for override in overrides.get("records", []):
        for artist in records:
            if artist.artist_key != override.get("artist_key"):
                continue
            for location in artist.locations:
                same_key = location.location_key == override.get("location_key")
                same_source = (
                    location.source_text == override.get("source_text")
                    and location.source_field == override.get("source_field")
                )
                if not (same_key or same_source):
                    continue
                for field_name in ("day", "direction", "hall", "section", "table", "half", "status", "reason"):
                    if field_name in override:
                        setattr(location, field_name, override[field_name])
    return records


def _calibrate_booth(
    event: Dict[str, Any], calibration: Dict[str, Any], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate and normalize one reviewer-confirmed booth geometry.

    Coordinates are stored normalized to the rendered page.  The public viewer
    also accepts legacy pixel coordinates, so this remains backwards compatible
    with the C107 migration while keeping new calibrations resolution-safe.
    """
    map_id = normalize_text(payload.get("map_id"))
    map_item = next((item for item in calibration.get("maps", []) if item.get("map_id") == map_id), None)
    if map_item is None:
        raise ValueError(f"Unknown calibration map: {map_id or '<empty>'}")

    direction = normalize_direction(payload.get("direction"))
    section = normalize_section(payload.get("section"))
    table = normalize_table(payload.get("table"))
    hall = normalize_text(payload.get("hall")) or None
    half = normalize_half(payload.get("half"))
    if direction not in {"East", "West", "South"}:
        raise ValueError("direction must be East, West, or South")
    if not section or not table:
        raise ValueError("section and table are required")
    if half == "unknown":
        raise ValueError("half must be a, b, or ab for calibrated geometry")

    try:
        x = float(payload.get("x"))
        y = float(payload.get("y"))
    except (TypeError, ValueError) as exc:
        raise ValueError("x and y must be numeric normalized coordinates") from exc
    if not all(math.isfinite(value) and 0 <= value <= 1 for value in (x, y)):
        raise ValueError("x and y must be normalized values between 0 and 1")

    bounds = payload.get("bounds")
    if bounds in (None, "", []):
        normalized_bounds = None
    else:
        try:
            normalized_bounds = [float(value) for value in bounds]
        except (TypeError, ValueError) as exc:
            raise ValueError("bounds must contain numeric normalized values") from exc
        if len(normalized_bounds) != 4 or not all(
            math.isfinite(value) and 0 <= value <= 1 for value in normalized_bounds
        ):
            raise ValueError("bounds must be four normalized values between 0 and 1")

    booth_id = ":".join(
        [map_id, direction.lower(), hall or "unknown-hall", section, table, half]
    )
    booth = {
        "booth_id": booth_id,
        "map_id": map_id,
        "direction": direction,
        "hall": hall,
        "section": section,
        "table": table,
        "half": half,
        "x": x,
        "y": y,
        "bounds": normalized_bounds,
        "confidence": "manual",
        "source": "review",
    }
    existing = map_item.setdefault("booths", [])
    identity = (direction, hall, section, table, half)
    map_item["booths"] = [
        item
        for item in existing
        if (item.get("direction"), item.get("hall"), item.get("section"), item.get("table"), item.get("half")) != identity
    ] + [booth]
    calibration["status"] = "in_review"
    return booth


def command_import_artists(args: argparse.Namespace) -> int:
    event = _load_event_config(args.event)
    config = event_config_from_dict(event)
    parsed = read_artist_csv(Path(args.csv), args.event, config)
    manual_path = Path(args.manual) if args.manual else _manual_path(args.event)
    manual = read_manual_csv(manual_path, args.event) if manual_path.exists() else []
    merged = merge_records(parsed, manual)
    overrides_path = _overrides_path(args.event)
    overrides = read_json(overrides_path) if overrides_path.exists() else {"schema_version": SCHEMA_VERSION, "event_id": args.event, "records": []}
    merged = _apply_review_overrides(merged, overrides)
    write_json(event_dir(args.event) / "artists.json", [record.to_dict() for record in merged])
    write_json(overrides_path, overrides)
    candidates = sum(len(record.locations) for record in merged)
    unresolved = sum(
        1
        for record in merged
        for location in record.locations
        if location.status == "needs_review"
    )
    print(f"Imported {len(merged)} artist record(s), {candidates} location candidate(s)")
    print(f"Review required: {unresolved}")
    return 0


def _seed_bot_calibration(
    event: Dict[str, Any], calibration: Dict[str, Any], records: List[Any]
) -> tuple[int, List[str]]:
    """Add deterministic C108 cell anchors for newly imported bot booths."""
    maps = {item["map_id"]: item for item in event.get("maps", [])}
    existing = {
        (
            booth.get("direction"), booth.get("hall"), booth.get("section"),
            booth.get("table"), booth.get("half"),
        )
        for map_item in calibration.get("maps", [])
        for booth in map_item.get("booths", [])
    }
    seeded = 0
    missing: List[str] = []
    for record in records:
        for location in record.locations:
            if location.status != "accepted":
                continue
            identity = (
                location.direction, location.hall, location.section,
                location.table, location.half,
            )
            if identity in existing:
                continue
            booth = {
                "direction": location.direction,
                "section": location.section,
                "booth_code": format_booth_code(
                    location.direction, location.section, location.table, location.half
                ),
            }
            try:
                map_id = carry_over_map_id(booth, maps.values())
            except ValueError:
                missing.append(location.location_key)
                continue
            anchor = c108_anchor(map_id, location.section, location.table)
            map_item = maps.get(map_id, {})
            width = int(map_item.get("width") or 0)
            height = int(map_item.get("height") or 0)
            if anchor is None or not width or not height:
                missing.append(location.location_key)
                continue
            saved = _calibrate_booth(event, calibration, {
                "map_id": map_id,
                "direction": location.direction,
                "hall": location.hall,
                "section": location.section,
                "table": location.table,
                "half": location.half,
                "x": anchor[0] / width,
                "y": anchor[1] / height,
            })
            saved["confidence"] = "calibrated"
            saved["source"] = "c108-cell-calibration"
            existing.add(identity)
            seeded += 1
    return seeded, missing


def command_import_bot(args: argparse.Namespace) -> int:
    event = _load_event_config(args.event)
    artist_path = event_dir(args.event) / "artists.json"
    prior = read_json(artist_path) if artist_path.exists() else []
    records = read_bot_database(Path(args.db), args.event, prior)
    write_json(artist_path, [record.to_dict() for record in records])

    calibration = load_calibration(WORK_ROOT, args.event)
    seeded, missing = _seed_bot_calibration(event, calibration, records)
    write_json(event_dir(args.event) / "calibration.json", calibration)

    locations = sum(len(record.locations) for record in records)
    unresolved = sum(
        1 for record in records for location in record.locations
        if location.status == "needs_review"
    )
    print(f"Imported {len(records)} bot exhibitor(s), {locations} booth appearance(s)")
    print(f"Seeded {seeded} new booth calibration(s)")
    print(f"Review required: {unresolved}")
    if missing:
        print(f"Missing C108 map calibration: {len(missing)}")
        for key in missing:
            print(f"  - {key}")
        if not args.allow_missing_calibration:
            return 2
        print("Continuing with uncalibrated locations omitted from the public build")
    return 0


def _review_html(state: Dict[str, Any]) -> str:
    state_json = json.dumps(state, ensure_ascii=False).replace("</", "<\\/")
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comiket importer review</title><style>
body{font:14px system-ui,sans-serif;background:#101114;color:#eee;margin:0;padding:20px}main{max-width:1400px;margin:auto}
header{position:sticky;top:0;background:#101114;padding:12px 0;z-index:2;border-bottom:1px solid #333}h1{font-size:22px}
.summary{display:flex;gap:12px;flex-wrap:wrap}.pill{padding:8px 12px;background:#242730;border-radius:999px}
table{width:100%;border-collapse:collapse;margin-top:18px}th,td{border-bottom:1px solid #30333b;padding:8px;text-align:left;vertical-align:top}th{color:#9ed0ff}
input,select,button{background:#1e222b;color:#fff;border:1px solid #555;border-radius:5px;padding:6px}input{width:70px}button{cursor:pointer;margin:2px}.accepted{color:#8ee7aa}.needs_review{color:#ffd27d}.excluded,.rejected{color:#ff9a9a}.raw{max-width:360px;white-space:pre-wrap;color:#bbb;font-size:12px}.calibration{display:flex;gap:12px;overflow:auto;padding:12px 0}.map-card{min-width:300px;background:#1a1d24;border:1px solid #383d48;border-radius:8px;padding:10px}.map-preview{position:relative;background:#08090b;line-height:0}.map-preview img{width:100%;display:block;max-height:260px;object-fit:contain}.map-preview canvas{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.map-card label{display:inline-flex;gap:4px;align-items:center;margin-top:8px;font-size:11px}.map-card input{width:55px}.map-card small{display:block;color:#aaa;margin-top:8px}
</style></head><body><main><header><h1>Comiket importer review</h1><div id="summary"></div><p>Changes are saved to private work state on this localhost review server. Build remains blocked by unresolved records.</p></header><section id="calibration" class="calibration"></section><div id="app"></div></main>
<script>const initial=__STATE__;let state=initial;const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function all(){return state.artists.flatMap((a,ai)=>a.locations.map((l,li)=>({...l,ai,li,artist:a})));}
function drawCandidates(mapId){const map=state.calibration.maps.find((item)=>item.map_id===mapId),canvas=document.querySelector('[data-canvas="'+mapId+'"]'),image=document.querySelector('[data-image="'+mapId+'"]');if(!map||!canvas||!image)return;const candidates=map.suggestion?.booth_candidates?.candidates||[],rect=image.getBoundingClientRect(),ratio=window.devicePixelRatio||1;canvas.width=Math.max(1,Math.round(rect.width*ratio));canvas.height=Math.max(1,Math.round(rect.height*ratio));const context=canvas.getContext('2d');context.scale(ratio*rect.width/image.naturalWidth,ratio*rect.height/image.naturalHeight);context.strokeStyle='rgba(255,185,70,.55)';context.lineWidth=Math.max(1,image.naturalWidth/1600);candidates.forEach((candidate)=>{const [x,y,w,h]=candidate.bounds;context.strokeRect(x*image.naturalWidth,y*image.naturalHeight,w*image.naturalWidth,h*image.naturalHeight);});}
function renderCalibration(){const maps=state.calibration?.maps||[];document.querySelector('#calibration').innerHTML=maps.map((m)=>{const crop=m.crop||[0,0,1,1],candidateCount=m.suggestion?.booth_candidates?.count||0;return '<article class="map-card"><b>'+esc(m.map_id)+'</b> · page <input data-map="'+esc(m.map_id)+'" data-cal="page" value="'+esc(m.page)+'"><div class="crop-controls"><label>crop x <input data-map="'+esc(m.map_id)+'" data-cal="c0" value="'+esc(crop[0]??0)+'"></label><label>y <input data-map="'+esc(m.map_id)+'" data-cal="c1" value="'+esc(crop[1]??0)+'"></label><label>w <input data-map="'+esc(m.map_id)+'" data-cal="c2" value="'+esc(crop[2]??1)+'"></label><label>h <input data-map="'+esc(m.map_id)+'" data-cal="c3" value="'+esc(crop[3]??1)+'"></label></div><div class="map-preview" data-pick-map="'+esc(m.map_id)+'"><img data-image="'+esc(m.map_id)+'" src="/rendered/page-'+esc(m.page)+'.png" alt="Rendered PDF page"><canvas data-canvas="'+esc(m.map_id)+'"></canvas></div><p class="tip">Orange cells are advisory. Click the map to set a normalized booth point, then enter the label below.</p><label>x <input data-map="'+esc(m.map_id)+'" data-cal="x" value=""></label><label>y <input data-map="'+esc(m.map_id)+'" data-cal="y" value=""></label><label>dir <input data-map="'+esc(m.map_id)+'" data-booth="direction" placeholder="East"></label><label>hall <input data-map="'+esc(m.map_id)+'" data-booth="hall" placeholder="4"></label><label>section <input data-map="'+esc(m.map_id)+'" data-booth="section" placeholder="メ"></label><label>table <input data-map="'+esc(m.map_id)+'" data-booth="table" placeholder="40"></label><label>half <select data-map="'+esc(m.map_id)+'" data-booth="half"><option value="unknown">half…</option><option>a</option><option>b</option><option>ab</option></select></label><button data-save-booth="'+esc(m.map_id)+'">Save calibrated booth</button><div class="calibration-meta"><button data-save-map="'+esc(m.map_id)+'">Save crop/page</button><small>'+((m.booths||[]).length)+' calibrated booths · '+candidateCount+' advisory cell candidates</small></div></article>';}).join('');maps.forEach((m)=>{const image=document.querySelector('[data-image="'+m.map_id+'"]');if(image){image.onload=()=>drawCandidates(m.map_id);if(image.complete)drawCandidates(m.map_id);}});document.querySelectorAll('[data-save-map]').forEach((el)=>el.onclick=()=>saveCalibration(el.dataset.saveMap));document.querySelectorAll('[data-save-booth]').forEach((el)=>el.onclick=()=>saveBooth(el.dataset.saveBooth));document.querySelectorAll('[data-pick-map]').forEach((el)=>el.onclick=(event)=>pickPoint(el.dataset.pickMap,event));}
function pickPoint(mapId,event){const image=document.querySelector('[data-image="'+mapId+'"]'),rect=image?.getBoundingClientRect();if(!rect)return;const x=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width)),y=Math.max(0,Math.min(1,(event.clientY-rect.top)/rect.height));const set=(name,value)=>{const input=document.querySelector('[data-map="'+mapId+'"][data-cal="'+name+'"]');if(input)input.value=value.toFixed(6);};set('x',x);set('y',y);}
async function saveCalibration(mapId){const values={};document.querySelectorAll('[data-map="'+mapId+'"]').forEach((el)=>values[el.dataset.cal]=el.value);await fetch('/api/calibration',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({map_id:mapId,page:Number(values.page),crop:[0,1,2,3].map((i)=>Number(values['c'+i]))})});state=await (await fetch('/api/state')).json();renderCalibration();}
async function saveBooth(mapId){const payload={map_id:mapId};document.querySelectorAll('[data-map="'+mapId+'"][data-booth]').forEach((el)=>payload[el.dataset.booth]=el.value);document.querySelectorAll('[data-map="'+mapId+'"][data-cal]').forEach((el)=>payload[el.dataset.cal]=el.value);const response=await fetch('/api/booth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok){const body=await response.json().catch(()=>({}));alert(body.error||'Could not save booth');return;}state=await (await fetch('/api/state')).json();renderCalibration();}
function render(){const rows=all(),unresolved=rows.filter(x=>x.status==='needs_review').length,ready=state.readiness?.publish_ready;document.querySelector('#summary').innerHTML='<div class="summary"><span class="pill">Artists: '+state.artists.length+'</span><span class="pill">Candidates: '+rows.length+'</span><span class="pill">Unresolved: '+unresolved+'</span><span class="pill">Calibrated booths: '+(state.readiness?.calibrated_booths||0)+'</span><span class="pill">Publish: '+(ready?'ready':'blocked')+'</span><span class="pill">PDF: '+esc(state.event.source_pdf_sha256.slice(0,12))+'…</span></div>';
document.querySelector('#app').innerHTML='<table><thead><tr><th>Artist</th><th>Location</th><th>Raw source</th><th>Status/reason</th><th>Actions</th></tr></thead><tbody>'+rows.map((x,i)=>'<tr><td><b>'+esc(x.artist.display_name||x.artist.username)+'</b><br>@'+esc(x.artist.username)+'</td><td><input data-i="'+i+'" data-f="day" value="'+esc(x.day??'')+'" placeholder="day"><input data-i="'+i+'" data-f="direction" value="'+esc(x.direction||'')+'" placeholder="dir"><input data-i="'+i+'" data-f="section" value="'+esc(x.section||'')+'" placeholder="section"><input data-i="'+i+'" data-f="table" value="'+esc(x.table||'')+'" placeholder="table"><select data-i="'+i+'" data-f="half"><option>unknown</option><option'+(x.half==='a'?' selected':'')+'>a</option><option'+(x.half==='b'?' selected':'')+'>b</option><option'+(x.half==='ab'?' selected':'')+'>ab</option></select></td><td class="raw">'+esc(x.source_text)+'</td><td class="'+esc(x.status)+'">'+esc(x.status)+'<br>'+esc(x.reason)+'</td><td><button data-act="'+i+'" data-status="accepted">Accept</button><button data-act="'+i+'" data-status="rejected">Reject</button><button data-act="'+i+'" data-status="excluded">Exclude</button><button data-act="'+i+'" data-status="merge">Merge alias</button></td></tr>').join('')+'</tbody></table>';
document.querySelectorAll('[data-i]').forEach(el=>el.onchange=()=>{const row=rows[+el.dataset.i];row[el.dataset.f]=el.value;});document.querySelectorAll('[data-act]').forEach(el=>el.onclick=()=>act(Number(el.dataset.act),el.dataset.status));}
async function act(i,status){const rows=all(),row=rows[i];document.querySelectorAll('[data-i="'+i+'"]').forEach((el)=>row[el.dataset.f]=el.dataset.f==='day'?Number(el.value)||null:el.value);if(status==='merge'){row.reason=(row.reason?row.reason+',':'')+'merge-confirmed';status='accepted';}row.status=status;await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(row)});state=await (await fetch('/api/state')).json();render();}renderCalibration();render();</script></body></html>""".replace("__STATE__", state_json)


def _review_state(event_id: str) -> Dict[str, Any]:
    event = _load_event_config(event_id)
    artist_path = event_dir(event_id) / "artists.json"
    artists = read_json(artist_path) if artist_path.exists() else []
    calibration_path = event_dir(event_id) / "calibration.json"
    calibration = read_json(calibration_path) if calibration_path.exists() else {"maps": []}
    geometry_keys = {
        (booth.get("direction"), booth.get("hall"), booth.get("section"), booth.get("table"), booth.get("half"))
        for item in calibration.get("maps", [])
        for booth in item.get("booths", [])
    }
    locations = [location for artist in artists for location in artist.get("locations", [])]
    unresolved = [location for location in locations if location.get("status") == "needs_review"]
    missing_geometry = [
        location
        for location in locations
        if location.get("status") == "accepted"
        and (location.get("direction"), location.get("hall"), location.get("section"), location.get("table"), location.get("half")) not in geometry_keys
    ]
    return {
        "event": event,
        "artists": artists,
        "calibration": calibration,
        "readiness": {
            "unresolved": len(unresolved),
            "accepted": sum(location.get("status") == "accepted" for location in locations),
            "excluded": sum(location.get("status") in {"excluded", "rejected"} for location in locations),
            "calibrated_booths": len(geometry_keys),
            "missing_geometry": len(missing_geometry),
            "publish_ready": not unresolved and not missing_geometry,
        },
    }


class _ReviewHandler(http.server.BaseHTTPRequestHandler):
    event_id = ""

    def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            self._send(200, json.dumps(_review_state(self.event_id), ensure_ascii=False).encode())
            return
        if self.path.startswith("/rendered/"):
            filename = Path(self.path.removeprefix("/rendered/")).name
            rendered = event_dir(self.event_id) / "rendered" / filename
            if rendered.exists() and rendered.suffix == ".png":
                self._send(200, rendered.read_bytes(), "image/png")
                return
            self._send(404, b"{}")
            return
        html = _review_html(_review_state(self.event_id)).encode()
        self._send(200, html, "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send(400, json.dumps({"error": f"Invalid JSON: {exc}"}).encode())
            return
        if self.path == "/api/booth":
            try:
                path = event_dir(self.event_id) / "calibration.json"
                calibration = read_json(path)
                booth = _calibrate_booth(_load_event_config(self.event_id), calibration, payload)
                write_json(path, calibration)
                self._send(200, json.dumps({"ok": True, "booth": booth}, ensure_ascii=False).encode())
            except (FileNotFoundError, ValueError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode())
            return
        if self.path == "/api/calibration":
            path = event_dir(self.event_id) / "calibration.json"
            calibration = read_json(path)
            found = False
            for map_item in calibration.get("maps", []):
                if map_item.get("map_id") == payload.get("map_id"):
                    found = True
                    map_item["page"] = int(payload.get("page", map_item.get("page", 1)))
                    crop = payload.get("crop")
                    if crop is not None and (len(crop) != 4 or not all(isinstance(value, (int, float)) for value in crop)):
                        self._send(400, b'{"error":"crop must contain four numeric values"}')
                        return
                    map_item["crop"] = crop
                    calibration["status"] = "in_review"
            if not found:
                self._send(404, b'{"error":"Unknown calibration map"}')
                return
            write_json(path, calibration)
            self._send(200, b'{"ok":true}')
            return
        if self.path != "/api/review":
            self._send(404, b"{}")
            return
        path = event_dir(self.event_id) / "artists.json"
        artists = read_json(path)
        target = None
        for artist in artists:
            if artist.get("artist_key") == payload.get("artist_key"):
                for location in artist.get("locations", []):
                    if location.get("location_key") == payload.get("location_key"):
                        target = location
                        break
        if target is None:
            self._send(404, b"{}"); return
        for key in ("day", "direction", "hall", "section", "table", "half", "status", "reason"):
            if key in payload:
                target[key] = payload[key]
        write_json(path, artists)
        overrides_path = _overrides_path(self.event_id)
        overrides = read_json(overrides_path) if overrides_path.exists() else {"schema_version": SCHEMA_VERSION, "event_id": self.event_id, "records": []}
        clean = {key: payload.get(key) for key in ("artist_key", "location_key", "source_text", "source_field", "day", "direction", "hall", "section", "table", "half", "status", "reason") if key in payload}
        overrides["records"] = [item for item in overrides.get("records", []) if not (item.get("artist_key") == clean.get("artist_key") and item.get("location_key") == clean.get("location_key"))] + [clean]
        write_json(overrides_path, overrides)
        self._send(200, b'{"ok":true}')

    def log_message(self, *_args: object) -> None:
        return


def command_review(args: argparse.Namespace) -> int:
    state = _review_state(args.event)
    html_path = event_dir(args.event) / "review.html"
    html_path.write_text(_review_html(state), encoding="utf-8")
    print(f"Review UI: http://127.0.0.1:{args.port}/")
    if args.no_server:
        return 0
    handler = type("ReviewHandler", (_ReviewHandler,), {"event_id": args.event})
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    if args.open:
        threading.Timer(0.25, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}/")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _build_public(
    event_id: str,
    allow_unresolved: bool = False,
    carry_over_event: Optional[str] = None,
    allow_missing_calibration: bool = False,
) -> Dict[str, Any]:
    event = _load_event_config(event_id)
    calibration = load_calibration(WORK_ROOT, event_id)
    if carry_over_event:
        source_output = PUBLIC_ROOT / carry_over_event.lower()
        source_manifest = read_json(source_output / "manifest.json")
        source_booths = read_json(source_output / "booths.json")
        source_artists = read_json(source_output / "artists.json")
        target_manifest = {
            "event_id": event_id,
            "maps": event.get("maps", []),
        }
        # The target event config has map labels but not rendered dimensions;
        # init stored those dimensions in the private event manifest.
        target_manifest = _load_event_config(event_id)
        public_booth_list, public_artists = build_carry_over(
            source_manifest,
            source_booths,
            source_artists,
            target_manifest,
            require_target_calibration=event_id.upper() == "C108",
            target_calibration=calibration,
        )
        public_booths = {booth["booth_id"]: booth for booth in public_booth_list}
        event["data_status"] = "provisional-carry-over"
        event["data_notice"] = f"Preview data: booth assignments carried over from {carry_over_event.upper()} and not yet verified for {event_id.upper()}."
    else:
        public_artists = None
        public_booths = None
    artist_path = event_dir(event_id) / "artists.json"
    if not carry_over_event and not artist_path.exists():
        raise FileNotFoundError("Run import-artists first")
    artists = read_json(artist_path) if artist_path.exists() else []
    unresolved = [
        (artist.get("artist_key"), location)
        for artist in artists
        for location in artist.get("locations", [])
        if location.get("status") == "needs_review"
    ]
    if unresolved and not allow_unresolved and not carry_over_event:
        raise RuntimeError(f"Build blocked: {len(unresolved)} unresolved location record(s)")
    geometries = [booth for item in calibration.get("maps", []) for booth in item.get("booths", [])]
    by_key = {
        (booth.get("direction"), booth.get("hall"), booth.get("section"), booth.get("table"), booth.get("half")): booth
        for booth in geometries
    }
    skipped_missing_calibration = 0
    if not carry_over_event:
        public_artists = []
        public_booths = {}
    for artist in sorted(artists, key=lambda item: (item.get("username", "").lower(), item.get("artist_key", ""))):
        if carry_over_event:
            break
        public_locations = []
        for location in artist.get("locations", []):
            if location.get("status") != "accepted":
                continue
            key = (location.get("direction"), location.get("hall"), location.get("section"), location.get("table"), location.get("half"))
            geometry = by_key.get(key)
            if geometry is None:
                if not allow_missing_calibration:
                    raise RuntimeError(f"No calibrated booth geometry for {location.get('location_key')}")
                skipped_missing_calibration += 1
                continue
            booth_id = geometry["booth_id"]
            booth_code = format_booth_code(
                location.get("direction"),
                location.get("section"),
                location.get("table"),
                location.get("half", "unknown"),
            )
            public_location = {
                "day": location.get("day"),
                "map_id": geometry["map_id"],
                "booth_id": booth_id,
                "booth_code": booth_code,
            }
            public_locations.append(public_location)
            public_booths.setdefault(booth_id, {
                "booth_id": booth_id,
                "map_id": geometry["map_id"],
                "direction": geometry.get("direction"),
                "hall": geometry.get("hall"),
                "section": geometry.get("section"),
                "table": geometry.get("table"),
                "half": geometry.get("half"),
                "booth_code": geometry.get("booth_code") or booth_code,
                "x": geometry.get("x"), "y": geometry.get("y"),
                "bounds": geometry.get("bounds"), "artist_keys": [],
            })["artist_keys"].append(artist["artist_key"])
        if public_locations:
            public_locations.sort(key=lambda item: (item.get("day", 0), item.get("map_id", ""), item.get("booth_id", "")))
            public_artists.append({key: artist.get(key, 0 if key == "priority" else "") for key in ("artist_key", "user_id", "username", "display_name", "description", "profile_url", "avatar_url", "banner_url", "priority")} | {"locations": public_locations})
    maps = event.get("maps", [])
    days = event.get("days") or [{"id": f"day-{key}", "label": f"Day {key}"} for key in sorted(event.get("day_specs", {}), key=str)]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "name": event.get("name", event_id),
        "attribution": event.get("attribution", ""),
        "source_pdf_sha256": event.get("source_pdf_sha256", ""),
        "source_pdf": event.get("source_pdf_url", ""),
        "dates": event.get("dates", []),
        "maps": maps,
        "days": days,
        "generated_at": event.get("generated_at", ""),
    }
    if event.get("data_status"):
        manifest["data_status"] = event["data_status"]
        manifest["data_notice"] = event.get("data_notice", "")
    output = PUBLIC_ROOT / event_id.lower()
    output.mkdir(parents=True, exist_ok=True)
    _build_map_assets(event, event_dir(event_id), output)
    write_json(output / "manifest.json", manifest)
    for booth in public_booths.values():
        booth["artist_keys"] = sorted(set(booth["artist_keys"]))
    write_json(output / "booths.json", sorted(public_booths.values(), key=lambda item: (item["map_id"], item.get("section") or "", item.get("table") or "", item.get("half") or "")))
    write_json(output / "artists.json", public_artists)
    validate_public_event(output)
    index_path = PUBLIC_ROOT / "index.json"
    existing = read_json(index_path) if index_path.exists() else {"schema_version": SCHEMA_VERSION, "events": []}
    events = {item["event_id"]: item for item in existing.get("events", [])}
    events[event_id] = {"event_id": event_id, "name": manifest["name"], "manifest": f"events/{event_id.lower()}/manifest.json"}
    write_json(index_path, {"schema_version": SCHEMA_VERSION, "events": [events[key] for key in sorted(events)]})
    if skipped_missing_calibration:
        print(f"Skipped {skipped_missing_calibration} accepted location(s) without calibrated booth geometry")
    return manifest


def _build_map_assets(event: Dict[str, Any], source_dir: Path, output_dir: Path) -> None:
    """Convert complete rendered pages to the WebP assets referenced by a manifest."""
    maps_dir = output_dir / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    for map_item in event.get("maps", []):
        source = source_dir / "rendered" / f"page-{int(map_item['page'])}.png"
        target = maps_dir / f"{map_item['map_id']}.webp"
        if not source.exists():
            raise FileNotFoundError(f"Missing rendered page for {map_item['map_id']}: {source}")
        try:
            from PIL import Image  # type: ignore

            with Image.open(source) as image:
                image.save(target, "WEBP", quality=88, method=6)
            continue
        except ImportError:
            pass
        converter = shutil.which("cwebp")
        if converter is None:
            raise RuntimeError("Install Pillow or cwebp to build public map assets")
        result = subprocess.run([converter, "-quiet", "-q", "88", str(source), "-o", str(target)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr or "cwebp failed")


def command_build(args: argparse.Namespace) -> int:
    manifest = _build_public(
        args.event,
        args.allow_unresolved,
        args.carry_over_event,
        args.allow_missing_calibration,
    )
    print(f"Built public event {manifest['event_id']} at {PUBLIC_ROOT / args.event.lower()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m comiket_import")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="inspect and render an event PDF")
    init.add_argument("--event", required=True); init.add_argument("--pdf", required=True)
    init.add_argument("--config"); init.add_argument("--dpi", type=int, default=200)
    init.set_defaults(func=command_init)
    imp = commands.add_parser("import-artists", help="import an X-following CSV")
    imp.add_argument("--event", required=True); imp.add_argument("--csv", required=True); imp.add_argument("--manual")
    imp.set_defaults(func=command_import_artists)
    bot = commands.add_parser("import-bot", help="import reviewed exhibitors from the Nyaa bot database")
    bot.add_argument("--event", required=True); bot.add_argument("--db", required=True)
    bot.add_argument(
        "--allow-missing-calibration",
        action="store_true",
        help="continue when accepted locations lack calibrated map geometry",
    )
    bot.set_defaults(func=command_import_bot)
    review = commands.add_parser("review", help="serve the local review UI")
    review.add_argument("--event", required=True); review.add_argument("--port", type=int, default=8765)
    review.add_argument("--no-server", action="store_true"); review.add_argument("--open", action="store_true")
    review.set_defaults(func=command_review)
    build = commands.add_parser("build", help="validate and build public event JSON")
    build.add_argument("--event", required=True)
    build.add_argument("--allow-unresolved", action="store_true")
    build.add_argument(
        "--allow-missing-calibration",
        action="store_true",
        help="skip accepted locations that do not have calibrated map geometry",
    )
    build.add_argument("--carry-over-event", help="explicitly seed this event from a previous public event as provisional data")
    build.set_defaults(func=command_build)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
