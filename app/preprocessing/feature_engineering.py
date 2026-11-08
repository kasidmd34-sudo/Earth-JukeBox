"""Scientific time series feature engineering with zero future-lookahead leakage."""
import numpy as np
import pandas as pd
from typing import Tuple, List

class TimeSeriesFeatureEngineer:
    @staticmethod
    def create_lag_features(df: pd.DataFrame, target_col: str, lags: List[int]) -> pd.DataFrame:
        df = df.copy()
        for lag in lags:
            df[f"lag_{lag}"] = df[target_col].shift(lag)
        return df

    @staticmethod
    def create_calendar_features(df: pd.DataFrame, date_col: str = "timestamp") -> pd.DataFrame:
        df = df.copy()
        dates = pd.to_datetime(df[date_col])
        df["month"] = dates.dt.month
        # Cyclical Sine/Cosine transformation
        df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
        df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)
        return df

    @staticmethod
    def chronological_split(
        df: pd.DataFrame,
        train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Strict time-ordered split to prevent temporal leakage."""
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        split_idx = int(len(df_sorted) * train_ratio)
        train_df = df_sorted.iloc[:split_idx].copy()
        test_df = df_sorted.iloc[split_idx:].copy()
        return train_df, test_df