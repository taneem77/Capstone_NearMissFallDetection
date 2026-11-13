# Real Data Collection Protocol & Ethical Governance (ESA Specification)

This protocol outlines the strict experimental procedures, volunteer safety constraints, informed consent template, and data dictionary for collecting physical hardware telemetry.

---

## 1. Volunteer Safety Protocol (Level-Ground Walking Only)

1. **Safety First: Zero Induced Falls**:
   - In accordance with medical ethics guidelines (ICMR Ethical Guidelines / Declaration of Helsinki), **under no circumstances may elderly, frail, or student volunteers be subjected to induced physical perturbations, tripping wires, or destabilizing pushes**.
   - Physical hardware trials are strictly restricted to **supervised, level-ground steady walking** and intentional, controlled voluntary cane placement.
2. **Supervision & Environment**:
   - All walking sessions take place on marked, obstacle-free corridors with an attendant walking alongside the volunteer.
   - Cane height is adjusted to align with the volunteer's greater trochanter (wrist crease while arms hang naturally).
3. **Session Parameter Logging (Reviewer 1 Feedback)**:
   Every session recorded must note the environmental parameters:
   - Floor Surface: Smooth Ceramic Tile, Dense Low-Pile Carpet, Polished Hardwood, or Exterior Concrete.
   - Footwear: Cushioned Athletic Shoes, Hard-soled Loafers, Slippers, or Barefoot.

---

## 2. Telemetry Data Dictionary

The data dictionary strictly governs the output of `capstone/hardware_esa/SmartCane_Firmware_ESA.ino` and `capstone/data_esa/loader.py`:

| Column Name | Data Type | Physical Units | Valid Range | Physical Meaning & Coordinate Frame |
| :--- | :---: | :---: | :---: | :--- |
| `time_ms` | Integer | Milliseconds ($ms$) | $\ge 0$ | Monotonic clock from ESP32 boot (`millis()`). |
| `ax` | Float | $\text{m/s}^2$ | $[-39.2, +39.2]$ | Acceleration along $X$-axis (Lateral, coronal plane). |
| `ay` | Float | $\text{m/s}^2$ | $[-39.2, +39.2]$ | Acceleration along $Y$-axis (Forward walking progression). |
| `az` | Float | $\text{m/s}^2$ | $[-39.2, +39.2]$ | Acceleration along $Z$-axis (Longitudinal down cane shaft). |
| `gx` | Float | $\text{deg/s}$ | $[-500.0, +500.0]$ | Angular velocity around $X$-axis (Pitch). |
| `gy` | Float | $\text{deg/s}$ | $[-500.0, +500.0]$ | Angular velocity around $Y$-axis (Roll). |
| `gz` | Float | $\text{deg/s}$ | $[-500.0, +500.0]$ | Angular velocity around $Z$-axis (Yaw). |
| `grip_adc` | Integer | Raw Counts | $[0, 4095]$ | 12-bit ADC count from FSR 402 handle voltage divider on GPIO 34. |

---

## 3. Volunteer Informed Consent Template

```
PES UNIVERSITY | DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
CAPSTONE PROJECT PHASE-1: SMART CANE EVALUATION (PW_27_MHR_01)

VOLUNTEER INFORMED CONSENT & PARTICIPATION FORM

Project Title: Smart Cane for Near-Fall Detection Using Cane Kinematics & Grip Dynamics
Student Investigators: Tanisha Mathur, Samika Ojha, Saatvik Gupta, Pratham S Reddy
Faculty Guide: Dr. Mamatha H R, Professor, Department of CSE

Purpose of Study:
You are invited to participate in a gait measurement trial using an instrumented walking cane
equipped with low-voltage (3.3V) inertial and palm pressure sensors.

Participant Rights & Safety Protocol:
1. You will be asked to walk at a self-selected comfortable speed across a level corridor.
2. NO physical stumbles, trips, or balance perturbations will be induced.
3. Participation is completely voluntary; you may withdraw at any time without penalty.
4. All sensor telemetry is strictly anonymized with random alphanumeric identifiers (e.g., VOL_01)
   and contains no video, biometric imagery, or personal identifying information.

Consent Declaration:
I have read and understood the procedures outlined above. I agree to participate voluntarily.

Participant Name: ____________________________________ Date: ____________________
Signature:        ____________________________________
```
