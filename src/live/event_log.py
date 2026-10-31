
"""
Smart Cane Event Logger

Stores detected events in a structured CSV file.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone


EVENT_COLUMNS = [
    "event_id",
    "timestamp",
    "event_type",
    "detection_score",
    "source",
    "duration_s"
]


class EventLogger:

    def __init__(self, output_path="logs/events.csv"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(
            parents=True, exist_ok=True
        )

        self._write_header()

    def _write_header(self):
        if not self.output_path.exists() or self.output_path.stat().st_size == 0:
            with self.output_path.open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file, fieldnames=EVENT_COLUMNS
                )
                writer.writeheader()

    def log_event(
        self,
        event_id,
        timestamp,
        event_type,
        detection_score,
        source="detector",
        duration_s=None
    ):
        """Append one detected event to the event log."""

        row = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "detection_score": detection_score,
            "source": source,
            "duration_s": duration_s
        }

        with self.output_path.open(
            "a", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=EVENT_COLUMNS
            )
            writer.writerow(row)

        print(f"Logged event: {event_id}")


if __name__ == "__main__":

    logger = EventLogger()

    logger.log_event(
        event_id=1,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="recovery_like_event",
        detection_score=0.87,
        source="simulated_detector",
        duration_s=1.2
    )

    logger.log_event(
        event_id=2,
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="normal_activity",
        detection_score=0.12,
        source="simulated_detector",
        duration_s=0.8
    )

    print("Event logging test completed.")
