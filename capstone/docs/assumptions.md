# Engineering Assumptions & Methodological Transparency

To ensure strict academic honesty, scientific reproducibility, and defensibility during evaluation, this document codifies all foundational assumptions, coordinate conventions, and data provenance rules.

---

## 1. Physical & Biomechanical Assumptions

1. **Cane Coordinate Frame Definition**:
   - **Z-Axis**: Aligned longitudinally downward along the cylindrical cane shaft towards the rubber ferrule tip. Static gravity during upright stance registers primarily along $+Z$ ($\approx 9.81\text{ m/s}^2$).
   - **Y-Axis**: Aligned horizontally forward along the user's line of progression (sagittal plane). Decelerations during heel strike and tripping register predominantly on the $Y$ axis.
   - **X-Axis**: Aligned laterally (coronal plane). Slip perturbations and lateral corrective sways register predominantly on the $X$ axis.
2. **Handle Grip Contact Dynamics**:
   - Assumes unilateral palm contact where the thenar and hypothenar eminences (palm heel) exert pressure over the FSR 402 circular active area on top of the cane handle.
   - Assumes that during balance disruption, reflex grip tightening occurs prior to voluntary conscious release of the aid.
3. **Temporal Coincidence Bounds**:
   - Minimum physiological reflex latency: $t_{\text{min}} = 80\text{ ms}$ (physical lower limit of spinal monosynaptic and polysynaptic transmission).
   - Maximum coincidence window: $W_{\text{sync}} = 350\text{ ms}$ to $400\text{ ms}$, accounting for age-related neuromuscular conduction delays while excluding independent voluntary gestures.

---

## 2. Hardware & Electrical Assumptions

1. **Sampling Frequency & Clock Stability**:
   - Nominal sampling rate: $f_s = 100\text{ Hz}$ ($T_s = 10.0\text{ ms}$).
   - Allowable timing jitter: $<15\%$ deviation in inter-sample delta. Handled via dynamic delta time calculation in numerical differentiation: $dt = (t_k - t_{k-1}) / 1000.0$.
2. **Sensor Linearity & Saturation**:
   - Accelerometer range is configured to $\pm 4g$ ($\pm 39.2\text{ m/s}^2$), providing optimal balance between resolution ($8192\text{ LSB}/g$) and headroom against saturation during impacts.
   - Gyroscope range is configured to $\pm 500^\circ/\text{s}$ ($65.5\text{ LSB}/(^\circ/\text{s})$).
   - FSR resistance behavior is modeled using power-law conductance transfer functions to compensate for logarithmic resistance decay.

---

## 3. Strict Honesty & Data Provenance Statement

In accordance with academic integrity guidelines for the Final ESA:
* **Real Hardware Tested**: The ESP32 node, MPU-6050, and FSR 402 handle circuit were physically assembled, wired according to the documented schematic, loaded with the C++ firmware, and tested via serial streaming for steady walking telemetry.
* **Simulated Benchmarks**: Due to strict safety protocols (preventing vulnerable elderly volunteers from being subjected to induced fall hazards), multi-subject perturbation datasets (`near_miss_trip.csv`, `near_miss_slip.csv`, `benchmark_multi_subject.csv`) are mathematically synthesized using established biomechanical dynamics and calibrated against the K-Fall taxonomy.
* **Zero Fabrication**: No real patient clinical trial approvals or human trial subject counts are falsely claimed. All results are clearly delineated between *Physical Hardware Telemetry* and *Biomechanical Synthetic Benchmarks*.
