"""Import reviewed Comiket exhibitors from the Nyaa Discord bot database.

The Discord bot is the operational source of truth for the current list.  This
adapter intentionally imports only rows that the bot marked as exhibitors for
the requested event; unrelated saved links and rejected profiles stay out of
the map data.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .models import ArtistRecord, LocationCandidate
from .normalize import (
    artist_key,
    normalize_direction,
    normalize_half,
    normalize_priority,
    normalize_section,
    normalize_table,
    normalize_text,
    normalize_username,
)


_PROFILE_SUFFIX_RE = re.compile(
    r"\s*\(@[^\n)]*(?:\)|\.\.\.)?\s*(?:on X)?\s*$",
    re.IGNORECASE,
)
_HANDLE_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})\b")
_DISCORD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~])")
_RESERVED_X_ROUTES = {
    "compose",
    "explore",
    "home",
    "i",
    "intent",
    "messages",
    "notifications",
    "search",
    "settings",
    "share",
}


def _unescape_discord_markdown(value: object) -> str:
    return _DISCORD_ESCAPE_RE.sub(r"\1", str(value or ""))


def _username_from_url(url: object, author: object) -> str:
    parsed = urlparse(normalize_text(url))
    segments = [segment for segment in parsed.path.split("/") if segment]
    if parsed.netloc.lower() in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"} and segments:
        candidate = normalize_username(segments[0])
        if candidate.casefold() not in _RESERVED_X_ROUTES:
            return candidate
    author_text = normalize_text(author)
    handle_match = _HANDLE_RE.search(author_text)
    if handle_match:
        return normalize_username(handle_match.group(1))
    return normalize_username(author)


def _body_lines(body: object) -> List[str]:
    body_text = _unescape_discord_markdown(body)
    return [normalize_text(line) for line in body_text.splitlines() if normalize_text(line)]


def _display_name(username: str, author: object, body: object, existing: Dict[str, Any]) -> str:
    author_text = normalize_text(author)
    author_name = _PROFILE_SUFFIX_RE.sub("", author_text).strip()
    if author_name and normalize_username(author_name) != username:
        return author_name
    lines = _body_lines(body)
    if lines and lines[0].casefold() != "manual c108 profile metadata":
        candidate = _PROFILE_SUFFIX_RE.sub("", lines[0]).strip()
        if candidate:
            return candidate
    return normalize_text(existing.get("display_name")) or author_text or username


def _description(body: object, existing: Dict[str, Any]) -> str:
    preserved = normalize_text(_unescape_discord_markdown(existing.get("description")))
    if preserved:
        return preserved
    lines = _body_lines(body)
    if not lines:
        return ""
    if lines[0].casefold() == "manual c108 profile metadata":
        lines = [line for line in lines[1:] if not line.casefold().startswith("original name:")]
    else:
        lines = lines[1:]
    return "\n".join(lines)


def _existing_by_username(records: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        normalize_username(record.get("username")): record
        for record in records
        if normalize_username(record.get("username"))
    }


def read_bot_database(
    path: Path,
    event_id: str,
    existing_records: Iterable[Dict[str, Any]] = (),
) -> List[ArtistRecord]:
    """Read the bot DB in read-only mode and return its reviewed exhibitors."""
    database = path.expanduser().resolve()
    if not database.exists():
        raise FileNotFoundError(f"Discord bot database not found: {database}")

    existing = _existing_by_username(existing_records)
    records: Dict[str, ArtistRecord] = {}
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT
                a.id AS analysis_id,
                a.url,
                a.author,
                a.body,
                a.priority,
                l.day,
                l.direction,
                l.hall,
                l.section,
                l.space_no,
                l.half,
                l.booth,
                l.confidence,
                l.source_text
            FROM analyses AS a
            LEFT JOIN locations AS l ON l.analysis_id = a.id
            WHERE lower(a.event_code) = lower(?) AND a.is_exhibitor = 1
            ORDER BY a.id, l.id
            """,
            (event_id,),
        ).fetchall()
    finally:
        connection.close()

    for row in rows:
        username = _username_from_url(row["url"], row["author"])
        if not username:
            continue
        prior = existing.get(username, {})
        key = artist_key(prior.get("user_id", ""), username)
        record = records.get(username)
        if record is None:
            record = ArtistRecord(
                event_id=event_id,
                artist_key=key,
                user_id=normalize_text(prior.get("user_id")),
                username=username,
                display_name=_display_name(username, row["author"], row["body"], prior),
                description=_description(row["body"], prior),
                profile_url=f"https://x.com/{username}",
                avatar_url=normalize_text(prior.get("avatar_url")),
                banner_url=normalize_text(prior.get("banner_url")),
                priority=normalize_priority(row["priority"]),
            )
            records[username] = record
        else:
            # The current DB value is authoritative, including an intentional
            # downgrade from 10/5 to 0.
            record.priority = normalize_priority(row["priority"])

        day: Optional[int]
        try:
            day = int(row["day"]) if row["day"] is not None else None
        except (TypeError, ValueError):
            day = None
        direction = normalize_direction(row["direction"])
        hall = normalize_text(row["hall"]) or None
        section = normalize_section(row["section"])
        table = normalize_table(row["space_no"])
        half = normalize_half(row["half"])
        complete = (
            day is not None
            and direction in {"East", "West", "South"}
            and section is not None
            and table is not None
            and half != "unknown"
        )
        location = LocationCandidate(
            event_id=event_id,
            artist_key=key,
            username=username,
            display_name=record.display_name,
            day=day,
            direction=direction,
            hall=hall,
            section=section,
            table=table,
            half=half,
            confidence=normalize_text(row["confidence"]) or "reviewed",
            status="accepted" if complete else "needs_review",
            reason="bot-database-sync" if complete else "bot-database-sync,incomplete-location",
            source_text=normalize_text(row["source_text"] or row["booth"] or row["body"]),
            source_field="bot-database",
            source="bot-database",
        )
        if not any(item.location_key == location.location_key for item in record.locations):
            record.locations.append(location)

    return sorted(records.values(), key=lambda record: (record.username.casefold(), record.artist_key))
