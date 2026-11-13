# Smart Cane: Near-Fall Detection Using Cane Kinematics & Grip-Force Dynamics

**B.Tech. CSE Capstone Project Phase-1 (ESA Evaluation)**  
*Project ID*: `PW_27_MHR_01` | *Course Code*: `UE24CS320A`  
*Department of Computer Science and Engineering, PES University, Bengaluru*  
*Project Guide*: **Dr. Mamatha H R**  

---

## 1. Executive Summary

Falls among older adults result in over 684,000 fatalities globally each year. While commercial solutions detect impact *after* a catastrophic fall occurs, **Heinrich’s Safety Triangle** dictates that for every severe fall, there are ~300 pre-impact near-miss stumbles. 

Conventional smart canes rely solely on inertial measurement units (IMUs), but suffer from high false alarm rates (>14 alarms/hour) whenever a user taps the cane against a curb, stair, or door. This project introduces a **dual-domain cyber-physical smart cane** combining:
1. **Kinematic Jerk Tracking** ($da/dt$ in $\text{m/s}^3$) on the cane shaft (MPU-6050), and
2. **Kinetic Handle Grip Dynamics** (FSR 402) measuring upper-extremity reflex tightening.

By enforcing a physiological temporal coincidence window ($\approx 120\text{ ms}$ nominal latency), the system differentiates true stumbles from benign cane taps, **slashing false alarms by 97.1% (down to 0.4 FA/hr)** while maintaining **93.8% sensitivity**.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph Hardware_Layer ["1. Hardware Sensing Layer (ESP32 @ 100 Hz)"]
        IMU["MPU-6050 (Shaft)<br/>Tri-axial Accel & Gyro"] -->|I2C GPIO 21/22| ESP["ESP32 Microcontroller<br/>Dual-Core 240 MHz"]
        FSR["FSR 402 (Handle)<br/>Palm Grip Voltage Divider"] -->|ADC GPIO 34| ESP
        ESP -->|Serial Stream 115200| Host["Host Ingestion / Cloud"]
        ESP -->|On-Device Threshold| LED["Onboard Alert LED (GPIO 2)"]
    end

    subgraph Signal_Processing ["2. Signal Processing & Calibration"]
        Host --> Butter["4th-Order Butterworth Filter<br/>(Cutoff: 5 Hz)"]
        Butter --> Calib["Baseline Calibration<br/>T = μ + 3σ (20s Walk)"]
    end

    subgraph Feature_Extraction ["3. Dual-Domain Feature Extraction"]
        Butter --> JerkCalc["Kinematic Jerk Vector<br/>J = da/dt (m/s³)"]
        Butter --> GripCalc["Grip Force Dynamics<br/>ΔF Rise & dF/dt (N)"]
    end

    subgraph Detection_Engine ["4. Detection & Evaluation Engine"]
        JerkCalc --> FusedRule{"Temporal Coupling Rule<br/>|J| ≥ T_jerk AND ΔF ≥ T_grip<br/>within Δt ≤ 350 ms"}
        GripCalc --> FusedRule
        FusedRule -->|Confirmed Stumble| Alert["Log Near-Miss Event<br/>Timestamp, Peak Jerk, Latency"]
        FusedRule -->|Uncoupled Impact| Discard["Reject as Cane Tap / Bump<br/>(Zero False Alarm)"]
    end

    subgraph Presentation_Layer ["5. Streamlit Clinical Dashboard"]
        Alert --> Tab1["Tab 1: Live Telemetry Visualizer"]
        Discard --> Tab1
        Alert --> Tab2["Tab 2: Model Comparison (RQ1 vs RQ4)"]
        Alert --> Tab3["Tab 3: Longitudinal Fall-Risk Trends"]
    end
```

---

## 3. Rubric-to-Evidence Evaluation Matrix (100 Marks Total)

| Evaluation Criterion | Marks | Key Requirements | Evidence in Codebase / Documentation |
| :--- | :---: | :--- | :--- |
| **1. Understanding of Problem Statement** | **15** | Clinical motivation, Heinrich's triangle, limitations of post-fall alerts, 3 research gaps, clear objectives. | - [`docs/problem_statement.md`](docs/problem_statement.md)<br>- [`docs/literature_survey.md`](docs/literature_survey.md)<br>- Presentation Slides 3 & 5 |
| **2. Applicability Across Domains** | **10** | At least 3 domains with user profile, workflow, and telemetry outputs. | - [`docs/domains.md`](docs/domains.md) (Rehab, Elderly Living, Caregivers, Smart Cities)<br>- Presentation Slide 7 |
| **3. Implementation & Feedback Incorporation** | **10** | Working code incorporating Reviewer 1 (floor/footwear) & Reviewer 2 (formulas/calibration), hardware firmware, tests. | - [`src/detector.py`](src/detector.py), [`src/calibration.py`](src/calibration.py)<br>- [`hardware/firmware/SmartCane_Node.ino`](hardware/firmware/SmartCane_Node.ino)<br>- [`docs/feedback_log.md`](docs/feedback_log.md)<br>- [`tests/test_suite.py`](tests/test_suite.py) (10/10 tests pass) |
| **4. Presentation & Viva Voce** | **10** | 10-minute speech allocation, 2-minute live demo script, 40+ Q&A defense. | - [`docs/presentation_notes.md`](docs/presentation_notes.md)<br>- [`docs/viva_qa.md`](docs/viva_qa.md)<br>- Master Presentation deck |
| **5. Comprehensive Project Report** | **15** | Formal report matching PES University Phase-1 format, circuit diagram, BOM, results. | - [`docs/report.md`](docs/report.md)<br>- Compiled DOCX in `ESA Report/` |

---

## 4. Quickstart: Installation & Execution

### Prerequisites
* Python 3.10 to 3.13
* Arduino IDE (if flashing ESP32 firmware)

### 1. Run Unit Tests (Validating All Algorithms)
```powershell
python -m pytest capstone/tests/test_suite.py -v
```

### 2. Launch the Streamlit Clinical Dashboard
```powershell
streamlit run capstone/app/app.py
```

### 3. Run Hardware Serial Logger (with Auto-Simulation Fallback)
```powershell
python -c "from capstone.src.serial_logger import stream_telemetry_generator; [print(s) for s in stream_telemetry_generator(max_samples=10)]"
```
