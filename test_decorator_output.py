import time
import pandas as pd
from pymaap.monitoring import Timer

# --- Define test functions ---

@Timer(log_to_console=False, log_to_file=True, results_format="csv", use_multiprocessing=False)
def slow_csv(): time.sleep(0.3)

@Timer(log_to_console=False, log_to_file=True, results_format="parquet", use_multiprocessing=False)
def slow_parquet(): time.sleep(0.3)

# --- Run both functions ---
print("Running CSV test function...")
slow_csv()

print("Running Parquet test function...")
slow_parquet()

# --- Try reading the output files ---
print("\nReading logs/timing_results.csv:")
try:
    df_csv = pd.read_csv("logs/timing_results.csv")
    print(df_csv.head())
except Exception as e:
    print("Failed to read CSV:", e)

print("\nReading logs/timing_results.parquet:")
try:
    df_parquet = pd.read_parquet("logs/timing_results.parquet")
    print(df_parquet.head())
except Exception as e:
    print("Failed to read Parquet:", e)