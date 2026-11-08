"""Date and temporal calculation utilities for NASA observations."""
from datetime import datetime, date
from typing import Tuple, List
import pandas as pd

def parse_iso_or_power_date(date_str: str) -> datetime:
    """Parses standard ISO (YYYY-MM-DD) or POWER monthly (YYYYMM) strings."""
    date_clean = date_str.strip().replace("-", "")
    if len(date_clean) == 6:
        return datetime.strptime(date_clean, "%Y%m")
    elif len(date_clean) == 8:
        return datetime.strptime(date_clean, "%Y%m%d")
    return datetime.fromisoformat(date_str)

def generate_future_monthly_timestamps(last_timestamp_str: str, steps: int) -> List[str]:
    last_dt = pd.to_datetime(last_timestamp_str)
    return [(last_dt + pd.DateOffset(months=i)).strftime("%Y-%m-%d") for i in range(1, steps + 1)]

def get_year_range(start_date: str, end_date: str) -> Tuple[int, int]:
    s_yr = int(start_date.split("-")[0])
    e_yr = int(end_date.split("-")[0])
    return s_yr, e_yr