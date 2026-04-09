from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class PokemonNameEntry:
    species_id: str
    display_name: str


@dataclass(frozen=True)
class PokemonNameCandidate:
    species_id: str
    display_name: str
    score: float

    def to_dict(self) -> dict[str, str | float]:
        return {
            "species_id": self.species_id,
            "display_name": self.display_name,
            "score": round(self.score, 4),
        }


@dataclass(frozen=True)
class PokemonNameMatchResult:
    raw_text: str
    matched: bool
    species_id: str
    display_name: str
    score: float

    def to_dict(self) -> dict[str, str | float | bool]:
        return {
            "raw_text": self.raw_text,
            "matched": self.matched,
            "species_id": self.species_id,
            "display_name": self.display_name,
            "score": round(self.score, 4),
        }


def _normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    return normalized.replace(" ", "").replace("　", "")


def _expand_small_kana(value: str) -> str:
    translation_table = str.maketrans(
        {
            "ァ": "ア",
            "ィ": "イ",
            "ゥ": "ウ",
            "ェ": "エ",
            "ォ": "オ",
            "ャ": "ヤ",
            "ュ": "ユ",
            "ョ": "ヨ",
            "ッ": "ツ",
            "ヮ": "ワ",
        }
    )
    return value.translate(translation_table)


def _strip_diacritics(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return unicodedata.normalize("NFC", stripped)


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def load_pokemon_name_entries(master_data_path: Path) -> tuple[PokemonNameEntry, ...]:
    if not master_data_path.exists():
        raise FileNotFoundError(f"pokemon master data not found: {master_data_path}")

    with master_data_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ValueError("pokemon master data must be a list")

    entries: list[PokemonNameEntry] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        species_id = str(item.get("species_id", "")).strip()
        display_name = str(item.get("display_name", "")).strip()
        if not species_id or not display_name:
            continue
        entries.append(PokemonNameEntry(species_id=species_id, display_name=display_name))

    return tuple(entries)


def resolve_pokemon_name_candidates(
    raw_text: str,
    entries: tuple[PokemonNameEntry, ...],
    *,
    limit: int = 3,
) -> tuple[PokemonNameCandidate, ...]:
    normalized_raw_text = _normalize_name(raw_text)
    if not normalized_raw_text:
        return ()

    raw_text_without_diacritics = _strip_diacritics(normalized_raw_text)
    candidates: list[PokemonNameCandidate] = []

    for entry in entries:
        normalized_display_name = _normalize_name(entry.display_name)
        display_name_without_diacritics = _strip_diacritics(normalized_display_name)

        direct_score = _similarity(normalized_raw_text, normalized_display_name)
        diacritic_score = _similarity(
            raw_text_without_diacritics,
            display_name_without_diacritics,
        )
        score = max(direct_score, diacritic_score)

        candidates.append(
            PokemonNameCandidate(
                species_id=entry.species_id,
                display_name=entry.display_name,
                score=score,
            )
        )

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (-candidate.score, candidate.display_name),
    )
    return tuple(ranked_candidates[:limit])


def match_pokemon_name(
    raw_text: str,
    entries: tuple[PokemonNameEntry, ...],
    *,
    minimum_score: float = 0.6,
) -> PokemonNameMatchResult:
    normalized_raw_text = _normalize_name(raw_text)
    if not normalized_raw_text:
        return PokemonNameMatchResult(
            raw_text=raw_text,
            matched=False,
            species_id="unknown",
            display_name="unknown",
            score=0.0,
        )

    normalized_variants = {
        normalized_raw_text,
        _expand_small_kana(normalized_raw_text),
    }
    normalized_variants_without_diacritics = {
        _strip_diacritics(variant) for variant in normalized_variants
    }

    best_candidate: PokemonNameCandidate | None = None
    for entry in entries:
        normalized_display_name = _normalize_name(entry.display_name)
        display_name_variants = {
            normalized_display_name,
            _expand_small_kana(normalized_display_name),
        }
        display_name_variants_without_diacritics = {
            _strip_diacritics(variant) for variant in display_name_variants
        }

        score = 0.0
        for raw_variant in normalized_variants:
            for display_variant in display_name_variants:
                score = max(score, _similarity(raw_variant, display_variant))

        for raw_variant in normalized_variants_without_diacritics:
            for display_variant in display_name_variants_without_diacritics:
                score = max(score, _similarity(raw_variant, display_variant))

        candidate = PokemonNameCandidate(
            species_id=entry.species_id,
            display_name=entry.display_name,
            score=score,
        )
        if best_candidate is None or candidate.score > best_candidate.score:
            best_candidate = candidate

    if best_candidate is None or best_candidate.score < minimum_score:
        return PokemonNameMatchResult(
            raw_text=raw_text,
            matched=False,
            species_id="unknown",
            display_name="unknown",
            score=0.0,
        )

    return PokemonNameMatchResult(
        raw_text=raw_text,
        matched=True,
        species_id=best_candidate.species_id,
        display_name=best_candidate.display_name,
        score=best_candidate.score,
    )
