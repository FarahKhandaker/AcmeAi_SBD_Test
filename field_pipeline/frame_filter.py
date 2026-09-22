import cv2
import numpy as np

_MIN_GREEN_RATIO = 0.20

_LOWER_GREEN = np.array([35, 40, 40])
_UPPER_GREEN = np.array([85, 255, 255])


def is_frame_worth_analyzing(frame: np.ndarray) -> bool:
    """Return True if the frame looks like it contains a pitch worth detecting."""
    
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, _LOWER_GREEN, _UPPER_GREEN)
    green_ratio = float(mask.mean()) / 255.0
    return green_ratio >= _MIN_GREEN_RATIO