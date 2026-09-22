import logging
import time

import cv2
from shapely.geometry import Polygon

from field_pipeline.config import PipelineConfig
from field_pipeline.detectors import FieldDetector
from field_pipeline.exceptions import DetectorError, PipelineError
from field_pipeline.frame_filter import is_frame_worth_analyzing
from field_pipeline.summary import RunSummary

log = logging.getLogger("field_pipeline.pipeline")


class FieldBoundaryAnalyzer:
    def __init__(self, config: PipelineConfig, detector: FieldDetector) -> None:
        self.config = config
        self.detector = detector
        self.sport = config.field_detector.sport

    def process_video(self, video_path: str) -> RunSummary:
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
        recoverable_error_count = 0
        intersection_areas: list[float] = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                if not is_frame_worth_analyzing(frame):
                    skipped_count += 1
                    continue

                try:
                    poly = self.detector.detect(frame)
                except DetectorError:
                    raise
                except Exception as exc:
                    recoverable_error_count += 1
                    log.warning(
                        "frame_detection_failed",
                        extra={
                            "event": "frame_detection_failed",
                            "frame_index": frame_count,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        },
                    )
                    continue

                if poly is not None:
                    intersection_areas.append(poly.intersection(outer_boundary).area)

                time.sleep(0.005)
        finally:
            cap.release()

        mean_area = (
            sum(intersection_areas) / len(intersection_areas)
            if intersection_areas
            else 0.0
        )

        summary = RunSummary(
            frames_read=frame_count,
            frames_skipped=skipped_count,
            recoverable_errors=recoverable_error_count,
            boundaries_found=len(intersection_areas),
            mean_intersection_area=mean_area,
        )

        log.info(
            "video_processed",
            extra={"event": "video_processed", **summary.model_dump()},
        )
        return summary