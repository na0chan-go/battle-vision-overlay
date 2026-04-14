from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class NamePreprocessConfig:
    resize_factor: int = 3
    brightness_threshold: int = 180
    trim_padding: int = 8
    binary_threshold: int = 150


@dataclass(frozen=True)
class PreprocessedImage:
    name: str
    image: Image.Image


DEFAULT_NAME_PREPROCESS_CONFIG = NamePreprocessConfig()


def trim_bright_text_region(
    image: Image.Image,
    *,
    brightness_threshold: int = DEFAULT_NAME_PREPROCESS_CONFIG.brightness_threshold,
    padding: int = DEFAULT_NAME_PREPROCESS_CONFIG.trim_padding,
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


def _to_grayscale(image: Image.Image) -> Image.Image:
    return ImageOps.grayscale(image)


def _resize_for_ocr(image: Image.Image, resize_factor: int) -> Image.Image:
    return image.resize(
        (image.width * resize_factor, image.height * resize_factor),
        resample=Image.Resampling.LANCZOS,
    )


def _increase_contrast(image: Image.Image) -> Image.Image:
    return ImageOps.autocontrast(image)


def _threshold_text(image: Image.Image, threshold: int) -> Image.Image:
    return image.point(lambda pixel: 255 if pixel >= threshold else 0)


def _sharpen_text(image: Image.Image) -> Image.Image:
    return image.filter(ImageFilter.SHARPEN)


def preprocess_name_images(
    image: Image.Image,
    config: NamePreprocessConfig = DEFAULT_NAME_PREPROCESS_CONFIG,
) -> tuple[PreprocessedImage, ...]:
    trimmed = trim_bright_text_region(
        image,
        brightness_threshold=config.brightness_threshold,
        padding=config.trim_padding,
    )
    grayscale = _to_grayscale(trimmed)
    resized = _resize_for_ocr(grayscale, config.resize_factor)
    contrast = _increase_contrast(resized)
    threshold = _threshold_text(contrast, config.binary_threshold)
    sharpened_threshold = _sharpen_text(threshold)
    resize_suffix = f"{config.resize_factor}x"

    return (
        PreprocessedImage(name="raw_crop", image=trimmed.convert("RGB")),
        PreprocessedImage(name=f"gray_{resize_suffix}", image=resized),
        PreprocessedImage(name=f"contrast_{resize_suffix}", image=contrast),
        PreprocessedImage(name=f"threshold_{resize_suffix}", image=threshold),
        PreprocessedImage(name=f"sharp_threshold_{resize_suffix}", image=sharpened_threshold),
    )
