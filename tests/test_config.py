import pytest
from pydantic import ValidationError

from field_pipeline.config import PipelineConfig

VALID_MINIMAL = {
    "video_path": "test.mp4",
    "target_fps": 30,
    "field_detector": {
        "type": "mask_color_v1",
        "sport": "football",
        "min_area": 1000,
    },
}

def test_valid_minimal_config_loads(): 
    config = PipelineConfig(**VALID_MINIMAL)
    assert config.target_fps == 30
    assert config.field_detector.sport == "football"
    assert config.reporter is None
    assert config.log_level == "INFO"
    
def test_negative_fps_is_rejected():
    bad = {**VALID_MINIMAL, "target_fps": -1}
    with pytest.raises(ValidationError):
        PipelineConfig(**bad)

def test_zero_min_area_is_rejected():
    bad = {
        **VALID_MINIMAL,
        "field_detector": {**VALID_MINIMAL["field_detector"], "min_area": 0},
    }
    with pytest.raises(ValidationError):
        PipelineConfig(**bad)
        
def test_reporter_requires_url():
    bad = {**VALID_MINIMAL, "reporter": {"base_url": "mock_api: 5000"}}
    with pytest.raises(ValidationError):
        PipelineConfig(**bad)