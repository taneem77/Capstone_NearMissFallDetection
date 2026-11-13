# Comprehensive Repository Audit (Read-Only Analysis)

**Project Title**: Smart Cane for Near-Fall Detection Using Cane Kinematics and Grip-Force Dynamics  
**Audit Scope**: Entire codebase, documentation, firmware, hardware specs, presentation template, and report guidelines.  
**Policy**: Read-only audit. Zero edits or renames applied to existing files.

---

## 1. Inventory & Health Table of Existing Files

| Path in Repository | Category | Current Status | Observations & Functional State |
| :--- | :--- | :---: | :--- |
| `capstone/src/__init__.py` | Code | Exists | Valid package initialization. |
| `capstone/src/signal_proc.py` | Code | Exists | Contains `butter_lowpass_filter`, `moving_average_filter`, and `validate_stream_integrity`. Operational. |
| `capstone/src/features.py` | Code | Exists | Computes acceleration magnitude, jerk vector ($da/dt$), angular velocity, grip derivative, and sliding window matrices. |
| `capstone/src/calibration.py` | Code | Exists | Contains `adc_to_force_newtons` and statistical threshold calibration ($\mu + 3\sigma$). |
| `capstone/src/detector.py` | Code | Exists | Implements `IMUOnlyDetector`, `GripOnlyDetector`, `FusedCouplingDetector`, and `MLBaselineClassifier`. |
| `capstone/src/synthetic_data.py` | Code | Exists | Generates multi-subject synthetic data and sample benchmark files. |
| `capstone/src/serial_logger.py` | Code | Exists | Ingests ESP32 streams with metadata headers and graceful simulation fallback. |
| `capstone/app/app.py` | Code / UI | Exists | Interactive 3-tab Streamlit application. Functional. |
| `capstone/hardware/firmware/SmartCane_Node.ino` | Firmware | Exists | ESP32 Arduino sketch reading MPU-6050 & FSR, dual-threshold check, outputting JSON. |
| `capstone/hardware/wiring.md` | Hardware Doc | Exists | ASCII diagram, pin mappings, and cane shaft mounting tips. |
| `capstone/hardware/bom.md` | Hardware Doc | Exists | Bill of Materials with accurate INR prices (~₹1,534). |
| `capstone/data/sample/*.csv` | Data | Exists | 7 benchmark CSV files (`walking_baseline.csv`, `near_miss_trip.csv`, etc.). |
| `capstone/data/collected/README.md` | Protocol | Exists | Volunteer protocol and consent form template. |
| `capstone/docs/problem_statement.md` | Doc | Exists | Epidemiological context, Heinrich's triangle, 3 research gaps. |
| `capstone/docs/literature_survey.md` | Doc | Exists | 10 literature survey entries and gap analysis. |
| `capstone/docs/novelty_and_comparison.md`| Doc | Exists | System comparison matrix and novelty analysis. |
| `capstone/docs/feedback_log.md` | Doc | Exists | Audit of Reviewer 1 & 2 suggestions + 15 anticipated objections. |
| `capstone/docs/domains.md` | Doc | Exists | 4 application domains (Rehab, Elderly Living, Caregiver, Smart City). |
| `capstone/docs/presentation_notes.md` | Doc | Exists | 10-minute speech allocation for Tanisha, Saatvik, Samika, Pratham + 2-min demo script. |
| `capstone/docs/viva_qa.md` | Doc | Exists | 40+ viva defense questions and 1-page formula sheet. |
| `capstone/docs/assumptions.md` | Doc | Exists | Coordinate conventions and honesty rules. |
| `capstone/docs/todo_timeline.md` | Doc | Exists | Phased milestone timeline through Phase-2. |
| `capstone/docs/report.md` | Doc | Exists | Markdown draft matching PES University report format. |
| `capstone/tests/test_suite.py` | Tests | Exists | 10 automated unit tests passing cleanly in pytest. |
| `capstone/README.md` | Doc | Exists | Overview, quickstart, Mermaid architecture, and rubric-to-evidence matrix. |
| `capstone/requirements.txt` | Config | Exists | Pinned dependencies. |
| `capstone/.gitignore`, `capstone/LICENSE` | Config | Exists | Standard ignore and academic license. |
| `ESA PPT.pptx` | Root Asset | Exists | 10-slide master presentation template. |
| `ESA Report/ESA Report/Report/*.docx` | Root Asset | Exists | Official guidelines and generated Word document. |

---

## 2. Inconsistency & Gap Audit (Names, Units, Numbers, Thresholds)

| Item / Dimension | Existing Representation | Inconsistency / Gap Identified | Required Corrective Guidance |
| :--- | :--- | :--- | :--- |
| **Output Schema Contract** | Firmware in `SmartCane_Node.ino` outputs JSON stream (`{"t":..., "ax":...}`). | Reviewer / Task specification asks for clean standard CSV output format: `time_ms, ax, ay, az, gx, gy, gz, grip_adc`. | Provide a dedicated new firmware file in `capstone/hardware_esa/` that outputs raw CSV directly, along with a compatible logger. |
| **Simulated vs Real Data Labeling** | Sample CSVs in `capstone/data/sample/` contain labels, but header rows do not explicitly state `SIMULATED` on row 1. | In academic viva defense, panels demand unmistakable explicit header indicators so simulated data cannot be mistaken for physical human trials. | The new `capstone/data_esa/simulated_generator.py` writes explicit `# DATASET_TYPE: SIMULATED` metadata headers. |
| **Threshold Inconsistencies** | Code uses $J_{\text{thresh}} = 55.0$ or $60.0\text{ m/s}^3$ and grip rise of $12.0\text{ N}$ or $800\text{ ADC}$. | Different test functions use slight threshold variations ($45.0$ vs $55.0$ vs $60.0$). While each test validates a specific scenario, the relationship between data-derived thresholds and default sliders should be unified in the new analysis module. | The new `extended_analysis.py` derives thresholds dynamically using $\mu + k\sigma$ on calibration data and tests across parameter sweeps. |
| **Unit Verification: Jerk** | Units in documentation and `features.py` are correctly $\text{m/s}^3$. | In casual conversations or early slide drafts, jerk was occasionally referred to as $\text{m/s}^2$ (acceleration) instead of rate of acceleration change ($\text{m/s}^3$). | Ensure all new slides, viva notes, and reports strictly enforce $\text{m/s}^3$. |
| **Hardware Real Data** | Real hardware node is built, but recorded physical human stumble trials cannot be ethically collected on vulnerable seniors without clinical IRB approval. | Some presentation slides could be misinterpreted as claiming 50 real clinical patient falls. | Enforce strict honesty: clearly demarcate baseline steady walking (collected on physical hardware) from perturbation benchmarks (simulated for volunteer safety). |

---

## 3. What Was Missing and Is Now Covered in `_esa` Folders

1. **Dedicated CSV-native Firmware & Serial Ingestor**: Created in `capstone/hardware_esa/` outputting exact columns: `time_ms, ax, ay, az, gx, gy, gz, grip_adc`.
2. **Unified Loader for Real and Simulated Data**: Built in `capstone/data_esa/loader.py` that transparently handles both without breaking existing code.
3. **Verified Real Citations**: Fully web-searched, verified DOI and publisher links documented in `capstone/docs_esa/literature_survey.md`.
4. **Isolated Extended Analysis & LOSO Tests**: Built in `capstone/esa/extended_analysis.py` and `capstone/tests_esa/` without touching existing tests.
5. **Fresh Copy of Presentation Deck**: Built as `capstone/esa/ESA_PPT_Final.pptx` from the root template, leaving the root template completely intact.
