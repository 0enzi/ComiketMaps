"""Normalization shared by CSV parsing, review corrections, and joins."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


_DIRECTION_MAP = {"東": "East", "西": "West", "南": "South"}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).strip()


def normalize_username(value: object) -> str:
    return normalize_text(value).lstrip("@").lower()


def normalize_direction(value: object) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return _DIRECTION_MAP.get(normalized, normalized.title())


def normalize_section(value: object) -> Optional[str]:
    normalized = normalize_text(value)
    return normalized or None


def normalize_table(value: object) -> Optional[str]:
    normalized = normalize_text(value)
    if not normalized:
        return None
    match = re.search(r"\d{1,3}", normalized)
    return match.group(0).zfill(2) if match else normalized


def normalize_half(value: object) -> str:
    normalized = normalize_text(value).lower()
    return normalized if normalized in {"a", "b", "ab"} else "unknown"


def normalize_priority(value: object) -> int:
    normalized = normalize_text(value).lower()
    if normalized in {"10", "10.0", "!!"}:
        return 10
    if normalized in {"5", "5.0", "!"}:
        return 5
    return 0


def artist_key(user_id: object, username: object) -> str:
    normalized_id = normalize_text(user_id)
    if normalized_id and normalized_id.isdigit() and normalized_id != "0":
        return f"x:{normalized_id}"
    return f"xhandle:{normalize_username(username)}"


def format_booth_code(
    direction: Optional[str],
    section: Optional[str],
    table: Optional[str],
    half: str,
) -> str:
    direction_prefix = {"East": "東", "West": "西", "South": "南"}.get(direction or "", "")
    core = "".join(part for part in (section or "", table or "") if part)
    suffix = "" if half in {"", "unknown"} else half
    return f"{direction_prefix}{core}{suffix}" or "Unknown booth"
