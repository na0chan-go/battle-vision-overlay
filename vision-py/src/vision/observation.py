from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from vision.dto.observation import ActivePokemonObservation, Observation
from vision.gender import GenderClassificationResult
from vision.match.pokemon import PokemonNameMatchResult
from vision.name_match import ResolvedNameResult
from vision.name_ocr import NameOCRResult

_ACTIVE_REGION_MAP = {
    "opponent_name": ("opponent_active", "opponent_gender"),
    "player_name": ("player_active", "player_gender"),
}

DEFAULT_FORM = "unknown"
DEFAULT_MEGA_STATE = "base"


@dataclass(frozen=True)
class ActivePokemonMetadata:
    form: str = DEFAULT_FORM
    mega_state: str = DEFAULT_MEGA_STATE


def _normalize_gender(value: str) -> str:
    if value in {"male", "female"}:
        return value
    return "unknown"


def _normalize_form(value: str) -> str:
    return value.strip() if value.strip() else DEFAULT_FORM


def _normalize_mega_state(value: str) -> str:
    return value.strip() if value.strip() else DEFAULT_MEGA_STATE


def _build_active_observation(
    raw_result: NameOCRResult,
    gender_result: GenderClassificationResult,
    resolved_result: ResolvedNameResult | None,
    metadata: ActivePokemonMetadata,
) -> ActivePokemonObservation:
    match_result: PokemonNameMatchResult | None = (
        resolved_result.match_result if resolved_result is not None else None
    )
    matched = match_result is not None and match_result.matched
    species_id = match_result.species_id if matched else "unknown"
    display_name = match_result.display_name if matched else "unknown"
    gender = _normalize_gender(gender_result.gender)

    confidence = 0.0
    if matched:
        confidence = match_result.score
        if gender != "unknown":
            confidence = min(
                1.0,
                (match_result.score * 0.8) + (gender_result.score * 0.2),
            )

    return ActivePokemonObservation(
        species_id=species_id,
        display_name=display_name,
        gender=gender,
        form=_normalize_form(metadata.form),
        mega_state=_normalize_mega_state(metadata.mega_state),
        confidence=confidence,
    )


def build_battle_observation(
    ocr_results: dict[str, NameOCRResult],
    gender_results: dict[str, GenderClassificationResult],
    resolved_results: dict[str, ResolvedNameResult] | None,
    *,
    timestamp: int | None = None,
    player_metadata: ActivePokemonMetadata | None = None,
    opponent_metadata: ActivePokemonMetadata | None = None,
) -> Observation:
    active_payload: dict[str, ActivePokemonObservation] = {}
    metadata_by_active_key = {
        "player_active": player_metadata or ActivePokemonMetadata(),
        "opponent_active": opponent_metadata or ActivePokemonMetadata(),
    }

    for name_region, (active_key, gender_region) in _ACTIVE_REGION_MAP.items():
        active_payload[active_key] = _build_active_observation(
            ocr_results[name_region],
            gender_results[gender_region],
            resolved_results[name_region] if resolved_results is not None else None,
            metadata_by_active_key[active_key],
        )

    return Observation(
        scene="battle",
        timestamp=int(time.time()) if timestamp is None else int(timestamp),
        player_active=active_payload["player_active"],
        opponent_active=active_payload["opponent_active"],
    )


def write_observation_json(observation: Observation, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(observation.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
