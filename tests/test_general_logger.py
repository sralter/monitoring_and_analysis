# tests/test_general_logger.py

import os
import json
import re
import logging
import pytest

import pymaap

@pytest.fixture(autouse=True)
def tmp_logs(tmp_path, monkeypatch):
    # Run tests in an isolated tmpdir and ensure clean logs/
    monkeypatch.chdir(tmp_path)
    log_dir = tmp_path / "logs"
    if log_dir.exists():
        for f in log_dir.iterdir():
            f.unlink()
    return log_dir

def test_log_files_created(tmp_logs):
    # Initialize and verify directory + files exist
    pymaap.init_general_logger(log_dir=str(tmp_logs))
    assert tmp_logs.exists(), "log_dir should be created"
    assert (tmp_logs / "general.log").exists()
    assert (tmp_logs / "general.json.log").exists()

def test_text_log_and_console_output(tmp_logs, capsys):
    # Initialize
    logger = pymaap.init_general_logger(log_dir=str(tmp_logs))
    # Emit INFO
    logger.info("Hello, world")
    # Capture console
    captured = capsys.readouterr()
    assert "Hello, world" in captured.out
    # Read text log
    text = (tmp_logs / "general.log").read_text().strip().splitlines()[-1]
    # Check pattern: timestamp, level, uuid, [name.func], message
    pattern = (
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
        r"INFO [0-9a-f-]{36} \[.*\] Hello, world$"
    )
    assert re.match(pattern, text), f"Text log did not match: {text}"

def test_json_log_entries(tmp_logs):
    logger = pymaap.init_general_logger(log_dir=str(tmp_logs))
    logger.warning("JSON test message")
    lines = (tmp_logs / "general.json.log").read_text().strip().splitlines()
    assert lines, "JSON log should have at least one line"
    entry = json.loads(lines[-1])
    # Required keys and values
    assert "timestamp" in entry
    assert entry["level"] == "WARNING"
    assert entry["message"] == "JSON test message"
    assert isinstance(entry["uuid"], str) and len(entry["uuid"]) == 36
    assert "function" in entry

def test_multiple_messages_and_rotation(tmp_logs):
    # Force rotation by setting max_bytes small
    logger = pymaap.init_general_logger(
        log_dir=str(tmp_logs),
        max_bytes=100,  # tiny threshold
        backup_count=1,
    )
    # Emit several messages
    for i in range(20):
        logger.info(f"msg {i}")
    # After rotation, we should see .log and .1 files
    text_files = sorted(str(p.name) for p in tmp_logs.iterdir() if p.suffix == ".log")
    assert "general.log" in text_files
    # rotated backup file may be general.log.1
    assert any(f.startswith("general.log.") for f in text_files)

def test_reinit_no_duplicate_handlers(tmp_logs, capsys):
    # Initialize twice
    pymaap.init_general_logger(log_dir=str(tmp_logs))
    pymaap.init_general_logger(log_dir=str(tmp_logs))
    logger = logging.getLogger()  # root logger
    # There should only be 3 handlers: text, json, and console
    handler_types = {type(h) for h in logger.handlers}
    from logging.handlers import RotatingFileHandler
    from logging import StreamHandler
    assert handler_types == {RotatingFileHandler, StreamHandler}