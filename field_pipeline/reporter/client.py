import logging

import requests

from field_pipeline.config import ReporterConfig
from field_pipeline.reporter.payloads import EventPayload, ProgressPayload

log = logging.getLogger("field_pipeline.reporter")


class ReporterClient:
    """POSTs progress and event payloads to the reporting service."""

    def __init__(self, config: ReporterConfig) -> None:
        self._base_url = config.base_url.rstrip("/")
        self._timeout = config.timeout_seconds

    def send_progress(self, payload: ProgressPayload) -> bool:
        """POST a progress payload. Returns True on success, False otherwise."""
        return self._post("/api/v1/jobs/progress", payload.model_dump(mode="json"))

    def send_event(self, payload: EventPayload) -> bool:
        """POST an event payload. Returns True on success, False otherwise."""
        return self._post("/api/v1/jobs/events", payload.model_dump(mode="json"))

    def _post(self, path: str, body: dict) -> bool:
        url = f"{self._base_url}{path}"
        try:
            response = requests.post(url, json=body, timeout=self._timeout)
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            log.warning(
                "reporter_call_failed",
                extra={
                    "event": "reporter_call_failed",
                    "url": url,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            return False