"""PDF inspection, complete-page rendering, and calibration state.

The official Comiket maps are image-only Illustrator PDFs.  Rendering the
complete page is intentional: ``pdfimages`` exposes the hundreds of raster
fragments that make up a page, rather than the usable map.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import MapSpec, write_json
from .calibration import suggest_calibration


DEFAULT_C107_MAPS = [
    {"map_id": "east-4-6", "label": "East 4–6", "page": 1},
    {"map_id": "east-7-8", "label": "East 7–8", "page": 2},
    {"map_id": "south-1-2", "label": "South 1–2", "page": 3},
    {"map_id": "west-1-2", "label": "West 1–2", "page": 4},
]


@dataclass
class PdfInfo:
    pages: int
    width_points: float
    height_points: float
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required command is not installed: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"{args[0]} failed: {exc.output.strip()}") from exc


def inspect_pdf(pdf_path: Path) -> PdfInfo:
    output = _command("pdfinfo", str(pdf_path))
    values: Dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    page_size = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", values.get("Page size", ""))[:2]]
    if len(page_size) != 2:
        raise ValueError("Could not read PDF page dimensions from pdfinfo")
    return PdfInfo(
        pages=int(values.get("Pages", "0")),
        width_points=page_size[0],
        height_points=page_size[1],
        sha256=sha256_file(pdf_path),
    )


def render_pdf(pdf_path: Path, output_dir: Path, dpi: int = 200) -> List[Path]:
    """Render every complete page at a fixed DPI using Poppler."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    _command(
        "pdftoppm",
        "-png",
        "-r",
        str(dpi),
        str(pdf_path),
        str(prefix),
    )
    return sorted(output_dir.glob("page-*.png"))


def map_specs(config: Dict[str, Any], pages: int) -> List[MapSpec]:
    configured = config.get("maps")
    if not configured:
        if str(config.get("event_id", "")).upper() == "C107":
            configured = DEFAULT_C107_MAPS
        else:
            configured = [
                {"map_id": f"page-{page}", "label": f"Page {page}", "page": page}
                for page in range(1, pages + 1)
            ]
    result = []
    for item in configured:
        page = int(item["page"])
        result.append(
            MapSpec(
                map_id=str(item["map_id"]),
                label=str(item.get("label", item["map_id"])),
                page=page,
                asset=f"maps/{item['map_id']}.webp",
                width=int(item.get("width", 0)),
                height=int(item.get("height", 0)),
                crop=tuple(item["crop"]) if item.get("crop") else None,
            )
        )
    return result


def init_event(
    event_id: str,
    pdf_path: Path,
    work_root: Path,
    config: Optional[Dict[str, Any]] = None,
    dpi: int = 200,
) -> Dict[str, Any]:
    config = dict(config or {})
    config.setdefault("event_id", event_id)
    config.setdefault("event_code", event_id)
    info = inspect_pdf(pdf_path)
    specs = map_specs(config, info.pages)
    event_dir = work_root / "events" / event_id.lower()
    rendered_dir = event_dir / "rendered"
    event_dir.mkdir(parents=True, exist_ok=True)
    previous_event_path = event_dir / "event.json"
    previous_event = json.loads(previous_event_path.read_text(encoding="utf-8")) if previous_event_path.exists() else {}
    shutil.copy2(pdf_path, event_dir / "source.pdf")
    pages = render_pdf(pdf_path, rendered_dir, dpi=dpi)
    for spec in specs:
        if spec.page < 1 or spec.page > len(pages):
            raise ValueError(f"Map {spec.map_id} points to missing PDF page {spec.page}")
        spec.width = _png_dimension(pages[spec.page - 1], 0)
        spec.height = _png_dimension(pages[spec.page - 1], 1)
    event = {
        "event_id": event_id,
        "event_code": str(config.get("event_code", event_id)),
        "name": config.get("name", event_id),
        "dates": config.get("dates", []),
        "days": config.get("days", []),
        "day_specs": config.get("day_specs", {}),
        "source_pdf_url": config.get("source_pdf_url", ""),
        "attribution": config.get(
            "attribution",
            "Map source: Comiket official event map; derived image pending redistribution confirmation.",
        ),
        "source_pdf": str(pdf_path),
        "source_pdf_sha256": info.sha256,
        "generated_at": previous_event.get("generated_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "pdf": asdict(info),
        "maps": [spec.to_dict() for spec in specs],
        "render_dpi": dpi,
    }
    write_json(event_dir / "event.json", event)
    calibration_maps = []
    for spec in specs:
        calibration_maps.append(
            {
                "map_id": spec.map_id,
                "page": spec.page,
                "crop": spec.crop,
                "booths": [],
                "regions": [],
                "evidence": [],
                "suggestion": suggest_calibration(pages[spec.page - 1]),
            }
        )
    write_json(
        event_dir / "calibration.json",
        {
            "schema_version": "1.0.0",
            "event_id": event_id,
            "source_pdf_sha256": info.sha256,
            "status": "unreviewed",
            "maps": calibration_maps,
        },
    )
    return event


def _png_dimension(path: Path, axis: int) -> int:
    # PNG header is fixed-width and avoids requiring Pillow for initialization.
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        return 0
    return int.from_bytes(header[16 + axis * 4 : 20 + axis * 4], "big")


def load_event(work_root: Path, event_id: str) -> Dict[str, Any]:
    return json.loads(
        (work_root / "events" / event_id.lower() / "event.json").read_text(
            encoding="utf-8"
        )
    )


def load_calibration(work_root: Path, event_id: str) -> Dict[str, Any]:
    event_dir = work_root / "events" / event_id.lower()
    calibration = json.loads((event_dir / "calibration.json").read_text(encoding="utf-8"))
    event = load_event(work_root, event_id)
    if calibration.get("source_pdf_sha256") != event.get("source_pdf_sha256"):
        raise ValueError("Calibration is stale: source PDF hash changed")
    return calibration
