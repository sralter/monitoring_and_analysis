import json
import logging
import os
import csv
import functools
import time
import psutil
import uuid
from datetime import datetime
import pandas as pd
import geopandas as gpd
from logging.handlers import RotatingFileHandler

def sanitizer(arg_str):
    """
    Example sanitizer that replaces any digits with '*'.
    Usage:
      timer = Timer(max_arg_length=100, sanitize_func=sanitizer)
      error_handler = ErrorCatcher(sanitize_func=sanitizer)
    """
    return ''.join('*' if c.isdigit() else c for c in arg_str)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.__dict__.get("function_name", "N/A"),
            "uuid": record.__dict__.get("uuid", "N/A")
        }
        return json.dumps(log_record)

class Timer:
    """A decorator for timing and profiling function execution.
    
    By default, results are saved as a CSV file. With results_format="parquet",
    results are stored in a Parquet file, appending a new row for each call.
    """
    
    def __init__(self, log_to_console=True, log_to_file=True, track_resources=True, 
                 max_arg_length=None, sanitize_func=None, results_format="csv"):
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.track_resources = track_resources
        self.max_arg_length = max_arg_length
        self.sanitize_func = sanitize_func
        self.results_format = results_format.lower()  # "csv" or "parquet"

        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        if self.results_format == "csv":
            self.RESULTS_FILE = os.path.join(self.log_dir, "timing_results.csv")
        elif self.results_format == "parquet":
            self.RESULTS_FILE = os.path.join(self.log_dir, "timing_results.parquet")
        else:
            raise ValueError("results_format must be either 'csv' or 'parquet'")
        self.LOG_FILE = os.path.join(self.log_dir, "timing.log")

        self._ensure_files_exist()
        self._setup_logging()

    def _ensure_files_exist(self):
        """Ensure necessary files exist with proper headers (for CSV mode)."""
        if self.results_format == "csv":
            if not os.path.exists(self.RESULTS_FILE):
                with open(self.RESULTS_FILE, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "UUID", "Function Name", "Execution Time (s)", 
                                     "CPU Time (sec)", "Memory Change (MB)", "Final Memory Usage (MB)", "Arguments", "Log Message"])
                print(f"Created fresh {self.RESULTS_FILE}")
        if not os.path.exists(self.LOG_FILE):
            open(self.LOG_FILE, "w").close()
            print(f"Created fresh {self.LOG_FILE}")

    def _setup_logging(self):
        """Configure logging with JSON formatting and log rotation."""
        logging.shutdown()
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        rotating_handler = RotatingFileHandler(self.LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
        rotating_handler.setFormatter(JSONFormatter())
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(rotating_handler)
        logger.addHandler(console_handler)

    def _save_results(self, timestamp, call_uuid, function_name, elapsed_time, cpu_time, mem_change, final_mem, args_repr, log_message):
        """Save timing and resource results to the chosen file format."""
        if self.results_format == "csv":
            with open(self.RESULTS_FILE, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, call_uuid, function_name, elapsed_time, cpu_time, mem_change, final_mem, args_repr, log_message])
        elif self.results_format == "parquet":
            row = {
                "Timestamp": timestamp,
                "UUID": call_uuid,
                "Function Name": function_name,
                "Execution Time (s)": elapsed_time,
                "CPU Time (sec)": cpu_time,
                "Memory Change (MB)": mem_change,
                "Final Memory Usage (MB)": final_mem,
                "Arguments": args_repr,
                "Log Message": log_message
            }
            # Read existing parquet file if it exists
            try:
                df_existing = pd.read_parquet(self.RESULTS_FILE)
                df_new = pd.DataFrame([row])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            except (FileNotFoundError, ValueError):
                # File does not exist or is empty, so just create a new DataFrame.
                df_combined = pd.DataFrame([row])
            df_combined.to_parquet(self.RESULTS_FILE, index=False)

    def __call__(self, func):
        """Wrap the function call with timing and logging."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            call_uuid = str(uuid.uuid4())
            start_time = time.perf_counter()
            process = psutil.Process(os.getpid())
            cpu_start = (process.cpu_times().user + process.cpu_times().system) if self.track_resources else None
            mem_start = (process.memory_info().rss / (1024 ** 2)) if self.track_resources else None

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logging.exception("Function `%s` raised an exception", func.__name__,
                                  extra={"function_name": func.__name__, "uuid": call_uuid})
                raise

            elapsed_time = time.perf_counter() - start_time
            cpu_end = (process.cpu_times().user + process.cpu_times().system) if self.track_resources else None
            mem_end = (process.memory_info().rss / (1024 ** 2)) if self.track_resources else None

            cpu_time = cpu_end - cpu_start if cpu_start is not None else None
            mem_change = mem_end - mem_start if mem_start is not None else None
            final_mem = mem_end if mem_end is not None else None

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            def safe_serialize(obj):
                """Convert args/kwargs to string with optional sanitization and truncation."""
                if isinstance(obj, (pd.DataFrame, gpd.GeoDataFrame)):
                    return f"<DataFrame with {len(obj)} rows>"
                try:
                    s = str(obj)
                except Exception:
                    s = "<unserializable>"
                if self.sanitize_func:
                    s = self.sanitize_func(s)
                if self.max_arg_length is not None and len(s) > self.max_arg_length:
                    s = s[:self.max_arg_length] + "..."
                return s

            args_repr = json.dumps({
                "args": [safe_serialize(arg) for arg in args],
                "kwargs": {k: safe_serialize(v) for k, v in kwargs.items()}
            })

            log_message = f"Function `{func.__name__}` executed in {elapsed_time:.4f} sec"
            if self.track_resources:
                log_message += f", CPU Time: {cpu_time:.4f} sec, Memory Change: {mem_change:.4f} MB, Final Memory: {final_mem:.4f} MB"
            if self.log_to_console:
                print(log_message)
            logging.info(log_message, extra={"function_name": func.__name__, "uuid": call_uuid})

            if self.log_to_file:
                self._save_results(timestamp, call_uuid, func.__name__, elapsed_time, cpu_time, mem_change, final_mem, args_repr, log_message)

            return result

        return wrapper

class ErrorCatcher:
    """
    A decorator for catching and logging exceptions.
    
    Logs error details with a unique UUID and function name to a dedicated error log file
    (using log rotation, default: 10 MB max size, 5 backups). Optionally sanitizes the exception
    message and saves error details to a results file in CSV or Parquet format.
    """
    
    def __init__(self, log_to_console=True, log_to_file=True,
                 error_log_file=None, max_bytes=10*1024*1024, backup_count=5,
                 sanitize_func=None, results_format="csv", max_arg_length=None):
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.sanitize_func = sanitize_func
        self.max_arg_length = max_arg_length
        self.results_format = results_format.lower()

        if self.results_format == "csv":
            self.RESULTS_FILE = os.path.join("logs", "error_results.csv")
        elif self.results_format == "parquet":
            self.RESULTS_FILE = os.path.join("logs", "error_results.parquet")
        else:
            raise ValueError("results_format must be either 'csv' or 'parquet'")
            
        if error_log_file is None:
            self.error_log_file = os.path.join("logs", "error.log")
        else:
            self.error_log_file = error_log_file
        
        os.makedirs("logs", exist_ok=True)
        self._ensure_error_file()
        self._setup_error_logging()
    
    def _ensure_error_file(self):
        """Ensure the error results file exists (for CSV mode)."""
        if self.results_format == "csv":
            if not os.path.exists(self.RESULTS_FILE):
                with open(self.RESULTS_FILE, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Timestamp", "UUID", "Function Name", "Error Message", "Arguments"])
                print(f"Created fresh {self.RESULTS_FILE}")
    
    def _setup_error_logging(self):
        """Set up a dedicated logger for error catching with JSON formatting and log rotation."""
        self.logger = logging.getLogger("error_catcher")
        self.logger.setLevel(logging.ERROR)
        self.logger.handlers = []
        if self.log_to_file:
            rotating_handler = RotatingFileHandler(self.error_log_file, maxBytes=self.max_bytes, backupCount=self.backup_count)
            rotating_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(rotating_handler)
        if self.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(console_handler)
    
    def _safe_serialize(self, obj):
        """Serialize an object to string with optional sanitization and truncation."""
        try:
            s = str(obj)
        except Exception:
            s = "<unserializable>"
        if self.sanitize_func:
            s = self.sanitize_func(s)
        if self.max_arg_length is not None and len(s) > self.max_arg_length:
            s = s[:self.max_arg_length] + "..."
        return s
    
    def _save_error(self, timestamp, call_uuid, function_name, error_msg, args_repr):
        """Save error details to the chosen results file format."""
        if self.results_format == "csv":
            with open(self.RESULTS_FILE, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, call_uuid, function_name, error_msg, args_repr])
        elif self.results_format == "parquet":
            row = {
                "Timestamp": timestamp,
                "UUID": call_uuid,
                "Function Name": function_name,
                "Error Message": error_msg,
                "Arguments": args_repr
            }
            # Append the new row to existing data (if any)
            try:
                df_existing = pd.read_parquet(self.RESULTS_FILE)
                df_new = pd.DataFrame([row])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            except (FileNotFoundError, ValueError):
                df_combined = pd.DataFrame([row])
            df_combined.to_parquet(self.RESULTS_FILE, index=False)
    
    def __call__(self, func=None):
        """Wrap the function call to catch exceptions, log them, and save error details."""
        if func is None: # when no function argument is given
            # Returning a wrapper function so that @ErrorCatcher() works
            return lambda f: self.__call__(f)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            call_uuid = str(uuid.uuid4())
            try:
                return func(*args, **kwargs)
            except Exception as e:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_msg = str(e)
                if self.sanitize_func:
                    error_msg = self.sanitize_func(error_msg)
                args_repr = json.dumps({
                    "args": [self._safe_serialize(arg) for arg in args],
                    "kwargs": {k: self._safe_serialize(v) for k, v in kwargs.items()}
                })
                self.logger.exception(
                    "Function `%s` raised an exception: %s", func.__name__, error_msg,
                    extra={"function_name": func.__name__, "uuid": call_uuid}
                )
                self._save_error(timestamp, call_uuid, func.__name__, error_msg, args_repr)
                raise
        return wrapper
    