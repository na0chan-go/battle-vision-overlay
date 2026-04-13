from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from vision.gender import GenderClassificationResult
from vision.match.pokemon import PokemonNameMatchResult
from vision.name_match import ResolvedNameResult
from vision.name_ocr import NameOCRResult
from vision.observation import ActivePokemonMetadata
from vision.validation import (
    ValidationOptions,
    build_image_debug_dir,
    classify_validation_status,
    list_sample_images,
    run_sample_validation,
)


class ValidationTest(unittest.TestCase):
    def create_sample_image(self, image_path: Path) -> None:
        image = Image.new("RGB", (1920, 1080), color=(25, 25, 35))
        image.save(image_path)

    def make_ocr_results(self, output_dir: Path) -> dict[str, NameOCRResult]:
        return {
            "opponent_name": NameOCRResult(
                region_name="opponent_name",
                crop_path=output_dir / "opponent_name.png",
                preprocessed_path=output_dir / "opponent_name_preprocessed.png",
                raw_text="ガブリアス",
                error=None,
            ),
            "player_name": NameOCRResult(
                region_name="player_name",
                crop_path=output_dir / "player_name.png",
                preprocessed_path=output_dir / "player_name_preprocessed.png",
                raw_text="サーフゴー",
                error=None,
            ),
        }

    def make_gender_results(self, output_dir: Path) -> dict[str, GenderClassificationResult]:
        return {
            "opponent_gender": GenderClassificationResult(
                region_name="opponent_gender",
                crop_path=output_dir / "opponent_gender.png",
                gender="male",
                score=0.9,
                male_score=120.0,
                female_score=0.0,
            ),
            "player_gender": GenderClassificationResult(
                region_name="player_gender",
                crop_path=output_dir / "player_gender.png",
                gender="unknown",
                score=0.0,
                male_score=0.0,
                female_score=0.0,
            ),
        }

    def make_resolved_results(
        self,
        ocr_results: dict[str, NameOCRResult],
    ) -> dict[str, ResolvedNameResult]:
        return {
            "opponent_name": ResolvedNameResult(
                raw_result=ocr_results["opponent_name"],
                match_result=PokemonNameMatchResult(
                    raw_text="ガブリアス",
                    matched=True,
                    species_id="garchomp",
                    display_name="ガブリアス",
                    score=0.95,
                ),
            ),
            "player_name": ResolvedNameResult(
                raw_result=ocr_results["player_name"],
                match_result=PokemonNameMatchResult(
                    raw_text="サーフゴー",
                    matched=True,
                    species_id="gholdengo",
                    display_name="サーフゴー",
                    score=0.9,
                ),
            ),
        }

    def test_classify_validation_status(self) -> None:
        self.assertEqual(classify_validation_status("gholdengo", "garchomp"), "success")
        self.assertEqual(classify_validation_status("unknown", "garchomp"), "partial")
        self.assertEqual(classify_validation_status("gholdengo", "unknown"), "partial")
        self.assertEqual(classify_validation_status("unknown", "unknown"), "failed")

    def test_list_sample_images_filters_supported_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            samples_dir = Path(tmp_dir)
            (samples_dir / "sample.jpeg").write_bytes(b"")
            (samples_dir / "sample.PNG").write_bytes(b"")
            (samples_dir / "note.txt").write_text("skip", encoding="utf-8")

            images = list_sample_images(samples_dir)

            self.assertEqual([path.name for path in images], ["sample.PNG", "sample.jpeg"])

    def test_build_image_debug_dir_includes_extension(self) -> None:
        debug_root_dir = Path("debug")

        jpg_debug_dir = build_image_debug_dir(Path("battle.jpg"), debug_root_dir)
        png_debug_dir = build_image_debug_dir(Path("battle.png"), debug_root_dir)

        self.assertEqual(jpg_debug_dir, debug_root_dir / "battle.jpg")
        self.assertEqual(png_debug_dir, debug_root_dir / "battle.png")
        self.assertNotEqual(jpg_debug_dir, png_debug_dir)

    def test_run_sample_validation_continues_after_image_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            samples_dir = tmp_path / "samples"
            samples_dir.mkdir()
            self.create_sample_image(samples_dir / "ok.jpeg")
            self.create_sample_image(samples_dir / "broken.jpeg")
            debug_root_dir = tmp_path / "debug" / "validation"
            report_path = tmp_path / "debug" / "validation_report.json"
            master_data_path = tmp_path / "pokemon.json"
            master_data_path.write_text("[]\n", encoding="utf-8")

            def fake_extract_name_texts(image_path: Path, output_dir: Path):
                if image_path.name == "broken.jpeg":
                    raise ValueError("sample is not readable")
                return self.make_ocr_results(output_dir)

            def fake_extract_gender_marks(_image_path: Path, output_dir: Path):
                return self.make_gender_results(output_dir)

            def fake_resolve_name_results(ocr_results, *, master_data_path):
                return self.make_resolved_results(ocr_results)

            with (
                mock.patch(
                    "vision.validation.extract_name_texts",
                    side_effect=fake_extract_name_texts,
                ),
                mock.patch(
                    "vision.validation.extract_gender_marks",
                    side_effect=fake_extract_gender_marks,
                ),
                mock.patch(
                    "vision.validation.resolve_name_results",
                    side_effect=fake_resolve_name_results,
                ),
            ):
                report = run_sample_validation(
                    ValidationOptions(
                        samples_dir=samples_dir,
                        debug_root_dir=debug_root_dir,
                        report_path=report_path,
                        master_data_path=master_data_path,
                        player_metadata=ActivePokemonMetadata(),
                        opponent_metadata=ActivePokemonMetadata(),
                    )
                )

            self.assertEqual(report["summary"]["total"], 2)
            self.assertEqual(report["summary"]["success"], 1)
            self.assertEqual(report["summary"]["failed"], 1)
            self.assertTrue(report_path.exists())

            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["summary"]["partial"], 0)
            self.assertEqual(saved_report["results"][0]["file_name"], "broken.jpeg")
            self.assertEqual(saved_report["results"][0]["status"], "failed")
            self.assertEqual(saved_report["results"][1]["file_name"], "ok.jpeg")
            self.assertEqual(saved_report["results"][1]["status"], "success")
            self.assertEqual(
                saved_report["results"][1]["name_match"]["player_name"]["normalized_text"],
                "",
            )
            self.assertIn(
                "top_candidates",
                saved_report["results"][1]["name_match"]["player_name"],
            )


if __name__ == "__main__":
    unittest.main()
