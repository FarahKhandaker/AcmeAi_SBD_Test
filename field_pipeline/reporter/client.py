"""HTTP client for the reporting service."""

import logging

import requests
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from field_pipeline.config import ReporterConfig
from field_pipeline.reporter.payloads import EventPayload, ProgressPayload

log = logging.getLogger("field_pipeline.reporter")


class ReporterClient:
    """POSTs progress and event payloads to the reporting service."""

    def __init__(self, config: ReporterConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._timeout = config.timeout_seconds
        self._max_attempts = config.max_attempts

    def send_progress(self, payload: ProgressPayload) -> bool:
        return self._post("/api/v1/jobs/progress", payload.model_dump(mode="json"))

    def send_event(self, payload: EventPayload) -> bool:
        return self._post("/api/v1/jobs/events", payload.model_dump(mode="json"))

    def _post(self, path: str, body: dict) -> bool:
        url = f"{self._base_url}{path}"

        try:
            self._post_with_retries(url, body)
            return True
        except RetryError as exc:
            underlying = exc.last_attempt.exception()
            log.warning(
                "reporter_call_failed",
                extra={
                    "event": "reporter_call_failed",
                    "url": url,
                    "attempts": self._max_attempts,
                    "error_type": type(underlying).__name__ if underlying else "Unknown",
                    "error": str(underlying) if underlying else "unknown",
                },
            )
            return False

    def _post_with_retries(self, url: str, body: dict) -> None:
        """Post with retry-on-transient-failure. Raises RetryError on give-up."""

        @retry(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
            retry=retry_if_exception_type(requests.RequestException),
            reraise=False,
        )
        def _do_post() -> None:
            response = requests.post(url, json=body, timeout=self._timeout)
            response.raise_for_status()

        _do_post()