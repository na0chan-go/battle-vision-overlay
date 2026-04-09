from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vision.capture.loader import load_image
from vision.debug.crop_debug import crop_region, save_crop
from vision.ocr.engine import OCRResult, OCRRuntimeError, recognize_text
from vision.preprocess.text import preprocess_name_images
from vision.regions.battle import build_name_regions


@dataclass(frozen=True)
class NameOCRResult:
    region_name: str
    crop_path: Path
    preprocessed_path: Path
    raw_text: str
    error: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "crop_path": str(self.crop_path),
            "preprocessed_path": str(self.preprocessed_path),
            "raw_text": self.raw_text,
            "error": self.error,
        }


def extract_name_texts(image_path: Path, output_dir: Path) -> dict[str, NameOCRResult]:
    image = load_image(image_path)
    regions = build_name_regions(*image.size)

    results: dict[str, NameOCRResult] = {}
    for region in regions:
        cropped = crop_region(image, region)
        crop_path = output_dir / f"{region.name}.png"
        save_crop(cropped, crop_path)

        best_result = OCRResult(text="", confidence=-1.0)
        preprocessed_path = output_dir / f"{region.name}_preprocessed.png"
        error: str | None = None
        tried_any_variant = False

        for variant in preprocess_name_images(cropped):
            tried_any_variant = True
            variant_path = output_dir / f"{region.name}_{variant.name}.png"
            save_crop(variant.image, variant_path)

            try:
                ocr_result = recognize_text(variant_path)
            except OCRRuntimeError as exc:
                error = str(exc)
                continue

            if (
                ocr_result.confidence > best_result.confidence
                or (
                    ocr_result.confidence == best_result.confidence
                    and len(ocr_result.text) > len(best_result.text)
                )
            ):
                best_result = ocr_result
                save_crop(variant.image, preprocessed_path)

        if not tried_any_variant or best_result.confidence < 0:
            raw_text = "unknown"
            if error is None:
                error = "ocr backend failed"
        else:
            raw_text = best_result.text or "unknown"

        results[region.name] = NameOCRResult(
            region_name=region.name,
            crop_path=crop_path,
            preprocessed_path=preprocessed_path,
            raw_text=raw_text,
            error=error,
        )

    return results
