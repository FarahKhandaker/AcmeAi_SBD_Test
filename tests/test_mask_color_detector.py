import numpy as np
import pytest

from field_pipeline.detectors.mask_color import MaskColorDetector


HEIGHT = 720
WIDTH = 1280
GREEN_BGR = (34, 139, 34)


def _blank_frame() -> np.ndarray:
    return np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)


def test_pure_black_frame_returns_none():
    detector = MaskColorDetector(min_area=1000)
    assert detector.detect(_blank_frame()) is None


def test_fully_green_frame_is_rejected_as_implausible():
    """A frame that is entirely green looks like a close-up, not a pitch."""
    frame = np.full((HEIGHT, WIDTH, 3), GREEN_BGR, dtype=np.uint8)
    detector = MaskColorDetector(min_area=1000)
    assert detector.detect(frame) is None


def test_partial_green_region_returns_polygon():
    """A green region covering ~half the frame should be detected."""
    frame = _blank_frame()
    frame[200:520, 300:980] = GREEN_BGR  # 320x680 = 217,600 px, ~24% of frame
    detector = MaskColorDetector(min_area=1000)
    result = detector.detect(frame)
    assert result is not None
    assert result.is_valid


def test_min_area_zero_is_rejected_at_construction():
    with pytest.raises(ValueError, match="must be positive"):
        MaskColorDetector(min_area=0)