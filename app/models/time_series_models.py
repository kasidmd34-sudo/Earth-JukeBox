"""Autoregressive Ridge models with baseline persistence comparison and empirical uncertainty."""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.models.base import BaseEnvironmentalModel
from app.models.uncertainty import ResidualUncertaintyEstimator
from app.preprocessing.feature_engineering import TimeSeriesFeatureEngineer


class ValidatedTimeSeriesModel(BaseEnvironmentalModel):
    def __init__(self, name: str, version: str = "1.0.0", non_negative: bool = False):
        super().__init__(name=name, version=version)
        self.model = Ridge(alpha=1.0)
        self.lags = [1, 2, 12]
        self.residuals = np.array([])
        self.baseline_mae = 0.0
        self.non_negative = non_negative

    def _prepare_matrix(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        df_feat = TimeSeriesFeatureEngineer.create_lag_features(df, target_col, self.lags)
        df_feat = TimeSeriesFeatureEngineer.create_calendar_features(df_feat)
        return df_feat.dropna().reset_index(drop=True)

    def fit(self, train_df: pd.DataFrame, target_col: str) -> Dict[str, float]:
        if len(train_df) < 24:
            raise ValueError(f"Insufficient training observations: {len(train_df)} found, >= 24 required.")

        # 1. Prepare feature matrix across continuous timeline first (avoids NaNs in validation split)
        full_matrix = self._prepare_matrix(train_df, target_col)

        if len(full_matrix) < 6:
            raise ValueError(f"Feature matrix after lag generation has too few samples ({len(full_matrix)}).")

        # 2. Chronological split (80% train, 20% validation) to prevent data leakage
        train_split, val_split = TimeSeriesFeatureEngineer.chronological_split(full_matrix, 0.8)

        feature_cols = [f"lag_{lag}" for lag in self.lags] + ["sin_month", "cos_month"]
        X_train, y_train = train_split[feature_cols], train_split[target_col]
        X_val, y_val = val_split[feature_cols], val_split[target_col]

        # 3. Calculate Seasonal-Naive Baseline (Lag-12 or Lag-1)
        baseline_preds = val_split["lag_12"] if "lag_12" in val_split else val_split["lag_1"]
        self.baseline_mae = float(mean_absolute_error(y_val, baseline_preds))

        # 4. Fit model on training slice
        self.model.fit(X_train, y_train)
        val_preds = self.model.predict(X_val)
        if self.non_negative:
            val_preds = np.clip(val_preds, 0.0, None)

        # 5. Calculate validation metrics & residuals
        val_mae = float(mean_absolute_error(y_val, val_preds))
        val_mse = float(mean_squared_error(y_val, val_preds))
        val_rmse = float(np.sqrt(val_mse))
        val_r2 = float(r2_score(y_val, val_preds))

        self.residuals = y_val.values - val_preds
        self.metrics = {
            "mae": round(val_mae, 3),
            "rmse": round(val_rmse, 3),
            "r2": round(val_r2, 3),
            "baseline_mae": round(self.baseline_mae, 3),
        }
        self.is_trained = True
        return self.metrics

    def predict_forward(
        self,
        historical_df: pd.DataFrame,
        target_col: str,
        steps: int,
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        if not self.is_trained:
            raise RuntimeError("Model must be trained prior to forward prediction.")

        df = historical_df.copy().sort_values("timestamp").reset_index(drop=True)
        predictions: List[float] = []

        last_timestamp = pd.to_datetime(df["timestamp"].iloc[-1])
        current_history = df[target_col].tolist()
        feature_cols = [f"lag_{lag}" for lag in self.lags] + ["sin_month", "cos_month"]

        for step in range(1, steps + 1):
            next_date = last_timestamp + pd.DateOffset(months=step)
            month = next_date.month
            sin_m = np.sin(2 * np.pi * month / 12.0)
            cos_m = np.cos(2 * np.pi * month / 12.0)

            lag_1 = current_history[-1]
            lag_2 = current_history[-2] if len(current_history) >= 2 else lag_1
            lag_12 = current_history[-12] if len(current_history) >= 12 else lag_1

            feature_df = pd.DataFrame(
                [[lag_1, lag_2, lag_12, sin_m, cos_m]],
                columns=feature_cols,
            )
            raw_pred = float(self.model.predict(feature_df)[0])
            pred_val = max(0.0, raw_pred) if self.non_negative else raw_pred
            predictions.append(pred_val)
            current_history.append(pred_val)

        intervals = ResidualUncertaintyEstimator.compute_prediction_intervals(
            self.residuals, predictions, confidence_level=0.95
        )
        if self.non_negative:
            intervals = [(max(0.0, low), max(0.0, up)) for low, up in intervals]

        return predictions, intervals

    def save(self, filepath: str) -> None:
        bundle = {
            "model": self.model,
            "residuals": self.residuals,
            "metrics": self.metrics,
            "baseline_mae": self.baseline_mae,
            "non_negative": self.non_negative,
        }
        joblib.dump(bundle, filepath)

    def load(self, filepath: str) -> None:
        bundle = joblib.load(filepath)
        self.model = bundle["model"]
        self.residuals = bundle["residuals"]
        self.metrics = bundle["metrics"]
        self.baseline_mae = bundle.get("baseline_mae", 0.0)
        self.non_negative = bundle.get("non_negative", False)
        self.is_trained = True
