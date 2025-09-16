# services/model/data_access/__init__.py
"""
Facade layer to keep old imports working while exposing the new class-based API.
"""

from .config_loader import ConfigService
from .db import Database
from .readers import MatchReader, FixtureReader
from .writers import ModelVersionRepo, PredictionRepo

from .uow import UnitOfWork

import pandas as pd

# -------- Legacy Compatibility Wrappers --------

def load_cfg(path: str = "services/model/config/config.yaml"):
    return ConfigService(path).load()

def get_engine(cfg):
    return Database(cfg).engine()

def read_match_clean(cfg, columns=None) -> pd.DataFrame:
    return MatchReader(Database(cfg), cfg).read_match_clean(columns)

def read_fixtures_scheduled(cfg) -> pd.DataFrame:
    return FixtureReader(Database(cfg), cfg).read_scheduled()

def read_upcoming_fixtures(cfg) -> pd.DataFrame:
    return FixtureReader(Database(cfg), cfg).read_scheduled()

def read_training_frame(cfg) -> pd.DataFrame:
    return MatchReader(Database(cfg), cfg).read_training_frame()

def write_model_version(cfg, model_name, trained_on_dset, metrics, artifact_uri) -> int:
    return ModelVersionRepo(Database(cfg), cfg).insert(
        model_name=model_name,
        trained_on_dset=trained_on_dset,
        metrics=metrics,
        artifact_uri=artifact_uri
    )

def upsert_predictions(cfg, df: pd.DataFrame) -> int:
    return PredictionRepo(Database(cfg), cfg).upsert(df)

__all__ = [
    "ConfigService",
    "Database",
    "MatchReader",
    "FixtureReader",
    "ModelVersionRepo",
    "PredictionRepo",
    "UnitOfWork",
    "load_cfg",
    "get_engine",
    "read_match_clean",
    "read_fixtures_scheduled",
    "read_upcoming_fixtures",
    "read_training_frame",
    "write_model_version",
    "upsert_predictions",
]
