from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vision.poc import extract_regions


def build_active_payload(
    ocr_results: dict[str, object],
    gender_results: dict[str, object],
    resolved_results: dict[str, object] | None,
    active_metadata: dict[str, object] | None = None,
) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    active_region_map = {
        "opponent_name": ("opponent_active", "opponent_gender"),
        "player_name": ("player_active", "player_gender"),
    }

    for name_region, (active_key, gender_region) in active_region_map.items():
        raw_result = ocr_results[name_region]
        gender_result = gender_results[gender_region]
        metadata = active_metadata[active_key] if active_metadata else None
        active_payload: dict[str, object] = {
            "raw_text": raw_result.raw_text,
            "name_crop_path": str(raw_result.crop_path),
            "preprocessed_path": str(raw_result.preprocessed_path),
            "gender_crop_path": str(gender_result.crop_path),
            "gender": gender_result.gender,
            "form": metadata.form if metadata is not None else "unknown",
            "mega_state": metadata.mega_state if metadata is not None else "base",
            "gender_score": gender_result.score,
            "error": raw_result.error,
        }
        if resolved_results is not None:
            match_result = resolved_results[name_region].match_result
            active_payload.update(
                {
                    "matched": match_result.matched,
                    "species_id": match_result.species_id,
                    "display_name": match_result.display_name,
                    "score": match_result.score,
                }
            )

        payload[active_key] = active_payload

    return payload


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
        "--emit-observation",
        action="store_true",
        help="build and print an observation DTO JSON",
    )
    parser.add_argument(
        "--observation-output",
        type=Path,
        default=None,
        help="optional path to save the observation JSON",
    )
    parser.add_argument(
        "--player-form",
        default="unknown",
        help="temporary player form value for observation DTO",
    )
    parser.add_argument(
        "--player-mega-state",
        default="base",
        help="temporary player mega_state value for observation DTO",
    )
    parser.add_argument(
        "--opponent-form",
        default="unknown",
        help="temporary opponent form value for observation DTO",
    )
    parser.add_argument(
        "--opponent-mega-state",
        default="base",
        help="temporary opponent mega_state value for observation DTO",
    )
    parser.add_argument(
        "--request-overlay",
        action="store_true",
        help="POST the observation DTO to engine-go and print the overlay JSON",
    )
    parser.add_argument(
        "--overlay-endpoint",
        default="http://localhost:8080/api/v1/overlay/preview",
        help="engine-go overlay preview endpoint",
    )
    parser.add_argument(
        "--overlay-output",
        type=Path,
        default=None,
        help="optional path to save the overlay response JSON",
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
    if args.emit_observation and not args.ocr_names:
        parser.error("--emit-observation requires --ocr-names")
    if args.request_overlay and not args.ocr_names:
        parser.error("--request-overlay requires --ocr-names")

    try:
        if args.ocr_names:
            from vision.gender import extract_gender_marks
            from vision.name_match import resolve_name_results
            from vision.name_ocr import extract_name_texts
            from vision.observation import (
                ActivePokemonMetadata,
                build_battle_observation,
                write_observation_json,
            )
            from vision.transport import post_observation, write_overlay_response_json

            active_metadata = {
                "player_active": ActivePokemonMetadata(
                    form=args.player_form,
                    mega_state=args.player_mega_state,
                ),
                "opponent_active": ActivePokemonMetadata(
                    form=args.opponent_form,
                    mega_state=args.opponent_mega_state,
                ),
            }
            ocr_results = extract_name_texts(args.image, args.output_dir)
            gender_results = extract_gender_marks(args.image, args.output_dir)
            should_resolve_names = args.resolve_names or args.emit_observation
            should_resolve_names = should_resolve_names or args.request_overlay
            resolved_results = (
                resolve_name_results(
                    ocr_results,
                    master_data_path=args.master_data,
                )
                if should_resolve_names
                else None
            )
        else:
            saved_files = extract_regions(args.image, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        task_name = "vision ocr" if args.ocr_names else "vision crop"
        print(f"{task_name} failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.ocr_names:
        active_payload = build_active_payload(
            ocr_results,
            gender_results,
            resolved_results,
            active_metadata,
        )
        if args.emit_observation:
            observation = build_battle_observation(
                ocr_results,
                gender_results,
                resolved_results,
                player_metadata=active_metadata["player_active"],
                opponent_metadata=active_metadata["opponent_active"],
            )
            observation_output_path = (
                args.observation_output
                if args.observation_output is not None
                else args.output_dir / "observation.json"
            )
            write_observation_json(observation, observation_output_path)
            print(json.dumps(observation.to_dict(), ensure_ascii=False, indent=2))
            return
        if args.request_overlay:
            observation = build_battle_observation(
                ocr_results,
                gender_results,
                resolved_results,
                player_metadata=active_metadata["player_active"],
                opponent_metadata=active_metadata["opponent_active"],
            )
            try:
                overlay_response = post_observation(
                    observation.to_dict(),
                    endpoint_url=args.overlay_endpoint,
                )
            except RuntimeError as exc:
                print(f"overlay request failed: {exc}", file=sys.stderr)
                raise SystemExit(1) from exc

            overlay_output_path = (
                args.overlay_output
                if args.overlay_output is not None
                else args.output_dir / "overlay_response.json"
            )
            write_overlay_response_json(overlay_response, overlay_output_path)
            print(json.dumps(overlay_response, ensure_ascii=False, indent=2))
            return
        if args.json:
            print(json.dumps(active_payload, ensure_ascii=False, indent=2))
            return

        for active_key, payload in active_payload.items():
            print(f"{active_key}_raw: {payload['raw_text']}")
            print(f"{active_key}_name_crop: {payload['name_crop_path']}")
            print(f"{active_key}_preprocessed: {payload['preprocessed_path']}")
            print(f"{active_key}_gender_crop: {payload['gender_crop_path']}")
            print(f"{active_key}_gender: {payload['gender']}")
            print(f"{active_key}_gender_score: {payload['gender_score']:.4f}")
            if payload["error"] is not None:
                print(f"{active_key}_error: {payload['error']}")
            if resolved_results is not None:
                print(f"{active_key}_matched: {payload['matched']}")
                print(f"{active_key}_species_id: {payload['species_id']}")
                print(f"{active_key}_display_name: {payload['display_name']}")
                print(f"{active_key}_score: {payload['score']:.4f}")
        return

    for region_name, saved_path in saved_files.items():
        print(f"{region_name}: {saved_path}")


if __name__ == "__main__":
    main()
