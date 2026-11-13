# Smart Cane Guided Interactive ESA Walkthrough System

**Comprehensive Capstone Project Phase-1 Demonstration**  
*Project ID*: `PW_27_MHR_01`  
*Course*: UE24CS320A – Capstone Project Phase-1  
*Department of Computer Science & Engineering, PES University, Bengaluru*  
*Guide*: **Dr. Mamatha H R**  
*Team Members*: **Tanisha Mathur, Samika Ojha, Saatvik Gupta, Pratham S Reddy**  

---

## 1. Quickstart & Windows Run Command

Start the demonstration with a single command from the project root:

```powershell
python capstone/demo/server.py
```

Or double-click:
```powershell
capstone\demo\run.bat
```

### Automatic System Capabilities:
1. **Port Hunting**: If port 5000 is occupied, it automatically checks 5001, 5002, 5005, etc., and cleanly binds without crashing.
2. **Auto-Browser Launch**: Automatically opens the default browser to `http://127.0.0.1:<port>`.
3. **100% Offline**: Zero external CDN calls or npm/build steps; all SVG, canvas, and mathematical logic run natively.
4. **Fixed Determinism**: Fixed random seed (`seed: 42`) guarantees repeatable numerical outputs.

---

## 2. Walkthrough Sections & Interactive Modules

### Phase 1: Problem & IoT Design
1. **Section 1: Problem & Clinical Need**:
   - Canvas stick-figure animation comparing *Without Cane Sensing* (unheralded ground impact) vs. *With Cane Sensing* (118 ms reflex grasp detection and recovery).
   - Domain switcher: Elderly Assisted Living (caregiver SMS), Visually Impaired Mobility (handle haptics), and Post-Stroke Rehabilitation (stability index).
2. **Section 2: IoT Architecture Simulation**:
   - Interactive SVG flow: `Transducers` $\rightarrow$ `ESP32` $\rightarrow$ `Serial/Wi-Fi` $\rightarrow$ `serial_logger.py` $\rightarrow$ `Dual Engine`.
   - Real vs. Planned tags (`BUILT` on all physical components).
   - Live traveling packet dot with live JSON stream inspector.
3. **Section 3: Hardware Schematic & Layout**:
   - SVG circuit diagram of ESP32 connected to MPU6050 (GPIO21/22) and FSR ($10\text{ k}\Omega$ pull-down divider to GPIO34).
   - Mechanical cane layout and interactive grip squeeze slider converting ADC counts ($0\text{--}4095$) to Newtons ($0\text{--}45\text{ N}$).

### Phase 2: Data, ML Pipeline & Results
4. **Section 4: Data Collection Simulator**:
   - 4-subject protocol panel across 5 activity classes (`walk`, `turn`, `sit`, `hardneg`, `nearmiss`).
   - `Record Trial` button generating waveforms with automated $\pm 0.4\text{ s}$ bounding boxes around impacts.
   - Side-by-side comparison: K-Fall (32 subjects, 5,075 files, public) vs. Smart Cane (Collected/Simulated).
5. **Section 5: Processing Pipeline Explorer**:
   - 5-stage interactive stepper:
     - *Stage 1*: Raw 100 Hz signal with transmission dropout gaps.
     - *Stage 2*: Linear interpolation repairing dropouts $\le 100\text{ ms}$.
     - *Stage 3*: 20 Hz low-pass zero-phase Butterworth filter.
     - *Stage 4*: 1.0s sliding windows (0.25s stride) with $\ge 0.25\text{ s}$ overlap labeling rule.
     - *Stage 5*: 59-dimensional feature matrix (50 IMU + 9 Grip features).
6. **Section 6: Live Detection Simulation (Main Demo)**:
   - 3-channel scrolling oscilloscope (Acceleration, Angular Velocity, Grip Force).
   - Status indicator light (Normal vs. Near-Miss Alarm).
   - 3 scripted test scenarios: Routine Walking, Hard Curb Jolt (Negative test), and Real Near-Miss Stumble.
   - Model switcher (Fused Coupling, Random Forest, Peak-Jerk Threshold, Normal-Only Isolation Forest).
   - Feature toggle (IMU-Only vs. Fused IMU+Grip): visually proves how IMU-only false alarms on curb shocks while Fused stays quiet.
7. **Section 7: Results Dashboard (RQ1–RQ4)**:
   - **RQ1**: K-Fall baseline: Threshold (73.7% sens, 496 FA/hr) vs. Random Forest (84.8% sens, 82.1 FA/hr) and top features.
   - **RQ2**: IMU-only (17.6% sens, 28 FP) vs. Fused (100% sens, 0 FP).
   - **RQ3**: Physiological $118.4\text{ ms}$ grasp reflex delay and weekly stumble trend log.
   - **RQ4**: Supervised RF vs. Normal-Only Anomaly detection with interactive labeled fraction slider.
   - Per-subject breakdown and honest failure cases audit (28 false negatives explained).
8. **Section 8: Honest Limitations Panel**:
   - Detailed academic self-critique: sensor placement divergence (lumbar vs. cane), lack of physical grip in K-Fall, healthy young volunteer cohort, and tethered breadboard power.

---

## 3. Unit Test Verification (10/10 Passing)

Run the test suite:
```powershell
python capstone/demo/test_demo.py
```
*Output: 10 tests passed in under 0.8 seconds.*
