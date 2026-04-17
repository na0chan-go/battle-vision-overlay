from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vision.dto.observation import ActivePokemonObservation, Observation
from vision.gender import GenderClassificationResult
from vision.match.pokemon import PokemonNameMatchResult
from vision.name_match import ResolvedNameResult
from vision.name_ocr import NameOCRResult
from vision.observation import (
    DEFAULT_FORM,
    DEFAULT_MEGA_STATE,
    ActivePokemonMetadata,
    build_battle_observation,
    write_observation_json,
)


class ObservationTest(unittest.TestCase):
    def make_ocr_results(self) -> dict[str, NameOCRResult]:
        return {
            "opponent_name": NameOCRResult(
                region_name="opponent_name",
                crop_path=Path("assets/debug/opponent_name.png"),
                preprocessed_path=Path("assets/debug/opponent_name_preprocessed.png"),
                raw_text="ガブリアス",
                error=None,
            ),
            "player_name": NameOCRResult(
                region_name="player_name",
                crop_path=Path("assets/debug/player_name.png"),
                preprocessed_path=Path("assets/debug/player_name_preprocessed.png"),
                raw_text="サーフゴー",
                error=None,
            ),
        }

    def make_gender_results(self) -> dict[str, GenderClassificationResult]:
        return {
            "opponent_gender": GenderClassificationResult(
                region_name="opponent_gender",
                crop_path=Path("assets/debug/opponent_gender.png"),
                gender="male",
                score=0.93,
                male_score=120.0,
                female_score=0.0,
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

    def make_resolved_results(self) -> dict[str, ResolvedNameResult]:
        ocr_results = self.make_ocr_results()
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

    def test_observation_to_dict_serializes_expected_shape(self) -> None:
        observation = Observation(
            scene="battle",
            timestamp=1710000000,
            player_active=ActivePokemonObservation(
                species_id="gholdengo",
                display_name="サーフゴー",
                gender="unknown",
                form="unknown",
                mega_state="base",
                confidence=0.9,
            ),
            opponent_active=ActivePokemonObservation(
                species_id="garchomp",
                display_name="ガブリアス",
                gender="male",
                form="unknown",
                mega_state="base",
                confidence=0.954,
            ),
        )

        payload = observation.to_dict()

        self.assertEqual(payload["scene"], "battle")
        self.assertEqual(payload["timestamp"], 1710000000)
        self.assertIsInstance(payload["timestamp"], int)
        self.assertEqual(payload["player_active"]["species_id"], "gholdengo")
        self.assertIsInstance(payload["player_active"]["species_id"], str)
        self.assertEqual(payload["opponent_active"]["gender"], "male")

    def test_build_battle_observation_includes_both_active_slots(self) -> None:
        observation = build_battle_observation(
            self.make_ocr_results(),
            self.make_gender_results(),
            self.make_resolved_results(),
            timestamp=1710000000,
        )

        payload = observation.to_dict()
        self.assertEqual(payload["scene"], "battle")
        self.assertEqual(payload["timestamp"], 1710000000)
        self.assertEqual(payload["player_active"]["display_name"], "サーフゴー")
        self.assertEqual(payload["opponent_active"]["species_id"], "garchomp")
        self.assertEqual(payload["opponent_active"]["gender"], "male")
        self.assertEqual(payload["player_active"]["gender"], "unknown")
        self.assertEqual(payload["player_active"]["form"], DEFAULT_FORM)
        self.assertEqual(payload["player_active"]["mega_state"], DEFAULT_MEGA_STATE)
        self.assertEqual(payload["opponent_active"]["form"], DEFAULT_FORM)
        self.assertEqual(payload["opponent_active"]["mega_state"], DEFAULT_MEGA_STATE)

    def test_build_battle_observation_allows_form_and_mega_overrides(self) -> None:
        observation = build_battle_observation(
            self.make_ocr_results(),
            self.make_gender_results(),
            self.make_resolved_results(),
            timestamp=1710000000,
            player_metadata=ActivePokemonMetadata(
                form="unknown",
                mega_state="mega",
            ),
            opponent_metadata=ActivePokemonMetadata(
                form="normal",
                mega_state="base",
            ),
        )

        self.assertEqual(observation.player_active.form, "unknown")
        self.assertEqual(observation.player_active.mega_state, "mega")
        self.assertEqual(observation.opponent_active.form, "normal")
        self.assertEqual(observation.opponent_active.mega_state, "base")

    def test_build_battle_observation_rejects_invalid_mega_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "mega_state must be one of"):
            build_battle_observation(
                self.make_ocr_results(),
                self.make_gender_results(),
                self.make_resolved_results(),
                timestamp=1710000000,
                player_metadata=ActivePokemonMetadata(mega_state="unknown"),
            )

    def test_build_battle_observation_returns_unknown_for_unmatched_name(self) -> None:
        ocr_results = self.make_ocr_results()
        gender_results = self.make_gender_results()
        resolved_results = {
            "opponent_name": ResolvedNameResult(
                raw_result=ocr_results["opponent_name"],
                match_result=PokemonNameMatchResult(
                    raw_text="???",
                    matched=False,
                    species_id="unknown",
                    display_name="unknown",
                    score=0.0,
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

        observation = build_battle_observation(
            ocr_results,
            gender_results,
            resolved_results,
            timestamp=1710000000,
        )

        self.assertEqual(observation.opponent_active.species_id, "unknown")
        self.assertEqual(observation.opponent_active.display_name, "unknown")
        self.assertEqual(observation.opponent_active.confidence, 0.0)

    def test_write_observation_json_writes_pretty_json(self) -> None:
        observation = build_battle_observation(
            self.make_ocr_results(),
            self.make_gender_results(),
            self.make_resolved_results(),
            timestamp=1710000000,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "observation.json"
            write_observation_json(observation, output_path)

            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["scene"], "battle")
            self.assertIn("player_active", payload)
            self.assertIn("opponent_active", payload)


if __name__ == "__main__":
    unittest.main()
