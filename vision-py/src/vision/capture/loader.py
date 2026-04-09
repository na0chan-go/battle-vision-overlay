from __future__ import annotations

from pathlib import Path

from PIL import Image


def load_image(image_path: Path) -> Image.Image:
    if not image_path.exists():
        raise FileNotFoundError(f"sample image not found: {image_path}")

    try:
        image = Image.open(image_path)
        image.load()
    except OSError as exc:
        raise ValueError(f"failed to load image: {image_path}") from exc

    return image
