"""Model Registry tracking model metadata, operational status, and persistence."""
import os
from typing import Dict, Optional
from app.models.time_series_models import ValidatedTimeSeriesModel
from app.config import settings


class ModelRegistry:
    NON_NEGATIVE_CATEGORIES = {"rain", "wind"}

    def __init__(self):
        self._models: Dict[str, ValidatedTimeSeriesModel] = {}

    def get_or_create_model(self, category: str) -> ValidatedTimeSeriesModel:
        if category not in self._models:
            is_non_neg = category.lower() in self.NON_NEGATIVE_CATEGORIES
            model = ValidatedTimeSeriesModel(
                name=f"{category}_autoreg_ridge",
                version="1.0.0",
                non_negative=is_non_neg,
            )
            artifact_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, f"{category}_model.joblib")
            if os.path.exists(artifact_path):
                try:
                    model.load(artifact_path)
                except Exception:
                    pass
            self._models[category] = model
        return self._models[category]


model_registry = ModelRegistry()
