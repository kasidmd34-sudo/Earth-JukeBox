"""Train and serialize validated baseline models for forecastable continuous modules."""
import asyncio
import os
import sys

# Ensure repository root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from app.data.nasa_power import NASAPowerAdapter
from app.models.time_series_models import ValidatedTimeSeriesModel
from app.config import settings

TARGET_CONFIGS = [
    {"category": "temperature", "var": "T2M", "unit": "degrees_Celsius"},
    {"category": "rain", "var": "PRECTOTCORR", "unit": "mm/day"},
    {"category": "wind", "var": "WS10M", "unit": "m/s"},
]


async def train_all():
    os.makedirs(settings.MODEL_ARTIFACTS_DIR, exist_ok=True)
    print("=======================================================")
    print("Training Earth Jukebox Production Baseline Models...")
    print("=======================================================")

    for cfg in TARGET_CONFIGS:
        cat = cfg["category"]
        var = cfg["var"]
        unit = cfg["unit"]
        print(f"\nFetching NASA POWER Climatology for {cat.upper()} ({var})...")
        try:
            payload = await NASAPowerAdapter.fetch_monthly_climatology(19.0760, 72.8777, 2015, 2023, [var])
            pts = NASAPowerAdapter.parse_monthly_series(payload, var, unit)
            if len(pts) < 24:
                print(f"Skipping {cat}: insufficient observations ({len(pts)} found).")
                continue

            df = pd.DataFrame([{"timestamp": p.timestamp, "value": p.value} for p in pts])
            model = ValidatedTimeSeriesModel(f"{cat}_autoreg_ridge")
            metrics = model.fit(df, "value")

            out_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, f"{cat}_model.joblib")
            model.save(out_path)
            print(f"SUCCESS: {cat.upper()} Model Saved -> {out_path}")
            print(f"  MAE: {metrics['mae']} | Baseline MAE: {metrics['baseline_mae']} | R2: {metrics['r2']}")
        except Exception as e:
            print(f"FAILED to train {cat}: {e}")

    print("\n=======================================================")
    print("Training process complete.")
    print("=======================================================")


if __name__ == "__main__":
    asyncio.run(train_all())
