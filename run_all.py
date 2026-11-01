import argparse
from pathlib import Path

import yaml

from smartcane.dataset import build_dataset
from smartcane.eval import write_results
from smartcane.rq4 import run_rq4


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.demo:
        cfg["data"]["source"] = "demo"

    X, y, groups, feature_names = build_dataset(cfg)
    print(f"data: {X.shape[0]} windows, {X.shape[1]} features, {len(set(groups))} subjects, {int(y.sum())} near-miss windows")

    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    rq4 = run_rq4(X, y, groups, cfg)

    for name, res in rq4["headline"].items():
        write_results(res, out_dir, f"rq4_{name}")
    rq4["headline_table"].to_csv(out_dir / "rq4_headline.csv", index=False)
    rq4["supervised_label_sweep"].to_csv(out_dir / "rq4_supervised_label_sweep.csv", index=False)
    rq4["normal_only_data_sweep"].to_csv(out_dir / "rq4_normal_only_data_sweep.csv", index=False)

    print("\nRQ4 headline (leave-one-subject-out)")
    print(rq4["headline_table"].round(3).to_string(index=False))
    print("\nsupervised: labeled near-miss fraction sweep")
    print(rq4["supervised_label_sweep"].round(3).to_string(index=False))
    print("\nnormal-only: normal data fraction sweep")
    print(rq4["normal_only_data_sweep"].round(3).to_string(index=False))
    print(f"\nresults written to {out_dir}/")


if __name__ == "__main__":
    main()
