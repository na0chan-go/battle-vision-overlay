from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vision.match.pokemon import (
    PokemonNameMatchResult,
    load_pokemon_name_entries,
    match_pokemon_name,
)
from vision.name_ocr import NameOCRResult


@dataclass(frozen=True)
class ResolvedNameResult:
    raw_result: NameOCRResult
    match_result: PokemonNameMatchResult

    def to_dict(self) -> dict[str, object]:
        payload = self.raw_result.to_dict()
        payload.update(self.match_result.to_dict())
        return payload


def resolve_name_results(
    ocr_results: dict[str, NameOCRResult],
    *,
    master_data_path: Path,
    limit: int = 3,
) -> dict[str, ResolvedNameResult]:
    entries = load_pokemon_name_entries(master_data_path)
    resolved_results: dict[str, ResolvedNameResult] = {}

    for region_name, ocr_result in ocr_results.items():
        match_result = match_pokemon_name(
            ocr_result.raw_text,
            entries,
        )
        resolved_results[region_name] = ResolvedNameResult(
            raw_result=ocr_result,
            match_result=match_result,
        )

    return resolved_results
