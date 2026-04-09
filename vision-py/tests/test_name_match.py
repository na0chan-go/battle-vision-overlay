from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vision.match.pokemon import (
    load_pokemon_name_entries,
    match_pokemon_name,
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

            self.assertEqual(len(entries), 4)
            self.assertEqual(entries[0].display_name, "ガブリアス")

    def test_match_pokemon_name_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("ガブリアス", entries)

            self.assertTrue(result.matched)
            self.assertEqual(result.species_id, "garchomp")
            self.assertEqual(result.display_name, "ガブリアス")

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

    def test_match_pokemon_name_returns_unknown_for_unrelated_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            result = match_pokemon_name("???", entries)

            self.assertFalse(result.matched)
            self.assertEqual(result.species_id, "unknown")
            self.assertEqual(result.display_name, "unknown")
            self.assertEqual(result.score, 0.0)

    def test_resolve_pokemon_name_candidates_returns_ranked_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            master_data_path = self.write_master_data(Path(tmp_dir))
            entries = load_pokemon_name_entries(master_data_path)

            candidates = resolve_pokemon_name_candidates("ガブリァス", entries)

            self.assertEqual(candidates[0].display_name, "ガブリアス")


if __name__ == "__main__":
    unittest.main()
