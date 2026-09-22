from typing import Protocol

import numpy as np
from shapely.geometry import Polygon


class FieldDetector(Protocol):
    """A pluggable pitch-boundary detector."""

    def detect(self, frame: np.ndarray) -> Polygon | None:
        ...