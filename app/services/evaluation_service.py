"""Model evaluation and baseline comparison service."""
import pandas as pd
from typing import Dict, Any
from app.models.registry import model_registry
from app.services.observation_service import ObservationService

class EvaluationService:
    @classmethod
    async def evaluate_module(
        cls,
        category: str,
        latitude: float = 19.0760,
        longitude: float = 72.8777,
        start_date: str = "2018-01-01",
        end_date: str = "2023-12-31"
    ) -> Dict[str, Any]:
        pts, meta, unit = await ObservationService.get_observations(
            category, latitude, longitude, start_date, end_date
        )
        if len(pts) < 24:
            return {
                "category": category,
                "status": "insufficient_data",
                "message": f"Requires >= 24 monthly observations. Found {len(pts)}."
            }

        df = pd.DataFrame([{"timestamp": p.timestamp, "value": p.value} for p in pts])
        model = model_registry.get_or_create_model(category)
        metrics = model.fit(df, "value")

        return {
            "category": category,
            "status": "evaluated",
            "validation_method": "Chronological 80/20 Holdout",
            "sample_size": len(df),
            "metrics": metrics,
            "beats_baseline": metrics["mae"] < metrics.get("baseline_mae", float("inf")),
            "unit": unit,
            "data_source": meta.dataset_name
        }