from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from vision.capture.loader import load_image
from vision.name_ocr import extract_name_texts
from vision.ocr.engine import OCRResult, OCRRuntimeError
from vision.poc import extract_regions
from vision.regions.battle import build_status_panel_regions


class RegionCropTest(unittest.TestCase):
    def create_sample_image(self, image_path: Path, size: tuple[int, int] = (1920, 1080)) -> None:
        image = Image.new("RGB", size, color=(25, 25, 35))
        draw = ImageDraw.Draw(image)
        if size[0] >= 1920 and size[1] >= 1080:
            for region in build_status_panel_regions(*size):
                draw.rounded_rectangle(
                    (region.left, region.top, region.right, region.bottom),
                    radius=18,
                    fill=(90, 80, 210) if region.name == "opponent_status_panel" else (220, 60, 140),
                )
        image.save(image_path)

    def test_extract_regions_saves_two_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            saved_files = extract_regions(image_path, output_dir)
            regions = build_status_panel_regions(1920, 1080)

            self.assertEqual(set(saved_files.keys()), {"opponent_status_panel", "player_status_panel"})
            for region in regions:
                saved_path = saved_files[region.name]
                self.assertTrue(saved_path.exists())
                with Image.open(saved_path) as cropped:
                    self.assertEqual(cropped.size, (region.width, region.height))

    def test_extract_regions_uses_1080p_reference_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample_1080p.png"
            output_dir = tmp_path / "debug"
            image_size = (1920, 1080)
            self.create_sample_image(image_path)

            saved_files = extract_regions(image_path, output_dir)
            regions = build_status_panel_regions(*image_size)

            for region in regions:
                with Image.open(saved_files[region.name]) as cropped:
                    self.assertEqual(cropped.size, (region.width, region.height))

    def test_load_image_missing_file_raises_clear_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_image(Path("missing-sample.png"))

    def test_extract_name_regions_rejects_small_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "small.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path, size=(320, 180))

            with self.assertRaises(ValueError):
                extract_regions(image_path, output_dir)

    def test_main_reports_missing_sample(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vision.main",
                "--image",
                "missing-sample.png",
            ],
            cwd=Path(__file__).resolve().parents[2],
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
            },
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("vision crop failed", result.stderr)

    def test_main_requires_image_argument(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vision.main",
            ],
            cwd=Path(__file__).resolve().parents[2],
            env={
                **os.environ,
                "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
            },
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("--image", result.stderr)

    def test_extract_name_texts_saves_debug_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=[
                    OCRResult(text="ドリュウズ", confidence=0.9),
                    OCRResult(text="ドリュウズ", confidence=0.8),
                    OCRResult(text="ドリュウズ", confidence=0.7),
                    OCRResult(text="ゲッコウガ", confidence=0.9),
                    OCRResult(text="ゲッコウガ", confidence=0.8),
                    OCRResult(text="ゲッコウガ", confidence=0.7),
                ],
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(set(results.keys()), {"opponent_name", "player_name"})
            self.assertEqual(results["opponent_name"].raw_text, "ドリュウズ")
            self.assertTrue(results["opponent_name"].crop_path.exists())
            self.assertTrue(results["opponent_name"].preprocessed_path.exists())
            self.assertTrue(results["player_name"].crop_path.exists())
            self.assertTrue(results["player_name"].preprocessed_path.exists())

    def test_extract_name_texts_returns_unknown_on_ocr_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=OCRRuntimeError("ocr backend failed"),
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(results["opponent_name"].raw_text, "unknown")
            self.assertEqual(results["player_name"].raw_text, "unknown")
            self.assertEqual(results["opponent_name"].error, "ocr backend failed")


if __name__ == "__main__":
    unittest.main()
