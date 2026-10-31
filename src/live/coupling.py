"""
RQ3: Temporal coupling between cane movement and handle-grip pressure.

Expected CSV columns:
timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, grip

Timestamps are in seconds.
Acceleration is in m/s^2.
Gyroscope is in deg/s.
Grip is a raw or calibrated sensor value.
"""

import argparse
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "acc_x", "acc_y", "acc_z",
    "gyro_x", "gyro_y", "gyro_z",
    "grip"
]


def load_recording(path):
    """Load and validate synchronized sensor data."""
    df = pd.read_csv(path)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")

    df = df[REQUIRED_COLUMNS].copy()

    for column in REQUIRED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna().sort_values("timestamp")
    df = df.drop_duplicates(subset="timestamp")

    if len(df) < 10:
        raise ValueError("Not enough valid samples.")

    if not np.all(np.diff(df["timestamp"]) > 0):
        raise ValueError("Timestamps must be strictly increasing.")

    return df.reset_index(drop=True)


def calculate_signals(df):
    """Calculate motion magnitudes and grip change."""
    result = df.copy()

    acc = result[["acc_x", "acc_y", "acc_z"]].to_numpy()
    gyro = result[["gyro_x", "gyro_y", "gyro_z"]].to_numpy()

    result["acc_magnitude"] = np.linalg.norm(acc, axis=1)
    result["gyro_magnitude"] = np.linalg.norm(gyro, axis=1)

    # Remove the static acceleration component approximately.
    result["acc_dynamic"] = (
        result["acc_magnitude"]
        - result["acc_magnitude"].median()
    )

    # Grip change relative to the recording's median baseline.
    result["grip_change"] = (
        result["grip"] - result["grip"].median()
    )

    return result


def peak_time_lag(df):
    """
    Compare the largest motion and grip-change peaks.

    Positive lag means the grip peak occurs after the motion peak.
    This is a descriptive measurement, not proof of causation.
    """
    motion_index = df["acc_dynamic"].abs().idxmax()
    grip_index = df["grip_change"].abs().idxmax()

    motion_time = df.loc[motion_index, "timestamp"]
    grip_time = df.loc[grip_index, "timestamp"]

    return {
        "motion_peak_time_s": float(motion_time),
        "grip_peak_time_s": float(grip_time),
        "grip_minus_motion_lag_s": float(grip_time - motion_time)
    }


def cross_correlation_lag(df, max_lag_s=1.0):
    """
    Estimate the lag with maximum normalized cross-correlation.

    Positive lag means grip changes tend to follow motion changes.
    Signals are standardized before correlation.
    """
    motion = df["acc_dynamic"].to_numpy(dtype=float)
    grip = df["grip_change"].to_numpy(dtype=float)

    motion_std = motion.std()
    grip_std = grip.std()

    if motion_std < 1e-10 or grip_std < 1e-10:
        return {
            "correlation": float("nan"),
            "lag_s": float("nan")
        }

    motion = (motion - motion.mean()) / motion_std
    grip = (grip - grip.mean()) / grip_std

    dt = float(np.median(np.diff(df["timestamp"])))
    max_lag = max(1, int(round(max_lag_s / dt)))

    correlations = []
    lags = range(-max_lag, max_lag + 1)

    for lag in lags:
        if lag > 0:
            x, y = motion[:-lag], grip[lag:]
        elif lag < 0:
            x, y = motion[-lag:], grip[:lag]
        else:
            x, y = motion, grip

        if len(x) < 3:
            correlations.append(np.nan)
        else:
            correlations.append(float(np.mean(x * y)))

    correlations = np.asarray(correlations)

    if not np.isfinite(correlations).any():
        return {
            "correlation": float("nan"),
            "lag_s": float("nan")
        }

    best = int(np.nanargmax(correlations))
    best_lag = list(lags)[best]

    return {
        "correlation": float(correlations[best]),
        "lag_s": float(best_lag * dt)
    }


def analyse_recording(path):
    """Run the RQ3 analysis on one synchronized recording."""
    df = calculate_signals(load_recording(path))

    peak_result = peak_time_lag(df)
    correlation_result = cross_correlation_lag(df)

    return {
        "samples": len(df),
        "duration_s": float(
            df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]
        ),
        **peak_result,
        "cross_correlation": correlation_result["correlation"],
        "cross_correlation_lag_s": correlation_result["lag_s"]
    }


def main():
    parser = argparse.ArgumentParser(
        description="RQ3 IMU-grip temporal coupling analysis"
    )
    parser.add_argument("csv", help="Path to synchronized sensor CSV")
    parser.add_argument("--output", default="coupling_results.csv")

    args = parser.parse_args()

    result = analyse_recording(args.csv)

    pd.DataFrame([result]).to_csv(args.output, index=False)

    print("\nRQ3 Coupling Analysis")
    print("---------------------")

    for key, value in result.items():
        print(f"{key}: {value}")

    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()