import logging
import time

import cv2
from shapely.geometry import Polygon

from field_pipeline.config import PipelineConfig
from field_pipeline.detectors import FieldDetector
from field_pipeline.exceptions import PipelineError
from field_pipeline.frame_filter import is_frame_worth_analyzing

log = logging.getLogger("field_pipeline.pipeline")


class FieldBoundaryAnalyzer:
    def __init__(self, config: PipelineConfig, detector: FieldDetector) -> None:
        self.config = config
        self.detector = detector
        self.sport = config.field_detector.sport

    def process_video(self, video_path: str):
        log.info(
            "video_open",
            extra={"event": "video_open", "video_path": video_path},
        )
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise PipelineError(f"Could not open video stream: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        outer_boundary = Polygon(
            [(0, 0), (width, 0), (width, height), (0, height)]
        )

        frame_count = 0
        skipped_count = 0
        detected_polygons = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                if not is_frame_worth_analyzing(frame):
                    skipped_count += 1
                    continue

                poly = self.detector.detect(frame)

                if poly is not None:
                    intersection_area = poly.intersection(outer_boundary).area
                    detected_polygons.append((frame_count, poly, intersection_area))

                time.sleep(0.005)
        finally:
            cap.release()

        log.info(
            "video_processed",
            extra={
                "event": "video_processed",
                "frames_read": frame_count,
                "frames_skipped": skipped_count,
                "boundaries_found": len(detected_polygons),
            },
        )
        return detected_polygons