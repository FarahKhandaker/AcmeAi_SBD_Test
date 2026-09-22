"""Deprecated."""

from pathlib import Path

from field_pipeline.config_loader import load_config
from field_pipeline.detectors import build_detector
from field_pipeline.pipeline import FieldBoundaryAnalyzer
from synthetic_generator import generate_synthetic_video


def run_pipeline():
    config = load_config(Path("config.yaml"))
    generate_synthetic_video(str(config.video_path))
    detector = build_detector(config.field_detector)
    analyzer = FieldBoundaryAnalyzer(config, detector)
    results = analyzer.process_video(str(config.video_path))
    print(f"Pipeline finished with {len(results) if results else 0} results.")


if __name__ == "__main__":
    run_pipeline()