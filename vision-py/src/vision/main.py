from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vision.poc import extract_regions


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Crop fixed battle-screen status panels for debugging."
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=root / "assets" / "samples" / "battle_sample.png",
        help="source battle image path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "assets" / "debug",
        help="directory for cropped debug images",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        saved_files = extract_regions(args.image, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"vision crop failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    for region_name, saved_path in saved_files.items():
        print(f"{region_name}: {saved_path}")


if __name__ == "__main__":
    main()
