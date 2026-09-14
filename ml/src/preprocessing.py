"""Reusable, inference-safe preprocessing utilities for future ML workflows."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from .config import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERICAL_COLUMNS, TARGET_COLUMNS
except ImportError:  # Allows direct execution/import from ml/src.
    from config import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERICAL_COLUMNS, TARGET_COLUMNS


def get_feature_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Return input features only; targets and identifiers cannot enter a model."""
    missing = set(FEATURE_COLUMNS).difference(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing feature columns: {sorted(missing)}")
    return data.loc[:, FEATURE_COLUMNS].copy()


def get_targets(data: pd.DataFrame) -> pd.DataFrame:
    """Return the prediction outcomes, kept separate from model inputs."""
    missing = set(TARGET_COLUMNS).difference(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing target columns: {sorted(missing)}")
    return data.loc[:, TARGET_COLUMNS].copy()


def build_preprocessor() -> ColumnTransformer:
    """Build a serializable preprocessing pipeline for training and inference."""
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipeline, list(NUMERICAL_COLUMNS)),
        ("categorical", categorical_pipeline, list(CATEGORICAL_COLUMNS)),
    ], remainder="drop")

