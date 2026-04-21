from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class NamePreprocessConfig:
    resize_factor: int = 3
    brightness_threshold: int = 180
    trim_padding: int = 8
    binary_threshold: int = 150

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class GenderClassifierConfig:
    min_active_score: float = 120.0
    min_dominant_ratio: float = 0.7
    min_score_margin: float = 0.25
    min_pixel_color_score: float = 0.25
    min_pixel_value: float = 0.2
    male_hue_min: float = 0.52
    male_hue_max: float = 0.72
    female_hue_min: float = 0.90
    female_hue_max: float = 0.06

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class RegionBoxConfig:
    name: str
    left: int
    top: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass(frozen=True)
class RegionReferenceConfig:
    reference_width: int = 1920
    reference_height: int = 1080
    status_panel_regions: tuple[RegionBoxConfig, ...] = (
        RegionBoxConfig(
            name="opponent_status_panel",
            left=1480,
            top=37,
            width=400,
            height=128,
        ),
        RegionBoxConfig(
            name="player_status_panel",
            left=43,
            top=910,
            width=404,
            height=140,
        ),
    )
    name_regions: tuple[RegionBoxConfig, ...] = (
        RegionBoxConfig(name="opponent_name", left=1590, top=54, width=210, height=50),
        RegionBoxConfig(name="player_name", left=153, top=930, width=210, height=52),
    )
    gender_regions: tuple[RegionBoxConfig, ...] = (
        RegionBoxConfig(name="opponent_gender", left=1832, top=56, width=36, height=36),
        RegionBoxConfig(name="player_gender", left=394, top=940, width=36, height=36),
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_width": self.reference_width,
            "reference_height": self.reference_height,
            "status_panel_regions": [
                region.to_dict()
                for region in self.status_panel_regions
            ],
            "name_regions": [
                region.to_dict()
                for region in self.name_regions
            ],
            "gender_regions": [
                region.to_dict()
                for region in self.gender_regions
            ],
        }


@dataclass(frozen=True)
class VisionTuningConfig:
    name_preprocess: NamePreprocessConfig = NamePreprocessConfig()
    gender_classifier: GenderClassifierConfig = GenderClassifierConfig()
    region_reference: RegionReferenceConfig = RegionReferenceConfig()

    def to_dict(self) -> dict[str, object]:
        return {
            "name_preprocess": self.name_preprocess.to_dict(),
            "gender_classifier": self.gender_classifier.to_dict(),
            "region_reference": self.region_reference.to_dict(),
        }


DEFAULT_NAME_PREPROCESS_CONFIG = NamePreprocessConfig()
DEFAULT_GENDER_CLASSIFIER_CONFIG = GenderClassifierConfig()
DEFAULT_REGION_REFERENCE_CONFIG = RegionReferenceConfig()
DEFAULT_VISION_TUNING_CONFIG = VisionTuningConfig(
    name_preprocess=DEFAULT_NAME_PREPROCESS_CONFIG,
    gender_classifier=DEFAULT_GENDER_CLASSIFIER_CONFIG,
    region_reference=DEFAULT_REGION_REFERENCE_CONFIG,
)


def build_tuning_parameters_payload(
    config: VisionTuningConfig = DEFAULT_VISION_TUNING_CONFIG,
) -> dict[str, object]:
    return config.to_dict()
