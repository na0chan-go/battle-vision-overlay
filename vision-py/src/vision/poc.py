from __future__ import annotations

from pathlib import Path

from vision.capture.loader import load_image
from vision.debug.crop_debug import crop_region, save_crop
from vision.dto.region import Region
from vision.regions.battle import build_status_panel_regions


def extract_regions(image_path: Path, output_dir: Path) -> dict[str, Path]:
    image = load_image(image_path)
    regions = build_status_panel_regions(*image.size)

    saved_files: dict[str, Path] = {}
    for region in regions:
        cropped = crop_region(image, region)
        output_path = output_dir / f"{region.name}_raw.png"
        save_crop(cropped, output_path)
        saved_files[region.name] = output_path

    return saved_files


def list_regions(image_width: int, image_height: int) -> tuple[Region, ...]:
    return build_status_panel_regions(image_width, image_height)
