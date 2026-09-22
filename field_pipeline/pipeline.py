import time

import cv2
from shapely.geometry import Polygon

from field_pipeline.config import PipelineConfig
from field_pipeline.detectors import FieldDetector

class FieldBoundaryAnalyzer:
    def __init__(self, config: PipelineConfig, detector: FieldDetector) -> None:
        self.config = config
        self.detector = detector
        self.sport = config.field_detector.sport

    def process_video(self, video_path: str):
        print(f"Starting processing for video: {video_path}")
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("Error: Could not open video stream.")
            return

        frame_count = 0
        detected_polygons = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            poly = self.detector.detect(frame)

            if poly is not None:
                outer_boundary = Polygon([(0, 0), (1280, 0), (1280, 720), (0, 720)])
                intersection_area = poly.intersection(outer_boundary).area
                detected_polygons.append((frame_count, poly, intersection_area))

            # Simulate heavy per-frame processing latency
            time.sleep(0.005)

        cap.release()
        print(f"Processed {frame_count} frames. Found {len(detected_polygons)} boundaries.")
        return detected_polygons