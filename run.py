"""Entry point for the pitch-boundary pipeline."""

import argparse
import sys
from pathlib import Path

from field_pipeline.config_loader import load_config
from field_pipeline.detectors import build_detector
from field_pipeline.exceptions import (
    ConfigError,
    DetectorError,
    PipelineError,
    ReporterError,
)
from field_pipeline.pipeline import FieldBoundaryAnalyzer
from synthetic_generator import generate_synthetic_video


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the pitch-boundary pipeline.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to the YAML config file (default: config.yaml).",
    )
    parser.add_argument(
        "--generate-video",
        action="store_true",
        help="Generate the synthetic video feed before running.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"[config] {exc}", file=sys.stderr)
        return 2

    if args.generate_video:
        generate_synthetic_video(str(config.video_path))

    try:
        detector = build_detector(config.field_detector)
        analyzer = FieldBoundaryAnalyzer(config, detector)
        results = analyzer.process_video(str(config.video_path))
        print(f"Pipeline finished with {len(results) if results else 0} results.")
        return 0
    except DetectorError as exc:
        print(f"[detector] {exc}", file=sys.stderr)
        return 3
    except ReporterError as exc:
        print(f"[reporter] {exc}", file=sys.stderr)
        return 4
    except PipelineError as exc:
        print(f"[pipeline] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())