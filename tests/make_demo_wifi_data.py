
import json
import math

output_file = "logs/demo_wifi_data.jsonl"

with open(output_file, "w", encoding="utf-8") as file:

    for i in range(1000):

        timestamp = i / 100

        # Normal background movement.
        acc_x = 0.2 * math.sin(timestamp)
        acc_y = 0.1 * math.cos(timestamp)
        acc_z = 9.80665

        gyro_x = 0.5 * math.sin(timestamp)
        gyro_y = 0.3 * math.cos(timestamp)
        gyro_z = 0.1

        grip = 120 + 10 * math.sin(timestamp)

        # Simulated high-motion interval from 4 to 4.5 seconds.
        if 4.0 <= timestamp <= 4.5:
            acc_x += 5.0 * math.sin(20 * timestamp)
            gyro_x += 120.0 * math.sin(20 * timestamp)

            # Simulated grip response after the motion begins.
            if timestamp >= 4.2:
                grip += 35.0

        message = {
            "timestamp": timestamp,
            "acc_x": acc_x,
            "acc_y": acc_y,
            "acc_z": acc_z,
            "gyro_x": gyro_x,
            "gyro_y": gyro_y,
            "gyro_z": gyro_z,
            "grip": grip
        }

        file.write(json.dumps(message) + "\n")

print("Generated 1000 simulated sensor messages.")
print("Includes a high-motion interval from 4.0 to 4.5 seconds.")
