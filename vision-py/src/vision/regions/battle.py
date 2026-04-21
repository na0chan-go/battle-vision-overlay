from __future__ import annotations

from dataclasses import dataclass

from vision.dto.region import Region
from vision.tuning import DEFAULT_REGION_REFERENCE_CONFIG, RegionBoxConfig

REFERENCE_WIDTH = DEFAULT_REGION_REFERENCE_CONFIG.reference_width
REFERENCE_HEIGHT = DEFAULT_REGION_REFERENCE_CONFIG.reference_height


@dataclass(frozen=True)
class NormalizedRegion:
    name: str
    left: float
    top: float
    width: float
    height: float

    @classmethod
    def from_reference_pixels(
        cls,
        *,
        name: str,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> NormalizedRegion:
        return cls(
            name=name,
            left=left / REFERENCE_WIDTH,
            top=top / REFERENCE_HEIGHT,
            width=width / REFERENCE_WIDTH,
            height=height / REFERENCE_HEIGHT,
        )

    def resolve(self, image_width: int, image_height: int) -> Region:
        if image_width <= 0 or image_height <= 0:
            raise ValueError(
                f"battle image size must be positive: got {image_width}x{image_height}"
            )

        left = round(self.left * image_width)
        top = round(self.top * image_height)
        right = round((self.left + self.width) * image_width)
        bottom = round((self.top + self.height) * image_height)

        left = min(max(left, 0), image_width - 1)
        top = min(max(top, 0), image_height - 1)
        right = min(max(right, left + 1), image_width)
        bottom = min(max(bottom, top + 1), image_height)

        return Region(
            name=self.name,
            left=left,
            top=top,
            width=right - left,
            height=bottom - top,
        )


def _reference_region(
    *,
    name: str,
    left: int,
    top: int,
    width: int,
    height: int,
) -> NormalizedRegion:
    return NormalizedRegion.from_reference_pixels(
        name=name,
        left=left,
        top=top,
        width=width,
        height=height,
    )


def _reference_regions(
    regions: tuple[RegionBoxConfig, ...],
) -> tuple[NormalizedRegion, ...]:
    return tuple(
        _reference_region(
            name=region.name,
            left=region.left,
            top=region.top,
            width=region.width,
            height=region.height,
        )
        for region in regions
    )


STATUS_PANEL_REGIONS = _reference_regions(
    DEFAULT_REGION_REFERENCE_CONFIG.status_panel_regions,
)
NAME_REGIONS = _reference_regions(DEFAULT_REGION_REFERENCE_CONFIG.name_regions)
GENDER_REGIONS = _reference_regions(DEFAULT_REGION_REFERENCE_CONFIG.gender_regions)


def resolve_regions(
    regions: tuple[NormalizedRegion, ...], image_width: int, image_height: int
) -> tuple[Region, ...]:
    return tuple(region.resolve(image_width, image_height) for region in regions)


def build_status_panel_regions(image_width: int, image_height: int) -> tuple[Region, ...]:
    return resolve_regions(STATUS_PANEL_REGIONS, image_width, image_height)


def build_name_regions(image_width: int, image_height: int) -> tuple[Region, ...]:
    return resolve_regions(NAME_REGIONS, image_width, image_height)


def build_gender_regions(image_width: int, image_height: int) -> tuple[Region, ...]:
    return resolve_regions(GENDER_REGIONS, image_width, image_height)


def build_active_recognition_regions(
    image_width: int,
    image_height: int,
) -> dict[str, Region]:
    regions = (
        *build_name_regions(image_width, image_height),
        *build_gender_regions(image_width, image_height),
    )
    return {region.name: region for region in regions}


def build_active_recognition_region_payload(
    image_width: int,
    image_height: int,
) -> dict[str, dict[str, int | str]]:
    return {
        name: region.to_dict()
        for name, region in build_active_recognition_regions(image_width, image_height).items()
    }
