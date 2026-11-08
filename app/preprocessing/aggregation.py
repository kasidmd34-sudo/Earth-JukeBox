"""Temporal aggregation routines for irregular NASA satellite observations."""
import pandas as pd
from typing import Literal

class TemporalAggregator:
    @staticmethod
    def aggregate(
        df: pd.DataFrame,
        freq: Literal["D", "W", "MS"] = "MS",
        agg_func: str = "mean",
        date_col: str = "timestamp",
        val_col: str = "value"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        temp_df = df.copy()
        temp_df[date_col] = pd.to_datetime(temp_df[date_col])
        resampled = temp_df.set_index(date_col).resample(freq).agg({val_col: agg_func}).dropna()
        resampled = resampled.reset_index()
        resampled[date_col] = resampled[date_col].dt.strftime("%Y-%m-%d")
        return resampled