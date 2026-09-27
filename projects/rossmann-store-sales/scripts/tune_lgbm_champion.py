"""Optuna fine-tune LightGBM for the champion FE1 GBDT (std ⊕ month-ahead).

Protocol:
- Expanding-window CV (2 × 42d), full-store FE1 caches
- Same hypers for standard + month-ahead; score = mean RMSPE of harmonic blend
- First trial = current baseline params
- Writes data/lgbm_champion_best_params.json
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features import CAT_COLS, harmonic_mean_preds  # noqa: E402

DATA = ROOT / "data"
SEED = 42
H = 42
N_FOLDS = 2
N_TRIALS = 25

FEATURES = CAT_COLS + [
    "CompetitionDistance",
    "Year",
    "Month",
    "WeekOfYear",
    "DayOfMonth",
    "DayOfYear",
    "CompetitionOpenMonths",
    "Promo2OpenWeeks",
    "PromoDayCount",
    "DaysSincePromoOn",
    "HolidaysThisWeek",
    "HolidaysLastWeek",
    "HolidaysNextWeek",
    "Sales_lag_7",
    "Sales_lag_14",
    "Sales_lag_28",
    "Sales_roll_mean_7",
    "Sales_roll_mean_28",
    "Sales_roll_mean_90",
    "Sales_roll_std_28",
    "Customers_lag_7",
    "Customers_roll_mean_28",
    "Store_expanding_mean",
    "StoreDow_expanding_mean",
    "StorePromo_expanding_mean",
    "Sales_trend_28",
]

BASELINE = {
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 1e-3,
    "lambda_l2": 1e-3,
}

np.random.seed(SEED)


def rmspe(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = y != 0
    return float(np.sqrt(np.mean(((y[m] - p[m]) / y[m]) ** 2)))


def expanding_folds(max_date, n_folds=N_FOLDS, horizon=H):
    folds = []
    for i in range(n_folds, 0, -1):
        vend = max_date - pd.Timedelta(days=(i - 1) * horizon)
        vstart = vend - pd.Timedelta(days=horizon - 1)
        folds.append(
            dict(
                fold=f"fold_{n_folds - i + 1}",
                train_end=vstart - pd.Timedelta(days=1),
                valid_start=vstart,
                valid_end=vend,
            )
        )
    return folds


def encode_lgb(train_X, valid_X):
    tr, va = train_X.copy(), valid_X.copy()
    for c in CAT_COLS:
        tr[c] = tr[c].astype("category")
        va[c] = pd.Categorical(va[c], categories=tr[c].cat.categories)
    return tr, va


def fit_predict(hist, valid, params: dict) -> np.ndarray:
    hist_fit = hist.loc[(hist["Open"] == 1) & (hist["Sales"] > 0)].copy()
    va_fit = valid.loc[(valid["Open"] == 1) & (valid["Sales"] > 0)].copy()
    X_tr, X_va = encode_lgb(hist_fit[FEATURES], va_fit[FEATURES])
    _, X_all = encode_lgb(hist_fit[FEATURES], valid[FEATURES])
    model = lgb.train(
        {
            "objective": "regression",
            "metric": "rmse",
            "verbosity": -1,
            "seed": SEED,
            "bagging_freq": int(params["bagging_freq"]),
            "learning_rate": float(params["learning_rate"]),
            "num_leaves": int(params["num_leaves"]),
            "min_data_in_leaf": int(params["min_data_in_leaf"]),
            "feature_fraction": float(params["feature_fraction"]),
            "bagging_fraction": float(params["bagging_fraction"]),
            "lambda_l1": float(params["lambda_l1"]),
            "lambda_l2": float(params["lambda_l2"]),
        },
        lgb.Dataset(
            X_tr, np.log1p(hist_fit["Sales"].to_numpy(float)), categorical_feature=CAT_COLS, free_raw_data=False
        ),
        num_boost_round=4000,
        valid_sets=[
            lgb.Dataset(
                X_va, np.log1p(va_fit["Sales"].to_numpy(float)), categorical_feature=CAT_COLS, free_raw_data=False
            )
        ],
        callbacks=[lgb.early_stopping(100, verbose=False), lgb.log_evaluation(0)],
    )
    pred = np.clip(np.expm1(model.predict(X_all, num_iteration=model.best_iteration)), 0, None)
    return np.where(valid["Open"].to_numpy() == 0, 0.0, pred)


def load_feat(tag: str) -> pd.DataFrame:
    path = DATA / f"train_features_{tag}.parquet"
    df = pd.read_parquet(path)
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise RuntimeError(f"{path.name} missing {missing}")
    return df


def eval_params(df_std, df_ma, folds, params: dict, *, with_ma: bool = True) -> tuple[float, list[float]]:
    scores = []
    for f in folds:
        hist_std = df_std.loc[df_std.Date <= f["train_end"]]
        valid_std = (
            df_std.loc[(df_std.Date >= f["valid_start"]) & (df_std.Date <= f["valid_end"])]
            .sort_values(["Store", "Date"])
            .reset_index(drop=True)
        )
        p_std = fit_predict(hist_std, valid_std, params)
        if with_ma:
            hist_ma = df_ma.loc[df_ma.Date <= f["train_end"]]
            valid_ma = (
                df_ma.loc[(df_ma.Date >= f["valid_start"]) & (df_ma.Date <= f["valid_end"])]
                .sort_values(["Store", "Date"])
                .reset_index(drop=True)
            )
            p_ma = fit_predict(hist_ma, valid_ma, params)
            p = harmonic_mean_preds([p_std, p_ma])
            y = valid_std["Sales"].to_numpy(float)
        else:
            p = p_std
            y = valid_std["Sales"].to_numpy(float)
        scores.append(rmspe(y, p))
    return float(np.mean(scores)), scores


def main():
    print("Loading FE1 feature caches...", flush=True)
    df_std = load_feat("standard")
    df_ma = load_feat("month_ahead")
    folds = expanding_folds(df_std["Date"].max())
    print(f"folds={[ (f['fold'], str(f['valid_start'].date()), str(f['valid_end'].date())) for f in folds ]}", flush=True)

    # Search objective: std-only (2× faster). Final report uses harmonic std⊕ma.
    print("\nBaseline (std-only search metric)...", flush=True)
    base_search, _ = eval_params(df_std, df_ma, folds, BASELINE, with_ma=False)
    print(f"  baseline std RMSPE={base_search:.5f}", flush=True)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 31, 255),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 20, 200),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
            "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
            "lambda_l1": trial.suggest_float("lambda_l1", 1e-3, 10.0, log=True),
            "lambda_l2": trial.suggest_float("lambda_l2", 1e-3, 10.0, log=True),
        }
        mean, fold_scores = eval_params(df_std, df_ma, folds, params, with_ma=False)
        trial.set_user_attr("fold_scores", fold_scores)
        print(
            f"  trial {trial.number:02d} std_RMSPE={mean:.5f} "
            f"leaves={params['num_leaves']} lr={params['learning_rate']:.4f}",
            flush=True,
        )
        # Incremental checkpoint so a crash mid-run is recoverable
        row = dict(number=trial.number, std_rmspe=mean, **params)
        pd.DataFrame([row]).to_csv(
            DATA / "lgbm_champion_tune_trials.csv",
            mode="a",
            header=not (DATA / "lgbm_champion_tune_trials.csv").exists(),
            index=False,
        )
        return mean

    trials_path = DATA / "lgbm_champion_tune_trials.csv"
    if trials_path.exists():
        trials_path.unlink()

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=SEED),
        storage=f"sqlite:///{DATA / 'lgbm_champion_optuna.db'}",
        study_name="lgbm_champion",
        load_if_exists=True,
    )
    # Only enqueue baseline when starting fresh
    if len(study.trials) == 0:
        study.enqueue_trial(BASELINE)
    remaining = max(0, N_TRIALS - len([t for t in study.trials if t.state.name == "COMPLETE"]))
    print(f"Optuna: {len(study.trials)} existing trials, running {remaining} more...", flush=True)
    if remaining:
        study.optimize(objective, n_trials=remaining, show_progress_bar=False)

    best = study.best_trial
    # Save params immediately before the slower harmonic re-eval
    interim = {
        "best_std_rmspe": best.value,
        "best_params": best.params,
        "n_trials": len(study.trials),
        "best_rmspe": best.value,
    }
    (DATA / "lgbm_champion_best_params.json").write_text(json.dumps(interim, indent=2))
    print(f"Checkpointed best std params → lgbm_champion_best_params.json", flush=True)

    print("\nFinal harmonic eval (baseline vs best)...", flush=True)
    base_harm, base_folds = eval_params(df_std, df_ma, folds, BASELINE, with_ma=True)
    best_harm, best_folds = eval_params(df_std, df_ma, folds, best.params, with_ma=True)
    print(f"  baseline harmonic={base_harm:.5f} folds={['%.5f'%s for s in base_folds]}", flush=True)
    print(f"  tuned    harmonic={best_harm:.5f} folds={['%.5f'%s for s in best_folds]}", flush=True)

    out = {
        "baseline_std_rmspe": base_search,
        "baseline_harmonic_rmspe": base_harm,
        "best_std_rmspe": best.value,
        "best_harmonic_rmspe": best_harm,
        "best_params": best.params,
        "best_fold_scores_std": best.user_attrs.get("fold_scores"),
        "best_fold_scores_harmonic": best_folds,
        "n_trials": len(study.trials),
        "improvement_harmonic": base_harm - best_harm,
        # keep key used by submission script
        "best_rmspe": best_harm,
        "baseline_rmspe": base_harm,
        "baseline_params": BASELINE,
    }
    path = DATA / "lgbm_champion_best_params.json"
    path.write_text(json.dumps(out, indent=2))
    print(
        f"\nBEST harmonic RMSPE={best_harm:.5f} "
        f"(baseline {base_harm:.5f}, Δ={out['improvement_harmonic']:+.5f})",
        flush=True,
    )
    print(json.dumps(best.params, indent=2), flush=True)
    print(f"Saved {path}", flush=True)

    hist = []
    for t in study.trials:
        if t.value is None:
            continue
        row = dict(number=t.number, std_rmspe=t.value, **t.params)
        hist.append(row)
    pd.DataFrame(hist).sort_values("std_rmspe").to_csv(DATA / "lgbm_champion_tune_trials.csv", index=False)


if __name__ == "__main__":
    main()
