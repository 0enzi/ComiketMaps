"""Build explicitly provisional event data from a previous public event.

The source event can provide useful artist assignments, but its map geometry
must not be copied blindly: Comiket changes page layouts and booth grids from
event to event.  The C108 anchors below are event calibration keyed by map,
section, and printed table number.  They deliberately contain no artist
identity or artist-specific coordinates.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple


# Centers of the printed booth cells on the official C108 render (2867x2024).
# A pair such as ``40 | 9`` uses the center of the cell containing the printed
# table number, even when the imported booth half is ``a``/``b``/``ab``.
# Coordinates are calibration data, not application or artist data.
C108_CELL_ANCHORS: Dict[Tuple[str, str, str], Tuple[float, float]] = {
    # East 1–3.
    ("east-1-3", "ア", "8"): (2754.0, 1060.5),
    ("east-1-3", "ア", "17"): (2772.5, 694.0),
    ("east-1-3", "ア", "18"): (2772.5, 668.0),
    ("east-1-3", "ア", "19"): (2773.0, 641.5),
    ("east-1-3", "ア", "20"): (2755.0, 579.0),
    ("east-1-3", "ア", "29"): (2500.5, 451.0),
    ("east-1-3", "ア", "48"): (1553.5, 421.0),
    ("east-1-3", "ア", "60"): (858.5, 448.5),
    ("east-1-3", "ア", "64"): (706.0, 420.0),
    ("east-1-3", "ア", "80"): (124.5, 720.5),
    ("east-1-3", "ア", "84"): (142.0, 842.5),
    ("east-1-3", "ア", "85"): (142.0, 980.5),
    ("east-1-3", "イ", "19"): (2687.5, 727.0),
    ("east-1-3", "キ", "9"): (2373.0, 1123.5),
    ("east-1-3", "ウ", "15"): (2627.5, 980.0),
    ("east-1-3", "ウ", "24"): (2627.5, 727.0),
    ("east-1-3", "ケ", "14"): (2210.5, 980.0),
    ("east-1-3", "ク", "47"): (2284.5, 936.0),
    ("east-1-3", "ク", "48"): (2284.5, 959.0),
    ("east-1-3", "ク", "51"): (2284.0, 1022.0),
    ("east-1-3", "ノ", "9"): (1157.0, 1086.5),
    ("east-1-3", "ノ", "30"): (1157.0, 558.25),
    ("east-1-3", "ヒ", "9"): (1004.5, 1021.5),
    ("east-1-3", "ホ", "9"): (820.0, 1122.5),
    ("east-1-3", "マ", "18"): (756.5, 854.75),
    ("east-1-3", "メ", "16"): (570.5, 935.5),
    ("east-1-3", "メ", "34"): (544.5, 579.5),
    ("east-1-3", "メ", "36"): (544.5, 621.75),
    ("east-1-3", "メ", "38"): (544.5, 665.25),
    ("east-1-3", "メ", "39"): (544.5, 703.5),
    ("east-1-3", "メ", "40"): (544.5, 725.0),
    ("east-1-3", "メ", "42"): (544.5, 768.5),
    ("east-1-3", "メ", "44"): (544.5, 811.0),
    ("east-1-3", "ユ", "37"): (293.5, 578.5),
    ("east-1-3", "ユ", "40"): (293.5, 642.5),
    ("east-1-3", "ユ", "43"): (293.5, 725.5),
    ("east-1-3", "ユ", "49"): (293.5, 854.75),
    ("east-1-3", "ユ", "52"): (293.5, 979.75),
    ("east-1-3", "ヨ", "49"): (229.0, 1166.5),

    # East 7.
    ("east-7", "A", "1"): (997.06, 1693.40),
    ("east-7", "A", "4"): (1047.74, 1613.56),
    ("east-7", "A", "7"): (1107.64, 1520.86),
    ("east-7", "A", "9"): (1190.56, 1391.40),
    ("east-7", "A", "10"): (1207.0, 1364.0),
    ("east-7", "A", "13"): (1280.0, 1252.0),
    ("east-7", "A", "17"): (1362.2, 1121.3),
    ("east-7", "A", "19"): (1045.5, 287.5),
    ("east-7", "A", "21"): (974.5, 287.5),
    ("east-7", "A", "23"): (694.0, 287.0),
    ("east-7", "A", "34"): (249.0, 287.0),
    ("east-7", "B", "4"): (1342.0, 915.0),
    ("east-7", "D", "1"): (1183.5, 987.0),
    ("east-7", "E", "44"): (1072.5, 892.0),
    ("east-7", "E", "24"): (1101.0, 379.0),
    ("east-7", "I", "48"): (709.0, 987.0),
    ("east-7", "J", "2"): (625.5, 961.0),
    ("east-7", "K", "18"): (542.0, 520.0),
    ("east-7", "L", "45"): (427.5, 915.0),
    ("east-7", "M", "12"): (369.0, 728.0),

    # West 1–2.  The source export has one ``メ25`` spelling; the printed
    # C108 section is the hiragana ``め`` perimeter, so both spellings share
    # the same calibrated cell.
    ("west-1-2", "あ", "34"): (2664.5, 505.0),
    ("west-1-2", "あ", "36"): (2664.5, 418.0),
    ("west-1-2", "あ", "38"): (2649.5, 315.0),
    ("west-1-2", "あ", "5"): (2262.5, 1843.0),
    ("west-1-2", "あ", "45"): (2309.0, 179.5),
    ("west-1-2", "あ", "53"): (1748.5, 179.5),
    ("west-1-2", "あ", "55"): (1620.5, 199.0),
    ("west-1-2", "あ", "57"): (1556.0, 199.0),
    ("west-1-2", "さ", "20"): (2246.0, 435.5),
    ("west-1-2", "す", "19"): (1978.0, 388.5),
    ("west-1-2", "す", "21"): (1978.0, 435.5),
    ("west-1-2", "と", "15"): (1031.0, 291.5),
    ("west-1-2", "は", "41"): (491.0, 682.5),
    ("west-1-2", "ひ", "50"): (398.5, 973.5),
    ("west-1-2", "へ", "4"): (708.5, 1693.0),
    ("west-1-2", "へ", "9"): (708.5, 1526.0),
    ("west-1-2", "へ", "10"): (708.5, 1503.0),
    ("west-1-2", "へ", "36"): (674.5, 1303.0),
    ("west-1-2", "ほ", "33"): (580.5, 1198.5),
    ("west-1-2", "ほ", "36"): (580.0, 1303.0),
    ("west-1-2", "め", "24"): (217.5, 1380.5),
    ("west-1-2", "め", "26"): (217.5, 1153.25),
    ("west-1-2", "め", "27"): (217.5, 1121.0),
    ("west-1-2", "め", "28"): (217.5, 896.0),
    ("west-1-2", "め", "32"): (217.5, 608.5),
    ("west-1-2", "め", "47"): (663.0, 198.5),
    ("west-1-2", "め", "72"): (815.0, 1717.0),
    ("west-1-2", "メ", "25"): (217.5, 1185.5),

    # South 1–2, upper perimeter of the ``a`` section.
    ("south-1-2", "a", "29"): (2033.0, 348.0),
    ("south-1-2", "a", "30"): (1736.5, 302.0),
    ("south-1-2", "i", "11"): (1687.0, 873.5),
}


def _canonical_table(value: Any) -> str:
    text = str(value or "").strip()
    stripped = text.lstrip("0")
    return stripped or "0"


def c108_anchor(map_id: str, section: Any, table: Any) -> Optional[Tuple[float, float]]:
    section_text = str(section or "").strip()
    table_text = _canonical_table(table)
    direct = C108_CELL_ANCHORS.get((map_id, section_text, table_text))
    if direct is not None:
        return direct
    # The imported C107 record for this one West section uses katakana while
    # the official C108 page prints hiragana.
    if map_id == "west-1-2" and section_text in {"メ", "め"}:
        return C108_CELL_ANCHORS.get((map_id, "め", table_text))
    return None


# Kept as an internal alias for callers from older revisions.
_c108_anchor = c108_anchor


def _coordinate(value: Any, size: int) -> float:
    number = float(value)
    return number if 0 <= number <= 1 else number / size


def _canonical_section(value: Any) -> str:
    text = str(value or "").strip()
    # The C108 West page prints the perimeter section in hiragana while an
    # older export contains the visually equivalent katakana spelling.
    return "め" if text == "メ" else text


def _pixel_bounds(value: Any, width: int, height: int) -> Optional[List[float]]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        bounds = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(item) for item in bounds):
        return None
    if all(0 <= item <= 1 for item in bounds):
        x, y, bound_width, bound_height = bounds
        return [x * width, y * height, bound_width * width, bound_height * height]
    return bounds


def _review_calibration_point(
    target_calibration: Optional[Dict[str, Any]],
    source_booth: Dict[str, Any],
    target_map_id: str,
    target_map: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Find a reviewer-confirmed point for a carried-over booth.

    C108's built-in anchors are useful for the initial preview, but they only
    cover the carried-over records known when the preview was generated.  A
    maintainer can add any new booth in the localhost review UI.  Those
    normalized coordinates must take precedence here so the review action is
    reflected in the next build.
    """
    if not target_calibration:
        return None
    source_direction = str(source_booth.get("direction") or "").strip().casefold()
    source_hall = str(source_booth.get("hall") or "").strip()
    source_section = _canonical_section(source_booth.get("section"))
    source_table = _canonical_table(source_booth.get("table"))
    source_half = str(source_booth.get("half") or "unknown").strip().casefold()
    matches: List[Tuple[int, Dict[str, Any]]] = []

    for map_item in target_calibration.get("maps", []):
        if map_item.get("map_id") != target_map_id:
            continue
        for booth in map_item.get("booths", []):
            direction = str(booth.get("direction") or "").strip().casefold()
            if direction != source_direction:
                continue
            if _canonical_section(booth.get("section")) != source_section:
                continue
            if _canonical_table(booth.get("table")) != source_table:
                continue

            target_half = str(booth.get("half") or "unknown").strip().casefold()
            if source_half not in {"", "unknown"} and target_half != source_half:
                continue

            target_hall = str(booth.get("hall") or "").strip()
            if source_hall and target_hall and source_hall != target_hall:
                continue

            score = 0
            if source_half not in {"", "unknown"} and target_half == source_half:
                score += 4
            if source_hall and target_hall == source_hall:
                score += 2
            if target_half not in {"", "unknown"}:
                score += 1
            if target_hall:
                score += 1
            matches.append((score, booth))

    if not matches:
        return None
    _, booth = max(matches, key=lambda item: item[0])
    try:
        width = int(target_map["width"])
        height = int(target_map["height"])
        x = float(booth["x"])
        y = float(booth["y"])
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (x, y)):
        return None
    return {
        "x": _coordinate(x, width) * width,
        "y": _coordinate(y, height) * height,
        "bounds": _pixel_bounds(booth.get("bounds"), width, height),
    }


def carry_over_map_id(booth: Dict[str, Any], target_maps: Iterable[Dict[str, Any]]) -> str:
    direction = booth.get("direction")
    section = str(booth.get("section") or "")
    if direction == "East":
        # C108 puts the alphabetic East sections on East 7 and the Japanese
        # sections on the East 1–3 page.
        wanted = "east-7" if section.isascii() and section.isalpha() else "east-1-3"
    elif direction == "West":
        wanted = "west-1-2"
    elif direction == "South":
        wanted = "south-1-2"
    else:
        wanted = ""
    available = {str(item.get("map_id")) for item in target_maps}
    if wanted not in available:
        raise ValueError(f"No target map for carried-over booth {booth.get('booth_code')}: {wanted or '<unknown>'}")
    return wanted


def build_carry_over(
    source_manifest: Dict[str, Any],
    source_booths: List[Dict[str, Any]],
    source_artists: List[Dict[str, Any]],
    target_manifest: Dict[str, Any],
    require_target_calibration: bool = False,
    target_calibration: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    source_maps = {item["map_id"]: item for item in source_manifest.get("maps", [])}
    target_maps = {item["map_id"]: item for item in target_manifest.get("maps", [])}
    referenced_booth_ids = {
        location.get("booth_id")
        for artist in source_artists
        for location in artist.get("locations", [])
    }
    geometries: Dict[str, Dict[str, Any]] = {}
    public_booths: Dict[str, Dict[str, Any]] = {}

    for source_booth in source_booths:
        if source_booth.get("booth_id") not in referenced_booth_ids:
            continue
        source_map = source_maps.get(source_booth.get("map_id"))
        target_map_id = carry_over_map_id(source_booth, target_maps.values())
        target_map = target_maps[target_map_id]
        if not source_map or not source_map.get("width") or not source_map.get("height"):
            raise ValueError(f"Missing source map dimensions for {source_booth.get('booth_id')}")

        booth_id = f"{target_manifest['event_id'].lower()}:carry-over:{source_booth['booth_id']}"
        review_point = _review_calibration_point(target_calibration, source_booth, target_map_id, target_map)
        anchor = _c108_anchor(target_map_id, source_booth.get("section"), source_booth.get("table"))
        if require_target_calibration and review_point is None and anchor is None:
            raise ValueError(
                "Missing target cell calibration for "
                f"{target_map_id}|{source_booth.get('section')}|{source_booth.get('table')}"
            )
        bounds = None
        if review_point is not None:
            x, y = review_point["x"], review_point["y"]
            bounds = review_point["bounds"]
            confidence = "manual"
            source = "review-calibration"
        elif anchor is None:
            x = round(_coordinate(source_booth.get("x"), source_map["width"]) * target_map["width"], 3)
            y = round(_coordinate(source_booth.get("y"), source_map["height"]) * target_map["height"], 3)
            confidence = "provisional"
            source = "c107-carry-over"
        else:
            x, y = anchor
            confidence = "calibrated"
            source = "c108-cell-calibration"
        geometry = {
            "booth_id": booth_id,
            "map_id": target_map_id,
            "direction": source_booth.get("direction"),
            "hall": source_booth.get("hall"),
            "section": source_booth.get("section"),
            "table": source_booth.get("table"),
            "half": source_booth.get("half", "unknown"),
            "booth_code": source_booth.get("booth_code", "Unknown booth"),
            "x": x,
            "y": y,
            "bounds": bounds,
            "confidence": confidence,
            "source": source,
            "artist_keys": [],
        }
        geometries[source_booth["booth_id"]] = geometry
        public_booths[booth_id] = geometry

    public_artists: List[Dict[str, Any]] = []
    for source_artist in sorted(source_artists, key=lambda item: (item.get("username", "").lower(), item.get("artist_key", ""))):
        locations = []
        for source_location in source_artist.get("locations", []):
            geometry = geometries.get(source_location.get("booth_id"))
            if geometry is None:
                continue
            geometry["artist_keys"].append(source_artist["artist_key"])
            locations.append({
                "day": source_location.get("day"),
                "map_id": geometry["map_id"],
                "booth_id": geometry["booth_id"],
                "booth_code": source_location.get("booth_code") or geometry["booth_code"],
            })
        if locations:
            public_artists.append({
                key: source_artist.get(key, 0 if key == "priority" else "")
                for key in ("artist_key", "user_id", "username", "display_name", "description", "profile_url", "avatar_url", "banner_url", "priority")
            } | {"locations": locations})

    for booth in public_booths.values():
        booth["artist_keys"] = sorted(set(booth["artist_keys"]))
    return list(public_booths.values()), public_artists
