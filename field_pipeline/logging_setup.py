import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def __init__(self, run_id: str) -> None:
        super().__init__()
        self._run_id = run_id

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": self._run_id,
        }

        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(run_id: str, level: str = "INFO") -> None:
    """Wire the root logger to emit JSON to stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter(run_id))

    root = logging.getLogger()
    root.setLevel(level)
    # Remove any handlers installed by libraries or previous calls.
    root.handlers.clear()
    root.addHandler(handler)