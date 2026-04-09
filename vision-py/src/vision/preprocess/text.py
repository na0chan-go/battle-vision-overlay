from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class PreprocessedImage:
    name: str
    image: Image.Image


def trim_bright_text_region(
    image: Image.Image,
    *,
    brightness_threshold: int = 180,
    padding: int = 8,
) -> Image.Image:
    rgb_image = image.convert("RGB")
    xs: list[int] = []
    ys: list[int] = []

    for y in range(rgb_image.height):
        for x in range(rgb_image.width):
            red, green, blue = rgb_image.getpixel((x, y))
            if (
                red >= brightness_threshold
                and green >= brightness_threshold
                and blue >= brightness_threshold
            ):
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return image

    left = max(min(xs) - padding, 0)
    top = max(min(ys) - padding, 0)
    right = min(max(xs) + padding + 1, rgb_image.width)
    bottom = min(max(ys) + padding + 1, rgb_image.height)
    return image.crop((left, top, right, bottom))


def _grayscale_resized(image: Image.Image, resize_factor: int) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    return grayscale.resize(
        (grayscale.width * resize_factor, grayscale.height * resize_factor),
        resample=Image.Resampling.LANCZOS,
    )


def preprocess_name_images(image: Image.Image) -> tuple[PreprocessedImage, ...]:
    trimmed = trim_bright_text_region(image)

    gray_2x = _grayscale_resized(trimmed, 2)
    threshold_3x = _grayscale_resized(trimmed, 3).point(
        lambda pixel: 255 if pixel >= 150 else 0
    )
    sharp_3x = _grayscale_resized(trimmed, 3).filter(ImageFilter.SHARPEN)

    return (
        PreprocessedImage(name="gray_2x", image=gray_2x),
        PreprocessedImage(name="threshold_3x", image=threshold_3x),
        PreprocessedImage(name="sharp_3x", image=sharp_3x),
    )
