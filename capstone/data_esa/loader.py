"""
Unified Telemetry Data Loader for Smart Cane Evaluation.
Transparently loads both SIMULATED benchmark datasets and REAL physical hardware recordings.
Extracts metadata headers, enforces standard schema, validates monotonic timestamps,
and flags data provenance to prevent mixing.
"""
import os
import json
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ['time_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'grip_adc']

def load_cane_dataset(filepath):
    """
    Loads a Smart Cane CSV file (real or simulated).
    
    Returns:
        tuple: (df, metadata_dict)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Telemetry file not found: {filepath}")
        
    metadata = {
        "dataset_type": "UNKNOWN",
        "filepath": filepath
    }
    
    # Read comment / metadata lines if present
    header_lines = 0
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("#"):
                header_lines += 1
                if "DATASET_METADATA:" in line_str:
                    try:
                        json_str = line_str.split("DATASET_METADATA:", 1)[1].strip()
                        metadata.update(json.loads(json_str))
                    except Exception:
                        pass
                elif "DATASET_TYPE:" in line_str:
                    metadata["dataset_type"] = line_str.split("DATASET_TYPE:", 1)[1].strip()
            else:
                break
                
    # Read tabular data
    df = pd.read_csv(filepath, skiprows=header_lines)
    
    # Standardize column mappings if needed
    col_map = {
        'timestamp': 'time_ms',
        'timestamp_ms': 'time_ms',
        'acc_x': 'ax', 'acc_y': 'ay', 'acc_z': 'az',
        'gyro_x': 'gx', 'gyro_y': 'gy', 'gyro_z': 'gz',
        'grip': 'grip_adc'
    }
    df = df.rename(columns=col_map)
    
    # Check for required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        # If gyros are missing, fill with 0.0
        for m in missing:
            if m.startswith('g') and m != 'grip_adc':
                df[m] = 0.0
            else:
                raise ValueError(f"File {filepath} is missing required column: {m}")
                
    # Verify timestamp monotonicity
    t = df['time_ms'].values
    if len(t) > 1 and not np.all(np.diff(t) > 0):
        # Monotonize if small jitter
        df['time_ms'] = np.maximum.accumulate(t)
        metadata["monotonicity_corrected"] = True
    else:
        metadata["monotonicity_corrected"] = False

    # Mark provenance in metadata if not yet set
    if "is_simulated" in metadata:
        metadata["dataset_type"] = "SIMULATED" if metadata["is_simulated"] else "REAL_VOLUNTEER"
    elif "dataset_type" not in metadata or metadata["dataset_type"] == "UNKNOWN":
        # Heuristic: check if path contains 'sample' or 'simulated'
        if any(w in filepath.lower() for w in ['sample', 'simulated', 'benchmark']):
            metadata["dataset_type"] = "SIMULATED"
        else:
            metadata["dataset_type"] = "REAL_VOLUNTEER"

    return df, metadata
