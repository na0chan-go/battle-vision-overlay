from __future__ import annotations

import colorsys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from vision.capture.loader import load_image
from vision.debug.crop_debug import crop_region, save_crop
from vision.regions.battle import build_gender_regions

_MIN_ACTIVE_SCORE = 120.0
_MIN_DOMINANT_RATIO = 0.7
_MALE_HUE_MIN = 0.52
_MALE_HUE_MAX = 0.72
_FEMALE_HUE_MAX = 0.06
_FEMALE_HUE_MIN = 0.90


@dataclass(frozen=True)
class GenderClassificationResult:
    region_name: str
    crop_path: Path
    gender: str
    score: float
    male_score: float
    female_score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "crop_path": str(self.crop_path),
            "gender": self.gender,
            "score": self.score,
            "male_score": self.male_score,
            "female_score": self.female_score,
        }


def classify_gender_symbol(image: Image.Image) -> tuple[str, float, float, float]:
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
            if color_score < 0.25 or value < 0.2:
                continue

            if _MALE_HUE_MIN <= hue <= _MALE_HUE_MAX:
                male_score += color_score
            elif hue <= _FEMALE_HUE_MAX or hue >= _FEMALE_HUE_MIN:
                female_score += color_score

    active_score = male_score + female_score
    if active_score < _MIN_ACTIVE_SCORE:
        return "unknown", 0.0, male_score, female_score

    dominant_score = max(male_score, female_score)
    dominant_ratio = dominant_score / active_score
    if dominant_ratio < _MIN_DOMINANT_RATIO:
        return "unknown", dominant_ratio, male_score, female_score

    gender = "male" if male_score > female_score else "female"
    return gender, dominant_ratio, male_score, female_score


def extract_gender_marks(
    image_path: Path,
    output_dir: Path,
) -> dict[str, GenderClassificationResult]:
    image = load_image(image_path)
    regions = build_gender_regions(*image.size)

    results: dict[str, GenderClassificationResult] = {}
    for region in regions:
        cropped = crop_region(image, region)
        crop_path = output_dir / f"{region.name}.png"
        save_crop(cropped, crop_path)

        gender, score, male_score, female_score = classify_gender_symbol(cropped)
        results[region.name] = GenderClassificationResult(
            region_name=region.name,
            crop_path=crop_path,
            gender=gender,
            score=score,
            male_score=male_score,
            female_score=female_score,
        )

    return results
