"""Tests for cross-module environmental intelligence synthesis."""
import pytest
from unittest.mock import patch
from app.services.intelligence_service import IntelligenceService


@pytest.mark.asyncio
async def test_intelligence_synthesis_mocked(mock_nasa_power_temperature_response, mock_nasa_power_rain_response):
    async def mock_get_call(endpoint, params=None, headers=None, use_cache=True):
        params = params or {}
        p_str = params.get("parameters", "")
        if "T2M" in p_str:
            return mock_nasa_power_temperature_response
        return mock_nasa_power_rain_response

    with patch("app.data.nasa_client.nasa_client.get_with_retry", side_effect=mock_get_call):
        report = await IntelligenceService.synthesize(
            latitude=19.0760,
            longitude=72.8777,
            start_date="2020-01-01",
            end_date="2022-12-31",
            location_name="Mumbai Test Site",
        )
        assert report.status == "success"
        assert report.data_completeness_ratio > 0.0
        assert len(report.unified_narrative) > 20
        assert "Mumbai Test Site" in report.unified_narrative
        # Verify non-polar ice logic
        assert "ice" in report.modules_aggregated
        assert report.modules_aggregated["ice"]["status"] == "not_applicable_non_polar"
