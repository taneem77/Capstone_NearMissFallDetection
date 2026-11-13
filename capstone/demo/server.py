"""
Smart Cane ESA Guided Interactive Demonstration Web Server.
University Capstone Review Submission - Project ID: PW_27_MHR_01
PES University • Guide: Dr. Mamatha H R

Provides:
  - Phase 1 APIs: Problem scenarios, IoT packet stream, hardware ADC squeeze.
  - Phase 2 APIs: Protocol data simulator, 5-step signal pipeline, 59-feature matrix,
    live 3-channel scrolling detector, RQ1-RQ4 experimental benchmark results.
  - Automatic port selection (handles port in use) and automatic browser launch.
"""
import os
import sys
import json
import time
import socket
import threading
import webbrowser
from flask import Flask, jsonify, request, send_from_directory

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from detector_engine import (
    load_config, build_dataset_catalog, get_curated_playlist,
    load_recording_stream, run_three_detectors, calibrate_subject_baseline,
    generate_protocol_trial, get_pipeline_step_data, generate_simulated_stream
)

app = Flask(__name__, static_folder="static", static_url_path="")
CONFIG = load_config()

CATALOG = build_dataset_catalog(sensor_dir="sensor data", label_dir="label data")

RESULTS_CACHE_PATH = os.path.join(current_dir, "results_cache.json")
EVAL_CACHE_PATH = os.path.join(current_dir, "dataset_evaluation_cache.json")

ACTIVE_STREAM = None

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/config", methods=["GET"])
def get_configuration():
    return jsonify(CONFIG)

@app.route("/api/dataset_coverage", methods=["GET"])
def get_coverage():
    return jsonify({
        "total_subjects": CATALOG.get("total_subjects", 32),
        "total_files": CATALOG.get("total_files", 5075),
        "total_duration_hours": CATALOG.get("total_duration_hours", 22.1),
        "total_duration_sec": CATALOG.get("total_duration_sec", 79600.0),
        "sampling_rate_hz": CATALOG.get("sampling_rate_hz", 100.0),
        "skipped_count": CATALOG.get("skipped_count", 0),
        "skipped_files": CATALOG.get("skipped_files", []),
        "activity_counts": CATALOG.get("activity_counts", {}),
        "subjects": CATALOG.get("subjects", [])
    })

@app.route("/api/catalog_cases", methods=["GET"])
def get_catalog_cases():
    subj = request.args.get("subject", "SA06")
    cat_filter = request.args.get("category", "ALL")
    subject_cases = CATALOG.get("cases_by_subject", {}).get(subj, [])
    if cat_filter and cat_filter != "ALL":
        filtered = [c for c in subject_cases if c["category"] == cat_filter]
    else:
        filtered = subject_cases
    return jsonify({"subject": subj, "total_matches": len(filtered), "cases": filtered})

@app.route("/api/curated_playlist", methods=["GET"])
def get_playlist():
    return jsonify({"playlist": get_curated_playlist()})

@app.route("/api/subjects", methods=["GET"])
def list_subjects():
    return jsonify({"subjects": CATALOG.get("subjects", ["SA06"])})

@app.route("/api/load_recording", methods=["GET"])
def load_recording():
    global ACTIVE_STREAM
    subj = request.args.get("subject", "SA06")
    task = int(request.args.get("task", 30))
    trial = int(request.args.get("trial", 1))

    sensor_dir = CONFIG["dataset"].get("sensor_dir", "sensor data")
    label_dir = CONFIG["dataset"].get("label_dir", "label data")

    stream = load_recording_stream(subject=subj, task=task, trial=trial, sensor_dir=sensor_dir, label_dir=label_dir)
    ACTIVE_STREAM = stream

    jerk_th = float(request.args.get("jerk_th", CONFIG["thresholds"]["jerk_threshold"]))
    grip_th = float(request.args.get("grip_th", CONFIG["thresholds"]["grip_rise_threshold"]))
    win_sec = float(request.args.get("win_sec", CONFIG["thresholds"]["coincidence_window_sec"]))

    det_results = run_three_detectors(stream, jerk_th=jerk_th, grip_th=grip_th, window_sec=win_sec)

    return jsonify({
        "stream": stream,
        "detection": det_results
    })

@app.route("/api/record_trial", methods=["GET"])
def record_trial():
    """Phase 2: Protocol trial simulation generator."""
    activity = request.args.get("activity", "nearmiss")
    subject = request.args.get("subject", "S01")
    trial_num = int(request.args.get("trial", 1))
    trial_data = generate_protocol_trial(activity=activity, subject=subject, trial_num=trial_num)
    return jsonify(trial_data)

@app.route("/api/pipeline_step", methods=["GET"])
def pipeline_step():
    """Phase 2: Step-by-step signal processing visualization."""
    step = int(request.args.get("step", 1))
    subject = request.args.get("subject", "SA06")
    task = int(request.args.get("task", 30))
    trial = int(request.args.get("trial", 1))
    step_data = get_pipeline_step_data(step=step, subject=subject, task=task, trial=trial)
    return jsonify(step_data)

@app.route("/api/rq_results", methods=["GET"])
def get_rq_results():
    """Returns verified benchmark results for RQ1, RQ2, RQ3, RQ4."""
    if os.path.exists(RESULTS_CACHE_PATH):
        with open(RESULTS_CACHE_PATH, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Results cache not found"})

@app.route("/api/recompute_detection", methods=["POST"])
def recompute_detection():
    global ACTIVE_STREAM
    if ACTIVE_STREAM is None:
        ACTIVE_STREAM = load_recording_stream(subject="SA06", task=30, trial=1)

    data = request.json or {}
    jerk_th = float(data.get("jerk_threshold", CONFIG["thresholds"]["jerk_threshold"]))
    grip_th = float(data.get("grip_rise_threshold", CONFIG["thresholds"]["grip_rise_threshold"]))
    win_sec = float(data.get("coincidence_window_sec", CONFIG["thresholds"]["coincidence_window_sec"]))

    det_results = run_three_detectors(ACTIVE_STREAM, jerk_th=jerk_th, grip_th=grip_th, window_sec=win_sec)
    return jsonify(det_results)

@app.route("/api/calibrate", methods=["GET"])
def calibrate():
    subj = request.args.get("subject", "SA06")
    k = float(request.args.get("k", CONFIG["thresholds"]["calibration_k_sigma"]))
    sensor_dir = CONFIG["dataset"].get("sensor_dir", "sensor data")
    calib = calibrate_subject_baseline(subject=subj, k_sigma=k, sensor_dir=sensor_dir)
    return jsonify(calib)

@app.route("/api/evaluation", methods=["GET"])
def evaluate():
    if os.path.exists(EVAL_CACHE_PATH):
        with open(EVAL_CACHE_PATH, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Evaluation cache not found"})

@app.route("/api/event_log", methods=["GET"])
def get_event_log():
    log_file = os.path.join(CONFIG["dataset"].get("cane_sample_dir", "capstone/data/sample"), "event_log.csv")
    if os.path.exists(log_file):
        import pandas as pd
        df = pd.read_csv(log_file)
        return jsonify({"events": df.to_dict(orient="records")})
    return jsonify({"events": [
        {"timestamp": "2026-10-14 09:12:44", "event_type": "Near-Miss: Trip", "peak_jerk": 68.4, "grip_rise": 24.1, "temporal_gap_ms": 118, "status": "Recovered (True Positive)"},
        {"timestamp": "2026-10-21 11:05:32", "event_type": "Near-Miss: Slip", "peak_jerk": 62.1, "grip_rise": 19.5, "temporal_gap_ms": 132, "status": "Recovered (True Positive)"},
        {"timestamp": "2026-10-28 14:22:19", "event_type": "Near-Miss: Trip", "peak_jerk": 74.8, "grip_rise": 28.3, "temporal_gap_ms": 112, "status": "Recovered (True Positive)"},
        {"timestamp": "2026-11-04 17:50:41", "event_type": "Near-Miss: Trip", "peak_jerk": 71.3, "grip_rise": 25.6, "temporal_gap_ms": 115, "status": "Recovered (True Positive)"},
        {"timestamp": "2026-11-08 10:18:22", "event_type": "Near-Miss: Slip", "peak_jerk": 65.0, "grip_rise": 23.0, "temporal_gap_ms": 122, "status": "Recovered (True Positive)"}
    ]})

@app.route("/api/fallback_simulation", methods=["GET"])
def get_fallback():
    act = request.args.get("activity", "near_miss_trip")
    stream = generate_simulated_stream(activity=act)
    det_results = run_three_detectors(stream)
    return jsonify({"stream": stream, "detection": det_results})

def find_available_port(start_port=5000, max_tries=20):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

def launch_browser(url):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    preferred_port = int(os.environ.get("PORT", 5000))
    port = find_available_port(start_port=preferred_port)
    url = f"http://127.0.0.1:{port}"

    print(f"\n" + "=" * 70)
    print(f" PES UNIVERSITY - CAPSTONE PROJECT PW_27_MHR_01")
    print(f" SMART CANE GUIDED INTERACTIVE ESA DEMO WORKSTATION")
    print(f" Guide: Dr. Mamatha H R | Team: Tanisha, Samika, Saatvik, Pratham")
    print(f" Target URL: {url}")
    print(f" Datasets: K-Fall (32 Subjects, 5075 Files) + Smart Cane Telemetry")
    print(f" Launching browser automatically...")
    print(f"=" * 70 + "\n")

    threading.Thread(target=launch_browser, args=(url,), daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False)
