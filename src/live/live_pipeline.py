
"""
Smart Cane Live Processing Pipeline.

Connects:
1. Sensor message validation
2. Candidate event detection
3. Event logging

Currently processes JSON-lines input for testing.
Actual Wi-Fi integration will be added after the ESP32
communication protocol is confirmed.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.live.wifi_logger import read_json_lines, validate_message
from src.live.event_detector import CandidateEventDetector
from src.live.event_log import EventLogger


def run_pipeline(input_path, event_output):
    detector = CandidateEventDetector()
    logger = EventLogger(event_output)

    processed = 0
    rejected = 0
    detected = 0

    for raw_message in read_json_lines(input_path):

        try:
            message = validate_message(raw_message)
        except ValueError as error:
            print(f"Rejected sensor message: {error}")
            rejected += 1
            continue

        processed += 1

        event = detector.process(message)

        if event is not None:
            detected += 1

            logger.log_event(
                event_id=detected,
                timestamp=str(event["timestamp"]),
                event_type=event["event_type"],
                detection_score=1.0,
                source="candidate_motion_detector",
                duration_s=None
            )

    print("\nLive Pipeline Summary")
    print("---------------------")
    print(f"Processed messages: {processed}")
    print(f"Rejected messages: {rejected}")
    print(f"Candidate events: {detected}")
    print(f"Event output: {event_output}")


def main():
    parser = argparse.ArgumentParser(
        description="Smart Cane live processing pipeline"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="JSON-lines sensor input file"
    )

    parser.add_argument(
        "--events",
        default="logs/pipeline_events.csv",
        help="Output event CSV file"
    )

    args = parser.parse_args()

    run_pipeline(args.input, args.events)


if __name__ == "__main__":
    main()
