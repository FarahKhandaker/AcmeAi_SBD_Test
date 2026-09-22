"""Detector implementations for the pitch-boundary pipeline."""

from field_pipeline.config import FieldDetectorConfig
from field_pipeline.detectors.base import FieldDetector
from field_pipeline.detectors.mask_color import MaskColorDetector
from field_pipeline.exceptions import DetectorError

__all__ = ["FieldDetector", "MaskColorDetector", "build_detector"]


def build_detector(config: FieldDetectorConfig) -> FieldDetector:
    """Construct a detector from validated config.

    This is the single place that maps a detector `type` string to a
    concrete class. Add new detectors by adding a branch here and a
    new value to the Literal type in FieldDetectorConfig.
    """
    if config.type == "mask_color_v1":
        return MaskColorDetector(min_area=config.min_area)

    raise DetectorError(f"Unknown detector type: {config.type!r}")