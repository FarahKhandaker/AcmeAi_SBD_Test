"""Entry point for the pitch-boundary pipeline."""

import argparse
import logging
import sys
import uuid
from pathlib import Path

from field_pipeline.config import PipelineConfig
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
from field_pipeline.reporter import (
    EventPayload,
    EventType,
    ReporterClient,
)
from field_pipeline.summary import RunSummary
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


def _build_reporter(config: PipelineConfig) -> ReporterClient | None:
    """Return a configured reporter, or None if reporting isn't configured."""
    if config.reporter is None:
        return None
    return ReporterClient(config.reporter)


def _report_event(
    reporter: ReporterClient | None,
    run_id: str,
    event_type: EventType,
    log: logging.Logger,
    summary: RunSummary | None = None,
    error: str | None = None,
) -> None:
    """Send a lifecycle event; log a warning if the send fails but never raise."""
    if reporter is None:
        return
    payload = EventPayload(
        run_id=run_id,
        event=event_type,
        summary=summary,
        error=error,
    )
    ok = reporter.send_event(payload)
    if not ok:
        log.warning(
            "reporter_event_not_delivered",
            extra={
                "event": "reporter_event_not_delivered",
                "reported_event": event_type.value,
            },
        )


def main() -> int:
    args = parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"[config] {exc}", file=sys.stderr)
        return 2

    run_id = config.run_id or f"run-{uuid.uuid4().hex[:12]}"
    configure_logging(run_id=run_id, level=config.log_level)
    log = logging.getLogger("field_pipeline.runner")

    log.info(
        "run_starting",
        extra={"event": "run_starting", "config_path": str(args.config)},
    )

    if args.generate_video:
        log.info(
            "generating_synthetic_video",
            extra={"event": "generating_synthetic_video"},
        )
        generate_synthetic_video(str(config.video_path))

    reporter = _build_reporter(config)
    _report_event(reporter, run_id, EventType.RUN_STARTED, log)

    try:
        detector = build_detector(config.field_detector)
        analyzer = FieldBoundaryAnalyzer(config, detector)
        summary = analyzer.process_video(str(config.video_path))
        log.info(
            "run_finished",
            extra={"event": "run_finished", **summary.model_dump()},
        )
        _report_event(
            reporter, run_id, EventType.RUN_FINISHED, log, summary=summary
        )
        return 0
    except DetectorError as exc:
        log.error(
            "detector_error",
            extra={"event": "detector_error", "error": str(exc)},
        )
        _report_event(
            reporter, run_id, EventType.RUN_FAILED, log, error=str(exc)
        )
        return 3
    except ReporterError as exc:
        log.error(
            "reporter_error",
            extra={"event": "reporter_error", "error": str(exc)},
        )
        return 4
    except PipelineError as exc:
        log.error(
            "pipeline_error",
            extra={"event": "pipeline_error", "error": str(exc)},
        )
        _report_event(
            reporter, run_id, EventType.RUN_FAILED, log, error=str(exc)
        )
        return 3


if __name__ == "__main__":
    sys.exit(main())