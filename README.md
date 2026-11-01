# Smart Cane — Near-Miss Fall Detection (Capstone)

IMU + grip-force sensing on a cane to detect near-miss falls.

| Layer | Where | What |
|---|---|---|
| Data layer + RQ1 baselines | `smartcane/io.py`, `windows.py`, `sources/`, `detectors/`, `rq1_baselines.py` | KFall loading, cleaning, windowing, threshold + random-forest baselines |
| Features | `smartcane/features.py` | IMU-only and fused IMU+grip window features |
| Live software (RQ3) | `src/live/` | ESP32 serial/Wi-Fi logger, event detection, event log, weekly trends, IMU–grip coupling |
| Evaluation + RQ4 | `smartcane/eval.py`, `rq4.py`, `build_features.py`, `run_all.py` | LOSO metrics, normal-only vs supervised, data-efficiency sweeps |

## Setup

    python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m pytest                                      # all tests, no dataset needed

## Quick demo (no dataset)

    python run_all.py --demo

## Full pipeline (needs the KFall dataset)

Put the dataset under `data/` (git-ignored):

    data/sensor data/SA06/S06T01R01.csv ...
    data/label data/SA06_label.xlsx ...

Then:

    python -m smartcane.rq1_baselines --sensors "data/sensor data" --labels "data/label data" --cache data/cache
    python -m smartcane.build_features
    # edit config.yaml -> data.source: features_csv
    python run_all.py

More: `docs/eval_rq4.md`.

## Live software

Synthetic-data generators and tests live in `tests/` (`make_demo_data.py`, `make_demo_wifi_data.py`).
ESP32 firmware and real sensor validation are still pending; synthetic results are not experimental results.

## Notes

- KFall is a waist-worn IMU with real falls, a stand-in for cane data until recorded.
- Live-sensor CSV format: `timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z,grip` (see `smartcane/io.py`).
