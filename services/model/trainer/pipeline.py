from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Dict

import numpy as np
import pandas as pd

from services.model.data_access import load_cfg, read_training_frame
from services.model.feature_builder import FeatureBuilder, EloRatingsAdapter

from .splitter import TimeBasedSplitter
from .model_rf import RandomForestMulticlassTrainer, RFConfig
from .metrics import ensure_three_class_proba, evaluate_multiclass
from .artifact_store import LocalArtifactStore
from .registry import DBModelRegistry

from Playmaker.shared.logging.logger import Logger
log = Logger.get_logger(name="playmaker.model.trainer.pipeline")

def _split_summary_dict(split_date, train_range, valid_range) -> Dict[str, str]:
    return {"split_date": str(split_date), "train_range": train_range, "valid_range": valid_range}

def train_pipeline(cfg_path: str) -> Tuple[int, str]:
    log.info("train.start", extra={"cfg_path": cfg_path})

    cfg = load_cfg(cfg_path)

    df = read_training_frame(cfg)
    if df is None or len(df) == 0:
        log.error("train.empty_training_table")
        raise RuntimeError("Training table returned no rows.")
    log.info("train.data_loaded", extra={"rows": len(df)})

    # Build features
    elo_adapter = EloRatingsAdapter()
    fb = FeatureBuilder(elo_port=elo_adapter)
    X, y, meta = fb.build(df)
    log.info("train.features_built", extra={"X_rows": len(X), "y_rows": len(y)})

    # Drop NaN labels (defensive)
    if y.isna().any():
        n_bad = int(y.isna().sum())
        log.warning("train.drop_nan_labels", extra={"n": n_bad})
        keep = ~y.isna()
        X, y, meta = X.loc[keep].reset_index(drop=True), y.loc[keep].reset_index(drop=True), meta.loc[keep].reset_index(drop=True)

    if X.empty or y.empty:
        log.error("train.no_data_after_label_cleanup")
        raise RuntimeError("After dropping NaN labels, no training data remains. Add more matches.")

    # Split
    splitter = TimeBasedSplitter(pct=0.8)
    split = splitter.split(meta)
    log.info("train.split_ready", extra={"n_train": len(split.train_idx), "n_valid": len(split.valid_idx),
                                         "train_range": split.train_range, "valid_range": split.valid_range})

    X_train, y_train = X.iloc[split.train_idx], y.iloc[split.train_idx]
    X_valid, y_valid = X.iloc[split.valid_idx], y.iloc[split.valid_idx]
    if len(y_valid) == 0:
        log.warning("train.no_valid_samples_using_train_for_eval")
        X_valid, y_valid = X_train, y_train

    # Train
    seed = int(cfg.get("seed", 42))
    trainer = RandomForestMulticlassTrainer(RFConfig(random_state=seed))
    trainer.fit(X_train, y_train)

    # Evaluate
    y_pred, y_proba, classes_ = trainer.predict(X_valid)
    y_proba = ensure_three_class_proba(y_proba, classes_)
    metrics = evaluate_multiclass(y_valid, y_pred, y_proba)
    log.info("train.metrics", extra=metrics)

    # Save artifact
    store = LocalArtifactStore(base_dir="services/model/models")
    split_info = _split_summary_dict(split.split_date, split.train_range, split.valid_range)
    artifact = store.save(
        model=trainer.model,
        feature_cols=list(X.columns),
        split_info=split_info,
        random_state=seed,
        algo_name="RandomForestClassifier",
        classes=[0, 1, 2],
    )
    log.info("train.saved_artifact", extra={"path": artifact.path})

    # Register
    registry = DBModelRegistry(cfg)
    trained_on_dset = f"train <= {split.train_range.split('→')[-1].strip()}, valid = {split.valid_range}"
    model_id = registry.register(
        model_name="rf_v1",
        trained_on_dset=trained_on_dset,
        metrics=metrics,
        artifact_uri=artifact.path,
    )
    log.info("train.registered", extra={"model_id": int(model_id)})

    return model_id, artifact.path

def main():
    try:
        cfg_path = str(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
        print(">> Loading config from:", cfg_path)
        model_id, artifact = train_pipeline(cfg_path=cfg_path)
        print("\n✅ Training complete.")
        print(f"   model_id      : {model_id}")
        print(f"   artifact_path : {artifact}")
    except Exception as e:
        log.exception("train.failed", extra={"error": str(e)})
        print(f"\n❌ Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
