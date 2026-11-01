
"""
Smart Cane Candidate Event Detector.

Identifies candidate high-motion episodes using IMU signals.
Includes a cooldown to prevent repeated detections.
"""

import numpy as np


class CandidateEventDetector:

    def __init__(
        self,
        acceleration_threshold=3.0,
        gyroscope_threshold=100.0,
        consecutive_samples=5,
        cooldown_s=1.0
    ):
        self.acceleration_threshold = acceleration_threshold
        self.gyroscope_threshold = gyroscope_threshold
        self.consecutive_samples = consecutive_samples
        self.cooldown_s = cooldown_s

        self.motion_count = 0
        self.last_event_time = None

    def process(self, message):

        acceleration = np.array([
            message["acc_x"],
            message["acc_y"],
            message["acc_z"]
        ], dtype=float)

        gyroscope = np.array([
            message["gyro_x"],
            message["gyro_y"],
            message["gyro_z"]
        ], dtype=float)

        acceleration_magnitude = np.linalg.norm(acceleration)
        gyroscope_magnitude = np.linalg.norm(gyroscope)

        dynamic_acceleration = abs(
            acceleration_magnitude - 9.80665
        )

        high_motion = (
            dynamic_acceleration >= self.acceleration_threshold
            or gyroscope_magnitude >= self.gyroscope_threshold
        )

        if high_motion:
            self.motion_count += 1
        else:
            self.motion_count = 0

        if self.motion_count < self.consecutive_samples:
            return None

        timestamp = float(message["timestamp"])

        if self.last_event_time is not None:
            if timestamp - self.last_event_time < self.cooldown_s:
                return None

        self.last_event_time = timestamp

        return {
            "timestamp": timestamp,
            "event_type": "candidate_high_motion",
            "acceleration_magnitude": float(acceleration_magnitude),
            "gyroscope_magnitude": float(gyroscope_magnitude),
            "grip": float(message["grip"])
        }


if __name__ == "__main__":
    print("Candidate Event Detector loaded successfully.")
