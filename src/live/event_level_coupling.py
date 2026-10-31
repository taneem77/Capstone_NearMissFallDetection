
"""
RQ3: Event-level temporal coupling analysis.

Calculates:
- Acceleration onset
- Gyroscope onset
- Grip response onset
- Grip response onset lag
- Acceleration and grip peak times
- Peak-time lag
- Event duration

Uses manually annotated event boundaries and a pre-event
baseline to calculate signal deviations.
"""

import argparse
import numpy as np
import pandas as pd

# Support both direct script execution and package imports.
try:
    from .coupling import load_recording
except ImportError:
    from coupling import load_recording


def find_onset(time, signal, threshold):
    """Find the first time the signal crosses its threshold."""

    indices = np.where(np.abs(signal) >= threshold)[0]

    if len(indices) == 0:
        return np.nan

    return float(time[indices[0]])


def analyse_event(recording, annotation, onset_fraction=0.20):
    """Analyse motion-grip timing within one annotated event."""

    start = float(annotation["event_start_s"])
    end = float(annotation["event_end_s"])

    if start >= end:
        raise ValueError("Event start must be earlier than event end.")

    if not 0 < onset_fraction < 1:
        raise ValueError("onset_fraction must be between 0 and 1.")

    event = recording[
        (recording["timestamp"] >= start)
        & (recording["timestamp"] <= end)
    ].copy()

    if len(event) < 3:
        raise ValueError(
            f"Insufficient samples in event {annotation['event_id']}"
        )

    # Establish baseline using the 0.5 seconds before the event.
    baseline = recording[
        (recording["timestamp"] >= start - 0.5)
        & (recording["timestamp"] < start)
    ]

    if len(baseline) < 3:
        raise ValueError(
            f"Insufficient pre-event baseline for event "
            f"{annotation['event_id']}"
        )

    time = event["timestamp"].to_numpy()

    # Acceleration magnitude and baseline deviation.
    acc = event[
        ["acc_x", "acc_y", "acc_z"]
    ].to_numpy()

    acc_magnitude = np.linalg.norm(acc, axis=1)

    baseline_acc = np.linalg.norm(
        baseline[
            ["acc_x", "acc_y", "acc_z"]
        ].to_numpy(),
        axis=1
    )

    acc_deviation = acc_magnitude - np.median(baseline_acc)

    # Gyroscope magnitude and baseline deviation.
    gyro = event[
        ["gyro_x", "gyro_y", "gyro_z"]
    ].to_numpy()

    gyro_magnitude = np.linalg.norm(gyro, axis=1)

    baseline_gyro = np.linalg.norm(
        baseline[
            ["gyro_x", "gyro_y", "gyro_z"]
        ].to_numpy(),
        axis=1
    )

    gyro_deviation = gyro_magnitude - np.median(baseline_gyro)

    # Grip deviation from pre-event baseline.
    grip_baseline = baseline["grip"].median()

    grip_deviation = (
        event["grip"].to_numpy() - grip_baseline
    )

    # Calculate independent peak deviations.
    acc_peak = np.max(np.abs(acc_deviation))
    gyro_peak = np.max(np.abs(gyro_deviation))
    grip_peak = np.max(np.abs(grip_deviation))

    # Independent onset thresholds.
    acc_onset = (
        find_onset(time, acc_deviation, onset_fraction * acc_peak)
        if acc_peak > 1e-10 else np.nan
    )

    gyro_onset = (
        find_onset(time, gyro_deviation, onset_fraction * gyro_peak)
        if gyro_peak > 1e-10 else np.nan
    )

    grip_onset = (
        find_onset(time, grip_deviation, onset_fraction * grip_peak)
        if grip_peak > 1e-10 else np.nan
    )

    # Grip onset relative to acceleration onset.
    onset_lag = (
        grip_onset - acc_onset
        if np.isfinite(acc_onset) and np.isfinite(grip_onset)
        else np.nan
    )

    # Find peak times independently.
    acc_peak_time = (
        float(time[np.argmax(np.abs(acc_deviation))])
        if acc_peak > 1e-10 else np.nan
    )

    grip_peak_time = (
        float(time[np.argmax(np.abs(grip_deviation))])
        if grip_peak > 1e-10 else np.nan
    )

    peak_lag = (
        grip_peak_time - acc_peak_time
        if np.isfinite(acc_peak_time)
        and np.isfinite(grip_peak_time)
        else np.nan
    )

    return {
        "recording_id": annotation["recording_id"],
        "event_id": annotation["event_id"],
        "event_type": annotation["event_type"],
        "event_start_s": start,
        "event_end_s": end,
        "event_duration_s": end - start,
        "acceleration_onset_s": acc_onset,
        "gyroscope_onset_s": gyro_onset,
        "grip_onset_s": grip_onset,
        "grip_minus_acceleration_onset_s": onset_lag,
        "acceleration_peak_time_s": acc_peak_time,
        "grip_peak_time_s": grip_peak_time,
        "grip_minus_acceleration_peak_s": peak_lag,
        "acceleration_peak_deviation": acc_peak,
        "gyroscope_peak_deviation": gyro_peak,
        "grip_peak_deviation": grip_peak
    }


def analyse_annotations(
    recording_path,
    annotation_path,
    output_path,
    onset_fraction=0.20
):
    """Analyse all manually annotated events in a recording."""

    recording = load_recording(recording_path)
    annotations = pd.read_csv(annotation_path)

    required = [
        "recording_id",
        "event_id",
        "event_type",
        "event_start_s",
        "event_end_s"
    ]

    missing = set(required) - set(annotations.columns)

    if missing:
        raise ValueError(
            f"Missing annotation columns: {sorted(missing)}"
        )

    if annotations.empty:
        raise ValueError("Annotation file contains no events.")

    results = []

    for _, annotation in annotations.iterrows():
        results.append(
            analyse_event(
                recording,
                annotation,
                onset_fraction=onset_fraction
            )
        )

    result_df = pd.DataFrame(results)
    result_df.to_csv(output_path, index=False)

    print("\nEvent-Level RQ3 Analysis")
    print("-----------------------")
    print(result_df.to_string(index=False))
    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Event-level IMU-grip coupling analysis"
    )

    parser.add_argument(
        "recording",
        help="Path to synchronized sensor CSV"
    )

    parser.add_argument(
        "annotations",
        help="Path to manually annotated event CSV"
    )

    parser.add_argument(
        "--output",
        default="logs/event_level_coupling.csv"
    )

    parser.add_argument(
        "--onset-fraction",
        type=float,
        default=0.20,
        help="Fraction of maximum signal deviation used for onset detection"
    )

    args = parser.parse_args()

    analyse_annotations(
        args.recording,
        args.annotations,
        args.output,
        args.onset_fraction
    )


if __name__ == "__main__":
    main()
