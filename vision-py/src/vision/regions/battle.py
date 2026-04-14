from __future__ import annotations

from dataclasses import dataclass

from vision.dto.region import Region

REFERENCE_WIDTH = 1920
REFERENCE_HEIGHT = 1080


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


STATUS_PANEL_REGIONS: tuple[NormalizedRegion, ...] = (
    _reference_region(
        name="opponent_status_panel",
        left=1480,
        top=37,
        width=400,
        height=128,
    ),
    _reference_region(
        name="player_status_panel",
        left=43,
        top=910,
        width=404,
        height=140,
    ),
)

NAME_REGIONS: tuple[NormalizedRegion, ...] = (
    _reference_region(name="opponent_name", left=1590, top=54, width=210, height=50),
    _reference_region(name="player_name", left=153, top=930, width=210, height=52),
)

GENDER_REGIONS: tuple[NormalizedRegion, ...] = (
    _reference_region(name="opponent_gender", left=1832, top=56, width=36, height=36),
    _reference_region(name="player_gender", left=394, top=940, width=36, height=36),
)


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
