import numpy as np
import pandas as pd

fs = 100
duration = 10

t = np.arange(0, duration, 1 / fs)

# Synthetic motion disturbance around 4 seconds
motion = np.exp(-((t - 4.0) / 0.15) ** 2)

# Grip response occurs 0.2 seconds later
grip = 0.5 * np.exp(-((t - 4.2) / 0.15) ** 2)

rng = np.random.default_rng(42)

df = pd.DataFrame({
    "timestamp": t,
    "acc_x": motion + rng.normal(0, 0.02, len(t)),
    "acc_y": rng.normal(0, 0.02, len(t)),
    "acc_z": 9.80665 + rng.normal(0, 0.02, len(t)),
    "gyro_x": motion * 10 + rng.normal(0, 0.1, len(t)),
    "gyro_y": rng.normal(0, 0.1, len(t)),
    "gyro_z": rng.normal(0, 0.1, len(t)),
    "grip": 1.0 + grip + rng.normal(0, 0.01, len(t))
})

df.to_csv("logs/demo_sensor_data.csv", index=False)

print("Demo sensor recording generated.")