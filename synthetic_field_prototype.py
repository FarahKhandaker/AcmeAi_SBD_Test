from field_pipeline.pipeline import FieldBoundaryAnalyzer
from synthetic_generator import generate_synthetic_video

CONFIG = {
    "video_path": "synthetic_pitch_feed.mp4",
    "target_fps": 30,
    "confidence_threshold": 0.5,
    "field_detector": {
        "type": "sam_mask_v1",
        "sport": "football",
        "min_area": 1000,
    },
    "crop_search": {
        "aspect_ratio": "16:9",
        "padding_px": 20,
    },
    "debug_mode": True,
}


def run_pipeline():
    generate_synthetic_video(CONFIG["video_path"])
    analyzer = FieldBoundaryAnalyzer(CONFIG)
    results = analyzer.process_video(CONFIG["video_path"])
    print(f"Pipeline finished with {len(results) if results else 0} results.")


if __name__ == "__main__":
    run_pipeline()