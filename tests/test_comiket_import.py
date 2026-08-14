import json
import shutil
from pathlib import Path

import pytest

from comiket_import.artists import event_config_from_dict, merge_records, read_artist_csv, read_manual_csv
from comiket_import.carryover import C108_CELL_ANCHORS, build_carry_over, carry_over_map_id
from comiket_import.models import ArtistRecord, LocationCandidate
from comiket_import.normalize import artist_key, normalize_half, normalize_table, normalize_text
from comiket_import.calibration import detect_booth_candidates
from comiket_import.pdf_import import load_calibration, map_specs
from comiket_import.pipeline import _apply_review_overrides, _calibrate_booth
from comiket_import.validate import validate_public_event


CONFIG = {
    "event_code": "C107",
    "day_specs": {
        "1": {"month": 12, "day": 30, "weekday_kanji": "火"},
        "2": {"month": 12, "day": 31, "weekday_kanji": "水"},
    },
}


def test_nfkc_identity_and_missing_half_remains_unresolved(tmp_path: Path):
    assert normalize_text(" Ａ１２ ") == "A12"
    assert normalize_table("１") == "01"
    assert normalize_half("") == "unknown"
    assert artist_key("０", "@Enzi") == "xhandle:enzi"
    csv_path = tmp_path / "following.csv"
    csv_path.write_text("User ID,Username,Name,Bio\n123,artist,C107(火)東ア-01,\n", encoding="utf-8")
    records = read_artist_csv(csv_path, "C107", event_config_from_dict(CONFIG))
    assert records[0].locations[0].half == "unknown"
    assert records[0].locations[0].status == "needs_review"


def test_event_conflict_and_multiple_same_day_are_reviewed(tmp_path: Path):
    csv_path = tmp_path / "following.csv"
    csv_path.write_text(
        "User ID,Username,Name,Bio\n123,artist,C106(火)東ア-01a,1日目西め-02b\n",
        encoding="utf-8",
    )
    records = read_artist_csv(csv_path, "C107", event_config_from_dict(CONFIG))
    locations = records[0].locations
    assert len(locations) == 2
    assert all(location.status == "needs_review" for location in locations)
    assert all("multiple-locations-same-day" in location.reason for location in locations)
    assert all("event-code-conflict" in location.reason for location in locations if "C106" in location.source_text)


def test_manual_correction_overrides_parsed_day(tmp_path: Path):
    parsed = [ArtistRecord(
        event_id="C107", artist_key="x:123", user_id="123", username="artist", display_name="Artist",
        locations=[LocationCandidate("C107", "x:123", "artist", "Artist", 1, "East", "4", "ア", "01", "a", "high")],
    )]
    manual_path = tmp_path / "manual.csv"
    manual_path.write_text(
        "user_id,username,display_name,day,direction,hall,section,table,half,action\n123,artist,Artist,2,East,4,メ,07,b,replace\n",
        encoding="utf-8",
    )
    merged = merge_records(parsed, read_manual_csv(manual_path, "C107"))
    assert [(location.day, location.section, location.table) for location in merged[0].locations] == [(2, "メ", "07")]


def test_public_c107_contract_is_deterministic_and_private_free():
    root = Path(__file__).parents[1]
    index = json.loads((root / "public/events/index.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "public/events/c107/manifest.json").read_text(encoding="utf-8"))
    artists = json.loads((root / "public/events/c107/artists.json").read_text(encoding="utf-8"))
    booths = json.loads((root / "public/events/c107/booths.json").read_text(encoding="utf-8"))
    assert [item["map_id"] for item in manifest["maps"]] == ["east-4-6", "east-7-8", "south-1-2", "west-1-2"]
    booth_ids = {booth["booth_id"] for booth in booths}
    location_ids = [location["booth_id"] for artist in artists for location in artist["locations"]]
    assert set(location_ids) <= booth_ids
    assert len(location_ids) == len({(artist["artist_key"], location["day"], location["booth_id"]) for artist in artists for location in artist["locations"]})
    assert all("source_text" not in location and "status" not in location for artist in artists for location in artist["locations"])
    assert not (root / "public/events/c107/review-queue.json").exists()
    assert index["events"][0]["manifest"] == "events/c107/manifest.json"


def test_review_override_can_be_reapplied_after_reimport():
    record = ArtistRecord(
        event_id="C107", artist_key="x:123", user_id="123", username="artist", display_name="Artist",
        locations=[LocationCandidate("C107", "x:123", "artist", "Artist", 1, "East", "4", "ア", "01", "unknown", "low", reason="unknown-half", source_text="C107(火)東ア-01", source_field="name")],
    )
    updated = _apply_review_overrides([record], {"records": [{
        "artist_key": "x:123", "source_text": "C107(火)東ア-01", "source_field": "name", "half": "ab", "status": "accepted",
    }]})
    assert updated[0].locations[0].half == "ab"
    assert updated[0].locations[0].status == "accepted"


def test_calibration_is_invalidated_when_pdf_hash_changes(tmp_path: Path):
    event_dir = tmp_path / "events" / "c107"
    event_dir.mkdir(parents=True)
    (event_dir / "event.json").write_text(json.dumps({"source_pdf_sha256": "new-hash"}), encoding="utf-8")
    (event_dir / "calibration.json").write_text(json.dumps({"source_pdf_sha256": "old-hash"}), encoding="utf-8")
    with pytest.raises(ValueError, match="source PDF hash changed"):
        load_calibration(tmp_path, "C107")


def test_c108_config_uses_official_four_page_semantic_order():
    root = Path(__file__).parents[1]
    config = json.loads((root / "config/events/c108.json").read_text(encoding="utf-8"))
    specs = map_specs(config, pages=4)
    assert [(item.map_id, item.label, item.page) for item in specs] == [
        ("east-1-3", "East 1–3", 1),
        ("east-7", "East 7", 2),
        ("west-1-2", "West 1–2", 3),
        ("south-1-2", "South 1–2", 4),
    ]
    assert config["source_pdf_url"].endswith("C108Map_all_B4.pdf")


def test_public_c108_contract_contains_all_four_maps():
    root = Path(__file__).parents[1]
    index = json.loads((root / "public/events/index.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "public/events/c108/manifest.json").read_text(encoding="utf-8"))
    assert {item["event_id"] for item in index["events"]} >= {"C107", "C108"}
    assert [item["map_id"] for item in manifest["maps"]] == ["east-1-3", "east-7", "west-1-2", "south-1-2"]
    assert all((root / "public/events/c108" / item["asset"]).exists() for item in manifest["maps"])
    assert "data_status" not in manifest
    artists = json.loads((root / "public/events/c108/artists.json").read_text(encoding="utf-8"))
    booths = json.loads((root / "public/events/c108/booths.json").read_text(encoding="utf-8"))
    assert len(artists) == 19
    assert len(booths) == 20
    assert sum(len(artist["locations"]) for artist in artists) == 20
    assert all(booth["artist_keys"] for booth in booths)
    assert all(0 <= booth["x"] <= 1 and 0 <= booth["y"] <= 1 for booth in booths)


def test_carry_over_uses_target_map_and_normalized_geometry():
    source_manifest = {"maps": [{"map_id": "east-4-6", "width": 100, "height": 100}]}
    source_booths = [{
        "booth_id": "east-4-6:1:2", "map_id": "east-4-6", "direction": "East",
        "hall": None, "section": "メ", "table": "09", "half": "ab", "booth_code": "メ9ab",
        "x": 25, "y": 40,
    }]
    source_artists = [{
        "artist_key": "x:123", "user_id": "123", "username": "artist", "display_name": "Artist",
        "description": "", "profile_url": "", "avatar_url": "", "banner_url": "",
        "locations": [{"day": 1, "map_id": "east-4-6", "booth_id": "east-4-6:1:2", "booth_code": "メ9ab"}],
    }]
    target_manifest = {"event_id": "C108", "maps": [{"map_id": "east-1-3", "width": 200, "height": 400}]}
    assert carry_over_map_id(source_booths[0], target_manifest["maps"]) == "east-1-3"
    booths, artists = build_carry_over(source_manifest, source_booths, source_artists, target_manifest)
    assert booths[0]["x"] == 50
    assert booths[0]["y"] == 160
    assert artists[0]["locations"][0]["map_id"] == "east-1-3"


def test_c108_carry_over_requires_and_uses_printed_cell_calibration():
    source_manifest = {"maps": [{"map_id": "east-4-6", "width": 100, "height": 100}]}
    source_booths = [{
        "booth_id": "east-4-6:1:2", "map_id": "east-4-6", "direction": "East",
        "hall": None, "section": "ア", "table": "60", "half": "a", "booth_code": "ア60a",
        "x": 0.01, "y": 0.01,
    }]
    source_artists = [{
        "artist_key": "x:123", "user_id": "123", "username": "artist", "display_name": "Artist",
        "description": "", "profile_url": "", "avatar_url": "", "banner_url": "",
        "locations": [{"day": 1, "map_id": "east-4-6", "booth_id": "east-4-6:1:2", "booth_code": "ア60a"}],
    }]
    target_manifest = {"event_id": "C108", "maps": [{"map_id": "east-1-3", "width": 2867, "height": 2024}]}
    booths, _ = build_carry_over(
        source_manifest,
        source_booths,
        source_artists,
        target_manifest,
        require_target_calibration=True,
    )
    assert (booths[0]["x"], booths[0]["y"]) == C108_CELL_ANCHORS[("east-1-3", "ア", "60")]
    assert booths[0]["source"] == "c108-cell-calibration"


def test_review_calibration_overrides_c108_fallback_anchor():
    source_manifest = {"maps": [{"map_id": "east-4-6", "width": 100, "height": 100}]}
    source_booths = [{
        "booth_id": "east-4-6:1:2", "map_id": "east-4-6", "direction": "East",
        "hall": None, "section": "ア", "table": "60", "half": "a", "booth_code": "ア60a",
        "x": 0.01, "y": 0.01,
    }]
    source_artists = [{
        "artist_key": "x:123", "user_id": "123", "username": "artist", "display_name": "Artist",
        "description": "", "profile_url": "", "avatar_url": "", "banner_url": "",
        "locations": [{"day": 1, "map_id": "east-4-6", "booth_id": "east-4-6:1:2", "booth_code": "ア60a"}],
    }]
    target_manifest = {"event_id": "C108", "maps": [{"map_id": "east-1-3", "width": 2867, "height": 2024}]}
    target_calibration = {"maps": [{"map_id": "east-1-3", "booths": [{
        "direction": "East", "hall": None, "section": "ア", "table": "60", "half": "a",
        "x": 0.2, "y": 0.3, "bounds": [0.19, 0.29, 0.02, 0.03],
    }]}]}
    booths, _ = build_carry_over(
        source_manifest,
        source_booths,
        source_artists,
        target_manifest,
        require_target_calibration=True,
        target_calibration=target_calibration,
    )
    assert booths[0]["x"] == pytest.approx(2867 * 0.2)
    assert booths[0]["y"] == pytest.approx(2024 * 0.3)
    assert booths[0]["bounds"] == pytest.approx([2867 * 0.19, 2024 * 0.29, 2867 * 0.02, 2024 * 0.03])
    assert booths[0]["source"] == "review-calibration"


def test_c108_calibration_covers_every_generated_booth():
    root = Path(__file__).parents[1]
    booths = json.loads((root / "public/events/c108/booths.json").read_text(encoding="utf-8"))
    keys = {(booth["map_id"], booth["section"], str(int(booth["table"]))) for booth in booths}
    assert keys <= set(C108_CELL_ANCHORS)


def test_booth_candidate_detection_returns_normalized_geometry(tmp_path: Path):
    cv2 = pytest.importorskip("cv2")
    import numpy as np

    image = np.full((100, 100), 255, dtype=np.uint8)
    cv2.rectangle(image, (20, 30), (49, 59), 0, 1)
    image_path = tmp_path / "map.png"
    cv2.imwrite(str(image_path), image)
    result = detect_booth_candidates(image_path)
    assert result["status"] == "advisory"
    assert result["count"] >= 1
    candidate = result["candidates"][0]
    assert all(0 <= value <= 1 for value in candidate["bounds"])
    assert 0 <= candidate["x"] <= 1
    assert 0 <= candidate["y"] <= 1


def test_duplicate_csv_rows_are_kept_for_review(tmp_path: Path):
    csv_path = tmp_path / "following.csv"
    csv_path.write_text(
        "User ID,Username,Name,Bio\n123,artist,C107(火)東ア-01a,\n123,artist,C107(火)東ア-01a,\n",
        encoding="utf-8",
    )
    records = read_artist_csv(csv_path, "C107", event_config_from_dict(CONFIG))
    assert len(records) == 1
    assert len(records[0].locations) == 1
    assert records[0].locations[0].status == "needs_review"
    assert "duplicate-csv-row" in records[0].locations[0].reason


def test_manual_calibration_saves_normalized_semantic_geometry():
    calibration = {"maps": [{"map_id": "east-1-3", "booths": []}]}
    booth = _calibrate_booth({}, calibration, {
        "map_id": "east-1-3", "direction": "東", "hall": "1", "section": "メ",
        "table": "４０", "half": "AB", "x": "0.25", "y": "0.5",
    })
    assert booth["booth_id"] == "east-1-3:east:1:メ:40:ab"
    assert booth["x"] == 0.25
    assert calibration["maps"][0]["booths"] == [booth]


def test_explicit_half_uses_the_location_table_not_the_hall_number(tmp_path: Path):
    csv_path = tmp_path / "c108_half_formats.csv"
    csv_path.write_text(
        "User ID,Username,Name,Bio\n"
        ",hall-space,2日目東7 A07ab,\n"
        ",hyphen-space,C108 2日目東7ホールA23-b,\n"
        ",missing,C108 2日目東1ア29,\n",
        encoding="utf-8",
    )
    records = read_artist_csv(
        csv_path,
        "C108",
        event_config_from_dict({
            "event_code": "C108",
            "day_specs": {
                "1": {"month": 8, "day": 15, "weekday_kanji": "土"},
                "2": {"month": 8, "day": 16, "weekday_kanji": "日"},
            },
        }),
    )
    halves = {record.username: record.locations[0].half for record in records}
    assert halves == {"hall-space": "ab", "hyphen-space": "b", "missing": "unknown"}


def test_explicit_half_accepts_discord_escaped_separator():
    from comiket_import.artists import _explicit_half

    assert _explicit_half("C108 東7 A23\\-ab", "23") == "ab"


def test_public_validation_rejects_unknown_day(tmp_path: Path):
    source = Path(__file__).parents[1] / "public/events/c107"
    target = tmp_path / "c107"
    shutil.copytree(source, target)
    artists_path = target / "artists.json"
    artists = json.loads(artists_path.read_text(encoding="utf-8"))
    artists[0]["locations"][0]["day"] = 99
    artists_path.write_text(json.dumps(artists), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown day reference"):
        validate_public_event(target)
