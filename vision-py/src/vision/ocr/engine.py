from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


class OCRRuntimeError(RuntimeError):
    """Raised when the OCR backend cannot produce a result."""


@dataclass(frozen=True)
class OCRResult:
    text: str
    confidence: float


def _ocr_script_path() -> Path:
    return Path(files("vision.ocr").joinpath("vision_ocr.swift"))


def recognize_text(image_path: Path) -> OCRResult:
    command = ["swift", str(_ocr_script_path()), str(image_path)]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise OCRRuntimeError("swift command is not available") from exc

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "swift vision ocr failed"
        raise OCRRuntimeError(message)

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise OCRRuntimeError("swift vision ocr returned invalid json") from exc

    if payload.get("error"):
        raise OCRRuntimeError(str(payload["error"]))

    entries = payload.get("texts", [])
    if not isinstance(entries, list):
        raise OCRRuntimeError("swift vision ocr returned invalid texts payload")

    if not entries:
        return OCRResult(text="", confidence=0.0)

    top_entry = entries[0]
    if not isinstance(top_entry, dict):
        raise OCRRuntimeError("swift vision ocr returned invalid text entry")

    return OCRResult(
        text=str(top_entry.get("text", "")).strip(),
        confidence=float(top_entry.get("confidence", 0.0)),
    )
