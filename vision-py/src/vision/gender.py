from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from vision.capture.loader import load_image
from vision.debug.crop_debug import crop_region, save_crop
from vision.dto.region import Region
from vision.regions.battle import build_gender_regions
from vision.tuning import DEFAULT_GENDER_CLASSIFIER_CONFIG, GenderClassifierConfig


@dataclass(frozen=True)
class GenderClassificationDecision:
    gender: str
    score: float
    male_score: float
    female_score: float
    active_score: float
    threshold: float
    margin: float
    reason: str


@dataclass(frozen=True)
class GenderClassificationResult:
    region_name: str
    crop_path: Path
    gender: str
    score: float
    male_score: float
    female_score: float
    region: Region | None = None
    active_score: float = 0.0
    threshold: float = DEFAULT_GENDER_CLASSIFIER_CONFIG.min_active_score
    margin: float = 0.0
    reason: str = "not_recorded"

    def to_dict(self) -> dict[str, object]:
        return {
            "crop_path": str(self.crop_path),
            "region": self.region.to_dict() if self.region is not None else None,
            "gender": self.gender,
            "predicted_gender": self.gender,
            "score": self.score,
            "male_score": self.male_score,
            "female_score": self.female_score,
            "active_score": self.active_score,
            "threshold": self.threshold,
            "margin": self.margin,
            "reason": self.reason,
        }


def classify_gender_symbol_detail(
    image: Image.Image,
    config: GenderClassifierConfig = DEFAULT_GENDER_CLASSIFIER_CONFIG,
) -> GenderClassificationDecision:
    male_score = 0.0
    female_score = 0.0

    rgb_image = image.convert("RGB")
    pixels = rgb_image.load()
    width, height = rgb_image.size

    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            hue, saturation, value = colorsys.rgb_to_hsv(
                red / 255.0,
                green / 255.0,
                blue / 255.0,
            )
            color_score = saturation * value
            if (
                color_score < config.min_pixel_color_score
                or value < config.min_pixel_value
            ):
                continue

            if config.male_hue_min <= hue <= config.male_hue_max:
                male_score += color_score
            elif hue <= config.female_hue_max or hue >= config.female_hue_min:
                female_score += color_score

    active_score = male_score + female_score
    if active_score < config.min_active_score:
        return GenderClassificationDecision(
            gender="unknown",
            score=0.0,
            male_score=male_score,
            female_score=female_score,
            active_score=active_score,
            threshold=config.min_active_score,
            margin=0.0,
            reason="score_below_threshold",
        )

    dominant_score = max(male_score, female_score)
    dominant_ratio = dominant_score / active_score
    margin = abs(male_score - female_score) / active_score
    if margin < config.min_score_margin:
        return GenderClassificationDecision(
            gender="unknown",
            score=dominant_ratio,
            male_score=male_score,
            female_score=female_score,
            active_score=active_score,
            threshold=config.min_score_margin,
            margin=margin,
            reason="score_too_close",
        )

    if dominant_ratio < config.min_dominant_ratio:
        return GenderClassificationDecision(
            gender="unknown",
            score=dominant_ratio,
            male_score=male_score,
            female_score=female_score,
            active_score=active_score,
            threshold=config.min_dominant_ratio,
            margin=margin,
            reason="dominant_ratio_below_threshold",
        )

    gender = "male" if male_score > female_score else "female"
    return GenderClassificationDecision(
        gender=gender,
        score=dominant_ratio,
        male_score=male_score,
        female_score=female_score,
        active_score=active_score,
        threshold=config.min_dominant_ratio,
        margin=margin,
        reason=f"{gender}_above_threshold",
    )


def classify_gender_symbol(image: Image.Image) -> tuple[str, float, float, float]:
    decision = classify_gender_symbol_detail(image)
    return decision.gender, decision.score, decision.male_score, decision.female_score


def extract_gender_marks(
    image_path: Path,
    output_dir: Path,
) -> dict[str, GenderClassificationResult]:
    image = load_image(image_path)
    regions = build_gender_regions(*image.size)

    results: dict[str, GenderClassificationResult] = {}
    for region in regions:
        cropped = crop_region(image, region)
        crop_path = output_dir / f"{region.name}_raw.png"
        save_crop(cropped, crop_path)

        decision = classify_gender_symbol_detail(cropped)
        results[region.name] = GenderClassificationResult(
            region_name=region.name,
            crop_path=crop_path,
            gender=decision.gender,
            score=decision.score,
            male_score=decision.male_score,
            female_score=decision.female_score,
            region=region,
            active_score=decision.active_score,
            threshold=decision.threshold,
            margin=decision.margin,
            reason=decision.reason,
        )

    return results
