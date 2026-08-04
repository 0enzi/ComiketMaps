"""Advisory calibration suggestions.

Suggestions are never treated as reviewed geometry.  OpenCV and Japanese
Tesseract are optional; when unavailable the review UI still provides the
manual calibration surface and records that advisory analysis was skipped.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def detect_booth_candidates(image_path: Path) -> Dict[str, Any]:
    """Find rectangular booth-cell candidates as advisory normalized geometry.

    This deliberately does not assign hall, section, table, or half labels. It
    gives the reviewer a stable set of likely cells to inspect, while OCR and
    the eventual manual calibration remain authoritative.
    """
    try:
        import cv2  # type: ignore
    except ImportError:
        return {"status": "unavailable", "candidates": []}

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return {"status": "error", "candidates": []}
    image_height, image_width = image.shape[:2]
    _, binary = cv2.threshold(image, 220, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    seen = set()
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if not (12 <= width <= 60 and 10 <= height <= 50):
            continue
        ratio = width / height
        if not 0.5 <= ratio <= 2.4:
            continue
        area = cv2.contourArea(contour)
        if not 100 <= area <= 2500 or area / (width * height) < 0.45:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        if len(polygon) != 4:
            continue
        key = (x, y, width, height)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "bounds": [
                    x / image_width,
                    y / image_height,
                    width / image_width,
                    height / image_height,
                ],
                "x": (x + width / 2) / image_width,
                "y": (y + height / 2) / image_height,
                "confidence": "advisory",
                "source": "opencv-rectangular-contour",
            }
        )

    candidates.sort(key=lambda item: (item["y"], item["x"]))
    return {
        "status": "advisory",
        "image_width": image_width,
        "image_height": image_height,
        "count": len(candidates),
        "candidates": candidates,
    }


def suggest_calibration(image_path: Path) -> Dict[str, Any]:
    suggestion: Dict[str, Any] = {
        "status": "unavailable",
        "grid": {},
        "booth_candidates": detect_booth_candidates(image_path),
        "ocr": {},
    }
    try:
        import cv2  # type: ignore

        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is not None:
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, 3.14159 / 180, threshold=80, minLineLength=40, maxLineGap=8)
            horizontal = 0
            vertical = 0
            for line in (lines if lines is not None else []):
                # OpenCV versions differ: HoughLinesP may return either
                # ``[[x1, y1, x2, y2]]`` or ``[x1, y1, x2, y2]`` per row.
                coordinates = line.reshape(-1).tolist()
                if len(coordinates) < 4:
                    continue
                x1, y1, x2, y2 = coordinates[:4]
                if abs(x2 - x1) > abs(y2 - y1) * 4:
                    horizontal += 1
                elif abs(y2 - y1) > abs(x2 - x1) * 4:
                    vertical += 1
            suggestion["status"] = "advisory"
            suggestion["grid"] = {"horizontal_lines": horizontal, "vertical_lines": vertical}
    except (ImportError, OSError):
        suggestion["grid"] = {"note": "Install the pdf extra for OpenCV line detection."}

    tesseract = shutil.which("tesseract")
    if tesseract:
        try:
            languages = subprocess.check_output([tesseract, "--list-langs"], text=True, stderr=subprocess.STDOUT)
            if "jpn" in languages and "eng" in languages:
                text = subprocess.check_output(
                    [tesseract, str(image_path), "stdout", "-l", "jpn+eng", "--psm", "6"],
                    text=True,
                    stderr=subprocess.STDOUT,
                )
                suggestion["ocr"] = {"status": "advisory", "sample": text[:2000]}
            else:
                suggestion["ocr"] = {"status": "unavailable", "note": "Tesseract jpn+eng data is not installed."}
        except (OSError, subprocess.CalledProcessError) as exc:
            suggestion["ocr"] = {"status": "error", "note": str(exc)}
    else:
        suggestion["ocr"] = {"status": "unavailable", "note": "Tesseract is not installed."}
    return suggestion
