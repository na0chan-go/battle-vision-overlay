from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from vision.capture.loader import load_image
from vision.gender import extract_gender_marks
from vision.name_match import resolve_name_results
from vision.name_ocr import extract_name_texts
from vision.observation import (
    ActivePokemonMetadata,
    build_battle_observation,
    write_observation_json,
)
from vision.regions.battle import build_active_recognition_region_payload
from vision.tuning import build_tuning_parameters_payload

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})
UNKNOWN_SPECIES_ID = "unknown"
UNLABELED_CONDITION = "unlabeled"
_CONDITION_KEYWORDS = (
    "1080p",
    "720p",
    "scaled",
    "with_margin",
    "margin",
    "dark",
    "compressed",
)
_ACTIVE_REGION_MAP = {
    "player_active": ("player_name", "player_gender"),
    "opponent_active": ("opponent_name", "opponent_gender"),
}
_TOKEN_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ValidationOptions:
    samples_dir: Path
    debug_root_dir: Path
    report_path: Path
    master_data_path: Path
    player_metadata: ActivePokemonMetadata
    opponent_metadata: ActivePokemonMetadata


def list_sample_images(samples_dir: Path) -> tuple[Path, ...]:
    if not samples_dir.exists():
        raise FileNotFoundError(f"samples directory not found: {samples_dir}")
    if not samples_dir.is_dir():
        raise ValueError(f"samples path must be a directory: {samples_dir}")

    return tuple(
        sorted(
            path
            for path in samples_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        )
    )


def classify_validation_status(player_species_id: str, opponent_species_id: str) -> str:
    player_known = player_species_id != UNKNOWN_SPECIES_ID
    opponent_known = opponent_species_id != UNKNOWN_SPECIES_ID

    if player_known and opponent_known:
        return "success"
    if player_known or opponent_known:
        return "partial"
    return "failed"


def infer_condition_label(image_path: Path) -> str:
    normalized_stem = _TOKEN_SEPARATOR_PATTERN.sub("_", image_path.stem.lower())
    tokens = tuple(token for token in normalized_stem.split("_") if token)
    labels: list[str] = []
    for keyword in _CONDITION_KEYWORDS:
        keyword_tokens = tuple(keyword.split("_"))
        if keyword == "margin" and _has_condition_tokens(tokens, ("with", "margin")):
            continue
        if _has_condition_tokens(tokens, keyword_tokens):
            labels.append(keyword)
    if not labels:
        return UNLABELED_CONDITION
    return "+".join(labels)


def _has_condition_tokens(tokens: tuple[str, ...], keyword_tokens: tuple[str, ...]) -> bool:
    keyword_length = len(keyword_tokens)
    if keyword_length == 0 or len(tokens) < keyword_length:
        return False

    return any(
        tokens[index : index + keyword_length] == keyword_tokens
        for index in range(len(tokens) - keyword_length + 1)
    )


def _status_counts() -> dict[str, int]:
    return {"total": 0, "success": 0, "partial": 0, "failed": 0}


def _image_size_label(image_width: object, image_height: object) -> str:
    if isinstance(image_width, int) and isinstance(image_height, int):
        return f"{image_width}x{image_height}"
    return "unknown"


def build_image_debug_dir(image_path: Path, debug_root_dir: Path) -> Path:
    suffix = image_path.suffix.lower().lstrip(".")
    if suffix:
        return debug_root_dir / f"{image_path.stem}_{suffix}"
    return debug_root_dir / image_path.stem


def _build_active_validation_payload(
    active_payload: dict[str, object],
    *,
    ocr_result,
    resolved_result,
    gender_result,
) -> dict[str, object]:
    match_result = resolved_result.match_result
    payload = dict(active_payload)
    payload.update(
        {
            "raw_text": ocr_result.raw_text,
            "normalized_text": match_result.normalized_text,
            "matched": match_result.matched,
            "match_score": match_result.score,
            "match_reason": match_result.reason,
            "top_candidates": [
                candidate.to_dict()
                for candidate in match_result.top_candidates
            ],
            "ocr_confidence": ocr_result.ocr_confidence,
            "preprocess_name": ocr_result.preprocess_name,
            "name_crop_path": str(ocr_result.crop_path),
            "preprocessed_path": str(ocr_result.preprocessed_path),
            "gender_crop_path": str(gender_result.crop_path),
            "gender_score": gender_result.score,
            "gender_reason": gender_result.reason,
        }
    )
    return payload


def _build_failed_active_payload(metadata: ActivePokemonMetadata) -> dict[str, object]:
    return {
        "raw_text": UNKNOWN_SPECIES_ID,
        "species_id": UNKNOWN_SPECIES_ID,
        "display_name": UNKNOWN_SPECIES_ID,
        "gender": UNKNOWN_SPECIES_ID,
        "form": metadata.form.strip() or "unknown",
        "mega_state": metadata.mega_state.strip() or "base",
        "confidence": 0.0,
    }


def validate_sample_image(image_path: Path, options: ValidationOptions) -> dict[str, object]:
    image_debug_dir = build_image_debug_dir(image_path, options.debug_root_dir)
    condition_label = infer_condition_label(image_path)
    image_width: int | None = None
    image_height: int | None = None
    resolved_regions: dict[str, object] = {}

    try:
        image = load_image(image_path)
        image_width, image_height = image.size
        resolved_regions = build_active_recognition_region_payload(image_width, image_height)
        ocr_results = extract_name_texts(image_path, image_debug_dir)
        gender_results = extract_gender_marks(image_path, image_debug_dir)
        resolved_results = resolve_name_results(
            ocr_results,
            master_data_path=options.master_data_path,
        )
        observation = build_battle_observation(
            ocr_results,
            gender_results,
            resolved_results,
            player_metadata=options.player_metadata,
            opponent_metadata=options.opponent_metadata,
        )
        observation_path = image_debug_dir / "observation.json"
        write_observation_json(observation, observation_path)
        observation_payload = observation.to_dict()
        active_payload = {
            active_key: _build_active_validation_payload(
                observation_payload[active_key],
                ocr_result=ocr_results[name_region],
                resolved_result=resolved_results[name_region],
                gender_result=gender_results[gender_region],
            )
            for active_key, (name_region, gender_region) in _ACTIVE_REGION_MAP.items()
        }

        status = classify_validation_status(
            str(active_payload["player_active"]["species_id"]),
            str(active_payload["opponent_active"]["species_id"]),
        )

        return {
            "file_name": image_path.name,
            "condition_label": condition_label,
            "status": status,
            "error_message": None,
            "image_width": image_width,
            "image_height": image_height,
            "image_size": _image_size_label(image_width, image_height),
            "resolved_regions": resolved_regions,
            "debug_dir": str(image_debug_dir),
            "observation_path": str(observation_path),
            "player_active": active_payload["player_active"],
            "opponent_active": active_payload["opponent_active"],
            "ocr": {
                region_name: result.to_dict()
                for region_name, result in ocr_results.items()
            },
            "name_match": {
                region_name: result.to_dict()
                for region_name, result in resolved_results.items()
            },
            "gender": {
                region_name: result.to_dict()
                for region_name, result in gender_results.items()
            },
        }
    except Exception as exc:  # noqa: BLE001 - validation should continue per image.
        return {
            "file_name": image_path.name,
            "condition_label": condition_label,
            "status": "failed",
            "error_message": str(exc),
            "image_width": image_width,
            "image_height": image_height,
            "image_size": _image_size_label(image_width, image_height),
            "resolved_regions": resolved_regions,
            "debug_dir": str(image_debug_dir),
            "observation_path": None,
            "player_active": _build_failed_active_payload(options.player_metadata),
            "opponent_active": _build_failed_active_payload(options.opponent_metadata),
        }


def build_validation_report(
    results: list[dict[str, object]],
) -> dict[str, object]:
    summary = {"success": 0, "partial": 0, "failed": 0}
    by_condition: dict[str, dict[str, int]] = {}
    by_image_size: dict[str, dict[str, int]] = {}
    for result in results:
        status = str(result.get("status", "failed"))
        if status not in summary:
            status = "failed"
        summary[status] += 1

        condition_label = str(result.get("condition_label") or UNLABELED_CONDITION)
        condition_counts = by_condition.setdefault(condition_label, _status_counts())
        condition_counts["total"] += 1
        condition_counts[status] += 1

        image_size = _image_size_label(
            result.get("image_width"),
            result.get("image_height"),
        )
        size_counts = by_image_size.setdefault(image_size, _status_counts())
        size_counts["total"] += 1
        size_counts[status] += 1

    return {
        "tuning_parameters": build_tuning_parameters_payload(),
        "summary": {
            "total": len(results),
            **summary,
            "by_condition": by_condition,
            "by_image_size": by_image_size,
        },
        "results": results,
    }


def run_sample_validation(options: ValidationOptions) -> dict[str, object]:
    images = list_sample_images(options.samples_dir)
    results = [validate_sample_image(image_path, options) for image_path in images]
    report = build_validation_report(results)
    write_validation_report(report, options.report_path)
    return report


def write_validation_report(report: dict[str, object], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
