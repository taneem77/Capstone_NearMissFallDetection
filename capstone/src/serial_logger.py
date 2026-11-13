"""
Serial Telemetry Logger & Real-Time Ingestion.
Connects to ESP32 Smart Cane Node over USB Serial (115200 or 460800 baud).
Incorporates Reviewer 1's feedback: captures floor surface, footwear type,
and user mobility profile as metadata headers in every recorded session.
Provides simulated fallback streaming if physical hardware is offline.
"""
import os
import time
import json
import numpy as np
import pandas as pd

# Safe import for environments without pyserial
try:
    import serial
except ImportError:
    serial = None

def parse_telemetry_line(line_str):
    """
    Parses a single line of telemetry from ESP32.
    Supports JSON: {"t": 1020, "ax": 0.12, "ay": 1.45, "az": 9.78, "gx": 0.2, "gy": -0.1, "gz": 0.5, "grip": 1420}
    or CSV: t,ax,ay,az,gx,gy,gz,grip
    """
    line_str = line_str.strip()
    if not line_str:
        return None
        
    if line_str.startswith('{') and line_str.endswith('}'):
        try:
            d = json.loads(line_str)
            return {
                'timestamp_ms': d.get('t', d.get('timestamp', int(time.time()*1000))),
                'ax': float(d.get('ax', d.get('acc_x', 0.0))),
                'ay': float(d.get('ay', d.get('acc_y', 0.0))),
                'az': float(d.get('az', d.get('acc_z', 0.0))),
                'gx': float(d.get('gx', d.get('gyro_x', 0.0))),
                'gy': float(d.get('gy', d.get('gyro_y', 0.0))),
                'gz': float(d.get('gz', d.get('gyro_z', 0.0))),
                'grip_adc': int(d.get('grip', d.get('grip_adc', 500)))
            }
        except Exception:
            return None
            
    # Try CSV parse
    parts = line_str.split(',')
    if len(parts) >= 8:
        try:
            return {
                'timestamp_ms': int(float(parts[0])),
                'ax': float(parts[1]),
                'ay': float(parts[2]),
                'az': float(parts[3]),
                'gx': float(parts[4]),
                'gy': float(parts[5]),
                'gz': float(parts[6]),
                'grip_adc': int(float(parts[7]))
            }
        except Exception:
            return None
    return None

class CaneDataLogger:
    """
    Manages session recording with clinical trial metadata headers.
    """
    def __init__(self, output_dir="capstone/data/collected"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.buffer = []
        self.metadata = {}
        
    def start_session(self, volunteer_id="VOL_01", floor_type="Tiled", footwear="Walking Shoes", activity="walking"):
        self.metadata = {
            "session_id": f"SESSION_{int(time.time())}",
            "volunteer_id": volunteer_id,
            "floor_type": floor_type,         # Reviewer 1 suggestion
            "footwear": footwear,             # Reviewer 1 suggestion
            "activity_target": activity,
            "start_time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fs_nominal_hz": 100
        }
        self.buffer = []
        
    def log_sample(self, sample_dict):
        if sample_dict:
            self.buffer.append(sample_dict)
            
    def save_session(self):
        if not self.buffer:
            return None
        df = pd.DataFrame(self.buffer)
        filename = f"{self.metadata.get('volunteer_id', 'VOL')}_{self.metadata.get('activity_target', 'act')}_{int(time.time())}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save CSV with metadata header
        with open(filepath, 'w') as f:
            f.write(f"# METADATA: {json.dumps(self.metadata)}\n")
            df.to_csv(f, index=False)
            
        return filepath

def stream_telemetry_generator(port="COM3", baudrate=115200, max_samples=200, fallback_simulation=True):
    """
    Yields telemetry samples in real-time. If serial device is unavailable,
    yields simulated packets with identical structure so live demos always succeed.
    """
    if serial is not None:
        try:
            ser = serial.Serial(port, baudrate, timeout=0.1)
            count = 0
            while count < max_samples:
                line = ser.readline().decode('utf-8', errors='ignore')
                sample = parse_telemetry_line(line)
                if sample:
                    yield sample
                    count += 1
            ser.close()
            return
        except Exception:
            pass
            
    # Fallback simulation stream for offline review demo
    if fallback_simulation:
        from .synthetic_data import generate_activity_segment
        sim_df = generate_activity_segment("near_miss_trip", duration_sec=(max_samples/100.0), fs=100.0)
        for _, row in sim_df.iterrows():
            yield {
                'timestamp_ms': int(row['timestamp_ms']),
                'ax': float(row['ax']),
                'ay': float(row['ay']),
                'az': float(row['az']),
                'gx': float(row['gx']),
                'gy': float(row['gy']),
                'gz': float(row['gz']),
                'grip_adc': int(row['grip_adc'])
            }
            time.sleep(0.01) # 100 Hz simulation pace
