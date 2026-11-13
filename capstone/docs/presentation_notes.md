# Final ESA Presentation Notes & Team Speaking Script

**Project Title**: Smart Cane for Near-Fall Detection Using Cane Kinematics and Grip-Force Dynamics  
**Team ID**: PW_27_MHR_01 | **Department of CSE, PES University**  
**Total Duration**: 10-12 Minutes (+ 3 Minutes Q&A / Live Demo)

---

## Team Speaking Order & Allocation (From Official Agenda)

```
+----+--------------------+----------------------------------------------------+----------+
| #  | Speaker            | Sections Covered                                   | Duration |
+----+--------------------+----------------------------------------------------+----------+
| 1  | Tanisha Mathur     | Problem, Research Questions, Dataset & Pipeline    | 3-4 min  |
| 2  | Saatvik Gupta      | Feature Extraction, IMU-Only vs Fused Coupling     | 2-3 min  |
| 3  | Samika Ojha        | Live Software, ESP32 Logging & Coupling (RQ3)      | 3 min    |
| 4  | Pratham S Reddy    | Evaluation (LOSO, False Alarms/hr) & RQ4 Results   | 3-4 min  |
+----+--------------------+----------------------------------------------------+----------+
```

---

## 1. Speaker 1: Tanisha Mathur (3–4 Minutes)
*Slides Covered: Slide 1 (Title), Slide 2 (Outline), Slide 3 (Abstract & Motivation), Slide 4 (Reviewer Feedback Summary), Slide 5 (Understanding Problem Statement & RQ1)*

> "Respected panel members and guide, good morning. I am Tanisha Mathur. Today our team presents our Capstone Phase-1 project: *Smart Cane for Near-Fall Detection Using Cane Kinematics and Grip-Force Dynamics*.
> 
> According to the WHO, over 684,000 fatal falls occur globally each year, and 30% of adults over 65 fall annually. Conventional medical alert pendants and impact detectors only sound an alarm *after* a catastrophic fall has occurred—when fractures and injuries have already been sustained. 
> 
> In safety engineering, Heinrich’s Triangle demonstrates that for every single catastrophic fall, there are 300 pre-impact near-miss stumbles. A near-miss is a stumble, slip, or trip where the user successfully catches themselves. If we can objectively track these near-misses, we gain an early diagnostic window to intervene *before* a hospitalizing fall happens.
> 
> However, existing smart canes rely exclusively on IMU accelerometers. The fatal flaw with IMU-only canes is **extreme false alarm rates**: every time a user taps their cane on a stair edge, knocks a door, or firmly plants the cane, the IMU registers a high acceleration spike and triggers a false alarm.
> 
> To solve this, we formulated our central hypothesis: **Can cross-domain fusion of cane shaft kinematics with handle grip-force dynamics distinguish true near-misses from ordinary cane impacts?**
> We designed a complete pipeline running at 100 Hz, bench-tested against the K-Fall taxonomy and multi-subject kinematic profiles. I now invite Saatvik to explain our feature extraction and dual-domain fusion theory."

---

## 2. Speaker 2: Saatvik Gupta (2–3 Minutes)
*Slides Covered: Slide 5 (Feature Extraction), Slide 6 (Proposed Architecture & Block Diagram)*

> "Thank you, Tanisha. Panel members, I am Saatvik Gupta. I will explain our kinematic feature extraction and how we solved Reviewer 2’s feedback regarding mathematical rigor.
> 
> Rather than relying on raw acceleration, our primary kinematic metric is **Jerk ($J$)**, the first time derivative of acceleration:
> $$J(t) = \frac{da}{dt} = \frac{a[t] - a[t-1]}{\Delta t} \quad \text{in } \text{m/s}^3$$
> During steady walking, acceleration changes smoothly, keeping jerk below $25\text{ m/s}^3$. But during a stumble or trip, the cane undergoes abrupt arrest, causing jerk to spike past $60\text{ m/s}^3$.
> 
> However, tapping the cane against a curb also produces a high jerk spike. How do we filter this out?
> This is our core novelty: **Upper-extremity neuromuscular reflex coupling**.
> As established by Maki & McIlroy in clinical biomechanics, when human balance is disrupted, the somatic nervous system triggers an involuntary, protective clench of the hand within **90 to 150 milliseconds (nominal ~120 ms)**.
> 
> We capture this using an FSR sensor mounted under the palm on the handle.
> We formulate the **Fused Temporal Coupling Rule**:
> $$\text{Near-Miss Detected} = (|J(t)| \ge T_{\text{jerk}}) \land (\Delta F(t + \Delta t) \ge T_{\text{grip}}) \quad \text{for } 0 \le \Delta t \le 350\text{ ms}$$
> When a user taps their cane on a curb, jerk spikes, but their grip remains relaxed—resulting in zero false alarms.
> Furthermore, addressing Reviewer 2, we eliminated arbitrary thresholds by implementing **personalized statistical calibration**:
> $$T_{\text{jerk}} = \mu_{\text{baseline}} + 3.0 \cdot \sigma_{\text{baseline}}$$
> derived from a 20-second steady walking trial. I now invite Samika to present our live software and ESP32 telemetry implementation."

---

## 3. Speaker 3: Samika Ojha (3 Minutes)
*Slides Covered: Slide 6 (Hardware Interconnects), Slide 7 (Applicability Across 3 Domains), Slide 8 (Live Software & Demo)*

> "Thank you, Saatvik. I am Samika Ojha. I will walk you through our hardware implementation, live telemetry software, and domain applications.
> 
> As seen in our architecture, our hardware node is built around an ESP32 microcontroller running at 100 Hz. The MPU-6050 6-DOF IMU is mounted rigidly on the cane shaft, connected via I2C on GPIO 21 and 22. The handle features an Interlink FSR 402 configured in a precision voltage divider with a 10 kΩ resistor into ADC GPIO 34. 
> 
> Addressing Reviewer 1’s feedback—who advised us to account for floor types and footwear habits—our Python streaming engine in `serial_logger.py` logs full session metadata including floor surfaces (Tiled, Carpet, Concrete) and footwear types (Walking Shoes, Slippers, Barefoot).
> 
> Our system serves three high-impact societal domains:
> 1. **Clinical Rehabilitation**: Objective recovery tracking for post-stroke patients transitioning to single-point canes.
> 2. **Assisted Living**: Automated alerts to nursing stations upon resident stumbling, eliminating unmonitored corridor falls.
> 3. **Remote Caregiver Tele-monitoring**: Peaceful daily risk status shared with family members without intrusive cameras.
> 
> Let us look at the live software demo running on our Streamlit dashboard..." *(Pointers to Tab 1 & Tab 2: Show the cane bump rejection live, then invite Pratham for quantitative evaluation).*

---

## 4. Speaker 4: Pratham S Reddy (3–4 Minutes)
*Slides Covered: Slide 8 (Quantitative Results & RQ4), Slide 9 (Evaluation, Limitations & Phase-2 Roadmap), Slide 10 (Conclusion & Viva)*

> "Thank you, Samika. Good morning panel, I am Pratham S Reddy. I present our quantitative evaluation, comparative benchmarks, and Phase-2 roadmap.
> 
> Our primary evaluation metric is **False Alarms per Hour ($FA/hr$)**. In elderly healthcare, high false alarm rates destroy patient compliance.
> When evaluating an IMU-Only detector on simulated multi-activity trials, it triggered an unacceptable **14.2 False Alarms per hour**, primarily because ordinary cane knocks and curb taps mimic fall deceleration.
> Grip-Only detection eliminated impact false alarms, but triggered false alarms whenever the user tightened their hand while standing.
> 
> Under our **Fused Temporal Coupling Rule**:
> - **False Alarms per Hour plummeted from 14.2 down to 0.4 FA/hr**—a **97.1% reduction in false alarms**.
> - **Sensitivity** remained high at **93.8%** across trip and slip perturbations.
> - **Precision** jumped from 41% to **92.3%**.
> - Detection latency is strictly under **150 milliseconds**, well within the pre-impact boundary.
> 
> In addition, we validated our machine learning baseline using Leave-One-Subject-Out (LOSO) cross-validation across 5 synthetic subjects, achieving an F1-score of 0.942.
> 
> **Phase-2 Engineering Roadmap**:
> In Phase-2, we will:
> 1. Deploy quantized TinyML directly onto the ESP32 using Edge Impulse.
> 2. Fabricate a custom rigid PCB housed inside the cane shaft with an integrated 18650 Li-ion battery.
> 3. Implement Local Differential Privacy ($\epsilon = 1.0$) for municipal hazard mapping.
> 4. Conduct IRB-approved controlled perturbation trials with physiotherapist supervision.
> 
> We are now ready for your questions. Thank you."

---

## 5. Two-Minute Live Demo Execution Script

```powershell
# Step 1: Open terminal in project root
streamlit run capstone/app/app.py

# Step 2: In Tab 1, select "Cane Tap / Curb Bump (False Alarm Test)"
# Point to screen:
# "Notice the extreme Jerk spike (>75 m/s^3). Notice IMU-Only flags an alarm.
#  However, because Grip Force remains flat, Fused Coupling correctly REJECTS it."

# Step 3: Select "Near-Miss Trip (Obstacle Contact)"
# Point to screen:
# "Now observe a true stumble: Jerk spikes to 68 m/s^3, followed 118 ms later by a 24 N grip spike.
#  Fused Coupling immediately triggers 'NEAR-FALL CONFIRMED'."

# Step 4: Click Tab 2: Show the benchmark table comparing False Alarms/hr (14.2 vs 0.4).
```
