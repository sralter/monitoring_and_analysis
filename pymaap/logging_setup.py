# pymaap/logging_setup.py

import logging
import sys
import uuid
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import types


class UUIDFilter(logging.Filter):
    """
    Injects a unique UUID into each LogRecord as `record.uuid` for cross-log correlation.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        record.uuid = str(uuid.uuid4())
        return True


class JSONFormatter(logging.Formatter):
    """
    Formats LogRecords as JSON objects, one per line.
    Fields: timestamp, level, message, function, uuid
    """
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        # Use base class formatting (future-proof override)
        return super().formatTime(record, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S,%f")[:-3]
        log_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName or "N/A",
            "uuid": getattr(record, "uuid", "N/A"),
        }
        return json.dumps(log_record)


def init_general_logger(
    name: Optional[str] = None,
    log_dir: str = "logs",
    general_log: str = "general.log",
    json_log: Optional[str] = "general.json.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Initialize the general-purpose logger for PyMAAP.

    Sets up:
      - RotatingFileHandler writing plain-text logs to <log_dir>/<general_log>
      - Optional RotatingFileHandler writing JSON logs to <log_dir>/<json_log>
      - Console output via print(), at the specified console_level
    Each handler includes a UUIDFilter for unique IDs and uses a consistent formatter.

    Parameters:
        name: Logger name. If None, configures the root logger.
        log_dir: Directory where log files are stored.
        general_log: Filename for human-readable log output.
        json_log: Filename for machine-readable JSON log output. If None, JSON handler is not added.
        max_bytes: Maximum bytes before rotating log files.
        backup_count: Number of backup files to keep.
        console_level: Logging level for console output.

    Returns:
        Configured Logger instance.
    """
    # Determine target logger
    logger = logging.getLogger(name) if name else logging.getLogger()

    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Clear existing handlers and filters
    logger.handlers.clear()
    logger.filters.clear()

    # Capture all messages
    logger.setLevel(logging.DEBUG)
    # Prevent propagation
    logger.propagate = False

    # UUID filter
    uuid_filter = UUIDFilter()
    logger.addFilter(uuid_filter)

    # Formatter for plain-text
    text_fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(uuid)s [%(name)s.%(funcName)s] %(message)s"
    )

    # Plain-text rotating file handler
    text_handler = RotatingFileHandler(
        Path(log_dir) / general_log,
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    text_handler.setLevel(logging.DEBUG)
    text_handler.setFormatter(text_fmt)
    text_handler.addFilter(uuid_filter)
    # Custom naming for rotated backups: general.log.1.log, etc.
    text_handler.namer = lambda name: f"{name}.log"
    logger.addHandler(text_handler)

    # JSON rotating file handler
    if json_log:
        json_handler = RotatingFileHandler(
            Path(log_dir) / json_log,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        json_handler.addFilter(uuid_filter)
        # Custom naming for rotated backups: general.json.log.1.log, etc.
        json_handler.namer = lambda name: f"{name}.log"
        logger.addHandler(json_handler)

    # Console handler using print for capture-friendly output
    from logging import StreamHandler
    console_handler = StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(text_fmt)
    console_handler.addFilter(uuid_filter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            print(msg)
        except Exception:
            self.handleError(record)

    # Monkey-patch emit on this instance to use print()
    console_handler.emit = types.MethodType(emit, console_handler)
    logger.addHandler(console_handler)

    return logger
