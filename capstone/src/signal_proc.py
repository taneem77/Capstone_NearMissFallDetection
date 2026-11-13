"""
Signal Processing Module for Smart Cane Telemetry.
Handles low-pass filtering, moving average smoothing, and timestamp/sampling integrity validation.
"""
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

def butter_lowpass_filter(data, cutoff=5.0, fs=100.0, order=4):
    """
    Applies a zero-phase forward-backward Butterworth low-pass filter.
    
    Args:
        data (np.ndarray): 1D array of signal values.
        cutoff (float): Cutoff frequency in Hz (typical gait/kinematic cutoff: 3-8 Hz).
        fs (float): Sampling frequency in Hz.
        order (int): Filter order.
        
    Returns:
        np.ndarray: Filtered signal.
    """
    if len(data) <= order * 3:
        # Fallback to moving average if data is too short for IIR filter initialization
        return moving_average_filter(data, window_size=max(1, len(data) // 3))
    
    nyquist = 0.5 * fs
    normal_cutoff = min(cutoff / nyquist, 0.99)
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered = filtfilt(b, a, data)
    return filtered

def moving_average_filter(data, window_size=5):
    """
    Simple moving average smoothing filter.
    """
    if len(data) == 0:
        return np.array([])
    window_size = min(window_size, len(data))
    if window_size <= 1:
        return np.copy(data)
    kernel = np.ones(window_size) / window_size
    return np.convolve(data, kernel, mode='same')

def validate_stream_integrity(timestamps_ms, expected_fs=100.0, max_jitter_pct=0.25):
    """
    Validates stream timestamps for monotonicity, dropped packets, and frequency deviation.
    
    Args:
        timestamps_ms (np.ndarray or list): Monotonic timestamp values in milliseconds.
        expected_fs (float): Expected sampling frequency (Hz).
        max_jitter_pct (float): Maximum tolerable jitter fraction.
        
    Returns:
        dict: Integrity diagnostics containing:
            - is_monotonic (bool)
            - dropped_packet_count (int)
            - estimated_fs (float)
            - mean_dt_ms (float)
            - std_dt_ms (float)
            - healthy (bool)
    """
    ts = np.array(timestamps_ms, dtype=float)
    if len(ts) < 2:
        return {
            "is_monotonic": True,
            "dropped_packet_count": 0,
            "estimated_fs": expected_fs,
            "mean_dt_ms": 1000.0 / expected_fs,
            "std_dt_ms": 0.0,
            "healthy": True
        }
    
    dt = np.diff(ts)
    is_monotonic = bool(np.all(dt > 0))
    expected_dt_ms = 1000.0 / expected_fs
    
    # Dropped packet if dt > 1.8 * expected_dt_ms
    dropped = int(np.sum(dt > (1.8 * expected_dt_ms)))
    mean_dt = float(np.mean(dt))
    std_dt = float(np.std(dt))
    estimated_fs = float(1000.0 / mean_dt) if mean_dt > 0 else 0.0
    
    # Healthy if monotonic and frequency deviation is within jitter limits
    freq_err = abs(estimated_fs - expected_fs) / expected_fs if expected_fs > 0 else 1.0
    healthy = is_monotonic and (freq_err <= max_jitter_pct) and (dropped <= max(1, int(0.02 * len(ts))))
    
    return {
        "is_monotonic": is_monotonic,
        "dropped_packet_count": dropped,
        "estimated_fs": round(estimated_fs, 2),
        "mean_dt_ms": round(mean_dt, 3),
        "std_dt_ms": round(std_dt, 3),
        "healthy": healthy
    }
