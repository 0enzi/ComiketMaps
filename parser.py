"""
Comiket Booth-Location Parser

Usage:
    This module is designed to run as an offline batch script over a Twitter
    "following" list exported as a CSV.

    To use:
    1. Define an EventConfig for the upcoming Comiket:
       config = EventConfig(
           event_code="C108",
           day1=DaySpec(month=8, day=15, weekday_kanji="土"),
           day2=DaySpec(month=8, day=16, weekday_kanji="日")
       )
    2. Run the CSV parser:
       parse_csv_to_json("following.csv", "exhibitors.json", config)

    The output JSON file contains a list of exhibitor profiles ready to be
    merged into the ComiketMaps marker dataset.
"""
import re
import csv
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class DaySpec:
    month: int
    day: int
    weekday_kanji: str  # e.g. "火", "水", "土", "日"

@dataclass
class EventConfig:
    event_code: str  # e.g. "C108"
    day1: DaySpec
    day2: DaySpec

@dataclass
class Location:
    day: Optional[int]
    direction: Optional[str]
    section: Optional[str]
    table: Optional[str]
    half: Optional[str]
    confidence: str
    source_text: str
    source_field: str

@dataclass
class ParseResult:
    user_id: str = ""
    username: str = ""
    is_exhibitor: bool = False
    locations: List[Location] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "is_exhibitor": self.is_exhibitor,
            "locations": [
                {
                    "day": loc.day,
                    "direction": loc.direction,
                    "section": loc.section,
                    "table": loc.table,
                    "half": loc.half,
                    "confidence": loc.confidence,
                    "source_text": loc.source_text,
                    "source_field": loc.source_field
                } for loc in self.locations
            ]
        }

# --- Character Classes ---
# Hiragana, Full-width Katakana, Half-width Katakana, Latin Upper/Lower, Full-width Latin Upper/Lower
SECTION_CHARS = (
    r"\u3041-\u3096"
    r"\u30A1-\u30FA"
    r"\uFF66-\uFF9D"
    r"A-Za-z"
    r"\uFF21-\uFF3A"
    r"\uFF41-\uFF5A"
)

_PUNCT = r"[\u201C\u201D\u2018\u2019\"'〖〗【】\[\]（）()〈〉《》「」『』]"

# --- Regexes ---
_EVENT_KEYWORDS_RE = re.compile(
    r"C\d{3}"
    r"|ｺﾐｹｯﾄ"
    r"|ｺﾐｹ"
    r"|コミケット"
    r"|コミケ"
    r"|冬ｺﾐ"
    r"|夏ｺﾐ"
    r"|冬コミ"
    r"|夏コミ"
)

# Full-width to half-width digits
_FW_TO_ASCII = str.maketrans("０１２３４５６７８９", "0123456789")

_LOCATION_RE = re.compile(
    r"(?P<dir>[東西南])?"
    r"\s*"
    r"(?P<hall>[1-9])?"
    r"[\s/]*"
    r"(?:ホール)?"
    rf"(?:{_PUNCT})?"
    r"\s*"
    rf"(?P<section>[{SECTION_CHARS}])"
    rf"(?:{_PUNCT})?"
    r"[\s\-/]*"
    r"(?P<table>(?<!\d)\d{1,3}(?!\d))"
    r"(?P<half>[aAbB]{1,2})?"
)

# Partial regex for direction+section without table (used for low confidence fallback)
_PARTIAL_SECTION_RE = re.compile(
    r"(?P<dir>[東西南])\s*"
    r"(?P<hall>[1-9])?\s*"
    r"(?:ホール)?\s*"
    rf"(?:{_PUNCT})?\s*"
    rf"(?P<section>[{SECTION_CHARS}])"
    rf"(?:{_PUNCT})?"
    r"(?!\s*[-/]?\s*\d)"
)

_DIR_MAP = {"東": "East", "西": "West", "南": "South"}

def _normalize_digits(s: str) -> str:
    return s.translate(_FW_TO_ASCII)

def _build_day_marker_re(day_num: int, day_spec: DaySpec) -> re.Pattern:
    kanji_num = "一" if day_num == 1 else "二"
    weekday = day_spec.weekday_kanji
    m, d = day_spec.month, day_spec.day

    patterns = [
        rf"(?<!\d){day_num}日目",
        rf"{kanji_num}日目",
        rf"{weekday}曜(?:日)?",
        rf"[\(（]\s*{weekday}\s*[\)）]",
        rf"(?<!\d){m}\s*[/\-．.]\s*{d}(?!\d)",
        rf"{m}月{d}日",
    ]
    return re.compile("|".join(patterns))

def _infer_direction(section: str) -> Optional[str]:
    if not section:
        return None
    cp = ord(section[0])
    if 0x3041 <= cp <= 0x3096:
        return "West"
    if (0x30A1 <= cp <= 0x30FA) or (0xFF66 <= cp <= 0xFF9D):
        return "East"
    if (0xFF21 <= cp <= 0xFF3A) or ('A' <= section <= 'Z'):
        return "East"
    if (0xFF41 <= cp <= 0xFF5A) or ('a' <= section <= 'z'):
        return "South"
    return None

def _find_nearest_day(loc_start: int, day_markers: List[tuple]) -> Optional[int]:
    if not day_markers:
        return None
    preceding = [(s, e, d) for s, e, d in day_markers if e <= loc_start]
    if preceding:
        s, e, d = max(preceding, key=lambda x: x[0])
        return d
    following = [(s, e, d) for s, e, d in day_markers if s > loc_start]
    if following:
        s, e, d = min(following, key=lambda x: x[0])
        return d
    return None

def _compute_confidence(day: Optional[int], direction: Optional[str],
                        dir_explicit: bool, section: Optional[str],
                        table: Optional[str], half_explicit: bool,
                        has_event_kw: bool) -> Optional[str]:
    if not section or not table:
        if not has_event_kw and day is None:
            return None
        return "low"
    if day is None:
        if has_event_kw:
            return "low"
        return None
    if dir_explicit and half_explicit and has_event_kw:
        return "high"
    return "medium"

def _compute_source_text(original: str, match_start: int, match_end: int,
                         day_markers: list, event_kw_spans: list) -> str:
    day_start = None
    for s, e, _ in day_markers:
        if e <= match_start and (day_start is None or s > day_start):
            day_start = s

    preceding_kws = sorted([(s, e) for s, e in event_kw_spans if e <= match_start])
    kw_start = None
    if preceding_kws:
        latest_s, latest_e = preceding_kws[-1]
        ref = day_start if day_start is not None else match_start
        if latest_e >= ref - 5:
            kw_start = latest_s
            for s, e in reversed(preceding_kws[:-1]):
                if e >= kw_start - 2:
                    kw_start = s
                else:
                    break

    start = match_start
    if day_start is not None:
        start = min(start, day_start)
    if kw_start is not None:
        start = min(start, kw_start)

    end = match_end
    if day_start is None:
        following = [(s, e, d) for s, e, d in day_markers if s >= match_end]
        if following:
            s, e, d = min(following, key=lambda x: x[0])
            end = max(end, e)

    return original[start:end]

def parse_comiket_bio(text: str, event_config: EventConfig,
                      user_id: str = "", username: str = "",
                      source_field: str = "name") -> ParseResult:
    if not text:
        return ParseResult(user_id, username, False, [])

    normalized = _normalize_digits(text)

    # Scrub event keywords (replace with spaces to preserve positions)
    event_kw_spans = [(m.start(), m.end()) for m in _EVENT_KEYWORDS_RE.finditer(normalized)]
    has_event_kw = len(event_kw_spans) > 0
    scrubbed = _EVENT_KEYWORDS_RE.sub(lambda m: " " * (m.end() - m.start()), normalized)

    # Find day markers
    day1_re = _build_day_marker_re(1, event_config.day1)
    day2_re = _build_day_marker_re(2, event_config.day2)

    day_markers = []
    for m in day1_re.finditer(scrubbed):
        day_markers.append((m.start(), m.end(), 1))
    for m in day2_re.finditer(scrubbed):
        day_markers.append((m.start(), m.end(), 2))

    locations = []
    full_matches = list(_LOCATION_RE.finditer(scrubbed))

    for m in full_matches:
        section = m.group("section")
        table = m.group("table")
        dir_char = m.group("dir")

        if dir_char:
            direction = _DIR_MAP.get(dir_char)
            dir_explicit = True
        else:
            direction = _infer_direction(section)
            dir_explicit = False

        half_raw = m.group("half")
        half_explicit = half_raw is not None and half_raw.lower() in ("a", "b", "ab")
        half = half_raw.lower() if half_explicit else "ab"

        day = _find_nearest_day(m.start(), day_markers)
        confidence = _compute_confidence(
            day, direction, dir_explicit, section, table, half_explicit, has_event_kw
        )

        if confidence is None:
            continue

        source_text = _compute_source_text(text, m.start(), m.end(), day_markers, event_kw_spans)

        locations.append(Location(
            day=day, direction=direction, section=section, table=table,
            half=half, confidence=confidence, source_text=source_text,
            source_field=source_field
        ))

    # Partial matches fallback for low confidence incomplete data
    if not locations and (has_event_kw or day_markers):
        partial_matches = [
            pm for pm in _PARTIAL_SECTION_RE.finditer(scrubbed)
            if not any(fm.start() <= pm.start() < fm.end() for fm in full_matches)
        ]

        if partial_matches:
            for pm in partial_matches:
                day = _find_nearest_day(pm.start(), day_markers)
                dir_char = pm.group("dir")
                section = pm.group("section")
                direction = _DIR_MAP.get(dir_char) if dir_char else _infer_direction(section)
                source_text = _compute_source_text(text, pm.start(), pm.end(), day_markers, event_kw_spans)
                locations.append(Location(
                    day=day, direction=direction, section=section, table=None,
                    half=None, confidence="low", source_text=source_text, source_field=source_field
                ))
        elif day_markers:
            for ds, de, dn in day_markers:
                locations.append(Location(
                    day=dn, direction=None, section=None, table=None, half=None,
                    confidence="low", source_text=text[ds:de], source_field=source_field
                ))
        else:
            locations.append(Location(
                day=None, direction=None, section=None, table=None, half=None,
                confidence="low", source_text=text, source_field=source_field
            ))

    # Deduplicate
    seen = set()
    unique_locs = []
    for loc in locations:
        key = (loc.day, loc.direction, loc.section, loc.table, loc.half)
        if key not in seen:
            seen.add(key)
            unique_locs.append(loc)

    return ParseResult(
        user_id=user_id,
        username=username,
        is_exhibitor=len(unique_locs) > 0,
        locations=unique_locs
    )

def parse_row(row: Dict[str, str], event_config: EventConfig) -> ParseResult:
    user_id = row.get("User ID", "")
    username = row.get("Username", "")
    name = row.get("Name", "")
    bio = row.get("Bio", "")

    name_result = parse_comiket_bio(name, event_config, user_id, username, "name")
    bio_result = parse_comiket_bio(bio, event_config, user_id, username, "bio")

    return ParseResult(
        user_id=user_id,
        username=username,
        is_exhibitor=name_result.is_exhibitor or bio_result.is_exhibitor,
        locations=name_result.locations + bio_result.locations,
    )

def parse_csv_to_json(csv_path: str, json_path: str, event_config: EventConfig) -> None:
    results = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            res = parse_row(row, event_config)
            if res.is_exhibitor:
                results.append(res.to_dict())

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
