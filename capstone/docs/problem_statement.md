# Problem Statement & Clinical Motivation

## 1. Background & Epidemiological Context
Falls represent the second leading cause of unintentional injury deaths worldwide according to the World Health Organization (WHO), resulting in approximately **684,000 fatalities annually**. Among individuals aged 65 and older, approximately **28% to 35% experience at least one fall each year**, escalating to 40% among those over 75 years. In India, demographic aging has accelerated fall incidents, with post-fall complications (such as femoral neck fractures, subdural hematomas, and prolonged immobility) imposing catastrophic physical and financial burdens.

Although walking canes are the most prevalent assistive mobility aids—prescribed to improve balance, offload joint stress, and widen the base of support—conventional canes are passive mechanical struts. When a patient experiences a loss of balance, current commercial systems only trigger *after* impact occurs (e.g., push-button SOS or impact accelerometers).

---

## 2. Why Near-Misses Matter: Heinrich’s Safety Triangle in Geriatrics
A **near-fall (or near-miss)** is defined as an unexpected disruption of upright equilibrium during gait caused by a trip, slip, or misstep where the subject successfully executes a compensatory recovery maneuver to avert impact. 

Applying **Heinrich’s Safety Triangle** to clinical geriatrics reveals a profound principle:
- For every **1 catastrophic fall** resulting in fracture or hospitalization,
- There are **29 minor injurious falls**,
- And **300 near-miss stumble events**.

Near-misses are the earliest, highest-frequency diagnostic precursors of neuromuscular decline, muscle weakness, visual impairment, or adverse drug reactions. However, conventional geriatric care relies on subjective, recall-biased patient surveys (e.g., "How many times did you trip last month?"), which underestimate instability by over 60%. A Smart Cane that autonomously logs near-misses provides objective longitudinal biomarker tracking *before* an irreversible injury occurs.

---

## 3. Critical Limitations of Existing Technologies
Existing wearable and ambient fall prevention systems suffer from persistent clinical adoption bottlenecks:
1. **Wearable Compliance Fatigue**: Pendants, smartwatches, and chest patches require daily charging, user memory to wear, and are frequently abandoned by patients with mild cognitive impairment.
2. **Post-Fall Latency**: Impact detectors notify emergency contacts only *after* trauma has already occurred, offering zero preventative value.
3. **Severe False Alarm Rates in Cane-Mounted Systems**: Previous experimental smart canes utilizing only IMU accelerometers flag false alarms whenever a user taps the cane against a curb, places it down firmly, or gestures during conversation. High false alarm rates cause users to disable or ignore the device.

---

## 4. The Three Selected Research Gaps
From our comprehensive review of 2018–2026 biomechanics and pervasive computing literature, we identified three core gaps:

* **Gap 1: Kinematic False-Alarm Vulnerability**: Cane-only IMU thresholding cannot differentiate between intentional cane impacts (tapping stairs, knocking doors) and true postural recovery stumbles because both exhibit acceleration transients exceeding $3g$.
* **Gap 2: Neglect of Upper-Extremity Neuromuscular Coupling**: Human balance recovery involves rapid synergistic reflex actions. When equilibrium is disrupted, the central nervous system triggers a spinal-cortical reflex causing a sudden, involuntary clenching of the hand around the support aid. Existing smart canes completely overlook this kinetic grip-force signature.
* **Gap 3: Lack of On-Device Temporal Synchronization Rules**: Multi-sensor research often defers processing to heavy cloud neural networks with multi-second latencies. There is a lack of deterministic, lightweight, millisecond-accurate temporal coupling rules deployable on low-power microcontrollers (ESP32) for instant on-device validation.

---

## 5. Research Objectives & Expected Outcomes
To overcome these gaps, this project formulates and validates an end-to-end cyber-physical assistive system:

1. **Hardware Instrumentation**: Integrate a tri-axial IMU (MPU-6050) on the cane shaft and a piezoresistive Force Sensitive Resistor (Interlink FSR 402) on the handle under an ESP32 microcontroller running at 100 Hz.
2. **Temporal Coupling Rule Formulation**: Implement a dual-domain detection algorithm:
   $$\text{Near-Miss Flag} = \left(|J(t)| \ge T_{\text{jerk}}\right) \land \left(\Delta F(t + \Delta t) \ge T_{\text{grip}}\right) \quad \text{for } 0 \le \Delta t \le W_{\text{sync}}$$
   verifying that involuntary grip clenching succeeds kinematic jerk within a nominal window of $\approx 120\text{ ms}$.
3. **Dynamic Personalized Calibration**: Formulate a statistical threshold calculation $(\mu + k\sigma)$ derived from a 20-second steady-walking baseline to accommodate patient-specific gait signatures.
4. **Empirical Benchmark & False Alarm Suppression**: Demonstrate a $>90\%$ reduction in False Alarms per hour compared to IMU-only baselines while maintaining $>90\%$ sensitivity on trip and slip perturbations.
5. **Clinical Dashboard Deployment**: Provide a 3-tab interactive Streamlit interface displaying synchronized waveforms, model benchmarks, and weekly fall-risk trends.
