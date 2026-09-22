from pydantic import BaseModel, ConfigDict, Field


class RunSummary(BaseModel):
    """Aggregate outcome of a pipeline run."""

    model_config = ConfigDict(extra="forbid")

    frames_read: int = Field(ge=0)
    frames_skipped: int = Field(ge=0)
    recoverable_errors: int = Field(ge=0)
    boundaries_found: int = Field(ge=0)
    mean_intersection_area: float = Field(ge=0.0)

    @property
    def frames_analyzed(self) -> int:
        """Frames that made it past the pre-filter."""
        return self.frames_read - self.frames_skipped