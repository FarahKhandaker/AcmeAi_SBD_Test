"""Entry point for the pitch-boundary pipeline."""

import argparse
import logging
import sys
import uuid
from pathlib import Path

from field_pipeline.config_loader import load_config
from field_pipeline.detectors import build_detector
from field_pipeline.exceptions import (
    ConfigError,
    DetectorError,
    PipelineError,
    ReporterError,
)
from field_pipeline.logging_setup import configure_logging
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

    run_id = config.run_id or f"run-{uuid.uuid4().hex[:12]}"
    configure_logging(run_id=run_id, level=config.log_level)
    log = logging.getLogger("pitchcrop.runner")

    log.info("run_starting", extra={"event": "run_starting", "config_path": str(args.config)})

    if args.generate_video:
        log.info("generating_synthetic_video", extra={"event": "generating_synthetic_video"})
        generate_synthetic_video(str(config.video_path))

    try:
        detector = build_detector(config.field_detector)
        analyzer = FieldBoundaryAnalyzer(config, detector)
        results = analyzer.process_video(str(config.video_path))
        log.info(
            "run_finished",
            extra={"event": "run_finished", "result_count": len(results) if results else 0},
        )
        return 0
    except DetectorError as exc:
        log.error("detector_error", extra={"event": "detector_error", "error": str(exc)})
        return 3
    except ReporterError as exc:
        log.error("reporter_error", extra={"event": "reporter_error", "error": str(exc)})
        return 4
    except PipelineError as exc:
        log.error("pipeline_error", extra={"event": "pipeline_error", "error": str(exc)})
        return 3


if __name__ == "__main__":
    sys.exit(main())