from .monitoring import Timer, ErrorCatcher, get_metrics_start, get_metrics_end
from .analysis import generate_plots, parse_log_lines, detect_recent_dense_block

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # for Python < 3.8

__version__ = version("pymaap")