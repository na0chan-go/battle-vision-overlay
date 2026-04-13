from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vision.match.pokemon import (
    load_pokemon_name_entries,
    match_pokemon_name,
    normalize_pokemon_name_text,
    resolve_pokemon_name_candidates,
)


class NameMatchTest(unittest.TestCase):
    def write_master_data(self, directory: Path) -> Path:
        master_data_path = directory / "pokemon.json"
        payload = [
            {"species_id": "garchomp", "display_name": "ガブリアス"},
            {"species_id": "meowstic", "display_name": "ニャオニクス"},
            {"species_id": "basculegion", "display_name": "イダイトウ"},
            {"species_id": "gholdengo", "display_name": "サーフゴー"},
            {"species_id": "greninja", "display_name": "ゲッコウガ"},
            {"species_id": "porygon", "display_name": "ポリゴン"},
            {"species_id": "porygon2", "display_name": "ポリゴン2"},
            {"species_id": "porygonz", "display_name": "ポリゴンZ"},
            {"species_id": "nidoran_m", "display_name": "ニドラン♂"},
            {"species_id": "nidoran_f", "display_name": "ニドラン♀"},
        ]
        master_data_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return master_data_path

    def test_load_pokemon_name_entries_reads_master_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            self.assertEqual(len(entries), 10)
            self.assertEqual(entries[0].display_name, "ガブリアス")

    def test_normalize_pokemon_name_text_removes_common_ocr_noise(self) -> None:
        self.assertEqual(
            normalize_pokemon_name_text("  ※さーふごー♂ Lv.50  "),
            "サーフゴー♂",
        )

    def test_normalize_pokemon_name_text_keeps_meaningful_suffixes(self) -> None:
        self.assertEqual(
            normalize_pokemon_name_text("ポリゴン２ / porygon-z"),
            "ポリゴン2PORYGONZ",
        )

    def test_match_pokemon_name_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ガブリアス", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "garchomp")
            self.assertEqual(result.display_name, "ガブリアス")
            self.assertEqual(result.normalized_text, "ガブリアス")
            self.assertEqual(result.reason, "exact_match")

    def test_match_pokemon_name_absorbs_small_kana_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ガブリァス", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "garchomp")
            self.assertEqual(result.display_name, "ガブリアス")

    def test_match_pokemon_name_matches_surfugo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("サーフゴー", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "gholdengo")
            self.assertEqual(result.display_name, "サーフゴー")

    def test_match_pokemon_name_returns_unknown_for_empty_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("", entries)

            self.assertFalse(result.matched)
            self.assertEqual(result.species_id, "unknown")
            self.assertEqual(result.display_name, "unknown")
            self.assertEqual(result.score, 0.0)
            self.assertEqual(result.normalized_text, "")
            self.assertEqual(result.reason, "empty_after_normalize")

    def test_match_pokemon_name_returns_unknown_for_unrelated_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("???", entries)

            self.assertFalse(result.matched)
            self.assertEqual(result.species_id, "unknown")
            self.assertEqual(result.display_name, "unknown")
            self.assertEqual(result.score, 0.0)
            self.assertEqual(result.normalized_text, "")
            self.assertEqual(result.reason, "empty_after_normalize")

    def test_match_pokemon_name_absorbs_noise_around_known_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("※サーフゴー♂ Lv.50", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "gholdengo")
            self.assertEqual(result.display_name, "サーフゴー")
            self.assertEqual(result.normalized_text, "サーフゴー♂")

    def test_match_pokemon_name_distinguishes_digit_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ポリゴン2", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "porygon2")
            self.assertEqual(result.display_name, "ポリゴン2")
            self.assertEqual(result.score, 1.0)

    def test_match_pokemon_name_distinguishes_latin_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ポリゴンZ", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "porygonz")
            self.assertEqual(result.display_name, "ポリゴンZ")
            self.assertEqual(result.score, 1.0)

    def test_match_pokemon_name_distinguishes_gender_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ニドラン♀", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "nidoran_f")
            self.assertEqual(result.display_name, "ニドラン♀")
            self.assertEqual(result.score, 1.0)

    def test_match_pokemon_name_absorbs_validation_ocr_noise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("グッコウカ", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "greninja")
            self.assertEqual(result.display_name, "ゲッコウガ")
            self.assertEqual(result.reason, "best_similarity")

    def test_match_pokemon_name_returns_unknown_below_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ガ", entries)

            self.assertFalse(result.matched)
            self.assertEqual(result.species_id, "unknown")
            self.assertEqual(result.display_name, "unknown")
            self.assertEqual(result.score, 0.0)
            self.assertEqual(result.reason, "below_threshold")
            self.assertTrue(result.top_candidates)

    def test_resolve_pokemon_name_candidates_returns_ranked_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            candidates = resolve_pokemon_name_candidates("ガブリァス", entries)

            self.assertEqual(candidates[0].display_name, "ガブリアス")

    def test_match_pokemon_name_to_dict_includes_debug_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            payload = match_pokemon_name("ガブリァス", entries).to_dict()

            self.assertEqual(payload["normalized_text"], "ガブリァス")
            self.assertEqual(payload["reason"], "exact_match")
            self.assertIn("top_candidates", payload)
            self.assertEqual(payload["top_candidates"][0]["display_name"], "ガブリアス")


if __name__ == "__main__":
    unittest.main()
