from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict

from services.model.data_access import load_cfg, read_training_frame
# ✅ use the correct package name: features (plural)
from services.model.feature_builder import FeatureBuilder, EloRatingsAdapter

from .splitter import TimeBasedSplitter
from .model_rf import RandomForestMulticlassTrainer, RFConfig
from .metrics import ensure_three_class_proba, evaluate_multiclass
from .artifact_store import LocalArtifactStore
from .registry import DBModelRegistry


def _split_summary_dict(split_date, train_range, valid_range) -> Dict[str, str]:
    return {
        "split_date": str(split_date),
        "train_range": train_range,
        "valid_range": valid_range,
    }


def train_pipeline(cfg_path: str) -> Tuple[int, str]:
    print(">> Loading config…")
    cfg = load_cfg(cfg_path)

    print(">> Reading training data from DB…")
    df = read_training_frame(cfg)
    if df is None or len(df) == 0:
        raise RuntimeError("Training table returned no rows.")

    print(">> Building features (this may take a moment)…")
    # If you haven't implemented EloRatingsAdapter yet, temporarily swap to a fake adapter.
    elo_adapter = EloRatingsAdapter()  # must compute PRE-match elo only (no leakage)
    fb = FeatureBuilder(elo_port=elo_adapter)
    X, y, meta = fb.build(df)

    # --- Drop NaN labels defensively ---
    if y.isna().any():
        n_bad = int(y.isna().sum())
        print(f"[Warning] Dropping {n_bad} rows with unknown labels (NaN FTR).")
        keep = ~y.isna()
        X, y, meta = X.loc[keep].reset_index(drop=True), y.loc[keep].reset_index(drop=True), meta.loc[keep].reset_index(drop=True)

    if X.empty or y.empty:
        raise RuntimeError("After dropping NaN labels, no training data remains. Add more matches.")

    print(">> Creating time-based split…")
    splitter = TimeBasedSplitter(pct=0.8)
    split = splitter.split(meta)
    if len(split.train_idx) < 50 or len(split.valid_idx) < 1:
        print("[Warning] Very small train/valid split. Consider more data.")
    print(f"   Train: {split.train_range}  (n={len(split.train_idx)})")
    print(f"   Valid: {split.valid_range}  (n={len(split.valid_idx)})")

    X_train, y_train = X.iloc[split.train_idx], y.iloc[split.train_idx]
    X_valid, y_valid = X.iloc[split.valid_idx], y.iloc[split.valid_idx]

    # --- If still no valid rows, evaluate on train (keeps smoke tests running) ---
    if len(y_valid) == 0:
        print("[Warning] No validation samples; evaluating on train set (optimistic).")
        X_valid, y_valid = X_train, y_train

    seed = int(cfg.get("seed", 42))
    trainer = RandomForestMulticlassTrainer(RFConfig(random_state=seed))
    print(">> Training RandomForest…")
    trainer.fit(X_train, y_train)

    print(">> Evaluating…")
    y_pred, y_proba, classes_ = trainer.predict(X_valid)
    y_proba = ensure_three_class_proba(y_proba, classes_)
    metrics = evaluate_multiclass(y_valid, y_pred, y_proba)

    print(f"   Accuracy:  {metrics['accuracy']:.4f}")
    print(f"   Log loss:  {metrics['log_loss']:.4f}")
    print(f"   Brier:     {metrics['brier']:.4f}")

    print(">> Saving model artifact…")
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
    print(f"   Saved: {artifact.path}")

    print(">> Registering model in model_version…")
    registry = DBModelRegistry(cfg)
    trained_on_dset = f"train <= {split.train_range.split('→')[-1].strip()}, valid = {split.valid_range}"
    model_id = registry.register(
        model_name="rf_v1",
        trained_on_dset=trained_on_dset,
        metrics=metrics,
        artifact_uri=artifact.path,
    )
    print(f"   model_id: {model_id}")

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
        print(f"\n❌ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
