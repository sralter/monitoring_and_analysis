# pymaap/logging_setup.py

import logging
import sys
import uuid
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


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
        # Override to ensure consistent timestamp format
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
    console_level: int = logging.INFO,
) -> logging.Logger:
    """
    Initialize the general-purpose logger for PyMAAP.

    Sets up:
      - RotatingFileHandler writing plain-text logs to <log_dir>/<general_log>
      - Optional RotatingFileHandler writing JSON logs to <log_dir>/<json_log>
      - StreamHandler to stdout at the specified console_level
    Each handler includes a UUIDFilter for unique IDs and uses a consistent formatter.

    Parameters:
        name: Logger name (e.g., module name). If None, configures the root logger.
        log_dir: Directory where log files are stored.
        general_log: Filename for human-readable log output.
        json_log: Filename for machine-readable JSON log output. If None, JSON handler is not added.
        max_bytes: Maximum bytes before rotating log files.
        backup_count: Number of backup files to keep.
        console_level: Logging level for console output (e.g., logging.INFO).

    Returns:
        Configured Logger instance.
    """
    # Determine target logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    # Avoid adding duplicate handlers
    if not logger.handlers:
        # Ensure log directory exists
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # Common formatter for plain-text output
        text_fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(uuid)s [%(name)s.%(funcName)s] %(message)s"
        )
        # Setup UUID filter
        uuid_filter = UUIDFilter()
        logger.addFilter(uuid_filter)

        # Plain-text rotating file handler
        text_handler = RotatingFileHandler(
            Path(log_dir) / general_log,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        text_handler.setLevel(logging.DEBUG)
        text_handler.setFormatter(text_fmt)
        text_handler.addFilter(uuid_filter)
        logger.addHandler(text_handler)

        # JSON rotating file handler, if requested
        if json_log:
            json_handler = RotatingFileHandler(
                Path(log_dir) / json_log,
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(JSONFormatter())
            json_handler.addFilter(uuid_filter)
            logger.addHandler(json_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(text_fmt)
        console_handler.addFilter(uuid_filter)
        logger.addHandler(console_handler)

        # Prevent log propagation to ancestor loggers
        logger.propagate = False

    return logger
