from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from vision.gender import extract_gender_marks
from vision.name_match import resolve_name_results
from vision.name_ocr import extract_name_texts
from vision.observation import (
    ActivePokemonMetadata,
    build_battle_observation,
    write_observation_json,
)

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg"})
UNKNOWN_SPECIES_ID = "unknown"


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


def build_image_debug_dir(image_path: Path, debug_root_dir: Path) -> Path:
    return debug_root_dir / image_path.name


def validate_sample_image(image_path: Path, options: ValidationOptions) -> dict[str, object]:
    image_debug_dir = build_image_debug_dir(image_path, options.debug_root_dir)

    try:
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

        status = classify_validation_status(
            str(observation_payload["player_active"]["species_id"]),
            str(observation_payload["opponent_active"]["species_id"]),
        )

        return {
            "file_name": image_path.name,
            "status": status,
            "error_message": None,
            "debug_dir": str(image_debug_dir),
            "observation_path": str(observation_path),
            "player_active": observation_payload["player_active"],
            "opponent_active": observation_payload["opponent_active"],
            "ocr": {
                region_name: result.to_dict()
                for region_name, result in ocr_results.items()
            },
            "gender": {
                region_name: result.to_dict()
                for region_name, result in gender_results.items()
            },
        }
    except Exception as exc:  # noqa: BLE001 - validation should continue per image.
        return {
            "file_name": image_path.name,
            "status": "failed",
            "error_message": str(exc),
            "debug_dir": str(image_debug_dir),
            "observation_path": None,
            "player_active": {
                "species_id": UNKNOWN_SPECIES_ID,
                "display_name": UNKNOWN_SPECIES_ID,
                "gender": UNKNOWN_SPECIES_ID,
            },
            "opponent_active": {
                "species_id": UNKNOWN_SPECIES_ID,
                "display_name": UNKNOWN_SPECIES_ID,
                "gender": UNKNOWN_SPECIES_ID,
            },
        }


def build_validation_report(
    results: list[dict[str, object]],
) -> dict[str, object]:
    summary = {"success": 0, "partial": 0, "failed": 0}
    for result in results:
        status = str(result.get("status", "failed"))
        if status not in summary:
            status = "failed"
        summary[status] += 1

    return {
        "summary": {
            "total": len(results),
            **summary,
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
