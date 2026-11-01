# Evaluation and RQ4

## Run

    pip install -r requirements.txt
    python run_all.py --demo
    python -m pytest tests/test_eval.py

Results go to `results/`.

## Real data

Set `data.source: features_csv` in `config.yaml` and put a csv at `data/features.csv` with columns
`subject`, `label` (0 normal, 1 near-miss) and one column per feature. Rows must be in time order within each subject.

## Metrics

Leave-one-subject-out. Sensitivity, specificity, precision, f1, and false alarms per hour.
Consecutive false positive windows are merged into one alarm before counting per hour, since windows overlap.

## RQ4

Normal-only detector (isolation forest or one-class svm, trained on label 0 windows only) against a supervised random forest,
both under the same LOSO folds. Two sweeps: supervised with fewer labeled near-miss windows, normal-only with less normal data.
