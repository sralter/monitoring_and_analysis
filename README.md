# monitoring

By Samuel Alter

## Overview <a name='overview'></a>

A Python module for robust execution monitoring and error logging. This module provides two decorators:
* **Timer**: Logs function execution time, CPU usage, memory usage, and captures function arguments. Performance data is saved to a CSV file and logged in JSON format.
* **ErrorCatcher**: Catches and logs exceptions with a full traceback to a dedicated error log file using log rotation. Both decorators generate a unique UUID per function call for tracking.

## Table of Contents <a name='toc'></a>

1. [Overview ](#overview)
2. [Table of Contents](#toc)
3. [Features](#features)
4. [Installation](#installation)
5. [Usage](#usage)
   
   a. [Example Usage](#timer_example)
   

## Features <a name='features'></a>
* **High-Resolution Timing**: Uses time.perf_counter() for precise measurements.
* **Process-Specific Metrics**: Tracks CPU time and memory usage for your process.
* **Structured Logging**: Outputs logs in JSON format for easy integration with log aggregation tools.
* **Error Logging**: Separates error logging from performance logs for clarity and monitoring.
* **Customizable Sanitation**: Optionally sanitize logged arguments or error messages to mask sensitive data.
* **Log Rotation**: Automatically rotates log files (default: 10 MB max size, 5 backups).

## Installation <a name='install'></a>

Simply copy the monitoring.py file into your project. Ensure that you have the following Python packages installed:
* `psutil`
* `pandas`
* `geopandas` (if you plan to log dataframes)
* (Standard library modules such as `logging`, `csv`, `json`, `functools`, etc., are included with Python.)

You can install `psutil` using `pip`:
`pip install psutil`

## Usage <a name='usage'></a>

Import the decorators from the module and apply them to your functions. You can use them individually or together.

### Example with the Timer Decorator <a name='timer_example'></a>

```
