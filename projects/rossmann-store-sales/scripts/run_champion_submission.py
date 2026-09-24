"""Generate Kaggle submission with the champion model.

Champion: 80% LightGBM (FE1 standard ⊕ month-ahead harmonic)
         + 20% Chronos-2 covariates
Trains on ALL train.csv rows; predicts data/test.csv → data/submission_champion.csv
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features import (  # noqa: E402
    CAT_COLS,
    build_feature_frame,
    harmonic_mean_preds,
)

DATA = ROOT / "data"
SEED = 42
CONTEXT = 512
BATCH = 32
STORE_CHUNK = 64
BLEND_W_GBDT = 0.8
FUTR = ["Promo", "SchoolHoliday", "Open", "DayOfWeek"]
PARAMS_PATH = DATA / "lgbm_champion_best_params.json"

DEFAULT_LGBM = {
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 0.0,
    "lambda_l2": 0.0,
}


def load_lgbm_params() -> dict:
    if PARAMS_PATH.exists():
        payload = json.loads(PARAMS_PATH.read_text())
        params = dict(DEFAULT_LGBM)
        params.update(payload.get("best_params") or {})
        print(
            f"  using tuned LightGBM params from {PARAMS_PATH.name} "
            f"(CV RMSPE={payload.get('best_rmspe')})",
            flush=True,
        )
        return params
    print("  using default LightGBM params", flush=True)
    return dict(DEFAULT_LGBM)

# FE1 feature set used by the full-store Chronos stack champion
# (matches data/train_features_standard.parquet — not FE2 / winner packs)
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

np.random.seed(SEED)


def encode_lgb(train_X, pred_X):
    tr, pr = train_X.copy(), pred_X.copy()
    for c in CAT_COLS:
        tr[c] = tr[c].astype("category")
        pr[c] = pd.Categorical(pr[c], categories=tr[c].cat.categories)
    return tr, pr


def lgbm_train_params(hp: dict) -> dict:
    return {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": float(hp["learning_rate"]),
        "num_leaves": int(hp["num_leaves"]),
        "min_data_in_leaf": int(hp["min_data_in_leaf"]),
        "feature_fraction": float(hp["feature_fraction"]),
        "bagging_fraction": float(hp["bagging_fraction"]),
        "bagging_freq": int(hp["bagging_freq"]),
        "lambda_l1": float(hp.get("lambda_l1", 0.0)),
        "lambda_l2": float(hp.get("lambda_l2", 0.0)),
        "verbosity": -1,
        "seed": SEED,
    }


def fit_lgbm_full(train_df: pd.DataFrame, pred_df: pd.DataFrame, hp: dict | None = None) -> np.ndarray:
    """Train on all open/positive train rows; pick rounds via last-42d ES, refit on all."""
    hp = hp or load_lgbm_params()
    fit = train_df.loc[(train_df["Open"] == 1) & (train_df["Sales"] > 0)].copy()
    max_date = fit["Date"].max()
    es_start = max_date - pd.Timedelta(days=41)
    tr = fit.loc[fit["Date"] < es_start]
    va = fit.loc[fit["Date"] >= es_start]
    if len(va) < 1000:
        tr, va = fit.iloc[: int(len(fit) * 0.95)], fit.iloc[int(len(fit) * 0.95) :]

    X_tr, X_va = encode_lgb(tr[FEATURES], va[FEATURES])
    dtrain = lgb.Dataset(
        X_tr, np.log1p(tr["Sales"].to_numpy(float)), categorical_feature=CAT_COLS, free_raw_data=False
    )
    dvalid = lgb.Dataset(
        X_va, np.log1p(va["Sales"].to_numpy(float)), categorical_feature=CAT_COLS, free_raw_data=False
    )
    train_params = lgbm_train_params(hp)
    probe = lgb.train(
        train_params,
        dtrain,
        num_boost_round=4000,
        valid_sets=[dvalid],
        callbacks=[lgb.early_stopping(100, verbose=False), lgb.log_evaluation(0)],
    )
    n_rounds = max(int(probe.best_iteration), 200)
    print(f"  LightGBM best_iteration={n_rounds} (from last-~42d probe)", flush=True)

    # Refit on ALL training rows with fixed rounds (no early stopping)
    X_all_tr, X_pred = encode_lgb(fit[FEATURES], pred_df[FEATURES])
    dtrain_full = lgb.Dataset(
        X_all_tr, np.log1p(fit["Sales"].to_numpy(float)), categorical_feature=CAT_COLS, free_raw_data=False
    )
    final = lgb.train(
        train_params,
        dtrain_full,
        num_boost_round=n_rounds,
    )
    pred = np.clip(np.expm1(final.predict(X_pred)), 0, None)
    open_arr = pred_df["Open"].fillna(1).to_numpy()
    return np.where(open_arr == 0, 0.0, pred)


def build_train_test_features(month_ahead: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build FE frames with train history + test calendar; test Sales/Customers = NaN."""
    train = pd.read_csv(DATA / "train.csv", low_memory=False, parse_dates=["Date"])
    test = pd.read_csv(DATA / "test.csv", low_memory=False, parse_dates=["Date"])
    store = pd.read_csv(DATA / "store.csv")
    train = train.merge(store, on="Store", how="left")
    test = test.merge(store, on="Store", how="left")
    test["Open"] = test["Open"].fillna(1).astype(int)
    test_ids = test[["Id", "Store", "Date"]].copy()

    train = train.copy()
    train["Id"] = -1
    test = test.copy()
    test["Sales"] = np.nan
    test["Customers"] = np.nan
    # Align columns
    for c in train.columns:
        if c not in test.columns:
            test[c] = np.nan
    combined = pd.concat([train, test[train.columns]], ignore_index=True, sort=False)
    print(f"  building features month_ahead={month_ahead} on {len(combined):,} rows...", flush=True)
    feat = build_feature_frame(combined, month_ahead=month_ahead)
    missing = [c for c in FEATURES if c not in feat.columns]
    if missing:
        raise RuntimeError(f"Missing champion features: {missing}")

    tr = feat.loc[feat["Id"] == -1].copy()
    te = feat.loc[feat["Id"] != -1].copy()
    te = test_ids.merge(te.drop(columns=["Id"], errors="ignore"), on=["Store", "Date"], how="left")
    return tr, te


def prep_hist(d: pd.DataFrame) -> pd.DataFrame:
    o = d.rename(columns={"Store": "item_id", "Date": "timestamp", "Sales": "target"})
    return o[["item_id", "timestamp", "target", *FUTR]].sort_values(["item_id", "timestamp"])


def prep_fut(d: pd.DataFrame) -> pd.DataFrame:
    o = d.rename(columns={"Store": "item_id", "Date": "timestamp"})
    return o[["item_id", "timestamp", *FUTR]].sort_values(["item_id", "timestamp"])


def predict_chronos(pipe: Chronos2Pipeline, hist: pd.DataFrame, test: pd.DataFrame, horizon: int) -> np.ndarray:
    stores = test["Store"].drop_duplicates().tolist()
    parts = []
    n = len(stores)
    cut = test["Date"].min() - pd.Timedelta(days=CONTEXT + 14)
    hist = hist.loc[hist["Date"] >= cut]
    for i in range(0, n, STORE_CHUNK):
        chunk = stores[i : i + STORE_CHUNK]
        h = hist.loc[hist["Store"].isin(chunk)]
        v = test.loc[test["Store"].isin(chunk)].copy()
        # Per-store horizons may be identical (same calendar); use global horizon
        out = pipe.predict_df(
            prep_hist(h),
            future_df=prep_fut(v),
            prediction_length=horizon,
            quantile_levels=[0.5],
            batch_size=BATCH,
            context_length=CONTEXT,
            cross_learning=True,
            freq="D",
        )
        pred_col = "0.5" if "0.5" in out.columns else "predictions"
        merged = v[["Store", "Date", "Open"]].merge(
            out.rename(columns={"item_id": "Store", "timestamp": "Date"})[["Store", "Date", pred_col]],
            on=["Store", "Date"],
            how="left",
        )
        pred = merged[pred_col].fillna(merged[pred_col].median()).to_numpy(float)
        pred = np.clip(pred, 0, None)
        open_arr = merged["Open"].fillna(1).to_numpy()
        pred = np.where(open_arr == 0, 0.0, pred)
        parts.append(pd.DataFrame({"Store": merged.Store, "Date": merged.Date, "pred": pred}))
        print(f"    chronos stores {min(i + STORE_CHUNK, n)}/{n}", flush=True)
    out = pd.concat(parts, ignore_index=True)
    merged = test[["Store", "Date"]].merge(out, on=["Store", "Date"], how="left")
    return merged["pred"].fillna(merged["pred"].median()).to_numpy(float)


def main():
    print("Champion submission: 80% GBDT (std⊕MA harmonic) + 20% Chronos-2", flush=True)
    print("Training on ALL train.csv; predicting test.csv", flush=True)

    print("\n=== Features (standard) ===", flush=True)
    tr_std, te_std = build_train_test_features(month_ahead=False)
    print("\n=== Features (month-ahead) ===", flush=True)
    tr_ma, te_ma = build_train_test_features(month_ahead=True)

    # Align test rows by Id
    te_std = te_std.sort_values("Id").reset_index(drop=True)
    te_ma = te_ma.sort_values("Id").reset_index(drop=True)
    assert te_std["Id"].equals(te_ma["Id"])

    hp = load_lgbm_params()
    print("\n=== LightGBM standard (full train) ===", flush=True)
    p_std = fit_lgbm_full(tr_std, te_std, hp=hp)
    print("\n=== LightGBM month-ahead (full train) ===", flush=True)
    p_ma = fit_lgbm_full(tr_ma, te_ma, hp=hp)
    p_gbdt = harmonic_mean_preds([p_std, p_ma])
    print(f"  GBDT pred mean={p_gbdt.mean():.1f} (open days)", flush=True)

    # Chronos: raw train + test calendar
    train = pd.read_csv(DATA / "train.csv", low_memory=False, parse_dates=["Date"])
    test_raw = pd.read_csv(DATA / "test.csv", low_memory=False, parse_dates=["Date"])
    store = pd.read_csv(DATA / "store.csv")
    train = train.merge(store, on="Store", how="left")
    test_raw = test_raw.merge(store, on="Store", how="left")
    test_raw["Open"] = test_raw["Open"].fillna(1).astype(int)
    test_raw = test_raw.sort_values("Id").reset_index(drop=True)
    assert test_raw["Id"].equals(te_std["Id"])

    horizon = int((test_raw["Date"].max() - test_raw["Date"].min()).days) + 1
    print(f"\n=== Chronos-2 covariates (horizon={horizon}d, all train history) ===", flush=True)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"  device={device}", flush=True)
    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map=device)
    # Only stores that appear in test
    test_stores = test_raw["Store"].unique()
    hist = train.loc[train["Store"].isin(test_stores)].sort_values(["Store", "Date"])
    p_ch = predict_chronos(pipe, hist, test_raw, horizon=horizon)
    print(f"  Chronos pred mean={p_ch.mean():.1f}", flush=True)

    blend = BLEND_W_GBDT * p_gbdt + (1.0 - BLEND_W_GBDT) * p_ch
    open_arr = test_raw["Open"].to_numpy()
    blend = np.where(open_arr == 0, 0.0, blend)
    blend = np.clip(blend, 0, None)

    sub = pd.DataFrame({"Id": test_raw["Id"].astype(int), "Sales": blend})
    out_path = DATA / "submission_champion.csv"
    sub.to_csv(out_path, index=False)
    # Also overwrite sample_submission.csv as requested "create a sample_submission"
    sample_path = DATA / "sample_submission.csv"
    sub.to_csv(sample_path, index=False)
    print(f"\nWrote {out_path} and {sample_path}", flush=True)
    print(f"  rows={len(sub):,}  Sales mean={sub.Sales.mean():.1f}  "
          f"zeros={(sub.Sales==0).sum()}  min={sub.Sales.min():.1f} max={sub.Sales.max():.1f}", flush=True)


if __name__ == "__main__":
    main()
