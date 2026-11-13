"""
ESA Dedicated Telemetry Logger & Real-Time Serial Stream Ingestor.
Receives standard CSV formatted stream from ESP32:
time_ms,ax,ay,az,gx,gy,gz,grip_adc
Supports volunteer metadata logging and automatic simulation fallback for viva presentations.
"""
import os
import sys
import time
import json
import pandas as pd
import numpy as np

try:
    import serial
except ImportError:
    serial = None

CSV_HEADER = "time_ms,ax,ay,az,gx,gy,gz,grip_adc"

def parse_csv_telemetry_line(line_str):
    """
    Parses a single line of CSV telemetry: time_ms,ax,ay,az,gx,gy,gz,grip_adc.
    """
    line_str = line_str.strip()
    if not line_str or line_str.startswith("time_ms") or line_str.startswith("#"):
        return None
        
    parts = line_str.split(',')
    if len(parts) >= 8:
        try:
            return {
                'time_ms': int(float(parts[0])),
                'ax': float(parts[1]),
                'ay': float(parts[2]),
                'az': float(parts[3]),
                'gx': float(parts[4]),
                'gy': float(parts[5]),
                'gz': float(parts[6]),
                'grip_adc': int(float(parts[7]))
            }
        except (ValueError, IndexError):
            return None
    return None

class ESASerialLogger:
    """
    Manages session recording with clinical trial metadata headers.
    """
    def __init__(self, output_dir="capstone/data_esa"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.samples = []
        self.metadata = {}

    def start_recording(self, session_id="SESSION_01", volunteer_id="VOL_01", floor="Tiled", footwear="Shoes", is_simulated=False):
        self.metadata = {
            "session_id": session_id,
            "volunteer_id": volunteer_id,
            "floor_type": floor,
            "footwear": footwear,
            "is_simulated": is_simulated,
            "timestamp_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "columns": CSV_HEADER.split(',')
        }
        self.samples = []

    def add_sample(self, sample_dict):
        if sample_dict and all(k in sample_dict for k in ['time_ms', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'grip_adc']):
            self.samples.append(sample_dict)

    def save_to_csv(self, filename=None):
        if not self.samples:
            return None
        if not filename:
            tag = "SIMULATED" if self.metadata.get("is_simulated") else "REAL"
            filename = f"{self.metadata.get('volunteer_id','VOL')}_{tag}_{int(time.time())}.csv"
            
        filepath = os.path.join(self.output_dir, filename)
        df = pd.DataFrame(self.samples)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# DATASET_METADATA: {json.dumps(self.metadata)}\n")
            df.to_csv(f, index=False)
            
        return filepath

def read_telemetry_stream(port="COM3", baudrate=115200, max_samples=100, fallback_simulation=True):
    """
    Yields parsed telemetry samples in real-time. If physical serial is disconnected,
    yields realistic simulated packets so demos and automated pipelines never freeze.
    """
    if serial is not None:
        try:
            ser = serial.Serial(port, baudrate, timeout=0.1)
            count = 0
            while count < max_samples:
                line = ser.readline().decode('utf-8', errors='ignore')
                sample = parse_csv_telemetry_line(line)
                if sample:
                    yield sample
                    count += 1
            ser.close()
            return
        except Exception:
            pass # Fall through to fallback simulation

    if fallback_simulation:
        t_now = int(time.time() * 1000)
        for i in range(max_samples):
            # Normal walking with occasional stumble
            t_ms = t_now + (i * 10)
            phase = 2 * np.pi * 1.0 * (i * 0.01)
            ax = float(0.8 * np.sin(phase) + np.random.normal(0, 0.1))
            ay = float(1.5 + 1.2 * np.cos(phase) + np.random.normal(0, 0.1))
            az = float(9.6 + 0.9 * np.sin(2 * phase) + np.random.normal(0, 0.1))
            gx = float(np.random.normal(0, 1.0))
            gy = float(np.random.normal(0, 1.0))
            gz = float(np.random.normal(0, 1.0))
            grip_adc = int(750 + 120 * np.sin(phase) + np.random.normal(0, 15))
            
            # Inject trip anomaly at sample 50
            if 48 <= i <= 58:
                ay += 12.0
                az -= 6.0
                if i >= 52:
                    grip_adc += 1400 # reflex clench ~120 ms later
                    
            yield {
                'time_ms': t_ms,
                'ax': round(ax, 3),
                'ay': round(ay, 3),
                'az': round(az, 3),
                'gx': round(gx, 2),
                'gy': round(gy, 2),
                'gz': round(gz, 2),
                'grip_adc': int(np.clip(grip_adc, 100, 4095))
            }
            time.sleep(0.01) # 100 Hz simulation pace
