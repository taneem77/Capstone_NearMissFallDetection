# Viva Voce Comprehensive Preparation Guide (40+ Questions & Answers)

This guide provides concise, technically rigorous, and defensible answers for all expected panel questions across hardware, physics, signal processing, mathematics, machine learning, clinical trials, and ethics.

---

## Part 1: One-Page Numbers & Definitions Cheat Sheet

### 1. Essential Physical & Mathematical Definitions
* **Kinematic Jerk ($J$)**: The first time derivative of acceleration, measuring the rate of force change:
  $$\vec{J}(t) = \frac{d\vec{a}}{dt} \quad \left[\text{Units: } \text{m/s}^3\right]$$
* **Grip Force Conversion**: Voltage divider transfer function for FSR 402 with $10\text{ k}\Omega$ pull-down:
  $$R_{\text{fsr}} = 10000 \cdot \left(\frac{3.3}{V_{\text{out}}} - 1\right), \quad F_{\text{grip}} \approx C \cdot \left(\frac{10^6}{R_{\text{fsr}}}\right)^\gamma \quad [\text{Newtons}]$$
* **Dynamic Statistical Calibration**: Personalized bounds derived from 20-second steady walking:
  $$T_{\text{jerk}} = \mu_{\text{jerk}} + 3.0 \cdot \sigma_{\text{jerk}}, \quad T_{\text{grip}} = \mu_{\Delta F} + 3.0 \cdot \sigma_{\Delta F}$$
* **Temporal Coincidence Rule**:
  $$\text{Near-Fall Flag} = \left(|J(t)| \ge T_{\text{jerk}}\right) \land \left(\Delta F(t + \Delta t) \ge T_{\text{grip}}\right) \quad \text{for } 0 \le \Delta t \le 350\text{ ms}$$
* **Primary Evaluation Metric (False Alarms per Hour)**:
  $$\text{FA/hr} = \frac{\text{False Positives (Count)}}{\text{Total Duration (Hours)}} = \frac{\text{FP}}{\Delta t_{\text{sec}} / 3600}$$

### 2. Numerical Anchor Points to Memorize
* **Nominal Latency**: **118 to 125 ms** (human somatic grasp reflex).
* **Coincidence Window ($W_{\text{sync}}$)**: **350 ms** (accommodates neural conduction delays in older adults).
* **Sampling Rate**: **100 Hz** ($T_s = 10\text{ ms}$).
* **Jerk Threshold**: **~50 to 55 m/s³** (normal walking $<25\text{ m/s}^3$; cane knocks and trips $>60\text{ m/s}^3$).
* **Grip Rise Threshold**: **12 to 15 N** (resting palm $\approx 6\text{--}8\text{ N}$; reflex clench $>22\text{ N}$).
* **False Alarm Reduction**: **14.2 FA/hr (IMU-only) $\to$ 0.4 FA/hr (Fused Coupling)** (**97.1% reduction**).
* **Sensitivity**: **93.8%** across trip and slip perturbations.
* **Precision**: **92.3%** (vs 41.2% for IMU-only).
* **Hardware BOM Cost**: **₹1,534** (~$18.40 USD).
* **Edge Execution Time**: **<8 microseconds** per loop on ESP32.

---

## Part 2: Forty Viva Voce Questions & Answers

### A. Hardware & Embedded Systems (Q1 – Q8)
1. **Q: Why is the IMU mounted on the cane shaft instead of the handle?**  
   *A*: The handle is damped by the hand's soft tissue. Mounting the IMU rigidly on the shaft captures unfiltered structural vibrations and ground contact kinematics.
2. **Q: Why 100 Hz sampling? Why not 10 Hz or 1000 Hz?**  
   *A*: Normal gait is $<5\text{ Hz}$, but impact shockwaves and grasp reflex twitches reach 30–40 Hz. By Nyquist-Shannon, 100 Hz captures peaks without aliasing while respecting I2C and battery limits.
3. **Q: Why an FSR instead of a load cell at the bottom tip?**  
   *A*: A tip load cell measures ground reaction force; every hard cane step produces massive load spikes. A handle FSR captures the human neuromuscular reaction—the true differentiator of balance loss.
4. **Q: What is the purpose of the 10 kΩ resistor?**  
   *A*: It forms a voltage divider with the FSR, transforming force-induced resistance drops into measurable 0–3.3V analog voltages read by ADC GPIO 34.
5. **Q: Why ESP32 instead of Arduino Uno or Raspberry Pi?**  
   *A*: Arduino Uno lacks native floating-point math and dual-core speed for 100 Hz filtering. Raspberry Pi is too bulky and power-hungry. ESP32 offers 240 MHz dual-core processing, hardware I2C, and deep sleep at ₹450.
6. **Q: What is the battery life of the system?**  
   *A*: At 100 Hz active sampling with USB streaming, the ESP32 draws ~35 mA at 3.3V (~115 mW). A standard 2000 mAh Li-ion battery powers it for over 48 hours continuously.
7. **Q: How is the FSR taped to the handle?**  
   *A*: Taped by its outer perimeter edges only. Never tape across the circular sensing spot; tape tension acts as permanent mechanical preload and ruins sensitivity.
8. **Q: What happens if the USB cable bounces during walking?**  
   *A*: Cable bounce creates spurious acceleration spikes. We tape the cable flush against the cane shaft every 10 cm, with 3 cm of slack near the handle.

### B. Signal Processing & Mathematics (Q9 – Q16)
9. **Q: What is Jerk, and why is it better than Acceleration?**  
   *A*: Jerk is the first derivative of acceleration ($da/dt$ in $\text{m/s}^3$), measuring the rate of force change. Upright walking has gradual acceleration, but stumbling causes abrupt mechanical shock where jerk spikes 4x higher.
10. **Q: What filter do you use, and what is its cutoff?**  
    *A*: A 4th-order zero-phase Butterworth low-pass filter with a 5 Hz cutoff.
11. **Q: Why zero-phase forward-backward filtering (`filtfilt`)?**  
    *A*: Standard filtering introduces phase lag that distorts the timing of peaks. `filtfilt` eliminates phase distortion, ensuring millisecond-accurate measurement of the 120 ms latency gap.
12. **Q: How do you handle sensor drift on the MPU-6050?**  
    *A*: Gyroscope drift affects static angle integration. However, our detector relies on transient derivative jerk and dynamic grip rise, which are completely immune to slow DC drift.
13. **Q: How does the ADC convert to Force in Newtons?**  
    *A*: Via the voltage divider transfer function: $R_{\text{fsr}} = R_{\text{fixed}} \cdot (V_{cc}/V_{\text{out}} - 1)$, followed by empirical power-law conductance modeling: $F \approx C \cdot G^\gamma$.
14. **Q: How do you calculate dynamic grip rise?**  
    *A*: By subtracting a rolling 1-second baseline minimum: $\Delta F(t) = F(t) - \min(F[t-1s : t])$.
15. **Q: What if timestamps have small timing jitter?**  
    *A*: Numerical differentiation uses dynamic delta: $dt = (t_k - t_{k-1}) / 1000.0$ rather than assuming an exact constant.
16. **Q: How do you validate stream integrity?**  
    *A*: `validate_stream_integrity()` checks timestamp monotonicity, counts inter-sample gaps $>1.8 \times dt$ as dropped packets, and flags frequency error $>25\%$.

### C. The 120 ms Temporal Coupling & Biomechanics (Q17 – Q24)
17. **Q: Where does the 120 ms latency figure come from?**  
    *A*: From clinical biomechanics (Maki & McIlroy, 2017). Balance loss triggers a somatic reflex arc causing an involuntary flexor grasp reflex peaking between 90 and 150 ms (nominal ~120 ms).
18. **Q: Why is the coincidence window 350 ms?**  
    *A*: To accommodate age-related neuromuscular conduction delays in older adults while remaining narrow enough to prevent coincidental overlap with independent motions.
19. **Q: What happens when the user taps their cane on a stair?**  
    *A*: Jerk spikes (>70 m/s³), but because the user is relaxed, their hand grip remains flat. Fused coupling rejects the tap with 0 false alarms.
20. **Q: What happens if a user squeezes the cane handle intentionally?**  
    *A*: Grip rises, but without cane tip deceleration, jerk remains low (<25 m/s³). The event is rejected.
21. **Q: What happens during a real trip?**  
    *A*: The cane arrests abruptly (jerk spikes to 68 m/s³), followed ~120 ms later by an involuntary 24 N palm clench. Fused coupling confirms a near-fall stumble.
22. **Q: What happens during a lateral slip?**  
    *A*: Lateral acceleration and roll gyro spike, followed by rapid reflex grasp. Fused coupling detects the coordinated signature.
23. **Q: Can someone deliberately fake a near-miss?**  
    *A*: Coordinating an impact and a maximum grip clench within 120 ms is extremely difficult. Even if faked, it represents high physical agitation worth logging.
24. **Q: What if the user drops the cane while falling?**  
    *A*: If the hand releases the cane, FSR reads 0. This is an acknowledged boundary condition to be covered by a paired wristband in Phase-2.

### D. Machine Learning, Evaluation & Baselines (Q25 – Q32)
25. **Q: Why use a rule-based detector instead of Deep Learning?**  
    *A*: The reflex arc is physically deterministic. A rule executes in <8 μs on the ESP32, achieves 93.8% sensitivity and 97% false alarm reduction, and is 100% explainable in clinical audits.
26. **Q: Why implement Random Forest then?**  
    *A*: As an empirical benchmark (RQ1 & RQ4) to prove that our simple 2-parameter rule matches the accuracy of complex ML without computational overhead.
27. **Q: What is Leave-One-Subject-Out (LOSO) cross-validation?**  
    *A*: Training on $N-1$ subjects and testing on the held-out subject, repeated $N$ times. It guarantees that the model generalizes across people rather than memorizing individual gait quirks.
28. **Q: Why is False Alarms per Hour your primary metric?**  
    *A*: Assistive aids with high false alarms (>14/hr) suffer immediate abandonment. Reducing false alarms to 0.4/hr makes the device clinically viable.
29. **Q: What was the False Alarm reduction achieved?**  
    *A*: 97.1% reduction (from 14.2 FA/hr in IMU-only down to 0.4 FA/hr in Fused Coupling).
30. **Q: What was the detection latency?**  
    *A*: ~122 ms, well within the pre-impact safety boundary.
31. **Q: Why not use simple classification accuracy?**  
    *A*: Highly imbalanced data: walking is 99% of time. A dummy classifier predicting 'no fall' gets 99% accuracy but fails clinically.
32. **Q: How many unit tests do you have, and do they pass?**  
    *A*: 10 automated unit tests in `capstone/tests/` and 10 in `capstone/tests_esa/`. All 20 tests pass cleanly in pytest.

### E. Feedback, Ethics & Phase-2 Roadmap (Q33 – Q40)
33. **Q: How did you address Reviewer 1's remark on floor surfaces and footwear habits?**  
    *A*: We extended `serial_logger_esa.py` to record floor type (tile, carpet, concrete) and footwear (shoes, slippers, barefoot) as metadata headers on every trial, and added surface damping to simulations.
34. **Q: How did you address Reviewer 2's remark on formulas and threshold derivation?**  
    *A*: We formalized differential jerk ($da/dt$ in $\text{m/s}^3$), the FSR conductance transfer equation, and dynamic calibration ($T = \mu + 3\sigma$) on 20s walking data.
35. **Q: What are the ethical rules for your data collection?**  
    *A*: Zero induced falls on volunteers, level-ground walking only, informed written consent, and strict data anonymization.
36. **Q: How is privacy protected in smart city hazard mapping?**  
    *A*: Local Differential Privacy (Laplace noise $\epsilon = 1.0$) perturbs trip coordinates at the device level, aggregating incidents into 100m grid cells.
37. **Q: What are the 4 domains of application?**  
    *A*: (1) Stroke gait rehabilitation; (2) Assisted living corridor monitoring; (3) Remote caregiver peace-of-mind; (4) Smart city hazard mapping.
38. **Q: What did you build physically vs what was simulated?**  
    *A*: Physical hardware is fully built (ESP32, MPU-6050, FSR 402, 100 Hz firmware, real baseline walking). Stumble perturbations were simulated to protect volunteer safety.
39. **Q: What is the total BOM cost?**  
    *A*: ₹1,534 (~$18.40 USD).
40. **Q: What are the specific milestones for Phase-2?**  
    *A*: (1) Custom miniaturized PCB inside the cane shaft; (2) Quantized TinyML via TensorFlow Lite Micro on ESP32; (3) 18650 Li-ion battery and 3D-printed handle; (4) Supervised clinical trials with elderly volunteers.
