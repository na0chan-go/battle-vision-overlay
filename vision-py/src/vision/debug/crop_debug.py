from __future__ import annotations

from pathlib import Path

from PIL import Image

from vision.dto.region import Region


def crop_region(image: Image.Image, region: Region) -> Image.Image:
    image_width, image_height = image.size
    if region.left < 0 or region.top < 0:
        raise ValueError(f"region has negative origin: {region.name}")
    if region.right > image_width or region.bottom > image_height:
        raise ValueError(
            f"region {region.name} is outside image bounds {image_width}x{image_height}"
        )

    return image.crop((region.left, region.top, region.right, region.bottom))


def save_crop(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
