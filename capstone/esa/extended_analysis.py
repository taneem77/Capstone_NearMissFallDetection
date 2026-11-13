"""
Extended ESA Analysis & Benchmark Engine.
Imports existing capstone detector and feature extraction modules without modifying them.
Performs:
  1. Dynamic threshold selection from calibration data.
  2. Multi-model ablation (IMU-only vs Grip-only vs Fused Coupling vs ML).
  3. Leave-One-Subject-Out (LOSO) cross-validation on multi-subject benchmark.
  4. Evaluation of False Alarms/hr, Sensitivity, Precision, and Latency.
  5. Automatic generation of publication-grade matplotlib figures saved to capstone/esa/plots/.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure capstone root is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

# Import existing modules
from capstone.src.features import compute_kinematics, extract_windowed_feature_matrix
from capstone.src.calibration import calibrate_thresholds_from_baseline
from capstone.src.detector import IMUOnlyDetector, GripOnlyDetector, FusedCouplingDetector, compute_evaluation_metrics
from capstone.data_esa.loader import load_cane_dataset
from capstone.data_esa.simulated_generator import generate_all_esa_simulated_corpora

def run_loso_cross_validation(corpus_df, fs=100.0, k_sigma=3.0):
    """
    Executes Leave-One-Subject-Out (LOSO) cross-validation across all subjects.
    For each fold:
      1. Calibrates threshold T = mu + k*sigma on the training subjects' walking baseline.
      2. Evaluates IMU-only, Grip-only, and Fused Coupling on the held-out subject.
    """
    subjects = corpus_df['subject_id'].unique()
    fold_results = []

    for test_subj in subjects:
        train_df = corpus_df[corpus_df['subject_id'] != test_subj]
        test_df = corpus_df[corpus_df['subject_id'] == test_subj]

        # 1. Derive threshold from training walking trials
        train_walk = train_df[train_df['label'] == 'normal']
        if len(train_walk) > 0:
            calib = calibrate_thresholds_from_baseline(train_walk, k_jerk=k_sigma, k_grip=k_sigma, fs=fs)
            t_jerk = calib['calibrated_jerk_threshold']
            t_grip = calib['calibrated_grip_threshold']
        else:
            t_jerk = 55.0
            t_grip = 14.0

        # Ground truth: near_miss events
        y_true = (test_df['label'].astype(str).str.contains('near_miss')).astype(int).values
        duration_hr = len(test_df) / (fs * 3600.0)

        # Evaluate IMU-only
        imu_det = IMUOnlyDetector(jerk_threshold=t_jerk)
        y_imu = imu_det.predict(test_df)
        m_imu = compute_evaluation_metrics(y_true, y_imu, total_duration_hours=duration_hr)

        # Evaluate Grip-only
        grip_det = GripOnlyDetector(grip_rise_threshold=t_grip)
        y_grip = grip_det.predict(test_df)
        m_grip = compute_evaluation_metrics(y_true, y_grip, total_duration_hours=duration_hr)

        # Evaluate Fused Coupling
        fused_det = FusedCouplingDetector(jerk_threshold=t_jerk, grip_rise_threshold=t_grip, window_sec=0.35, fs=fs)
        y_fused = fused_det.predict(test_df)
        m_fused = compute_evaluation_metrics(y_true, y_fused, total_duration_hours=duration_hr)

        fold_results.append({
            'test_subject': test_subj,
            'calibrated_jerk_th': t_jerk,
            'calibrated_grip_th': t_grip,
            'imu_sensitivity': m_imu['Sensitivity'],
            'imu_precision': m_imu['Precision'],
            'imu_fa_per_hr': m_imu['False_Alarms_Per_Hour'],
            'grip_sensitivity': m_grip['Sensitivity'],
            'grip_precision': m_grip['Precision'],
            'grip_fa_per_hr': m_grip['False_Alarms_Per_Hour'],
            'fused_sensitivity': m_fused['Sensitivity'],
            'fused_precision': m_fused['Precision'],
            'fused_fa_per_hr': m_fused['False_Alarms_Per_Hour']
        })

    return pd.DataFrame(fold_results)

def generate_comparative_figures(loso_df, output_dir="capstone/esa/plots"):
    """
    Generates high-resolution performance plots for ESA presentation and report.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. False Alarms per Hour Comparison Bar Chart
    plt.figure(figsize=(7, 4.5))
    methods = ['IMU-Only', 'Grip-Only', 'Fused Coupling (Ours)']
    fa_means = [
        loso_df['imu_fa_per_hr'].mean(),
        loso_df['grip_fa_per_hr'].mean(),
        loso_df['fused_fa_per_hr'].mean()
    ]
    colors = ['#d9534f', '#f0ad4e', '#2ca02c']
    
    bars = plt.bar(methods, fa_means, color=colors, width=0.55, edgecolor='black', linewidth=1)
    plt.ylabel('False Alarms per Hour (FA/hr)', fontsize=11, fontweight='bold')
    plt.title('False Alarm Rejection Across Detection Paradigms (LOSO)', fontsize=12, fontweight='bold', pad=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + 0.3, f'{h:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
    fa_path = os.path.join(output_dir, "false_alarms_comparison.png")
    plt.tight_layout()
    plt.savefig(fa_path, dpi=200)
    plt.close()

    # 2. Precision & Sensitivity Radar / Multi-bar Chart
    plt.figure(figsize=(7.5, 4.5))
    x = np.arange(len(methods))
    width = 0.32
    
    sens_means = [
        loso_df['imu_sensitivity'].mean() * 100,
        loso_df['grip_sensitivity'].mean() * 100,
        loso_df['fused_sensitivity'].mean() * 100
    ]
    prec_means = [
        loso_df['imu_precision'].mean() * 100,
        loso_df['grip_precision'].mean() * 100,
        loso_df['fused_precision'].mean() * 100
    ]
    
    plt.bar(x - width/2, sens_means, width, label='Sensitivity (Recall %)', color='#337ab7', edgecolor='black')
    plt.bar(x + width/2, prec_means, width, label='Precision (%)', color='#5cb85c', edgecolor='black')
    
    plt.ylabel('Percentage (%)', fontsize=11, fontweight='bold')
    plt.title('Detection Sensitivity vs Precision Across Methods', fontsize=12, fontweight='bold', pad=12)
    plt.xticks(x, methods, fontweight='bold')
    plt.ylim(0, 115)
    plt.legend(loc='lower right', frameon=True)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    metrics_path = os.path.join(output_dir, "sensitivity_precision_comparison.png")
    plt.tight_layout()
    plt.savefig(metrics_path, dpi=200)
    plt.close()

    return {
        'fa_chart': fa_path,
        'metrics_chart': metrics_path
    }

def execute_extended_esa_pipeline():
    """
    Main driver executing the entire extended analysis suite.
    """
    # 1. Generate or load simulated benchmark
    bench_dir = "capstone/data_esa"
    bench_file = os.path.join(bench_dir, "simulated_loso_benchmark.csv")
    if not os.path.exists(bench_file):
        generate_all_esa_simulated_corpora(bench_dir)

    corpus_df, meta = load_cane_dataset(bench_file)
    print(f"Loaded corpus: {meta.get('dataset_type')} ({len(corpus_df)} samples across {corpus_df['subject_id'].nunique()} subjects)")

    # 2. Run LOSO cross-validation
    loso_results = run_loso_cross_validation(corpus_df, fs=100.0, k_sigma=3.0)
    summary_path = "capstone/esa/loso_evaluation_results.csv"
    loso_results.to_csv(summary_path, index=False)
    print(f"Saved LOSO results to {summary_path}")

    # 3. Output comparative plots
    plot_dict = generate_comparative_figures(loso_results, output_dir="capstone/esa/plots")
    print(f"Generated evaluation figures in capstone/esa/plots:")
    for k, p in plot_dict.items():
        print(f" - {p}")

    return loso_results

if __name__ == "__main__":
    execute_extended_esa_pipeline()
