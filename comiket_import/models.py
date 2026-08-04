"""Small, dependency-free data contracts for the importer and public viewer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = "1.0.0"


@dataclass
class LocationCandidate:
    event_id: str
    artist_key: str
    username: str
    display_name: str
    day: Optional[int]
    direction: Optional[str]
    hall: Optional[str]
    section: Optional[str]
    table: Optional[str]
    half: str
    confidence: str
    status: str = "needs_review"
    reason: str = ""
    source_text: str = ""
    source_field: str = ""
    source: str = "parser"

    @property
    def location_key(self) -> str:
        values = (
            self.event_id,
            str(self.day) if self.day is not None else "unknown-day",
            self.direction or "unknown-direction",
            self.hall or "unknown-hall",
            self.section or "unknown-section",
            self.table or "unknown-table",
            self.half or "unknown",
        )
        return ":".join(values)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["location_key"] = self.location_key
        return value


@dataclass
class ArtistRecord:
    event_id: str
    artist_key: str
    user_id: str
    username: str
    display_name: str
    description: str = ""
    profile_url: str = ""
    avatar_url: str = ""
    banner_url: str = ""
    locations: List[LocationCandidate] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["locations"] = [location.to_dict() for location in self.locations]
        return value


@dataclass
class BoothGeometry:
    booth_id: str
    map_id: str
    direction: Optional[str]
    hall: Optional[str]
    section: Optional[str]
    table: Optional[str]
    half: str
    x: float
    y: float
    bounds: Optional[Tuple[float, float, float, float]] = None
    confidence: str = "manual"
    source: str = "calibration"

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        if self.bounds is not None:
            value["bounds"] = list(self.bounds)
        return value


@dataclass
class MapSpec:
    map_id: str
    label: str
    page: int
    asset: str
    width: int = 0
    height: int = 0
    crop: Optional[Tuple[float, float, float, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        if self.crop is not None:
            value["crop"] = list(self.crop)
        return value


@dataclass
class EventManifest:
    event_id: str
    name: str
    attribution: str
    source_pdf_sha256: str
    maps: List[MapSpec]
    days: List[Dict[str, Any]]
    generated_at: str
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "name": self.name,
            "attribution": self.attribution,
            "source_pdf_sha256": self.source_pdf_sha256,
            "maps": [item.to_dict() for item in self.maps],
            "days": self.days,
            "generated_at": self.generated_at,
        }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
