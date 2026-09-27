#!/usr/bin/env python3
"""Reproduce the champion Rossmann submission end-to-end.

Champion
--------
80% LightGBM (FE1 features; standard ⊕ month-ahead harmonic mean)
+ 20% Chronos-2 zero-shot with known-future covariates
(Promo, SchoolHoliday, Open, DayOfWeek).

Outputs
-------
- data/submission_champion.csv
- data/sample_submission.csv  (same file; Kaggle upload format)

Usage
-----
From the project root:

    # optional: Optuna-tune LightGBM (writes data/lgbm_champion_best_params.json)
    python scripts/tune_lgbm_champion.py

    # build submission (uses tuned params if present, else defaults)
    python scripts/reproduce_champion.py

Requires: train.csv, test.csv, store.csv under data/; packages in requirements.txt
plus `chronos-forecasting` / torch for Chronos-2.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--tune",
        action="store_true",
        help="Run Optuna LightGBM tuning before submission (slow).",
    )
    ap.add_argument(
        "--skip-if-exists",
        action="store_true",
        help="Skip if data/submission_champion.csv already exists.",
    )
    args = ap.parse_args()

    for name in ("train.csv", "test.csv", "store.csv"):
        if not (DATA / name).exists():
            print(f"ERROR: missing data/{name}", file=sys.stderr)
            return 1

    out = DATA / "submission_champion.csv"
    if args.skip_if_exists and out.exists():
        print(f"Exists: {out} — skipping (--skip-if-exists).")
        return 0

    if args.tune:
        print("=== Optuna LightGBM tune ===", flush=True)
        r = subprocess.run([sys.executable, "-u", str(SCRIPTS / "tune_lgbm_champion.py")], cwd=ROOT)
        if r.returncode != 0:
            return r.returncode

    params = DATA / "lgbm_champion_best_params.json"
    if params.exists():
        payload = json.loads(params.read_text())
        print(
            f"Using tuned LightGBM params (harmonic CV RMSPE≈{payload.get('best_rmspe')})",
            flush=True,
        )
    else:
        print("No lgbm_champion_best_params.json — submission uses default LightGBM hypers.", flush=True)
        print("  Tip: python scripts/reproduce_champion.py --tune", flush=True)

    print("=== Champion submission (GBDT 80% ⊕ Chronos-2 20%) ===", flush=True)
    r = subprocess.run([sys.executable, "-u", str(SCRIPTS / "run_champion_submission.py")], cwd=ROOT)
    if r.returncode != 0:
        return r.returncode

    if out.exists():
        import pandas as pd

        sub = pd.read_csv(out)
        print(
            f"\nOK → {out}\n"
            f"  rows={len(sub):,}  mean Sales={sub.Sales.mean():.1f}  "
            f"zeros={(sub.Sales == 0).sum()}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
