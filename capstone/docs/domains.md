# Multi-Domain Applicability & Societal Impact

The Smart Cane cyber-physical architecture addresses critical safety and diagnostic challenges across four major societal and clinical domains.

---

## 1. Domain 1: Healthcare & Post-Stroke Rehabilitation

* **Primary End-Users**: Physiotherapists, rehabilitation clinicians, post-stroke and orthopedic surgery patients.
* **Operational Mechanism**:
  During post-stroke gait re-education, patients transition from parallel bars to single-point canes. Therapists currently assess recovery using periodic, qualitative visual scoring (e.g., Berg Balance Scale, Timed Up and Go). The Smart Cane transforms the cane into an objective continuous diagnostic tool. By logging subtle changes in recovery latency ($\Delta t$) and weekly near-miss frequency, the system detects whether a patient's neuromuscular reflex is improving or if compensatory gait fatigue is setting in.
* **Telemetry Data & Output**:
  - Longitudinal stumble frequency curves.
  - Reflex response latency trends (tracking recovery time down from 250 ms toward healthy 120 ms).
  - Quantitative gait symmetry and stance-time variance reports for clinical case conferences.

---

## 2. Domain 2: Elderly Assisted Living & Geriatric Care Facilities

* **Primary End-Users**: Care facility wardens, geriatric nurses, senior living residents.
* **Operational Mechanism**:
  Assisted living facilities struggle with high staff-to-resident ratios, leading to unobserved stumbles in resident rooms or corridors. When a resident experiences a near-miss stumble, the on-device ESP32 immediately registers the event and transmits an encrypted local Wi-Fi telemetry packet to the nursing station dashboard. Nurses can proactively check on the resident, inspect for floor hazards (spilled water, curled rugs), or review medications causing sudden dizziness (orthostatic hypotension).
* **Telemetry Data & Output**:
  - Real-time room location beacon alerts.
  - Automated weekly incident heatmaps across facility corridors and dining halls.
  - Objective clinical data logs replacing subjective resident recall.

---

## 3. Domain 3: Remote Caregiver Tele-Monitoring & Aging-in-Place

* **Primary End-Users**: Adult children, family caregivers, independent-living elderly individuals.
* **Operational Mechanism**:
  Senior citizens living independently often underreport stumbles to their adult children due to fear of losing independence or being moved to nursing homes. The Smart Cane aggregates daily mobility data and syncs summary metrics via BLE to a companion smartphone app. The app generates a peaceful "Green / Amber / Red" fall-risk status without invading the senior's visual privacy (no cameras or microphones).
* **Telemetry Data & Output**:
  - Daily mobility volume (active hours, strides taken).
  - Pre-impact stumble alerts sent via SMS/Push notification to family members.
  - Monthly fall-risk degradation indices enabling timely clinical intervention.

---

## 4. Domain 4: Smart-City Municipal Hazard Mapping (Local Differential Privacy)

* **Primary End-Users**: Municipal urban planners, public works departments, smart-city administrators.
* **Operational Mechanism**:
  Urban pedestrian infrastructure frequently harbors unmapped hazards: broken sidewalk pavers, sudden curb drops, uneven paving stones, and slippery access ramps. When smart cane users navigate public sidewalks, localized stumble events are geotagged via companion smartphone GPS. To strictly safeguard user privacy, data is perturbed at the edge using **Local Differential Privacy (LDP)** with Laplacian noise ($\epsilon = 1.0$), aggregating stumble coordinates into $100\text{m} \times 100\text{m}$ spatial grid clusters.
* **Telemetry Data & Output**:
  - Municipal "Sidewalk Hazard Index" heatmaps highlighting infrastructure defects.
  - Data-driven public works prioritization for pavement repair and ADA ramp retrofitting.
  - Measurable reduction in community pedestrian injury claims and emergency response costs.
