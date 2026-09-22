from unittest.mock import MagicMock

import numpy as np
import pytest

from field_pipeline.config import PipelineConfig
from field_pipeline.exceptions import DetectorError, PipelineError
from field_pipeline.pipeline import FieldBoundaryAnalyzer


VALID_CONFIG = PipelineConfig(
    video_path="does-not-matter.mp4",
    target_fps=30,
    field_detector={"type": "mask_color_v1", "sport": "football", "min_area": 1000},
)


def test_missing_video_raises_pipeline_error():
    detector = MagicMock()
    analyzer = FieldBoundaryAnalyzer(VALID_CONFIG, detector)
    with pytest.raises(PipelineError, match="Could not open"):
        analyzer.process_video("nonexistent.mp4")
    detector.detect.assert_not_called()


def test_detector_error_is_fatal(monkeypatch, tmp_path):
    """A DetectorError from the detector aborts the whole run."""
    _make_dummy_video(tmp_path / "in.mp4")
    detector = MagicMock()
    detector.detect.side_effect = DetectorError("model weights missing")

    analyzer = FieldBoundaryAnalyzer(VALID_CONFIG, detector)
    with pytest.raises(DetectorError, match="weights"):
        analyzer.process_video(str(tmp_path / "in.mp4"))


def test_generic_exception_from_detector_is_recoverable(tmp_path):
    """A non-DetectorError from the detector is logged and skipped, run continues."""
    _make_dummy_video(tmp_path / "in.mp4")
    detector = MagicMock()
    detector.detect.side_effect = RuntimeError("unexpected pixel format")

    analyzer = FieldBoundaryAnalyzer(VALID_CONFIG, detector)
    summary = analyzer.process_video(str(tmp_path / "in.mp4"))
    assert summary.boundaries_found == 0
    assert summary.recoverable_errors > 0
    assert detector.detect.call_count > 0


def _make_dummy_video(path):
    """Write a short synthetic video for testing."""
    import cv2
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 30.0, (320, 240))
    green = np.full((240, 320, 3), (34, 139, 34), dtype=np.uint8)
    for _ in range(10):
        writer.write(green)
    writer.release()