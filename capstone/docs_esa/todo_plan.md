# Dated ESA Preparation Roadmap & Action Plan

This document provides a day-by-day action plan leading up to the Final ESA Evaluation, highlighting exactly what tasks are automated in software and what actions only the student can do by hand.

---

## 1. Action Items: What Only You (The Student) Can Do by Hand

| Task # | Action Required | Details & Execution Steps | Target Completion |
| :---: | :--- | :--- | :---: |
| **H1** | **Physical Hardware Assembly** | Fasten MPU-6050 and mini-breadboard to cane shaft using dual Velcro straps. Tape FSR 402 on handle around edges only. Solder or connect jumper wires to ESP32 per `capstone/hardware_esa/build_guide.md`. | **D-4 (Nov 12)** |
| **H2** | **Flash ESA Firmware** | Open `capstone/hardware_esa/SmartCane_Firmware_ESA.ino` in Arduino IDE, select `ESP32 Dev Module`, and flash over USB cable. Verify 100 Hz CSV output on Serial Monitor at 115200 baud. | **D-3 (Nov 13)** |
| **H3** | **Record Real Walking Baseline** | Walk 20 meters along a corridor holding the cane naturally. Run: `python capstone/hardware_esa/serial_logger_esa.py`. Save CSV file in `capstone/data/collected/` with volunteer consent form signed. | **D-2 (Nov 14)** |
| **H4** | **Fill `[TO FILL]` in Report** | Open `capstone/docs_esa/report_draft.md` and replace the 5 `[TO FILL]` placeholders in Section 6.2 with your recorded walking baseline averages. | **D-2 (Nov 14)** |
| **H5** | **Rehearse 10-Minute Team Speech** | Conduct a 10-minute timed rehearsal with Tanisha, Samika, Saatvik, and Pratham using `capstone/docs_esa/presentation_notes.md` and `capstone/esa/ESA_PPT_Final.pptx`. | **D-1 (Nov 15)** |

---

## 2. Daily Timeline Leading to Final ESA Review

```
TIMELINE CALENDAR
Nov 12 (D-4) ─── Hardware physical check & breadboard mounting
Nov 13 (D-3) ─── Firmware flashing & bench test validation (LED & CSV check)
Nov 14 (D-2) ─── Real volunteer walking recording & fill [TO FILL] report metrics
Nov 15 (D-1) ─── Team dry-run rehearsal (10-min speech + 2-min demo)
Nov 16 (ESA) ─── FINAL ESA DEFENSE & PRESENTATION
```

### Day 1 (Nov 12): Hardware & Mechanical Setup
- Inspect ESP32 DevKit V1, MPU-6050, and FSR 402.
- Verify 10 kΩ pull-down resistor on breadboard between GPIO 34 and GND.
- Tape FSR 402 by outer perimeter edges only on top of cane handle.
- Fasten mini-breadboard flush to cane shaft using dual Velcro straps.

### Day 2 (Nov 13): Firmware Verification & Bench Check
- Flash `capstone/hardware_esa/SmartCane_Firmware_ESA.ino` to ESP32.
- Run bench checks per `build_guide.md`:
  - Upright cane gravity check: $a_z \approx 9.8\text{ m/s}^2$.
  - Hand squeeze check: `grip_adc` spikes from ~500 to >2000.
  - Cane tap check: Tap tip on floor without squeezing handle $\implies$ Onboard LED remains OFF (false alarm rejected).

### Day 3 (Nov 14): Real Baseline Data Recording & Final Report Fill
- Record 2–4 volunteer level-ground walking trials using `serial_logger_esa.py`.
- Run `python capstone/src/calibration.py` to derive baseline $\mu$ and $\sigma$.
- Open `capstone/docs_esa/report_draft.md` and fill in:
  - Average baseline walking velocity
  - Mean baseline jerk $\mu_{\text{jerk}}$ and $\sigma_{\text{jerk}}$
  - Mean baseline grip $\mu_{\text{grip}}$ and $\sigma_{\text{grip}}$
- Export final report Word document:
  `python capstone/scripts/generate_esa_report_docx.py`

### Day 4 (Nov 15): Full Team Rehearsal & Live Demo Practice
- Run team rehearsal with the 4 speakers:
  - Tanisha: Problem statement, research questions, baseline taxonomy (3 min)
  - Saatvik: Kinematic jerk ($da/dt$), grip dynamics, Fused Coupling formula (2.5 min)
  - Samika: Hardware build, ESP32 live streaming, 4 domains of application (2.5 min)
  - Pratham: Quantitative evaluation (LOSO, 97.1% false alarm reduction), roadmap (3 min)
- Practice the 2-minute live demo on `streamlit run capstone/app/app.py`:
  1. Show Cane Tap Rejection in Tab 1 (IMU-only false alarms vs Fused Coupling rejects).
  2. Show Near-Miss Trip Detection in Tab 1 (Coordinated 118 ms latency trigger).
  3. Show Benchmark table in Tab 2 (14.2 $\to$ 0.4 FA/hr).
- Verify backup plan: If USB disconnects, simulation fallback runs automatically.

### Day 5 (Nov 16): Review Day Checklist
- Bring:
  - Smart Cane prototype with USB cable
  - Laptop with Streamlit dashboard pre-launched
  - Printed copy of `capstone/docs_esa/report_draft.md` / DOCX
  - Loaded `capstone/esa/ESA_PPT_Final.pptx`
  - Signed volunteer informed consent forms
