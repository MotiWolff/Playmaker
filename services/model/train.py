# services/model/train.py
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss

from data_access import load_cfg, read_training_frame, write_model_version
from feature_builder import build_features


# ---------------------------
# Utilities
# ---------------------------

def ensure_models_dir(path: str = "services/model/models") -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def pick_time_split(meta: pd.DataFrame, pct: float = 0.8) -> pd.Timestamp:
    """
    Choose a time-based split date at the given percentile of the timeline.
    Train = dates <= split_date, Valid = > split_date.
    """
    if "Date" not in meta.columns:
        raise ValueError("meta must contain a 'Date' column for time-based split.")
    dates = pd.to_datetime(meta["Date"])
    if dates.isna().all():
        raise ValueError("All 'Date' values are NaT; cannot time-split.")
    # e.g., 80th percentile date
    split_date = dates.quantile(pct)
    return pd.to_datetime(split_date)


def brier_multiclass(y_true: np.ndarray, proba: np.ndarray, n_classes: int = 3) -> float:
    """
    Brier score for multi-class: mean over samples of sum_k (p_k - y_k)^2,
    where y_k is one-hot.
    """
    y_true = np.asarray(y_true).astype(int)
    Y = np.eye(n_classes)[y_true]  # one-hot
    return np.mean(np.sum((proba - Y) ** 2, axis=1))


def summarize_split(meta: pd.DataFrame, train_idx: np.ndarray, valid_idx: np.ndarray) -> Dict[str, str]:
    t_min, t_max = pd.to_datetime(meta.loc[train_idx, "Date"]).min(), pd.to_datetime(meta.loc[train_idx, "Date"]).max()
    v_min, v_max = pd.to_datetime(meta.loc[valid_idx, "Date"]).min(), pd.to_datetime(meta.loc[valid_idx, "Date"]).max()
    return {
        "train_range": f"{t_min.date()} → {t_max.date()}",
        "valid_range": f"{v_min.date()} → {v_max.date()}",
        "n_train": str(len(train_idx)),
        "n_valid": str(len(valid_idx)),
    }


# ---------------------------
# Training pipeline
# ---------------------------

def train_pipeline(cfg_path: str = "services/model/config/config.yaml") -> Tuple[int, str]:
    """
    1) Load config + training frame from Postgres
    2) Build leakage-safe features (3-class target)
    3) Time-based split
    4) Train RandomForest (multi-class)
    5) Evaluate (accuracy, log_loss, brier)
    6) Save artifact + register in model_version
    Returns: (model_id, artifact_path)
    """
    # ---- Load config and data
    print(">> Loading config…")
    cfg = load_cfg(cfg_path)

    print(">> Reading training data from DB…")
    df = read_training_frame(cfg)
    if df is None or len(df) == 0:
        raise RuntimeError("Training table returned no rows.")

    # ---- Feature engineering (safe, no leakage)
    print(">> Building features (this may take a moment)…")
    X, y, meta = build_features(df, min_history_games=1)  # raises with clear context on failure

    if X.empty or y.empty:
        raise RuntimeError("Feature builder returned empty X/y. Check data coverage.")

    # ---- Time-based split
    print(">> Creating time-based split…")
    split_date = pick_time_split(meta, pct=0.8)
    idx_all = np.arange(len(X))
    train_idx = idx_all[ pd.to_datetime(meta["Date"]) <= split_date ]
    valid_idx = idx_all[ pd.to_datetime(meta["Date"]) >  split_date ]

    if len(train_idx) < 50 or len(valid_idx) < 20:
        print("[Warning] Very small train/valid split. Consider more data.")

    split_info = summarize_split(meta, train_idx, valid_idx)
    print(f"   Train: {split_info['train_range']}  (n={split_info['n_train']})")
    print(f"   Valid: {split_info['valid_range']}  (n={split_info['n_valid']})")

    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_valid, y_valid = X.iloc[valid_idx], y.iloc[valid_idx]

    # ---- Model (RandomForest multi-class)
    # RF doesn’t need scaling; class_weight='balanced' helps with class imbalance (draws, etc.)
    seed = int(cfg.get("seed", 42))
    clf = RandomForestClassifier(
        n_estimators=400,
        max_depth=6,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )

    print(">> Training RandomForest…")
    clf.fit(X_train, y_train)

    # ---- Evaluation
    print(">> Evaluating…")
    y_pred = clf.predict(X_valid)
    y_proba = clf.predict_proba(X_valid)

    # Ensure probability matrix has all classes in consistent order [0,1,2]
    # (sklearn does this if it saw all classes in training; if not, handle gracefully)
    classes_ = getattr(clf, "classes_", np.array([0, 1, 2]))
    if set(classes_) != {0, 1, 2}:
        # Expand to 3-class columns
        proba_full = np.zeros((y_proba.shape[0], 3))
        for col_idx, cls in enumerate(classes_):
            proba_full[:, int(cls)] = y_proba[:, col_idx]
        y_proba = proba_full

    acc = float(accuracy_score(y_valid, y_pred))
    try:
        ll = float(log_loss(y_valid, y_proba, labels=[0, 1, 2]))
    except Exception as e:
        print(f"[Warning] log_loss failed ({e}); using NaN.")
        ll = float("nan")
    brier = float(brier_multiclass(y_valid.to_numpy(), y_proba, n_classes=3))

    print(f"   Accuracy:  {acc:.4f}")
    print(f"   Log loss:  {ll:.4f}")
    print(f"   Brier:     {brier:.4f}")

    # ---- Save artifact
    print(">> Saving model artifact…")
    models_dir = ensure_models_dir()
    ts = int(time.time())
    artifact_path = str(models_dir / f"rf_model_{ts}.joblib")
    metadata = {
        "algo": "RandomForestClassifier",
        "feature_cols": list(X.columns),
        "classes": [0, 1, 2],  # 0=H,1=D,2=A
        "split_date": str(split_date),
        "train_range": split_info["train_range"],
        "valid_range": split_info["valid_range"],
        "created_utc": datetime.utcnow().isoformat(),
        "random_state": seed,
        "params": {
            "n_estimators": 400,
            "max_depth": 6,
            "min_samples_leaf": 3,
            "class_weight": "balanced",
        },
    }
    joblib.dump({"model": clf, "meta": metadata}, artifact_path)
    print(f"   Saved: {artifact_path}")

    # ---- Register in model_version
    print(">> Registering model in model_version…")
    metrics = {"accuracy": acc, "log_loss": ll, "brier": brier}
    trained_on_dset = f"train <= {split_info['train_range'].split('→')[-1].strip()}, valid = {split_info['valid_range']}"
    model_id = write_model_version(
        cfg=cfg,
        model_name="rf_v1",
        trained_on_dset=trained_on_dset,
        metrics=metrics,
        artifact_uri=artifact_path,
    )
    print(f"   model_id: {model_id}")

    return model_id, artifact_path


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Train 3-class RF with time-based split.")
    parser.add_argument(
        "--cfg",
        default="services/model/config/config.yaml",
        help="Path to YAML config.",
    )
    args = parser.parse_args()

    try:
        model_id, artifact = train_pipeline(cfg_path=args.cfg)
        print("\n✅ Training complete.")
        print(f"   model_id      : {model_id}")
        print(f"   artifact_path : {artifact}")
    except Exception as e:
        # Surface a clean message; exit non-zero for CI/CD awareness
        print(f"\n❌ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
