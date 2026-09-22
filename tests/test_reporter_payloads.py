"""Unit tests for reporter payload models."""

import pytest
from pydantic import ValidationError

from field_pipeline.reporter.payloads import (
    EventPayload,
    EventType,
    ProgressPayload,
)
from field_pipeline.summary import RunSummary


def test_progress_payload_requires_run_id():
    with pytest.raises(ValidationError):
        ProgressPayload(
            run_id="",
            frames_read=0,
            frames_skipped=0,
            recoverable_errors=0,
            boundaries_found=0,
        )


def test_progress_payload_gets_default_timestamp():
    p = ProgressPayload(
        run_id="r-1",
        frames_read=10,
        frames_skipped=1,
        recoverable_errors=0,
        boundaries_found=8,
    )
    assert p.timestamp is not None
    assert p.timestamp.tzinfo is not None  # UTC-aware


def test_progress_payload_rejects_negative_counters():
    with pytest.raises(ValidationError):
        ProgressPayload(
            run_id="r-1",
            frames_read=-1,
            frames_skipped=0,
            recoverable_errors=0,
            boundaries_found=0,
        )


def test_progress_payload_rejects_extra_fields():
    with pytest.raises(ValidationError, match="extra"):
        ProgressPayload(
            run_id="r-1",
            frames_read=0,
            frames_skipped=0,
            recoverable_errors=0,
            boundaries_found=0,
            unknown_field="oops",
        )


def test_event_payload_with_summary_serializes():
    summary = RunSummary(
        frames_read=100,
        frames_skipped=5,
        recoverable_errors=0,
        boundaries_found=95,
        mean_intersection_area=1234.5,
    )
    p = EventPayload(
        run_id="r-1",
        event=EventType.RUN_FINISHED,
        summary=summary,
    )
    dumped = p.model_dump(mode="json")
    assert dumped["event"] == "run_finished"
    assert dumped["summary"]["boundaries_found"] == 95


def test_event_payload_with_error():
    p = EventPayload(
        run_id="r-1",
        event=EventType.RUN_FAILED,
        error="Could not open video stream: missing.mp4",
    )
    assert p.error is not None
    assert p.summary is None