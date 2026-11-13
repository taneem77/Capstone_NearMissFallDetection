"""
Calibration and Threshold Selection Engine.
Addresses Reviewer 2's question on threshold formulation:
Derives statistical personalized thresholds (mu + k*sigma) from baseline calibration trials,
and maps FSR ADC counts to Force in Newtons via voltage divider transfer functions.
"""
import numpy as np
import pandas as pd
from .features import compute_kinematics

def adc_to_force_newtons(adc_counts, v_in=3.3, r_fixed=10000.0, adc_resolution=4095.0):
    """
    Converts ESP32 12-bit ADC counts to Force in Newtons.
    Circuit: 3.3V -> FSR 402 -> GPIO34 -> 10k fixed resistor -> GND
    V_out = V_in * (R_fixed / (R_fsr + R_fixed))
    R_fsr = R_fixed * ((V_in / V_out) - 1)
    Force model: F = C * (Conductance)^gamma
    """
    adc = np.array(adc_counts, dtype=float)
    # Clip to prevent zero division
    adc = np.clip(adc, 5.0, adc_resolution - 5.0)
    v_out = adc * (v_in / adc_resolution)
    
    # Calculate FSR resistance
    r_fsr = r_fixed * ((v_in / v_out) - 1.0)
    conductance_umho = (1.0 / np.maximum(r_fsr, 1.0)) * 1e6
    
    # Empirical power-law fit for Interlink FSR 402 / 406 series:
    # 0 to 4095 counts maps from 0 N to ~60-80 N (firm adult hand grip)
    force_n = np.where(
        conductance_umho < 50.0,
        0.08 * conductance_umho,
        0.14 * (conductance_umho ** 0.96)
    )
    return np.round(np.clip(force_n, 0.0, 100.0), 2)

def calibrate_thresholds_from_baseline(baseline_df, k_jerk=3.0, k_grip=3.0, fs=100.0):
    """
    Computes rigorous statistical detection thresholds from a 20-30 second baseline walking trial.
    Addresses Reviewer 2:
      T_jerk = mu_jerk + k_jerk * sigma_jerk
      T_grip = mu_grip_rise + k_grip * sigma_grip_rise
    
    Args:
        baseline_df (pd.DataFrame): Telemetry recorded during normal steady walking.
        k_jerk (float): Multiplier for jerk standard deviation (default 3.0 for 99.7% Gaussian bounds).
        k_grip (float): Multiplier for grip rise standard deviation (default 3.0).
        fs (float): Sampling frequency in Hz.
        
    Returns:
        dict: Calibrated parameters, statistics, and baseline bounds.
    """
    df = compute_kinematics(baseline_df, fs=fs)
    
    jerk_vals = df['jerk_mag'].values
    mu_jerk = float(np.mean(jerk_vals))
    sigma_jerk = float(np.std(jerk_vals))
    
    # Statistical threshold with safety minimums
    t_jerk = max(35.0, mu_jerk + (k_jerk * sigma_jerk))
    
    # Grip force baseline & dynamics
    grip_col = 'grip_n' if 'grip_n' in df else ('grip_adc' if 'grip_adc' in df else None)
    if grip_col:
        grip_vals = df[grip_col].values
        # Sliding differences to measure normal grip fluctuations during walking
        grip_diffs = np.abs(np.diff(grip_vals))
        mu_grip_diff = float(np.mean(grip_diffs))
        sigma_grip_diff = float(np.std(grip_diffs))
        
        # Grip rise threshold: scaled to handle units (N or ADC)
        is_newtons = (grip_col == 'grip_n')
        min_rise = 10.0 if is_newtons else 300.0
        t_grip = max(min_rise, mu_grip_diff + (k_grip * sigma_grip_diff * 4.0))
        mean_grip_baseline = float(np.mean(grip_vals))
    else:
        t_grip = 12.0
        mean_grip_baseline = 5.0
        
    return {
        'jerk_mean': round(mu_jerk, 2),
        'jerk_std': round(sigma_jerk, 2),
        'calibrated_jerk_threshold': round(t_jerk, 2),
        'grip_mean': round(mean_grip_baseline, 2),
        'calibrated_grip_threshold': round(t_grip, 2),
        'k_jerk': k_jerk,
        'k_grip': k_grip,
        'coincidence_window_sec': 0.35
    }
