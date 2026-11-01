# Evaluation and RQ4

Leave-one-subject-out (LOSO). Metrics: sensitivity, specificity, precision, F1, false alarms per hour.
Consecutive false-positive windows are merged into one alarm before counting per hour, because windows overlap.

**RQ4:** normal-only detector (isolation forest or one-class SVM, trained on label-0 windows only) vs a supervised
random forest, same LOSO folds. Two sweeps: supervised with fewer labelled near-miss windows; normal-only with less normal data.

## Run

    python run_all.py --demo                      # synthetic data, ~1 min, no dataset needed

    python -m smartcane.build_features            # KFall -> data/features.csv   (needs the dataset)
    # set data.source: features_csv in config.yaml
    python run_all.py

Results land in `results/` (headline table, both sweeps, per-subject CSV/JSON).

## features.csv format

`subject`, `label` (0 normal / 1 near-miss), then one column per feature. Optional metadata columns
(`task`, `trial`, `t_start`, `t_end`) are ignored as features. Rows must be time-ordered within each subject.
`window.stride_sec` in `config.yaml` must match what the features were built with.
