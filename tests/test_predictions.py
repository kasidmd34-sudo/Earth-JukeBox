"""Uncertainty interval verification and scientific restriction guardrail tests."""
import pytest
import numpy as np
from unittest.mock import patch
from app.models.uncertainty import ResidualUncertaintyEstimator
from app.services.prediction_service import PredictionService
from app.schemas.common import ResultType


def test_residual_intervals():
    residuals = np.array([-1.5, -0.5, 0.0, 0.5, 1.5, -0.2, 0.3])
    preds = [25.0, 26.0]
    intervals = ResidualUncertaintyEstimator.compute_prediction_intervals(residuals, preds, 0.95)
    assert len(intervals) == 2
    for low, up in intervals:
        assert low < up


@pytest.mark.asyncio
async def test_fires_scientific_guardrail():
    # Fires must NEVER produce forecasts
    with patch("app.data.nasa_firms.NASAFirmsAdapter.fetch_active_fires") as mock_fires:
        mock_fires.return_value = [{"acq_date": "2023-01-01", "frp": 12.5}]
        res = await PredictionService.execute_prediction(
            category="fires",
            latitude=19.0760,
            longitude=72.8777,
            start_date="2022-01-01",
            end_date="2023-12-31",
            horizon=12,
        )
        assert res.result_type != ResultType.FORECAST
        assert len(res.predictions) == 0
        assert "UNAVAILABLE" in res.limitations[1] or "RESTRICTION" in res.limitations[0]


@pytest.mark.asyncio
async def test_storms_scientific_guardrail():
    # Storms must NEVER produce deterministic track/landfall forecasts
    res = await PredictionService.execute_prediction(
        category="storms",
        latitude=19.0760,
        longitude=72.8777,
        start_date="2022-01-01",
        end_date="2023-12-31",
        horizon=12,
    )
    assert res.result_type != ResultType.FORECAST
    assert len(res.predictions) == 0
    assert any("RESTRICTION" in lim for lim in res.limitations)


@pytest.mark.asyncio
async def test_ice_non_polar_guardrail():
    # Ice requested in non-polar tropics (lat 19.0760) must be UNAVAILABLE
    res = await PredictionService.execute_prediction(
        category="ice",
        latitude=19.0760,
        longitude=72.8777,
        start_date="2022-01-01",
        end_date="2023-12-31",
        horizon=6,
    )
    assert res.result_type == ResultType.UNAVAILABLE
    assert len(res.predictions) == 0
