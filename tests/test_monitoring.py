# tests/test_monitoring.py

import time
import multiprocessing
import os
import pandas as pd
import pytest
from pymaap.monitoring import Timer, ErrorCatcher, get_metrics_start, get_metrics_end
from pymaap.analysis import analysis

@pytest.fixture(scope="session", autouse=True)
def clear_logs():
    os.makedirs("logs", exist_ok=True)
    for f in ["timing_results.csv", "timing_results.parquet", "error_results.csv"]:
        path = os.path.join("logs", f)
        if os.path.exists(path):
            os.remove(path)
    yield  # tests run here

@Timer(log_to_console=False, log_to_file=True, results_format="csv", use_multiprocessing=False)
def slow_csv(x): time.sleep(x)

@Timer(log_to_console=False, log_to_file=True, results_format="parquet", use_multiprocessing=False)
def slow_parquet(x): time.sleep(x)

@Timer(log_to_console=False, log_to_file=True, results_format="csv", use_multiprocessing=True)
def slow_csv_mp(x): time.sleep(x)

@Timer(log_to_console=False, log_to_file=True, results_format="parquet", use_multiprocessing=True)
def slow_parquet_mp(x): time.sleep(x)

@ErrorCatcher(log_to_console=False, log_to_file=True, results_format="csv")
def faulty(): return 1 / 0

# ---- Tests ----

def test_csv_single():
    slow_csv(0.5)
    df = pd.read_csv("logs/timing_results.csv")
    assert not df.empty
    assert (df["Execution Time (s)"] > 0).all()
    assert "Function Name" in df.columns
    assert df["Function Name"].str.contains("slow_csv").any()

def test_parquet_single():
    slow_parquet(0.5)
    df = pd.read_parquet("logs/timing_results.parquet")
    assert not df.empty
    assert "Function Name" in df.columns
    assert df["Execution Time (s)"].max() > 0

@pytest.mark.skip(reason="Multiprocessing currently not supported in Timer")
def test_csv_multiprocessing():
    with multiprocessing.Pool(2) as pool:
        pool.map(slow_csv_mp, [0.5, 0.5])
    df = pd.read_csv("logs/timing_results.csv")
    assert len(df) >= 2

@pytest.mark.skip(reason="Multiprocessing currently not supported in Timer")
def test_parquet_multiprocessing():
    with multiprocessing.Pool(2) as pool:
        pool.map(slow_parquet_mp, [0.5, 0.5])
    df = pd.read_parquet("logs/timing_results.parquet")
    assert len(df) >= 2

def test_error_logging():
    with pytest.raises(ZeroDivisionError):
        faulty()
    df = pd.read_csv("logs/error_results.csv")
    assert not df.empty
    assert "Error Message" in df.columns
    assert df["Error Message"].str.contains("division").any()

def test_manual_metrics_tracking():
    start = get_metrics_start("manual_test")
    time.sleep(1)
    end = get_metrics_end(start, "manual_test")
    assert end["duration"] >= 1.0