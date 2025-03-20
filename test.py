import time
import multiprocessing
import pandas as pd
import sys
import os
from monitoring import Timer  # Import the Timer class from monitoring.py

# Set multiprocessing start method for compatibility
if __name__ == "__main__":
    if sys.platform != "win32":  # Windows does not support 'fork'
        multiprocessing.set_start_method("fork", force=True)
    multiprocessing.freeze_support()  # Required for Windows multiprocessing

# Single-Process Test Function (CSV)
@Timer(log_to_console=True, log_to_file=True, results_format="csv", use_multiprocessing=False)
def test_function_single_process_csv(n):
    """Simulate a function that takes time to execute (single process, CSV logging)."""
    time.sleep(n)
    return n

# Single-Process Test Function (Parquet)
@Timer(log_to_console=True, log_to_file=True, results_format="parquet", use_multiprocessing=False)
def test_function_single_process_parquet(n):
    """Simulate a function that takes time to execute (single process, Parquet logging)."""
    time.sleep(n)
    return n

# Multi-Process Test Function (CSV)
@Timer(log_to_console=True, log_to_file=True, results_format="csv", use_multiprocessing=False)
def test_function_multi_process_csv(n):
    """Simulate a function that takes time to execute (multi-process, CSV logging)."""
    time.sleep(n)
    return n

# Multi-Process Test Function (Parquet)
@Timer(log_to_console=True, log_to_file=True, results_format="parquet", use_multiprocessing=False)
def test_function_multi_process_parquet(n):
    """Simulate a function that takes time to execute (multi-process, Parquet logging)."""
    time.sleep(n)
    return n

# Run Single-Process Test (CSV)
def run_single_process_test_csv():
    print("\n--- Running Single Process Test (CSV) ---\n")
    for i in range(1, 4):
        test_function_single_process_csv(i * 0.5)

# Run Single-Process Test (Parquet)
def run_single_process_test_parquet():
    print("\n--- Running Single Process Test (Parquet) ---\n")
    for i in range(1, 4):
        test_function_single_process_parquet(i * 0.5)

# Run Multi-Processing Test (CSV)
def run_multiprocessing_test_csv():
    print("\n--- Running Multi-Process Test (CSV) ---\n")
    
    pool_size = 4
    sleep_times = [0.5, 1, 1.5, 2]

    with multiprocessing.Pool(pool_size) as pool:
        pool.map(test_function_multi_process_csv, sleep_times)

# Run Multi-Processing Test (Parquet)
def run_multiprocessing_test_parquet():
    print("\n--- Running Multi-Process Test (Parquet) ---\n")
    
    pool_size = 4
    sleep_times = [0.5, 1, 1.5, 2]

    with multiprocessing.Pool(pool_size) as pool:
        pool.map(test_function_multi_process_parquet, sleep_times)

# Verify CSV Results
def verify_csv_results():
    print("\n--- Verifying CSV Results ---\n")
    results_file = "logs/timing_results.csv"
    
    if os.path.exists(results_file):
        df = pd.read_csv(results_file)
        print(df.tail(5))
    else:
        print("CSV file not found! Test may have failed.")

# Verify Parquet Results
def verify_parquet_results():
    print("\n--- Verifying Parquet Results ---\n")
    results_file = "logs/timing_results.parquet"
    
    if os.path.exists(results_file):
        df = pd.read_parquet(results_file)
        print(df.tail(5))
    else:
        print("Parquet file not found! Test may have failed.")

# Main Execution Block
if __name__ == "__main__":
    run_single_process_test_csv()
    verify_csv_results()
    
    run_single_process_test_parquet()
    verify_parquet_results()
    
    run_multiprocessing_test_csv()
    verify_csv_results()
    
    run_multiprocessing_test_parquet()
    verify_parquet_results()

    print("\nAll tests completed successfully.")