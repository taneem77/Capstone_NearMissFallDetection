"""
Smart Cane Weekly Event Trends

Reads logged events and generates:
1. A weekly event-count summary CSV.
2. A weekly event-trend plot.
"""

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_FILE = Path("logs/events.csv")
SUMMARY_FILE = Path("logs/weekly_summary.csv")
PLOT_FILE = Path("logs/weekly_event_trends.png")


def get_week_start(timestamp):
    """Return the Monday of the week containing the timestamp."""
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    monday = dt.date() - timedelta(days=dt.weekday())
    return monday.isoformat()


def generate_weekly_summary():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    weekly_counts = defaultdict(lambda: defaultdict(int))

    with INPUT_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            week = get_week_start(row["timestamp"])
            event_type = row["event_type"]
            weekly_counts[week][event_type] += 1

    if not weekly_counts:
        print("No event records found.")
        return

    weeks = sorted(weekly_counts)
    event_types = sorted({
        event_type
        for counts in weekly_counts.values()
        for event_type in counts
    })

    # Write weekly summary CSV.
    with SUMMARY_FILE.open("w", newline="", encoding="utf-8") as file:
        fieldnames = ["week_start", "total_events"] + event_types
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for week in weeks:
            row = {
                "week_start": week,
                "total_events": sum(weekly_counts[week].values())
            }

            for event_type in event_types:
                row[event_type] = weekly_counts[week].get(event_type, 0)

            writer.writerow(row)

    # Plot weekly event counts by type.
    x_positions = list(range(len(weeks)))
    bar_width = 0.8 / max(len(event_types), 1)

    plt.figure(figsize=(10, 5))

    for index, event_type in enumerate(event_types):
        values = [
            weekly_counts[week].get(event_type, 0)
            for week in weeks
        ]

        offsets = [
            x + (index - (len(event_types) - 1) / 2) * bar_width
            for x in x_positions
        ]

        plt.bar(offsets, values, width=bar_width, label=event_type)

    plt.xticks(x_positions, weeks, rotation=30)
    plt.xlabel("Week starting (Monday)")
    plt.ylabel("Number of logged records")
    plt.title("Smart Cane Weekly Event Trends")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_FILE, dpi=150)
    plt.close()

    print("Weekly trend report generated successfully.")
    print(f"Summary CSV: {SUMMARY_FILE}")
    print(f"Trend plot: {PLOT_FILE}")


if __name__ == "__main__":
    generate_weekly_summary()