# Project Milestone Roadmap & Phase-2 Timeline

This document tracks the phased progression from Project Conception through Final ESA Evaluation and into Phase-2 deployment.

---

## 1. Phase-1 Completed Milestones (August – December 2026)

| Milestone Code | Target Date | Description / Deliverable | Status |
| :---: | :---: | :--- | :---: |
| **M1.1** | Sep 15, 2026 | Problem Formulation, Literature Survey & Review 1 Presentation | **COMPLETED** |
| **M1.2** | Oct 10, 2026 | Hardware Assembly (ESP32 + MPU6050 + FSR 402) on Breadboard | **COMPLETED** |
| **M1.3** | Oct 25, 2026 | Sensor Driver Firmware (100 Hz I2C & ADC Polling) in Arduino C++ | **COMPLETED** |
| **M1.4** | Nov 02, 2026 | Review 2 Evaluation: Feedback addressed on floor surfaces & formulas | **COMPLETED** |
| **M1.5** | Nov 08, 2026 | Dual-Domain Temporal Coupling Algorithm & Statistical Calibration Engine | **COMPLETED** |
| **M1.6** | Nov 11, 2026 | Streamlit 3-Tab Interactive Dashboard & Unit Test Suite (10/10 Passed) | **COMPLETED** |
| **M1.7** | Nov 15, 2026 | Final ESA Viva Voce, Comprehensive Report & Master Presentation | **READY FOR EVALUATION** |

---

## 2. Phase-2 Engineering Roadmap (January – May 2027)

```
2027 Timeline
Jan           Feb           Mar           Apr           May
[--PCB Design--]
              [--TinyML Port--]
                            [--BMS & Case--]
                                          [--IRB Trials--]
                                                        [--Final Defense--]
```

* **Sprint 1 (Jan 2027): Custom Embedded PCB Design**
  - Replace mini breadboard with a custom 2-layer rigid PCB designed in KiCad ($25\text{ mm} \times 60\text{ mm}$).
  - Integrate an ESP32-C3 module and surface-mount IMU (LSM6DSO) to fit entirely inside the cane shaft cavity.
* **Sprint 2 (Feb 2027): Edge TinyML Model Porting**
  - Train quantized Decision Tree and 1D-CNN using Edge Impulse.
  - Flash TensorFlow Lite Micro models directly onto ESP32 flash memory for sub-millisecond edge classification.
* **Sprint 3 (Mar 2027): Power Management & Industrial Casing**
  - Incorporate single-cell 18650 Li-ion battery with integrated TP4056 USB-C charging and battery management system (BMS).
  - 3D print an ergonomic IP54 splash-resistant handle casing.
* **Sprint 4 (Apr 2027): Supervised Clinical Validation**
  - Secure Institutional Review Board (IRB) ethical clearance.
  - Partner with local physiotherapy clinics to conduct supervised balance obstacle courses with mild balance-impaired volunteers.
* **Sprint 5 (May 2027): Final Phase-2 Dissertation & Public Dataset Release**
  - Release anonymized dual-sensor smart cane dataset on PhysioNet / IEEE Dataport.
  - Submit Phase-2 final thesis and journal manuscript.
