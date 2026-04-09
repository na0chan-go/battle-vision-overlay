from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vision.name_match import resolve_name_results
from vision.name_ocr import extract_name_texts
from vision.poc import extract_regions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crop fixed battle-screen status panels for debugging."
    )
    parser.add_argument(
        "--image",
        type=Path,
        required=True,
        help="source battle image path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets") / "debug",
        help="directory for cropped debug images",
    )
    parser.add_argument(
        "--ocr-names",
        action="store_true",
        help="run the name-region OCR PoC instead of status-panel cropping",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print OCR results as JSON",
    )
    parser.add_argument(
        "--resolve-names",
        action="store_true",
        help="match OCR raw text against pokemon master data",
    )
    parser.add_argument(
        "--master-data",
        type=Path,
        default=Path("shared") / "master-data" / "pokemon.json",
        help="pokemon master data path for name matching",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.ocr_names:
            ocr_results = extract_name_texts(args.image, args.output_dir)
            resolved_results = (
                resolve_name_results(
                    ocr_results,
                    master_data_path=args.master_data,
                )
                if args.resolve_names
                else None
            )
        else:
            saved_files = extract_regions(args.image, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        task_name = "vision ocr" if args.ocr_names else "vision crop"
        print(f"{task_name} failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.ocr_names:
        if args.json:
            source_results = resolved_results or ocr_results
            payload = {
                region_name: result.to_dict()
                for region_name, result in source_results.items()
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        for region_name, result in ocr_results.items():
            print(f"{region_name}_raw: {result.raw_text}")
            print(f"{region_name}_crop: {result.crop_path}")
            print(f"{region_name}_preprocessed: {result.preprocessed_path}")
            if resolved_results is not None:
                match_result = resolved_results[region_name].match_result
                print(f"{region_name}_matched: {match_result.matched}")
                print(f"{region_name}_species_id: {match_result.species_id}")
                print(f"{region_name}_display_name: {match_result.display_name}")
                print(f"{region_name}_score: {match_result.score:.4f}")
        return

    for region_name, saved_path in saved_files.items():
        print(f"{region_name}: {saved_path}")


if __name__ == "__main__":
    main()
