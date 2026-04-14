from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile

from vision.capture.loader import load_image
from vision.debug.crop_debug import crop_region, save_crop
from vision.dto.region import Region
from vision.ocr.engine import OCRRuntimeError, recognize_text
from vision.preprocess.text import preprocess_name_images
from vision.regions.battle import build_name_regions


@dataclass(frozen=True)
class NameOCRCandidate:
    preprocess_name: str
    image_path: Path
    raw_text: str
    confidence: float
    error: str | None = None

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "preprocess_name": self.preprocess_name,
            "image_path": str(self.image_path),
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass(frozen=True)
class NameOCRResult:
    region_name: str
    crop_path: Path
    preprocessed_path: Path
    raw_text: str
    region: Region | None = None
    error: str | None = None
    preprocess_name: str | None = None
    ocr_confidence: float = 0.0
    preprocess_candidates: tuple[NameOCRCandidate, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "crop_path": str(self.crop_path),
            "region": self.region.to_dict() if self.region is not None else None,
            "preprocessed_path": str(self.preprocessed_path),
            "raw_text": self.raw_text,
            "error": self.error,
            "preprocess_name": self.preprocess_name,
            "ocr_confidence": self.ocr_confidence,
            "preprocess_candidates": [
                candidate.to_dict()
                for candidate in self.preprocess_candidates
            ],
        }


def select_best_ocr_candidate(
    candidates: tuple[NameOCRCandidate, ...],
) -> NameOCRCandidate | None:
    successful_candidates = tuple(
        candidate
        for candidate in candidates
        if candidate.error is None and candidate.raw_text.strip()
    )
    if not successful_candidates:
        return None

    text_counts = Counter(candidate.raw_text for candidate in successful_candidates)
    best_text = max(
        text_counts,
        key=lambda text: (
            text_counts[text],
            max(
                candidate.confidence
                for candidate in successful_candidates
                if candidate.raw_text == text
            ),
        ),
    )
    return max(
        (
            candidate
            for candidate in successful_candidates
            if candidate.raw_text == best_text
        ),
        key=lambda candidate: candidate.confidence,
    )


def extract_name_texts(image_path: Path, output_dir: Path) -> dict[str, NameOCRResult]:
    image = load_image(image_path)
    regions = build_name_regions(*image.size)

    results: dict[str, NameOCRResult] = {}
    for region in regions:
        cropped = crop_region(image, region)
        crop_path = output_dir / f"{region.name}.png"
        save_crop(cropped, crop_path)

        preprocessed_path = output_dir / f"{region.name}_preprocessed.png"
        error: str | None = None
        tried_any_variant = False
        candidates: list[NameOCRCandidate] = []

        for variant in preprocess_name_images(cropped):
            tried_any_variant = True
            variant_path = output_dir / f"{region.name}_{variant.name}.png"
            save_crop(variant.image, variant_path)

            try:
                ocr_result = recognize_text(variant_path)
            except OCRRuntimeError as exc:
                error = str(exc)
                candidates.append(
                    NameOCRCandidate(
                        preprocess_name=variant.name,
                        image_path=variant_path,
                        raw_text="",
                        confidence=0.0,
                        error=error,
                    )
                )
                continue

            error = None
            candidates.append(
                NameOCRCandidate(
                    preprocess_name=variant.name,
                    image_path=variant_path,
                    raw_text=ocr_result.text,
                    confidence=ocr_result.confidence,
                    error=None,
                )
            )

        best_candidate = select_best_ocr_candidate(tuple(candidates))
        if not tried_any_variant or best_candidate is None:
            raw_text = "unknown"
            has_successful_ocr_call = any(candidate.error is None for candidate in candidates)
            if has_successful_ocr_call:
                error = None
            elif error is None:
                error = "ocr backend failed"
        else:
            raw_text = best_candidate.raw_text or "unknown"
            error = None
            copyfile(best_candidate.image_path, preprocessed_path)

        results[region.name] = NameOCRResult(
            region_name=region.name,
            crop_path=crop_path,
            region=region,
            preprocessed_path=preprocessed_path,
            raw_text=raw_text,
            error=error,
            preprocess_name=best_candidate.preprocess_name if best_candidate else None,
            ocr_confidence=best_candidate.confidence if best_candidate else 0.0,
            preprocess_candidates=tuple(candidates),
        )

    return results
