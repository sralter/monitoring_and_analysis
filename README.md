# monitoring

By Samuel Alter

## 1. Overview <a name='overview'></a>

A Python module for robust execution monitoring and error logging. This module provides two decorators:
* **Timer**: Logs function execution time, CPU usage, memory usage, and captures function arguments. Performance data is saved to a CSV file and logged in JSON format.
* **ErrorCatcher**: Catches and logs exceptions with a full traceback to a dedicated error log file using log rotation. Both decorators generate a unique UUID per function call for tracking.

Note: this decorator is not working for functions using multiprocessing.

## 2. Table of Contents <a name='toc'></a>

- [monitoring](#monitoring)
  - [1. Overview ](#1-overview-)
  - [2. Table of Contents ](#2-table-of-contents-)
  - [3. Features ](#3-features-)
  - [4. Installation ](#4-installation-)
  - [5. Configuration Options ](#5-configuration-options-)
    - [Timer Decorator Parameters ](#timer-decorator-parameters-)
    - [ErrorCatcher Decorator Parameters ](#errorcatcher-decorator-parameters-)
  - [6. Usage ](#6-usage-)
    - [Example with the Timer decorator ](#example-with-the-timer-decorator-)
    - [Example with the ErrorCatcher decorator ](#example-with-the-errorcatcher-decorator-)
    - [Example with both decorators combined ](#example-with-both-decorators-combined-)
  - [Customization ](#customization-)
  - [Contributing ](#contributing-)
   

## 3. Features <a name='features'></a>

[Back to TOC](#toc)

* **High-Resolution Timing**: Uses time.perf_counter() for precise measurements.
* **Process-Specific Metrics**: Tracks CPU time and memory usage for your process.
* **Structured Logging**: Outputs logs in JSON format for easy integration with log aggregation tools.
  * Saves log files in the working directory with the following structure:
  ```plaintext
  logs/
  ├── timing.log
  │   JSON-formatted performance logs
  │   (rotates at 10 MB, up to 5 backups)
  ├── timing_results.csv
  │   CSV file containing timing, CPU, and memory metrics
  │   for each function call
  └── error.log
      JSON-formatted error log capturing exceptions
      (rotates at 10 MB, up to 5 backups)
  ```
* **Error Logging**: Separates error logging from performance logs for clarity and monitoring.
* **Customizable Sanitation**: Optionally sanitize logged arguments or error messages to mask sensitive data.
* **Log Rotation**: Automatically rotates log files (default: 10 MB max size, 5 backups).

## 4. Installation <a name='install'></a>

[Back to TOC](#toc)

Simply copy the monitoring.py file into your project. Ensure that you have the following Python packages installed:
* `psutil`
* `pandas`
* `geopandas` (if you plan to log dataframes)
* (Standard library modules such as `logging`, `csv`, `json`, `functools`, etc., are included with Python.)

You can install `psutil` using `pip`:
```bash
pip install psutil
```

## 5. Configuration Options <a name='config'></a>

[Back to TOC](#toc)

Both decorators accept several optional arguments to customize their behavior.

### Timer Decorator Parameters <a name='tp'></a>

* **`log_to_console (bool, default=True)`**:  
  Print log messages to the console.

* **`log_to_file (bool, default=True)`**:  
  Save log messages to a file (`timing.log` for performance logs).

* **`track_resources (bool, default=True)`**:  
  Track CPU and memory usage during function execution.

* **`max_arg_length (int or None, default=None)`**:  
  If set, function arguments are truncated to the specified maximum length when logged.

* **`sanitize_func (callable or None, default=None)`**:  
  A function to sanitize logged strings (e.g., masking sensitive data).  
  _Example:_  
  ```python
  def sanitizer(arg_str):
      return ''.join('*' if c.isdigit() else c for c in arg_str)
  ```

* **`results_format (str, default='csv')`**:
  Specify the format for saving timing results. Use `'csv'` (default) to save to a CSV file or `'parquet'` to save to a Parquet file.

### ErrorCatcher Decorator Parameters <a name='ep'></a>

* **`log_to_console (bool, default=True)`**:
  Print error logs to the console.

* **`log_to_file (bool, default=True)`**:
  Save error logs to a dedicated error log file (`error.log`).

* **`error_log_file (str or None, default=None)`**:
  Custom path for the error log file. If None, defaults to `logs/error.log`.

* **`max_bytes (int, default=10*1024*1024)`**:
  Maximum size in bytes for the error log file before rotation (default is 10 MB).

* **`backup_count (int, default=5)`**:
  Number of backup files to keep during log rotation.

* **`sanitize_func (callable or None, default=None)`**:
  A function to sanitize error messages before logging (useful for masking sensitive data).

* **`max_arg_length (int or None, default=None)`**:  
  If set, function arguments are truncated to the specified maximum length when logged in the error results.

## 6. Usage <a name='usage'></a>

[Back to TOC](#toc)

Import the decorators from the module and apply them to your functions. You can use them individually or together.

### Example with the Timer decorator <a name='timer_example'></a>

[Back to TOC](#toc)

```python
from monitoring import Timer
import logging
import time

@Timer(max_arg_length=100, sanitize_func=lambda s: s.replace("secret", "*****"))
def my_function(x, y):
    """Dummy function that simulates processing with the timer decorator."""
    logging.info("My function started")
    time.sleep(2)  # Simulate processing
    logging.info("My function completed")
    return x + y

result = my_function(5, 10)
print(f"Result: {result}")
```

**What Happens**:
* The function’s start and completion messages are logged.
* Execution time, CPU time, memory change, and final memory usage are recorded in `logs/timing_results.csv`.
* A JSON-formatted log is written to `logs/timing.log`, which rotates once it reaches 10 MB.
* Function arguments are sanitized and truncated as specified.

### Example with the ErrorCatcher decorator <a name='error_example'></a>

[Back to TOC](#toc)

```python
from monitoring import ErrorCatcher
import logging

@ErrorCatcher(sanitize_func=lambda s: s.replace("password", "*****"))
def error_function():
    """Dummy function that simulates processing with an error and the error-catching decorator."""
    logging.info("Error function starting")
    # Deliberately raise an exception to test error logging.
    raise ValueError("This is a test error with a secret password!")

try:
    error_function()
except Exception as e:
    print(f"Caught an exception as expected: {e}")
```

**What Happens**:
* When `error_function` raises an exception, the ErrorCatcher logs a detailed error message (including a sanitized exception message) with a full traceback.
* The error log is written to `logs/error.log` with log rotation (default: 10 MB max, 5 backups).
* The exception is re‑raised so you can catch it in your code.

### Example with both decorators combined <a name='combined'></a>

[Back to TOC](#toc)

You can stack the decorators to get both error logging and performance modeling. 

Note that `ErrorCatcher` should be the outer decorator (i.e., placed above `Timer`). This way, it catches any exception thrown by the function itself or even from within the `Timer` decorator:

```python
from monitoring import Timer, ErrorCatcher, sanitizer
import logging
import time

@ErrorCatcher(sanitize_func=sanitizer)
@Timer(max_arg_length=100, sanitize_func=sanitizer)
def combined_function(a, b):
    """Dummy function to demonstrate both uses of monitoring decorators."""
    logging.info("Combined function started")
    time.sleep(1)
    if a < 0:
        raise ValueError("Invalid value for a!")
    logging.info("Combined function completed")
    return a * b

# Successful run
print("Combined function result:", combined_function(3, 7))

# Exception case
try:
    combined_function(-1, 7)
except Exception as e:
    print(f"Caught an exception: {e}")
```

## Customization <a name='custom'></a>

[Back to TOC](#toc)

**Sanitization**:  
Provide your own sanitizer function to remove or mask sensitive data from logged messages.

**Log Rotation Parameters**:  
Both Timer and ErrorCatcher use rotating file handlers. You can adjust the max file size and backup count by passing parameters to the decorators if needed.

## Contributing <a name='contribute'></a>

[Back to TOC](#toc)

Feel free to fork this repository and submit pull requests if you have improvements or bug fixes.
