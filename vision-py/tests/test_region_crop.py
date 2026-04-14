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
from vision.gender import (
    GenderClassificationResult,
    classify_gender_symbol,
    classify_gender_symbol_detail,
    extract_gender_marks,
)
from vision.main import build_active_payload
from vision.match.pokemon import PokemonNameMatchResult
from vision.name_match import ResolvedNameResult
from vision.name_ocr import (
    NameOCRCandidate,
    extract_name_texts,
    select_best_ocr_candidate,
)
from vision.ocr.engine import OCRResult, OCRRuntimeError
from vision.poc import extract_regions
from vision.preprocess.text import NamePreprocessConfig, preprocess_name_images
from vision.regions.battle import build_gender_regions, build_status_panel_regions


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
            for region in build_gender_regions(*size):
                draw.ellipse(
                    (region.left, region.top, region.right, region.bottom),
                    fill=(20, 100, 250) if region.name == "opponent_gender" else (245, 70, 80),
                )
        image.save(image_path)

    def fake_region_ocr_result(self, image_path: Path) -> OCRResult:
        image_path_text = str(image_path)
        if "player_name" in image_path_text:
            return OCRResult(text="ゲッコウガ", confidence=0.9)
        return OCRResult(text="ドリュウズ", confidence=0.9)

    def raise_temporary_ocr_failure(self) -> OCRResult:
        raise OCRRuntimeError("temporary ocr failure")

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

    def test_main_crop_mode_does_not_require_easyocr_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            poison_module_dir = tmp_path / "poison"
            poison_module_dir.mkdir()
            (poison_module_dir / "easyocr.py").write_text(
                'raise ImportError("easyocr is intentionally unavailable for this test")\n',
                encoding="utf-8",
            )
            self.create_sample_image(image_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "vision.main",
                    "--image",
                    str(image_path),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=Path(__file__).resolve().parents[2],
                env={
                    **os.environ,
                    "PYTHONPATH": (
                        f"{poison_module_dir}{os.pathsep}"
                        f"{Path(__file__).resolve().parents[1] / 'src'}"
                    ),
                },
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("opponent_status_panel", result.stdout)
            self.assertIn("player_status_panel", result.stdout)

    def test_extract_name_texts_saves_debug_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=self.fake_region_ocr_result,
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(set(results.keys()), {"opponent_name", "player_name"})
            self.assertEqual(results["opponent_name"].raw_text, "ドリュウズ")
            self.assertIsNotNone(results["opponent_name"].preprocess_name)
            self.assertGreater(results["opponent_name"].ocr_confidence, 0.0)
            self.assertTrue(results["opponent_name"].preprocess_candidates)
            self.assertTrue(results["opponent_name"].crop_path.exists())
            self.assertTrue(results["opponent_name"].preprocessed_path.exists())
            self.assertTrue(results["player_name"].crop_path.exists())
            self.assertTrue(results["player_name"].preprocessed_path.exists())

    def test_preprocess_name_images_returns_raw_and_processed_variants(self) -> None:
        image = Image.new("RGB", (80, 24), color=(20, 20, 80))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 6, 62, 17), fill=(240, 240, 240))

        variants = preprocess_name_images(
            image,
            NamePreprocessConfig(resize_factor=2, binary_threshold=150),
        )

        variant_names = [variant.name for variant in variants]
        self.assertEqual(
            variant_names,
            [
                "raw_crop",
                "gray_2x",
                "contrast_2x",
                "threshold_2x",
                "sharp_threshold_2x",
            ],
        )
        self.assertEqual(variants[0].image.mode, "RGB")
        self.assertEqual(variants[1].image.mode, "L")
        self.assertGreater(variants[1].image.width, variants[0].image.width)

    def test_select_best_ocr_candidate_prefers_consensus_text(self) -> None:
        candidates = (
            NameOCRCandidate(
                preprocess_name="raw_crop",
                image_path=Path("raw.png"),
                raw_text="グッコウガ",
                confidence=0.5,
            ),
            NameOCRCandidate(
                preprocess_name="gray_3x",
                image_path=Path("gray.png"),
                raw_text="グッコウカ",
                confidence=0.9,
            ),
            NameOCRCandidate(
                preprocess_name="threshold_3x",
                image_path=Path("threshold.png"),
                raw_text="グッコウガ",
                confidence=0.7,
            ),
        )

        result = select_best_ocr_candidate(candidates)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.raw_text, "グッコウガ")
        self.assertEqual(result.preprocess_name, "threshold_3x")

    def test_extract_gender_marks_saves_debug_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            results = extract_gender_marks(image_path, output_dir)

            self.assertEqual(set(results.keys()), {"opponent_gender", "player_gender"})
            self.assertEqual(results["opponent_gender"].gender, "male")
            self.assertEqual(results["player_gender"].gender, "female")
            self.assertTrue(results["opponent_gender"].crop_path.exists())
            self.assertTrue(results["player_gender"].crop_path.exists())
            self.assertEqual(results["opponent_gender"].reason, "male_above_threshold")
            self.assertEqual(results["player_gender"].reason, "female_above_threshold")

            serialized = results["opponent_gender"].to_dict()
            self.assertIn("predicted_gender", serialized)
            self.assertIn("active_score", serialized)
            self.assertIn("threshold", serialized)
            self.assertIn("margin", serialized)
            self.assertIn("reason", serialized)

    def test_classify_gender_symbol_detail_detects_clear_male(self) -> None:
        image = Image.new("RGB", (36, 36), color=(20, 100, 250))

        result = classify_gender_symbol_detail(image)

        self.assertEqual(result.gender, "male")
        self.assertGreaterEqual(result.score, 0.7)
        self.assertEqual(result.reason, "male_above_threshold")

    def test_classify_gender_symbol_detail_detects_clear_female(self) -> None:
        image = Image.new("RGB", (36, 36), color=(245, 70, 80))

        result = classify_gender_symbol_detail(image)

        self.assertEqual(result.gender, "female")
        self.assertGreaterEqual(result.score, 0.7)
        self.assertEqual(result.reason, "female_above_threshold")

    def test_classify_gender_symbol_handles_unknown(self) -> None:
        image = Image.new("RGB", (36, 36), color=(120, 120, 120))

        gender, score, male_score, female_score = classify_gender_symbol(image)

        self.assertEqual(gender, "unknown")
        self.assertEqual(score, 0.0)
        self.assertEqual(male_score, 0.0)
        self.assertEqual(female_score, 0.0)

    def test_classify_gender_symbol_detail_reports_unknown_reason(self) -> None:
        image = Image.new("RGB", (36, 36), color=(120, 120, 120))

        result = classify_gender_symbol_detail(image)

        self.assertEqual(result.gender, "unknown")
        self.assertEqual(result.reason, "score_below_threshold")
        self.assertEqual(result.threshold, 120.0)

    def test_classify_gender_symbol_detail_returns_unknown_when_scores_are_close(self) -> None:
        image = Image.new("RGB", (36, 36), color=(120, 120, 120))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 17, 35), fill=(20, 100, 250))
        draw.rectangle((18, 0, 35, 35), fill=(245, 70, 80))

        result = classify_gender_symbol_detail(image)

        self.assertEqual(result.gender, "unknown")
        self.assertEqual(result.reason, "score_too_close")
        self.assertLess(result.margin, 0.25)

    def test_build_active_payload_includes_gender(self) -> None:
        ocr_results = {
            "opponent_name": mock.Mock(
                raw_text="ニャオニクス",
                crop_path=Path("assets/debug/opponent_name.png"),
                preprocessed_path=Path("assets/debug/opponent_name_preprocessed.png"),
                error=None,
            ),
            "player_name": mock.Mock(
                raw_text="サーフゴー",
                crop_path=Path("assets/debug/player_name.png"),
                preprocessed_path=Path("assets/debug/player_name_preprocessed.png"),
                error=None,
            ),
        }
        gender_results = {
            "opponent_gender": GenderClassificationResult(
                region_name="opponent_gender",
                crop_path=Path("assets/debug/opponent_gender.png"),
                gender="female",
                score=0.92,
                male_score=10.0,
                female_score=120.0,
            ),
            "player_gender": GenderClassificationResult(
                region_name="player_gender",
                crop_path=Path("assets/debug/player_gender.png"),
                gender="unknown",
                score=0.0,
                male_score=0.0,
                female_score=0.0,
            ),
        }
        resolved_results = {
            "opponent_name": ResolvedNameResult(
                raw_result=ocr_results["opponent_name"],
                match_result=PokemonNameMatchResult(
                    raw_text="ニャオニクス",
                    matched=True,
                    species_id="meowstic",
                    display_name="ニャオニクス",
                    score=1.0,
                ),
            ),
            "player_name": ResolvedNameResult(
                raw_result=ocr_results["player_name"],
                match_result=PokemonNameMatchResult(
                    raw_text="サーフゴー",
                    matched=True,
                    species_id="gholdengo",
                    display_name="サーフゴー",
                    score=1.0,
                ),
            ),
        }

        payload = build_active_payload(
            ocr_results,
            gender_results,
            resolved_results,
        )

        self.assertEqual(payload["opponent_active"]["gender"], "female")
        self.assertEqual(payload["opponent_active"]["species_id"], "meowstic")
        self.assertEqual(payload["player_active"]["gender"], "unknown")
        self.assertEqual(payload["player_active"]["display_name"], "サーフゴー")

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

    def test_extract_name_texts_clears_error_after_later_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=lambda path: (
                    self.raise_temporary_ocr_failure()
                    if Path(path).name == "opponent_name_raw_crop.png"
                    else self.fake_region_ocr_result(Path(path))
                ),
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(results["opponent_name"].raw_text, "ドリュウズ")
            self.assertIsNone(results["opponent_name"].error)
            self.assertTrue(results["opponent_name"].preprocess_candidates[0].error)

    def test_extract_name_texts_clears_error_after_non_best_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=lambda path: (
                    self.raise_temporary_ocr_failure()
                    if Path(path).name == "opponent_name_gray_3x.png"
                    else self.fake_region_ocr_result(Path(path))
                ),
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(results["opponent_name"].raw_text, "ドリュウズ")
            self.assertIsNone(results["opponent_name"].error)

    def test_extract_name_texts_clears_error_when_final_variant_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            image_path = tmp_path / "battle_sample.png"
            output_dir = tmp_path / "debug"
            self.create_sample_image(image_path)

            with mock.patch(
                "vision.name_ocr.recognize_text",
                side_effect=lambda path: (
                    self.raise_temporary_ocr_failure()
                    if Path(path).name == "opponent_name_sharp_threshold_3x.png"
                    else self.fake_region_ocr_result(Path(path))
                ),
            ):
                results = extract_name_texts(image_path, output_dir)

            self.assertEqual(results["opponent_name"].raw_text, "ドリュウズ")
            self.assertIsNone(results["opponent_name"].error)


if __name__ == "__main__":
    unittest.main()
