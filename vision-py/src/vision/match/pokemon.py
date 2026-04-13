from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

DEFAULT_MINIMUM_SCORE = 0.72
DEFAULT_CANDIDATE_LIMIT = 3
UNKNOWN_NAME = "unknown"
_LEVEL_PATTERN = re.compile(r"(?i)(?:Lv|Level)\.?\s*\d+")


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
    normalized_text: str = ""
    reason: str = ""
    top_candidates: tuple[PokemonNameCandidate, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "matched": self.matched,
            "species_id": self.species_id,
            "display_name": self.display_name,
            "score": round(self.score, 4),
            "reason": self.reason,
            "top_candidates": [
                candidate.to_dict() for candidate in self.top_candidates
            ],
        }


def _is_name_character(char: str) -> bool:
    codepoint = ord(char)
    if char in {"ー", "・", "ヵ", "ヶ", "ゔ", "ヴ", "♂", "♀"}:
        return True
    if char.isascii() and char.isalnum():
        return True
    return (
        0x3040 <= codepoint <= 0x309F
        or 0x30A0 <= codepoint <= 0x30FF
        or 0x3400 <= codepoint <= 0x9FFF
    )


def _hiragana_to_katakana(value: str) -> str:
    chars: list[str] = []
    for char in value:
        codepoint = ord(char)
        if 0x3041 <= codepoint <= 0x3096:
            chars.append(chr(codepoint + 0x60))
        else:
            chars.append(char)
    return "".join(chars)


def normalize_pokemon_name_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    normalized = _LEVEL_PATTERN.sub("", normalized)
    without_space = "".join(char for char in normalized if not char.isspace())
    name_only = "".join(char for char in without_space if _is_name_character(char))
    return _hiragana_to_katakana(name_only).upper()


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


def _name_variants(value: str) -> tuple[str, ...]:
    variants = {
        value,
        _expand_small_kana(value),
    }
    variants.update(_strip_diacritics(variant) for variant in tuple(variants))
    return tuple(variant for variant in variants if variant)


def _score_name_match(raw_text: str, display_name: str) -> float:
    score = 0.0
    for raw_variant in _name_variants(raw_text):
        for display_variant in _name_variants(display_name):
            if raw_variant == display_variant:
                return 1.0
            score = max(score, _similarity(raw_variant, display_variant))
            if raw_variant in display_variant or display_variant in raw_variant:
                shorter = min(len(raw_variant), len(display_variant))
                longer = max(len(raw_variant), len(display_variant))
                score = max(score, shorter / longer)
    return score


def _rank_candidates(
    raw_text: str,
    entries: tuple[PokemonNameEntry, ...],
) -> tuple[PokemonNameCandidate, ...]:
    candidates_by_key: dict[tuple[str, str], PokemonNameCandidate] = {}

    for entry in entries:
        normalized_display_name = normalize_pokemon_name_text(entry.display_name)
        if not normalized_display_name:
            continue

        candidate = PokemonNameCandidate(
            species_id=entry.species_id,
            display_name=entry.display_name,
            score=_score_name_match(raw_text, normalized_display_name),
        )
        key = (candidate.species_id, candidate.display_name)
        current_candidate = candidates_by_key.get(key)
        if current_candidate is None or candidate.score > current_candidate.score:
            candidates_by_key[key] = candidate

    return tuple(
        sorted(
            candidates_by_key.values(),
            key=lambda candidate: (-candidate.score, candidate.display_name),
        )
    )


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
        entry = PokemonNameEntry(species_id=species_id, display_name=display_name)
        if entry not in entries:
            entries.append(entry)

    return tuple(entries)


def resolve_pokemon_name_candidates(
    raw_text: str,
    entries: tuple[PokemonNameEntry, ...],
    *,
    limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> tuple[PokemonNameCandidate, ...]:
    normalized_raw_text = normalize_pokemon_name_text(raw_text)
    if not normalized_raw_text:
        return ()

    return _rank_candidates(normalized_raw_text, entries)[:limit]


def match_pokemon_name(
    raw_text: str,
    entries: tuple[PokemonNameEntry, ...],
    *,
    minimum_score: float = DEFAULT_MINIMUM_SCORE,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
) -> PokemonNameMatchResult:
    normalized_raw_text = normalize_pokemon_name_text(raw_text)
    if not normalized_raw_text:
        return PokemonNameMatchResult(
            raw_text=raw_text,
            matched=False,
            species_id=UNKNOWN_NAME,
            display_name=UNKNOWN_NAME,
            score=0.0,
            normalized_text=normalized_raw_text,
            reason="empty_after_normalize",
        )

    top_candidates = _rank_candidates(normalized_raw_text, entries)[:candidate_limit]
    best_candidate = top_candidates[0] if top_candidates else None

    if best_candidate is None:
        return PokemonNameMatchResult(
            raw_text=raw_text,
            matched=False,
            species_id=UNKNOWN_NAME,
            display_name=UNKNOWN_NAME,
            score=0.0,
            normalized_text=normalized_raw_text,
            reason="no_candidates",
            top_candidates=top_candidates,
        )

    if best_candidate.score < minimum_score:
        return PokemonNameMatchResult(
            raw_text=raw_text,
            matched=False,
            species_id=UNKNOWN_NAME,
            display_name=UNKNOWN_NAME,
            score=0.0,
            normalized_text=normalized_raw_text,
            reason="below_threshold",
            top_candidates=top_candidates,
        )

    return PokemonNameMatchResult(
        raw_text=raw_text,
        matched=True,
        species_id=best_candidate.species_id,
        display_name=best_candidate.display_name,
        score=best_candidate.score,
        normalized_text=normalized_raw_text,
        reason="exact_match" if best_candidate.score == 1.0 else "best_similarity",
        top_candidates=top_candidates,
    )
