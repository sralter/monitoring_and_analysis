# pymaap/logging_backend.py
import multiprocessing
import atexit
import json
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

_log_queue = None
_writer_process = None
_log_file_path = None

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": getattr(record, "function_name", "N/A"),
            "uuid": getattr(record, "uuid", "N/A"),
        }
        return json.dumps(log_record)

def _writer_worker(queue, log_file):
    logger = logging.getLogger("mp_logger")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    while True:
        record = queue.get()
        if record == "STOP":
            break
        logger.handle(record)

def init_multiprocessing_logging(log_file="logs/timing.log"):
    global _log_queue, _writer_process, _log_file_path

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    _log_queue = multiprocessing.Queue()
    _log_file_path = log_file
    _writer_process = multiprocessing.Process(target=_writer_worker, args=(_log_queue, log_file))
    _writer_process.start()

    # Ensure it shuts down cleanly
    atexit.register(shutdown_multiprocessing_logging)

def shutdown_multiprocessing_logging():
    global _log_queue, _writer_process
    if _log_queue:
        _log_queue.put("STOP")
    if _writer_process:
        _writer_process.join()

def get_log_queue():
    return _log_queue