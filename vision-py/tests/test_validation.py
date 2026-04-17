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
    build_validation_report,
    classify_validation_status,
    infer_condition_label,
    list_sample_images,
    run_sample_validation,
)


class ValidationTest(unittest.TestCase):
    def create_sample_image(
        self,
        image_path: Path,
        size: tuple[int, int] = (1920, 1080),
    ) -> None:
        image = Image.new("RGB", size, color=(25, 25, 35))
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

    def test_infer_condition_label_from_file_name(self) -> None:
        self.assertEqual(
            infer_condition_label(Path("battle_720p_dark_compressed.jpeg")),
            "720p+dark+compressed",
        )
        self.assertEqual(
            infer_condition_label(Path("battle_1080p_with_margin.jpeg")),
            "1080p+with_margin",
        )
        self.assertEqual(
            infer_condition_label(Path("battle_1080p_uncompressed.jpeg")),
            "1080p",
        )
        self.assertEqual(infer_condition_label(Path("battle_sample.jpeg")), "unlabeled")

    def test_build_validation_report_groups_by_condition_and_image_size(self) -> None:
        report = build_validation_report(
            [
                {
                    "status": "success",
                    "condition_label": "1080p",
                    "image_width": 1920,
                    "image_height": 1080,
                },
                {
                    "status": "partial",
                    "condition_label": "720p",
                    "image_width": 1280,
                    "image_height": 720,
                },
                {
                    "status": "failed",
                    "condition_label": "720p",
                    "image_width": 1280,
                    "image_height": 720,
                },
            ]
        )

        self.assertEqual(report["summary"]["total"], 3)
        self.assertEqual(report["summary"]["success"], 1)
        self.assertEqual(report["summary"]["partial"], 1)
        self.assertEqual(report["summary"]["failed"], 1)
        self.assertEqual(report["summary"]["by_condition"]["1080p"]["success"], 1)
        self.assertEqual(report["summary"]["by_condition"]["720p"]["total"], 2)
        self.assertEqual(report["summary"]["by_condition"]["720p"]["partial"], 1)
        self.assertEqual(report["summary"]["by_condition"]["720p"]["failed"], 1)
        self.assertEqual(report["summary"]["by_image_size"]["1920x1080"]["success"], 1)
        self.assertEqual(report["summary"]["by_image_size"]["1280x720"]["total"], 2)

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
            self.create_sample_image(samples_dir / "broken_720p_dark.jpeg", (1280, 720))
            debug_root_dir = tmp_path / "debug" / "validation"
            report_path = tmp_path / "debug" / "validation_report.json"
            master_data_path = tmp_path / "pokemon.json"
            master_data_path.write_text("[]\n", encoding="utf-8")

            def fake_extract_name_texts(image_path: Path, output_dir: Path):
                if image_path.name == "broken_720p_dark.jpeg":
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
                        player_metadata=ActivePokemonMetadata(
                            form="bond",
                            mega_state="mega",
                        ),
                        opponent_metadata=ActivePokemonMetadata(
                            form="normal",
                            mega_state="base",
                        ),
                    )
                )

            self.assertEqual(report["summary"]["total"], 2)
            self.assertEqual(report["summary"]["success"], 1)
            self.assertEqual(report["summary"]["failed"], 1)
            self.assertTrue(report_path.exists())

            saved_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_report["summary"]["partial"], 0)
            self.assertEqual(saved_report["summary"]["by_condition"]["720p+dark"]["failed"], 1)
            self.assertEqual(saved_report["summary"]["by_condition"]["unlabeled"]["success"], 1)
            self.assertEqual(saved_report["summary"]["by_image_size"]["1280x720"]["failed"], 1)
            self.assertEqual(saved_report["summary"]["by_image_size"]["1920x1080"]["success"], 1)
            self.assertEqual(saved_report["results"][0]["file_name"], "broken_720p_dark.jpeg")
            self.assertEqual(saved_report["results"][0]["status"], "failed")
            self.assertEqual(saved_report["results"][0]["condition_label"], "720p+dark")
            self.assertEqual(saved_report["results"][0]["image_width"], 1280)
            self.assertEqual(saved_report["results"][0]["image_height"], 720)
            self.assertIn("opponent_name", saved_report["results"][0]["resolved_regions"])
            self.assertEqual(saved_report["results"][0]["player_active"]["form"], "bond")
            self.assertEqual(saved_report["results"][0]["player_active"]["mega_state"], "mega")
            self.assertEqual(saved_report["results"][0]["opponent_active"]["form"], "normal")
            self.assertEqual(saved_report["results"][0]["opponent_active"]["mega_state"], "base")
            self.assertEqual(saved_report["results"][1]["file_name"], "ok.jpeg")
            self.assertEqual(saved_report["results"][1]["status"], "success")
            self.assertEqual(saved_report["results"][1]["condition_label"], "unlabeled")
            self.assertEqual(saved_report["results"][1]["image_size"], "1920x1080")
            self.assertEqual(saved_report["results"][1]["image_width"], 1920)
            self.assertEqual(saved_report["results"][1]["image_height"], 1080)
            self.assertIn("opponent_name", saved_report["results"][1]["resolved_regions"])
            self.assertIn("player_gender", saved_report["results"][1]["resolved_regions"])
            self.assertEqual(
                saved_report["results"][1]["player_active"]["raw_text"],
                "サーフゴー",
            )
            self.assertEqual(
                saved_report["results"][1]["player_active"]["mega_state"],
                "mega",
            )
            self.assertEqual(
                saved_report["results"][1]["opponent_active"]["match_score"],
                0.95,
            )
            self.assertEqual(
                saved_report["results"][1]["opponent_active"]["gender_reason"],
                "not_recorded",
            )
            self.assertEqual(
                saved_report["results"][1]["name_match"]["player_name"]["normalized_text"],
                "",
            )
            self.assertIn(
                "top_candidates",
                saved_report["results"][1]["name_match"]["player_name"],
            )
            self.assertIn(
                "preprocess_candidates",
                saved_report["results"][1]["ocr"]["player_name"],
            )
            self.assertIn(
                "ocr_confidence",
                saved_report["results"][1]["ocr"]["player_name"],
            )


if __name__ == "__main__":
    unittest.main()
