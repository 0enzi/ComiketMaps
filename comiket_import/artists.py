"""CSV/manual artist import built around the existing Comiket parser."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from parser import DaySpec, EventConfig, parse_comiket_bio

from .models import ArtistRecord, LocationCandidate
from .normalize import (
    artist_key,
    normalize_direction,
    normalize_half,
    normalize_priority,
    normalize_section,
    normalize_table,
    normalize_text,
)


_EVENT_CODE_RE = re.compile(r"\bC\d{3}\b", re.IGNORECASE)
_EXPLICIT_HALF_RE = re.compile(r"\d{1,3}\s*\\?[-/]?\s*([aAbB]{1,2})(?![A-Za-z])")


def event_config_from_dict(value: Dict[str, object]) -> EventConfig:
    day_specs = value.get("day_specs", {})

    def make_day(day_number: int) -> DaySpec:
        item = day_specs[str(day_number)] if isinstance(day_specs, dict) else {}
        return DaySpec(
            int(item.get("month", 1)),
            int(item.get("day", 1)),
            str(item.get("weekday_kanji", "")),
        )

    all_days = {
        int(day_number): make_day(int(day_number))
        for day_number in (day_specs.keys() if isinstance(day_specs, dict) else [])
    }
    day1 = all_days.get(1, DaySpec(1, 1, ""))
    day2 = all_days.get(2, day1)
    return EventConfig(
        event_code=str(value["event_code"]),
        day1=day1,
        day2=day2,
        days=all_days or None,
    )


def _event_conflict(text: str, event_code: str) -> bool:
    mentioned = {item.upper() for item in _EVENT_CODE_RE.findall(text or "")}
    return bool(mentioned and event_code.upper() not in mentioned)


def _explicit_half(source_text: str, table: Optional[str] = None) -> str:
    text = source_text or ""
    if table:
        escaped_table = re.escape(str(table).strip())
        match = re.search(
            rf"(?<!\d){escaped_table}\s*\\?[-/]?\s*([aAbB]{{1,2}})(?![A-Za-z])",
            text,
        )
    else:
        match = _EXPLICIT_HALF_RE.search(text)
    return normalize_half(match.group(1)) if match else "unknown"


def _candidate_from_location(
    event_id: str,
    event_config: EventConfig,
    user_id: str,
    username: str,
    display_name: str,
    location: object,
    source_text: str,
    source_field: str,
) -> LocationCandidate:
    conflict = _event_conflict(source_text, event_config.event_code)
    half = _explicit_half(source_text, getattr(location, "table", None))
    reason_parts = []
    status = "accepted"
    if conflict:
        status = "needs_review"
        reason_parts.append("event-code-conflict")
    if location.day is None or not location.section or not location.table:
        status = "needs_review"
        reason_parts.append("incomplete-location")
    if half == "unknown":
        status = "needs_review"
        reason_parts.append("unknown-half")
    if location.confidence != "high":
        status = "needs_review"
        reason_parts.append(f"confidence-{location.confidence}")

    return LocationCandidate(
        event_id=event_id,
        artist_key=artist_key(user_id, username),
        username=username,
        display_name=display_name,
        day=location.day,
        direction=location.direction,
        hall=getattr(location, "hall", None),
        section=normalize_section(location.section),
        table=normalize_table(location.table),
        half=half,
        confidence=location.confidence,
        status=status,
        reason=",".join(reason_parts),
        source_text=source_text,
        source_field=source_field,
    )


def _parse_profile(event_id: str, event_config: EventConfig, row: Dict[str, str]) -> ArtistRecord:
    user_id = normalize_text(row.get("User ID", row.get("user_id", "")))
    username = normalize_text(row.get("Username", row.get("username", "")))
    display_name = normalize_text(row.get("Name", row.get("display_name", "")))
    bio = row.get("Bio", row.get("bio", "")) or ""
    name_result = parse_comiket_bio(
        display_name, event_config, user_id, username, "name"
    )
    bio_result = parse_comiket_bio(bio, event_config, user_id, username, "bio")

    locations: List[LocationCandidate] = []
    for result, source_text in ((name_result, display_name), (bio_result, bio)):
        for location in result.locations:
            locations.append(
                _candidate_from_location(
                    event_id,
                    event_config,
                    user_id,
                    username,
                    display_name,
                    location,
                    source_text,
                    location.source_field,
                )
            )

    # Keep the source parser's location de-duplication, then flag conflicts that
    # still contain multiple distinct locations for one artist and day.
    deduped: Dict[Tuple[object, ...], LocationCandidate] = {}
    for location in locations:
        key = (
            location.day,
            location.direction,
            location.hall,
            location.section,
            location.table,
            location.half,
        )
        deduped.setdefault(key, location)
    locations = list(deduped.values())
    by_day: Dict[Optional[int], List[LocationCandidate]] = {}
    for location in locations:
        by_day.setdefault(location.day, []).append(location)
    for day_locations in by_day.values():
        if len(day_locations) > 1:
            for location in day_locations:
                if "multiple-locations-same-day" not in location.reason:
                    location.reason = ",".join(
                        part for part in (location.reason, "multiple-locations-same-day") if part
                    )
                location.status = "needs_review"

    return ArtistRecord(
        event_id=event_id,
        artist_key=artist_key(user_id, username),
        user_id=user_id,
        username=username,
        display_name=display_name,
        description=normalize_text(bio),
        profile_url=normalize_text(row.get("Profile URL", row.get("profile_url", ""))),
        avatar_url=normalize_text(row.get("Avatar URL", row.get("avatar_url", ""))),
        banner_url=normalize_text(
            row.get("Profile Banner URL", row.get("banner_url", ""))
        ),
        priority=normalize_priority(row.get("Priority", row.get("priority", ""))),
        locations=locations,
    )


def read_artist_csv(path: Path, event_id: str, event_config: EventConfig) -> List[ArtistRecord]:
    records: Dict[str, ArtistRecord] = {}
    row_signatures: Dict[Tuple[str, ...], LocationCandidate] = {}
    seen_rows = set()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            parsed = _parse_profile(event_id, event_config, row)
            existing = records.get(parsed.artist_key)
            if existing is None:
                records[parsed.artist_key] = parsed
                existing = parsed
            else:
                for field_name in ("username", "display_name", "description", "profile_url", "avatar_url", "banner_url"):
                    if getattr(parsed, field_name) and not getattr(existing, field_name):
                        setattr(existing, field_name, getattr(parsed, field_name))
                existing.priority = max(existing.priority, parsed.priority)

            row_signature = tuple(
                normalize_text(row.get(column, ""))
                for column in ("User ID", "Username", "Name", "Bio")
            )
            duplicate_row = row_signature in seen_rows
            for location in parsed.locations:
                location_signature = row_signature + (
                    str(location.day), location.direction or "", location.hall or "",
                    location.section or "", location.table or "", location.half,
                )
                duplicate = duplicate_row or location_signature in row_signatures
                if duplicate:
                    prior = row_signatures.get(location_signature) or row_signatures.get(row_signature)
                    for candidate in (prior, location):
                        if candidate is None:
                            continue
                        candidate.status = "needs_review"
                        candidate.reason = ",".join(
                            part for part in (candidate.reason, "duplicate-csv-row") if part
                        )
                row_signatures[location_signature] = location
                if not any(item.location_key == location.location_key for item in existing.locations):
                    existing.locations.append(location)
            seen_rows.add(row_signature)
    return sorted(records.values(), key=lambda record: (record.username.lower(), record.artist_key))


def read_manual_csv(path: Path, event_id: str) -> List[ArtistRecord]:
    grouped: Dict[str, ArtistRecord] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            user_id = normalize_text(row.get("user_id", row.get("User ID", "")))
            username = normalize_text(row.get("username", row.get("Username", "")))
            display_name = normalize_text(row.get("display_name", row.get("Name", "")))
            key = artist_key(user_id, username)
            record = grouped.setdefault(
                key,
                ArtistRecord(
                    event_id=event_id,
                    artist_key=key,
                    user_id=user_id,
                    username=username,
                    display_name=display_name,
                ),
            )
            record.priority = max(
                record.priority,
                normalize_priority(row.get("priority", row.get("Priority", ""))),
            )
            location = LocationCandidate(
                event_id=event_id,
                artist_key=key,
                username=username,
                display_name=display_name,
                day=int(row["day"]) if row.get("day") else None,
                direction=normalize_direction(row.get("direction")),
                hall=normalize_text(row.get("hall")) or None,
                section=normalize_section(row.get("section")),
                table=normalize_table(row.get("table")),
                half=normalize_half(row.get("half")),
                confidence="high",
                status="accepted" if row.get("action", "accept") != "exclude" else "excluded",
                reason=(
                    "manual-replace"
                    if row.get("action", "accept").lower() in {"replace", "override"}
                    else "manual-correction"
                ),
                source_text=row.get("source_text", ""),
                source_field="manual",
                source="manual",
            )
            if location.half == "unknown":
                location.status = "needs_review"
                location.reason += ",unknown-half"
            record.locations.append(location)
    return list(grouped.values())


def merge_records(
    parsed: Iterable[ArtistRecord], manual: Iterable[ArtistRecord]
) -> List[ArtistRecord]:
    records: Dict[str, ArtistRecord] = {record.artist_key: record for record in parsed}
    for correction in manual:
        existing = records.get(correction.artist_key)
        if existing is None:
            records[correction.artist_key] = correction
            continue
        if any("manual-replace" in location.reason for location in correction.locations):
            existing.locations = list(correction.locations)
        else:
            existing.locations = [
                location
                for location in existing.locations
                if not any(
                    location.day == replacement.day
                    for replacement in correction.locations
                )
            ] + correction.locations
        for field_name in ("username", "display_name"):
            value = getattr(correction, field_name)
            if value:
                setattr(existing, field_name, value)
        existing.priority = max(existing.priority, correction.priority)
    return sorted(records.values(), key=lambda record: (record.username.lower(), record.artist_key))
