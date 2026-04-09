from __future__ import annotations

from vision.dto.region import Region

REFERENCE_WIDTH = 1920
REFERENCE_HEIGHT = 1080

# Fixed region coordinates for the initial battle-screen PoC.
# These are intentionally centralized so they can be tuned later
# without rewriting the crop pipeline.
REFERENCE_STATUS_PANEL_REGIONS: tuple[Region, ...] = (
    Region(name="opponent_status_panel", left=1480, top=37, width=400, height=128),
    Region(name="player_status_panel", left=43, top=910, width=404, height=140),
)


def _scale_regions(
    regions: tuple[Region, ...], image_width: int, image_height: int
) -> tuple[Region, ...]:
    if image_width < REFERENCE_WIDTH or image_height < REFERENCE_HEIGHT:
        raise ValueError(
            f"battle image is too small: expected at least {REFERENCE_WIDTH}x{REFERENCE_HEIGHT}, "
            f"got {image_width}x{image_height}"
        )

    scale_x = image_width / REFERENCE_WIDTH
    scale_y = image_height / REFERENCE_HEIGHT

    return tuple(
        Region(
            name=region.name,
            left=round(region.left * scale_x),
            top=round(region.top * scale_y),
            width=round(region.width * scale_x),
            height=round(region.height * scale_y),
        )
        for region in regions
    )


def build_status_panel_regions(image_width: int, image_height: int) -> tuple[Region, ...]:
    return _scale_regions(REFERENCE_STATUS_PANEL_REGIONS, image_width, image_height)
