# Engineering Assumptions & Methodological Transparency

This document lists all foundational assumptions, coordinate conventions, hardware specifications, and honesty rules governing the Phase-1 evaluation.

---

## 1. Physical & Biomechanical Assumptions

1. **Cane Coordinate Conventions**:
   - **Z-Axis**: Aligned longitudinally downward along the cylindrical cane shaft towards the rubber ferrule tip. Upright static gravity registers predominantly along $+Z$ ($\approx 9.81\text{ m/s}^2$).
   - **Y-Axis**: Aligned horizontally forward along the user's line of progression (sagittal plane). Trip decelerations register predominantly on the $Y$ axis.
   - **X-Axis**: Aligned laterally (coronal plane). Lateral slip perturbations register predominantly on the $X$ axis.
2. **Handle Grip Dynamics**:
   - Assumes unilateral palm contact where the thenar/hypothenar palm region rests directly over the circular active zone of the FSR 402.
   - Assumes that during loss of balance, the human somatic grasp reflex involuntarily contracts the hand flexor muscles around the handle prior to any voluntary release.
3. **Temporal Coincidence Bounds**:
   - Minimum physiological reflex latency: $80\text{ ms}$ (physical lower limit of spinal reflex transmission).
   - Maximum coincidence window: $W_{\text{sync}} = 350\text{ ms}$ (accommodating mild neural conduction delays in older adults while preventing accidental alignment with independent motions).

---

## 2. Hardware & Electrical Assumptions

1. **Sampling Frequency & Clock Stability**:
   - Nominal sampling rate: $f_s = 100\text{ Hz}$ ($T_s = 10.0\text{ ms}$).
   - Allowable timing jitter: $<15\%$ deviation in inter-sample delta. Dynamic delta time ($dt$) is computed on each tick for numerical derivative calculation.
2. **Sensor Headroom & Resolution**:
   - Accelerometer range is configured to $\pm 4g$ ($8192\text{ LSB}/g$), providing sufficient headroom against impact saturation while preserving sensitivity for steady walking.
   - Gyroscope range is configured to $\pm 500^\circ/\text{s}$ ($65.5\text{ LSB}/(^\circ/\text{s})$).
   - FSR resistance is mapped through a 10 kΩ pull-down resistor into a 12-bit ADC ($0 - 4095$ counts).

---

## 3. Strict Academic Honesty Rules

1. **Labeling of Data**:
   - All synthetic datasets are explicitly stamped with `# DATASET_TYPE: SIMULATED` metadata headers.
   - Real data is labeled with `# DATASET_TYPE: REAL_VOLUNTEER`.
2. **Zero Fabrication**:
   - No clinical trial participants or patient hospital counts are fabricated. Real physical tests were conducted with healthy volunteers performing level-ground baseline walking. High-velocity stumble perturbations are evaluated using calibrated biomechanical simulation to avoid inducing volunteer injury.
3. **Verification of Literature**:
   - Every cited academic paper corresponds to a real, verifiable publication with verified DOI / venue links.
4. **Hypothesis vs Proven Fact**:
   - System superiority claims are phrased as empirically supported hypotheses on our benchmark dataset until prospective clinical trials are conducted in Phase-2.
