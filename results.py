import argparse
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def detect_most_recent_block(lines, bin_seconds=10, min_lines=5):
    # Parse all timestamps
    timestamps = [datetime.strptime(line["timestamp"], "%Y-%m-%d %H:%M:%S,%f") for line in lines]
    
    # Bin timestamps into bins of `bin_seconds`
    binned = [ts - timedelta(seconds=ts.second % bin_seconds, microseconds=ts.microsecond) for ts in timestamps]
    counter = Counter(binned)

    # Filter bins with at least min_lines entries
    valid_bins = [(bin_time, count) for bin_time, count in counter.items() if count >= min_lines]
    if not valid_bins:
        return None, None

    # Find the most recent valid bin
    most_recent_bin = max(valid_bins, key=lambda x: x[0])[0]

    # Define time window for that bin (allow a few bins before/after)
    start_time = most_recent_bin - timedelta(seconds=bin_seconds)
    end_time = most_recent_bin + timedelta(seconds=2 * bin_seconds)
    return start_time, end_time


def parse_log_file(log_file, start_time=None, end_time=None):
    with open(log_file) as f:
        lines = [json.loads(line) for line in f if "message" in line]

    if start_time or end_time:
        def in_window(line):
            ts = datetime.strptime(line["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
            return (start_time is None or ts >= start_time) and (end_time is None or ts <= end_time)
        lines = [line for line in lines if in_window(line)]

    pattern = re.compile(
        r"(?P<func>\w+): (?P<type>start|end): wall=(?P<wall>[\d.]+) perf=(?P<perf>[\d.]+) id=(?P<id>[\w-]+)"
        r"(?: duration=(?P<duration>[\d.]+)sec)? cpu=(?P<cpu>[\d.]+)% rss=(?P<rss>\d+) vms=(?P<vms>\d+) "
        r"mem%=(?P<mem>[\d.]+) threads=(?P<threads>\d+) fds=(?P<fds>\d+)"
    )

    execution_data = defaultdict(dict)

    for line in lines:
        match = pattern.search(line["message"])
        if match:
            d = match.groupdict()
            key = (d["func"], d["id"])
            parsed = {
                "wall": float(d["wall"]),
                "perf": float(d["perf"]),
                "cpu": float(d["cpu"]),
                "rss": int(d["rss"]),
                "vms": int(d["vms"]),
                "mem_percent": float(d["mem"]),
                "threads": int(d["threads"]),
                "fds": int(d["fds"]),
                "timestamp": datetime.strptime(line["timestamp"], "%Y-%m-%d %H:%M:%S,%f")
            }
            if d["duration"]:
                parsed["duration"] = float(d["duration"])
            execution_data[key][d["type"]] = parsed

    records = []
    for (func, id_), event in execution_data.items():
        if "start" in event and "end" in event:
            record = {
                "Function": func,
                "Call ID": id_,
                "Start Time": event["start"]["timestamp"],
                "End Time": event["end"]["timestamp"],
                "Wall Duration (s)": event["end"]["wall"] - event["start"]["wall"],
                "Perf Duration (s)": event["end"]["perf"] - event["start"]["perf"],
                "Duration (from log)": event["end"].get("duration", None),
                "Start CPU (%)": event["start"]["cpu"],
                "End CPU (%)": event["end"]["cpu"],
                "Start RSS": event["start"]["rss"],
                "End RSS": event["end"]["rss"],
                "Start Mem %": event["start"]["mem_percent"],
                "End Mem %": event["end"]["mem_percent"],
                "Start Threads": event["start"]["threads"],
                "End Threads": event["end"]["threads"],
                "Start FDs": event["start"]["fds"],
                "End FDs": event["end"]["fds"]
            }
            records.append(record)

    df = pd.DataFrame(records)
    df = df.sort_values(by="Start Time")
    return df


def generate_figures(df, output_dir):
    sns.set(style="whitegrid")

    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="Function", y="Perf Duration (s)")
    plt.title("Distribution of Execution Time per Function")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "perf_duration_boxplot.png")

    df_sorted = df.sort_values("Start Time")
    df_sorted["Start Seconds"] = (df_sorted["Start Time"] - df_sorted["Start Time"].min()).dt.total_seconds()

    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=df_sorted, x="Start Seconds", y="Function", size="Perf Duration (s)",
                    hue="Perf Duration (s)", palette="coolwarm", sizes=(20, 200))
    plt.title("Function Calls Over Time")
    plt.xlabel("Time since start (seconds)")
    plt.ylabel("Function")
    plt.legend(title="Perf Duration (s)", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(output_dir / "function_calls_over_time.png")

    df["CPU Delta"] = df["End CPU (%)"] - df["Start CPU (%)"]
    df["Memory Delta (MB)"] = (df["End RSS"] - df["Start RSS"]) / 1e6

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="Function", y="Memory Delta (MB)")
    plt.title("Memory Change per Function Call")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "memory_change_barplot.png")


def main():
    parser = argparse.ArgumentParser(description="Parse a timing log and generate performance plots.")
    parser.add_argument("--logfile", type=str, required=True, help="Path to the timing.log file")
    parser.add_argument("--output-dir", type=str, default=str(Path.cwd()), help="Directory to save figures")
    parser.add_argument("--start-time", type=str, help="Only include logs after this timestamp (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end-time", type=str, help="Only include logs before this timestamp (YYYY-MM-DD HH:MM:SS)")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S") if args.start_time else None
    end_time = datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S") if args.end_time else None

    # Load all log lines
    with open(args.logfile) as f:
        raw_lines = [json.loads(line) for line in f if "message" in line]

    # If no start/end time is specified, detect the most recent block of calls
    if start_time is None and end_time is None:
        start_time, end_time = detect_most_recent_block(raw_lines)
        if start_time and end_time:
            print(f"Auto-detected most recent call block from {start_time} to {end_time}")
        else:
            print("Could not detect a recent block of calls — please use --start-time and --end-time.")
            return

    # Parse and generate figures for the selected time window
    df = parse_log_file(args.logfile, start_time=start_time, end_time=end_time)
    if df.empty:
        print("No function calls found in the specified time window.")
    else:
        generate_figures(df, output_dir)
        print(f"Figures saved in: {output_dir}")


if __name__ == "__main__":
    main()