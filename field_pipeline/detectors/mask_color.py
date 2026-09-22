import cv2
import numpy as np
from shapely.geometry import Polygon

_LOWER_GREEN = np.array([35, 40, 40])
_UPPER_GREEN = np.array([85, 255, 255])

_MAX_AREA_RATIO = 0.90


class MaskColorDetector:
    """Baseline detector: HSV green threshold → largest contour → polygon."""

    def __init__(self, min_area: int) -> None:
        if min_area <= 0:
            raise ValueError(f"min_area must be positive, got {min_area}")
        self._min_area = min_area

    def detect(self, frame: np.ndarray) -> Polygon | None:
        mask = self._extract_mask(frame)
        return self._derive_polygon(mask, frame.shape)

    def _extract_mask(self, frame: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, _LOWER_GREEN, _UPPER_GREEN)

    def _derive_polygon(
        self, mask: np.ndarray, frame_shape: tuple[int, ...]
    ) -> Polygon | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area <= self._min_area:
            return None

        frame_area = float(frame_shape[0] * frame_shape[1])
        if area / frame_area >= _MAX_AREA_RATIO:
            return None

        pts = largest.reshape(-1, 2)
        if len(pts) < 3:
            return None

        polygon = Polygon(pts)
        return polygon if polygon.is_valid else None