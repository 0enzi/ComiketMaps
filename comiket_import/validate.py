"""Validation for the generated public event contract.

The importer validates both the checked-in JSON Schemas and the cross-file
relationships that JSON Schema cannot express (day/map/booth references and
stable artist appearances).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict

from .models import read_json


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas"


def _validate_schema(filename: str, value: Any) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return
    schema = read_json(SCHEMA_ROOT / filename)
    try:
        jsonschema.validate(value, schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"{filename}: {exc.message}") from exc


def _coordinate_is_valid(value: Any, size: int) -> bool:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return False
    # New calibration stores normalized points; the C107 migration retains
    # pixel points. Accept either representation while checking both bounds.
    return 0 <= value <= 1 or (size > 0 and 0 <= value <= size)


def validate_public_event(path: Path) -> None:
    manifest = read_json(path / "manifest.json")
    booths = read_json(path / "booths.json")
    artists = read_json(path / "artists.json")
    _validate_schema("event-manifest.schema.json", manifest)
    _validate_schema("booths.schema.json", booths)
    _validate_schema("artists.schema.json", artists)

    required = {"schema_version", "event_id", "name", "maps", "days", "generated_at"}
    missing = required - set(manifest)
    if missing:
        raise ValueError(f"Manifest missing fields: {sorted(missing)}")

    maps = manifest["maps"]
    map_ids = {item.get("map_id") for item in maps}
    if None in map_ids or len(map_ids) != len(maps):
        raise ValueError("Manifest map IDs must be unique")
    map_by_id = {item["map_id"]: item for item in maps}
    for map_item in maps:
        if not isinstance(map_item.get("page"), int) or map_item["page"] < 1:
            raise ValueError(f"Invalid PDF page for map {map_item.get('map_id')}")
        if not isinstance(map_item.get("width"), int) or map_item["width"] <= 0:
            raise ValueError(f"Invalid map width for {map_item.get('map_id')}")
        if not isinstance(map_item.get("height"), int) or map_item["height"] <= 0:
            raise ValueError(f"Invalid map height for {map_item.get('map_id')}")

    days = manifest["days"]
    day_ids = {str(item.get("id")) for item in days}
    day_numbers = {int(item["number"]) for item in days if item.get("number") is not None}
    if None in day_ids or len(day_ids) != len(days):
        raise ValueError("Manifest day IDs must be unique")
    if len(day_numbers) != len(days):
        raise ValueError("Manifest day numbers must be unique")

    booth_ids = {booth.get("booth_id") for booth in booths}
    if None in booth_ids or len(booth_ids) != len(booths):
        raise ValueError("Booth IDs must be unique")
    booth_by_id = {booth["booth_id"]: booth for booth in booths}
    for booth in booths:
        map_item = map_by_id.get(booth.get("map_id"))
        if map_item is None:
            raise ValueError(f"Unknown map reference: {booth.get('map_id')}")
        if booth.get("half") not in {"a", "b", "ab", "unknown"}:
            raise ValueError(f"Invalid booth half: {booth.get('booth_id')}")
        if not _coordinate_is_valid(booth.get("x"), map_item["width"]):
            raise ValueError(f"Invalid booth x coordinate: {booth.get('booth_id')}")
        if not _coordinate_is_valid(booth.get("y"), map_item["height"]):
            raise ValueError(f"Invalid booth y coordinate: {booth.get('booth_id')}")
        bounds = booth.get("bounds")
        if bounds is not None and (
            not isinstance(bounds, list)
            or len(bounds) != 4
            or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in bounds)
        ):
            raise ValueError(f"Invalid booth bounds: {booth.get('booth_id')}")

    artist_keys = [artist.get("artist_key") for artist in artists]
    if None in artist_keys or len(artist_keys) != len(set(artist_keys)):
        raise ValueError("Artist keys must be unique")
    allowed_artist_fields = {
        "artist_key", "user_id", "username", "display_name", "description",
        "profile_url", "avatar_url", "banner_url", "priority", "locations",
    }
    appearance_ids = set()
    for artist in artists:
        if not str(artist.get("artist_key", "")).startswith(("x:", "xhandle:")):
            raise ValueError(f"Invalid artist identity: {artist.get('artist_key')}")
        private_fields = set(artist) - allowed_artist_fields
        if private_fields:
            raise ValueError(f"Private artist fields leaked: {sorted(private_fields)}")
        if artist.get("priority", 0) not in {0, 5, 10}:
            raise ValueError(f"Invalid artist priority: {artist.get('artist_key')}")
        for location in artist.get("locations", []):
            if set(location) != {"day", "map_id", "booth_id", "booth_code"}:
                raise ValueError(f"Public location has unexpected/private fields: {sorted(set(location))}")
            day = location.get("day")
            if not isinstance(day, int) or day not in day_numbers:
                raise ValueError(f"Unknown day reference: {day}")
            booth = booth_by_id.get(location.get("booth_id"))
            if booth is None:
                raise ValueError(f"Unknown booth reference: {location.get('booth_id')}")
            if location.get("map_id") not in map_by_id:
                raise ValueError(f"Unknown map reference: {location.get('map_id')}")
            if booth["map_id"] != location["map_id"]:
                raise ValueError(f"Location map disagrees with booth: {location.get('booth_id')}")
            appearance_id = f"{manifest['event_id']}:{artist['artist_key']}:{day}:{location['booth_id']}"
            if appearance_id in appearance_ids:
                raise ValueError(f"Duplicate artist appearance: {appearance_id}")
            appearance_ids.add(appearance_id)

    for booth in booths:
        artist_keys_at_booth = booth.get("artist_keys")
        if artist_keys_at_booth is not None:
            if len(artist_keys_at_booth) != len(set(artist_keys_at_booth)):
                raise ValueError(f"Duplicate artist at booth: {booth['booth_id']}")
            if not set(artist_keys_at_booth).issubset(set(artist_keys)):
                raise ValueError(f"Booth references an unknown artist: {booth['booth_id']}")
