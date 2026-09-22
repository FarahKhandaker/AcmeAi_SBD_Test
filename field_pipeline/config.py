from pathlib import Path 
from typing import Literal 

from pydantic import BaseModel, ConfigDict, Field 

class FieldDetectorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    type: Literal["mask_color_v1"] = Field(description="Detector implementatkon key. Add new values as detectors are added.")
    sport: str = Field(min_length=1)
    min_area: int = Field(gt=0, description="Discard boundary polygons below this pixel area.")
    
class ReporterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    base_url: str = Field(pattern=r"^https?://")
    timeout_seconds: float = Field(default=5.0, gt=0)
    max_attempts: int = Field(default=3, ge=1, le=10)
    
class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    video_path: Path
    target_fps: int = Field(gt=0, le=240)
    field_detector: FieldDetectorConfig
    reporter: ReporterConfig | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    run_id: str | None = Field(
        default=None,
        description="Correlates all logs and reporter events for one run.",
    )