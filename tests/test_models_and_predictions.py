"""Tests for time-series ML training, no future leakage, and prediction execution."""
import pytest
import pandas as pd
from unittest.mock import patch
from app.models.time_series_models import ValidatedTimeSeriesModel
from app.services.prediction_service import PredictionService

def test_model_training_and_validation():
    # Build 36-month synthetic dataset for model test
    dates = pd.date_range("2020-01-01", periods=36, freq="MS")
    df = pd.DataFrame({
        "timestamp": [d.strftime("%Y-%m-%d") for d in dates],
        "value": [20.0 + 10.0 * (i % 12) / 12.0 for i in range(36)]
    })
    
    model = ValidatedTimeSeriesModel(name="test_temp_model")
    metrics = model.fit(df, "value")
    
    assert model.is_trained is True
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "baseline_mae" in metrics
    
    preds, intervals = model.predict_forward(df, "value", steps=6)
    assert len(preds) == 6
    assert len(intervals) == 6
    for lower, upper in intervals:
        assert lower <= upper

@pytest.mark.asyncio
async def test_prediction_service_mocked(mock_nasa_power_temperature_response):
    with patch("app.data.nasa_client.nasa_client.get_with_retry") as mock_get:
        mock_get.return_value = mock_nasa_power_temperature_response
        res = await PredictionService.execute_prediction(
            category="temperature",
            latitude=19.0760,
            longitude=72.8777,
            start_date="2020-01-01",
            end_date="2022-12-31",
            horizon=6
        )
        assert res.status == "success"
        assert res.condition == "temperature"
        assert len(res.historical_data) > 0
        assert len(res.predictions) == 6
        assert res.uncertainty.available is True
        assert res.model is not None
        assert res.sonification is not None
        assert len(res.sonification.parameters) == len(res.historical_data) + len(res.predictions)