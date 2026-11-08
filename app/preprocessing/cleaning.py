"""Data cleaning, deduplication, and NASA fill-value handling."""
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class DataCleaner:
    NASA_FILL_VALUES = [-999.0, -9999.0, -99.0, 9999.0]

    @classmethod
    def clean_time_series(cls, records: List[Dict[str, Any]], value_col: str = "value") -> pd.DataFrame:
        if not records:
            return pd.DataFrame(columns=["timestamp", value_col])
        
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

        # Replace NASA fill values with NaN
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        df[value_col] = df[value_col].replace(cls.NASA_FILL_VALUES, np.nan)

        # Forward-fill followed by backward-fill for small isolated drops
        df[value_col] = df[value_col].ffill().bfill()
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d")
        return df.reset_index(drop=True)