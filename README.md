## Summary
Implemented the live software components for the Smart Cane Near-Miss Detection project, with a focus on RQ3 temporal coupling analysis.

## Deliverables
- Python serial logger for ESP32 sensor data.
- JSON-based sensor data logging and validation.
- Event logging and weekly event trend visualization.
- Candidate high-motion event detection.
- Integrated live processing pipeline.
- Recording-level IMU–grip force coupling analysis.
- Event-level temporal coupling analysis.
- Synthetic data generators and automated unit tests.

## Testing
- 20 automated tests passed.
- Serial logger tested using simulated serial input.
- Coupling analysis tested using synthetic sensor recordings.
- Integrated pipeline tested using simulated sensor messages.

## Pending
- ESP32 firmware and physical sensor integration.
- Validation using actual IMU and grip-force recordings.
- Further calibration and evaluation of event detection thresholds.

**Note:** Synthetic data was used for software testing and does not represent real experimental results.
