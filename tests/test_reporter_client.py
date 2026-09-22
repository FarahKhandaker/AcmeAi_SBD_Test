"""Unit tests for ReporterClient — mocks the HTTP layer."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from field_pipeline.config import ReporterConfig
from field_pipeline.reporter.client import ReporterClient
from field_pipeline.reporter.payloads import (
    EventPayload,
    EventType,
    ProgressPayload,
)


@pytest.fixture
def config() -> ReporterConfig:
    return ReporterConfig(
        base_url="http://localhost:5000",
        timeout_seconds=1.0,
        max_attempts=3,
    )


@pytest.fixture
def progress() -> ProgressPayload:
    return ProgressPayload(
        run_id="r-1",
        frames_read=10,
        frames_skipped=1,
        recoverable_errors=0,
        boundaries_found=8,
    )


@pytest.fixture
def event() -> EventPayload:
    return EventPayload(run_id="r-1", event=EventType.RUN_STARTED)


def test_send_progress_success(config, progress):
    with patch("field_pipeline.reporter.client.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )
        client = ReporterClient(config)
        assert client.send_progress(progress) is True

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["timeout"] == 1.0
    assert call_kwargs["json"]["run_id"] == "r-1"


def test_send_event_success(config, event):
    with patch("field_pipeline.reporter.client.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )
        client = ReporterClient(config)
        assert client.send_event(event) is True


def test_send_returns_false_on_connection_error(config, progress):
    with patch("field_pipeline.reporter.client.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("connection refused")
        client = ReporterClient(config)
        assert client.send_progress(progress) is False


def test_send_returns_false_on_http_error(config, event):
    with patch("field_pipeline.reporter.client.requests.post") as mock_post:
        response = MagicMock()
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = response
        client = ReporterClient(config)
        assert client.send_event(event) is False


def test_base_url_trailing_slash_normalised(progress):
    config = ReporterConfig(base_url="http://localhost:5000/", timeout_seconds=1.0)
    with patch("field_pipeline.reporter.client.requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200, raise_for_status=lambda: None
        )
        client = ReporterClient(config)
        client.send_progress(progress)

    called_url = mock_post.call_args.args[0]
    assert called_url == "http://localhost:5000/api/v1/jobs/progress"