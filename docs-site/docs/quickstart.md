## 🚀 Getting Started with PyMAAP

PyMAAP helps you monitor, log, and analyze the performance and behavior of your Python functions. It includes two main tools:

- `monitoring.py`: Decorators and tools to **track performance, log errors, and save metrics**.
- `analysis.py`: CLI script to **analyze log files and generate insightful plots**.

---

## 📦 Installation

```bash
uv pip install pymaap
```

---

## 🔍 1. Monitoring Functions

Import the decorators and wrap your functions:

```python
from pymaap.monitoring import Timer, ErrorCatcher, sanitizer

timer = Timer(results_format="csv", max_arg_length=200, sanitize_func=sanitizer)
error_handler = ErrorCatcher(results_format="csv", sanitize_func=sanitizer)

@error_handler
@timer
def my_function(x, y):
    return x + y
```

### ✅ Options

- `results_format`: `"csv"` or `"parquet"`
- `sanitize_func`: Custom sanitizer for sensitive args/logs
- `log_to_console`: Print logs to console (default `True`)
- `use_multiprocessing`: Use locks/log queues in multi-process apps

This creates:
- `logs/timing_results.csv` or `.parquet`
- `logs/error_results.csv` or `.parquet`
- `logs/timing.log`
- `logs/error.log`

---

### 📏 Manual Metrics

You can also log timing manually using:

```python
from pymaap.monitoring import get_metrics_start, get_metrics_end

start_metrics = get_metrics_start("my_custom_block")
# ... your code ...
end_metrics = get_metrics_end(start_metrics)
```

---

## 📊 2. Analyzing Logs

Once you’ve collected logs, analyze them via CLI:

```bash
python -m pymaap.analysis \
  --logdir logs \
  --subtitle "Post-deployment test" \
  --tag run1
```

### CLI Options

- `--logdir`: Folder with `timing.log` files
- `--subtitle`: Subtitle for all plots (or `"none"` to disable)
- `--tag`: Folder name suffix for outputs (default: `"run"`)
- `--start-time` / `--end-time`: Optional override of time window

Outputs go to `figs/YYYY-MM-DD_HH-MM-SS_run1/`:
- Execution plots
- Histograms
- Aggregate CSVs
- Metadata

---

## 📁 Example Output Structure

```
figs/
└── 2025-04-01_14-00-01_run1/
    ├── execution_time_per_function.png
    ├── function_calls_over_time.png
    ├── memory_change_per_function_call.png
    ├── top10_functions_by_total_time.png
    ├── hist_*.png
    ├── results.csv
    ├── results_aggregate.csv
    └── README.txt
```
