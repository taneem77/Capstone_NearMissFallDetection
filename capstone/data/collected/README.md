# Real Data Collection Protocol & Telemetry Contract

This document specifies the safe experimental protocol for recording real walking telemetry using the physical ESP32 Smart Cane, incorporating Reviewer 1's guidance regarding floor surfaces and footwear habits.

---

## 1. Volunteer Safety Protocol (Level-Ground Walking)

To ensure zero risk of injury while gathering real volunteer walking dynamics:
1. **Zero Induced Falls**: Under no circumstances should volunteers be pushed, tripped, or forced into balance disruption during preliminary data gathering.
2. **Supervised Baseline Walking**: Volunteers walk along a marked 20-meter straight corridor at a self-selected comfortable cadence. A spotter walks alongside the volunteer at all times.
3. **Environmental Logging (Reviewer 1)**: Each trial must record:
   - Floor Surface: Smooth Tile, Low-pile Carpet, Rough Concrete, Wooden Parquet.
   - Footwear: Cushioned Sneakers, Hard-soled Loafers, Slippers, Barefoot.
   - Cane Height Adjustment: Set so the top of the handle aligns with the volunteer's greater trochanter (wrist crease) when standing upright.

---

## 2. Ingestion CSV Telemetry Schema

Every recorded CSV session saved to `capstone/data/collected/` adheres to the following strict contract:

```csv
# METADATA: {"session_id": "SESSION_1731320000", "volunteer_id": "VOL_01", "floor_type": "Tiled", "footwear": "Walking Shoes", "activity_target": "normal_walking", "fs_nominal_hz": 100}
timestamp_ms,ax,ay,az,gx,gy,gz,grip_adc
10,0.12,1.45,9.78,0.2,-0.1,0.5,1420
20,0.14,1.48,9.75,0.3,-0.2,0.4,1425
```

### Column Definitions & Physical Units:
* `timestamp_ms` (integer): Millisecond timestamp from ESP32 boot (`millis()`).
* `ax, ay, az` (float): Tri-axial acceleration in $\text{m/s}^2$ ($Z$ along cane shaft, $Y$ forward, $X$ lateral).
* `gx, gy, gz` (float): Tri-axial angular velocity in $\text{deg/s}$.
* `grip_adc` (integer): Raw 12-bit analog-to-digital converter counts ($0 - 4095$) from GPIO 34.

---

## 3. Volunteer Informed Consent Template

```
VOLUNTEER INFORMED CONSENT FORM
Project: Smart Cane for Near-Fall Detection (PES University Capstone)
Investigators: Tanisha Mathur, Samika Ojha, Saatvik Gupta, Pratham S Reddy
Guide: Dr. Mamatha H R, Department of CSE

I hereby volunteer to participate in walking trials using an instrumented walking cane.
1. I understand I will walk at a normal, comfortable pace on level ground.
2. No hazardous obstacles or balance disturbances will be induced.
3. All telemetry data recorded is strictly anonymized and devoid of personally identifiable information.
4. I understand participation is voluntary and I may stop at any moment.

Volunteer Name: _______________________ Date: ___________________
Signature:      _______________________
```
