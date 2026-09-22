from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from field_pipeline.summary import RunSummary


class EventType(str, Enum):
    RUN_STARTED = "run_started"
    RUN_FINISHED = "run_finished"
    RUN_FAILED = "run_failed"


class ProgressPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    frames_read: int = Field(ge=0)
    frames_skipped: int = Field(ge=0)
    recoverable_errors: int = Field(ge=0)
    boundaries_found: int = Field(ge=0)


class EventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    event: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: RunSummary | None = None
    error: str | None = None