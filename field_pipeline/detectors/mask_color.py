import cv2
import numpy as np
from shapely.geometry import Polygon

_LOWER_GREEN = np.array([35, 40, 40])
_UPPER_GREEN = np.array([85, 255, 255])

class MaskColorDetector:
    def __init__(self, min_area: int) -> None:
        if min_area <= 0:
            raise ValueError(f"min_area must be positive, got {min_area}")
        self._min_area = min_area

    def detect(self, frame: np.ndarray) -> Polygon | None:
        mask = self._extract_mask(frame)
        return self._derive_polygon(mask)

    def _extract_mask(self, frame: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return cv2.inRange(hsv, _LOWER_GREEN, _UPPER_GREEN)

    def _derive_polygon(self, mask: np.ndarray) -> Polygon | None:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) <= self._min_area:
            return None

        pts = largest.reshape(-1, 2)
        if len(pts) < 3:
            return None

        polygon = Polygon(pts)
        return polygon if polygon.is_valid else None