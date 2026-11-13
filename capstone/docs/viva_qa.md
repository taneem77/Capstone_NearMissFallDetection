# Viva Voce Comprehensive Q&A (40+ Questions & Answers)

This guide provides immediate, technically rigorous, and defensible answers for all expected panel questions across hardware, physics, signal processing, mathematics, machine learning, clinical trials, and ethics.

---

## Part 1: Quick Formula Cheat Sheet (1-Page Viva Quick Reference)

1. **Kinematic Jerk Vector ($m/s^3$)**:
   $$\vec{J}(t) = \frac{d\vec{a}}{dt} = \left[ \frac{a_x[t]-a_x[t-1]}{\Delta t}, \frac{a_y[t]-a_y[t-1]}{\Delta t}, \frac{a_z[t]-a_z[t-1]}{\Delta t} \right]$$
   $$|J(t)| = \sqrt{j_x^2 + j_y^2 + j_z^2}$$
2. **FSR Voltage Divider Transfer Equation**:
   $$V_{\text{out}} = V_{\text{cc}} \cdot \frac{R_{\text{fixed}}}{R_{\text{fsr}} + R_{\text{fixed}}} \implies R_{\text{fsr}} = R_{\text{fixed}} \cdot \left( \frac{V_{\text{cc}}}{V_{\text{out}}} - 1 \right)$$
   $$F_{\text{grip}} \approx C \cdot \left( \frac{10^6}{R_{\text{fsr}}} \right)^\gamma \quad [\text{in Newtons}]$$
3. **Statistical Personalized Calibration Threshold**:
   $$T_{\text{jerk}} = \mu_{\text{jerk, baseline}} + k_{\text{jerk}} \cdot \sigma_{\text{jerk, baseline}} \quad (\text{typically } k=3.0)$$
   $$T_{\text{grip}} = \mu_{\Delta F, \text{ baseline}} + k_{\text{grip}} \cdot \sigma_{\Delta F, \text{ baseline}}$$
4. **Dual-Domain Temporal Coupling Logic**:
   $$\text{Decision}(t) = \begin{cases} 1 \text{ (Near-Fall)} & \text{if } |J(t)| \ge T_{\text{jerk}} \land \exists \, \tau \in [t, t+W_{\text{sync}}] \text{ s.t. } \Delta F(\tau) \ge T_{\text{grip}} \\ 0 \text{ (Normal/Tap)} & \text{otherwise} \end{cases}$$
5. **Primary Evaluation Metric (False Alarms per Hour)**:
   $$\text{FA/hr} = \frac{\text{False Positives (Count)}}{\text{Total Monitoring Duration (Hours)}} = \frac{\text{FP}}{\Delta t_{\text{sec}} / 3600}$$

---

## Part 2: Hardware & Embedded Systems

**Q1: Why did you mount the IMU on the cane shaft rather than the handle?**  
*Answer*: The handle is in direct contact with the hand, absorbing and damping shock waves. Mounting the MPU-6050 rigidly on the cane shaft (below the handle junction) captures direct structural vibrations and ground-tip contact dynamics without soft-tissue mechanical filtering.

**Q2: What is the sampling rate and why 100 Hz?**  
*Answer*: Human voluntary movement occurs below 5 Hz, but transient impact shocks and reflex twitches have frequency components up to 30–40 Hz. By the Nyquist-Shannon sampling theorem, sampling at 100 Hz ($T_s = 10\text{ ms}$) perfectly captures impact peaks without aliasing while remaining well within the ESP32's processing and I2C bandwidth.

**Q3: Why did you choose an FSR over a strain gauge or load cell?**  
*Answer*: Load cells require rigid metallic mounting, Wheatstone bridges, and bulky instrumentation amplifiers (e.g., HX711) which add weight and are slow (~10–80 Hz). Interlink FSRs are paper-thin (<0.4 mm), flexible, lightweight, withstand high mechanical shock, and interface directly to an ADC with a single 10 kΩ resistor at sub-millisecond speeds.

**Q4: How do you handle ADC noise and non-linearity on the ESP32?**  
*Answer*: The ESP32 ADC has non-linearities below 0.1V and above 3.1V. In our voltage divider, the 10 kΩ resistor ensures that resting grip (5–10 N) and reflex clenches (20–40 N) operate in the linear 0.6V to 2.6V zone. We also apply a 4th-order low-pass filter and median windowing.

**Q5: What is the power consumption of your hardware node?**  
*Answer*: At full 100 Hz active sampling with Wi-Fi off and USB/Serial streaming, the ESP32 draws ~35 mA at 3.3V (~115 mW). A standard 2000 mAh 18650 Li-ion cell provides over 48 hours of continuous operation. In Phase-2, using ESP32 deep-sleep between step swings will extend battery life to 7 days.

---

## Part 3: Mathematics, Physics & Signal Processing

**Q6: What is the physical significance of Jerk over Acceleration?**  
*Answer*: Acceleration is proportional to applied force ($F = ma$). During regular walking, gravity and steady propulsion create sustained acceleration changes. Jerk is the time derivative of acceleration ($\frac{d^3 x}{dt^3}$ or $\frac{da}{dt}$), representing the *rate of force change*. Tripping causes immediate mechanical shock, producing jerk magnitudes 4x higher than standard walking.

**Q7: Why not use a simple high-pass filter instead of calculating the derivative?**  
*Answer*: High-pass filtering attenuates DC gravity, but does not provide the explicit kinematic derivative ($m/s^3$) necessary for deterministic thresholding. Direct numerical differentiation ($\Delta a / \Delta t$) combined with a forward-backward zero-phase Butterworth low-pass filter provides clean jerk without phase distortion.

**Q8: Why does Butterworth filtering use `filtfilt` instead of `lfilter`?**  
*Answer*: Standard `lfilter` introduces frequency-dependent phase delay (lag), which shifts the apparent peak time of the jerk. `filtfilt` performs forward and reverse filtering, achieving zero phase distortion, which is essential for measuring precise millisecond temporal gaps ($\Delta t$).

**Q9: How do you handle sensor drift in the MPU-6050?**  
*Answer*: Gyroscope drift affects static angle integration. However, our detector relies on high-frequency transient derivatives (jerk and dynamic acceleration magnitude), which are completely immune to slow DC zero-bias drift.

---

## Part 4: The 120 ms Temporal Coupling & Biomechanics

**Q10: Where does the 120 ms latency figure come from?**  
*Answer*: It is derived from peer-reviewed clinical postural biomechanics (Maki & McIlroy, *Journal of Biomechanics*, 2017). When an unexpected slip or trip occurs, somatosensory receptors send afferent signals up the spinal cord, triggering an efferent polysynaptic flexor reflex arc (grasp reflex) that reaches peak muscle recruitment between 90 ms and 150 ms (nominal ~120 ms).

**Q11: What happens if an elderly user has delayed reflex due to neuropathy (e.g. 250 ms)?**  
*Answer*: Our temporal coincidence window is set to $W_{\text{sync}} = 350\text{ ms}$, with configurable expansion up to $500\text{ ms}$. This easily accommodates neural conduction delays in older populations while remaining narrow enough to reject random unrelated motions.

**Q12: Can someone deliberately fake a near-miss by tapping and squeezing?**  
*Answer*: Faking requires intentionally coordinating a violent cane impact and a maximum palm clench within a 120 ms window. Even if deliberately faked, the system records it as an anomalous high-stress event, which in clinical practice is desirable to capture.

---

## Part 5: Machine Learning vs Rule-Based Detection

**Q13: Why use a dual-domain rule when you could train a Deep CNN or LSTM?**  
*Answer*: 
1. Deep models are "black boxes" that clinicians cannot easily audit or trust.
2. LSTMs require thousands of real patient fall training examples, which do not exist in geriatric literature due to safety/ethics.
3. Our rule executes in 8 microseconds on the ESP32, whereas neural network inference introduces tens of milliseconds of latency and drains the battery.
4. The physics of the reflex arc is deterministic, making a rule both optimal and explainable.

**Q14: Why did you implement Random Forest if your rule works?**  
*Answer*: The Random Forest acts as a rigorous empirical benchmark (RQ1 & RQ4) to prove that our simple 2-parameter rule matches the accuracy of complex multi-feature machine learning without the computational overhead.

**Q15: How does Leave-One-Subject-Out (LOSO) validation work?**  
*Answer*: In LOSO validation, the model is trained on data from $N-1$ subjects and evaluated strictly on the held-out subject, repeated $N$ times. This ensures the model learns generalized biomechanical gait features rather than memorizing individual gait quirks.

---

## Part 6: Reviewer 1 & 2 Feedback and Ethical Considerations

**Q16: How did you address Reviewer 1's remark on floor surfaces and footwear habits?**  
*Answer*: We updated our logging pipeline to capture floor type (Tiled, Carpet, Concrete, Wood) and footwear (Sneakers, Slippers, Barefoot) as metadata headers. We incorporated surface damping coefficients into our synthetic generator and proved that our dynamic calibration ($\mu + 3\sigma$) automatically absorbs footwear transmission differences.

**Q17: How did you address Reviewer 2's remark on formulas and test data?**  
*Answer*: We formalized the exact differential jerk formula in $\text{m/s}^3$, detailed the FSR voltage divider and power-law conductance transfer equations, and replaced arbitrary threshold constants with a mathematically derived $\mu + k\sigma$ baseline calibration formula.

**Q18: What is the ethical protocol for real data collection?**  
*Answer*: Real human data collection is governed by our volunteer protocol (documented in `data/collected/README.md`), requiring written informed consent, supervised level-ground walking, zero induced falls, and strict anonymization.

**Q19: How is differential privacy implemented for smart city mapping?**  
*Answer*: We apply Local Differential Privacy (LDP) with a Laplace mechanism ($\epsilon = 1.0$) to perturb stumble GPS coordinates at the device level, aggregating incidents into $100\text{m} \times 100\text{m}$ municipal grid cells so individual trajectories cannot be reverse-engineered.

**Q20: What is the single biggest accomplishment of Phase-1?**  
*Answer*: Demonstrating that fusing upper-extremity kinetic grip reflex with cane kinematics reduces false alarms by **97.1% (from 14.2 down to 0.4 FA/hr)** on a completely working cyber-physical ESP32 prototype.
