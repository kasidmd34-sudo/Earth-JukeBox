"""Tests verifying NASA data adapters and caching mechanisms."""
import pytest
from unittest.mock import patch
from app.data.nasa_power import NASAPowerAdapter
from app.data.nasa_firms import NASAFirmsAdapter
from app.data.ocean import OceanDataAdapter
from app.data.ice import CryosphereDataAdapter
from app.data.storms import StormsDataAdapter
from app.data.nasa_modis import NASAModisAdapter
from app.services.observation_service import ObservationService
from app.utils.caching import DiskCache


def test_parse_monthly_series(mock_nasa_power_temperature_response):
    pts = NASAPowerAdapter.parse_monthly_series(
        mock_nasa_power_temperature_response, "T2M", "degrees_Celsius"
    )
    assert len(pts) == 36
    assert pts[0].unit == "degrees_Celsius"
    assert pts[0].value > 0


def test_parse_monthly_series_missing_values():
    payload = {
        "properties": {
            "parameter": {
                "T2M": {
                    "202301": 24.5,
                    "202302": -999.0,  # NASA fill value
                    "202303": 26.1,
                    "202313": 25.0,   # Annual average (13th month)
                }
            }
        }
    }
    pts = NASAPowerAdapter.parse_monthly_series(payload, "T2M", "degrees_Celsius")
    # 202302 (-999.0) and 202313 (annual avg) must be excluded
    assert len(pts) == 2
    assert pts[0].timestamp == "2023-01-01"
    assert pts[1].timestamp == "2023-03-01"


def test_firms_missing_key_behavior():
    with patch("app.config.settings.NASA_FIRMS_MAP_KEY", ""):
        import asyncio
        fires = asyncio.run(NASAFirmsAdapter.fetch_active_fires(19.0, 72.0))
        assert fires == []


def test_disk_cache_operations(tmp_path):
    cache = DiskCache(cache_dir=str(tmp_path), ttl_seconds=2)
    cache.set("test_key", {"val": 123})
    assert cache.has("test_key") is True
    assert cache.get("test_key")["val"] == 123
    assert cache.delete("test_key") is True
    assert cache.has("test_key") is False


@pytest.mark.asyncio
async def test_observation_service_all_eight_modules():
    async def mock_get(endpoint, params=None, headers=None, use_cache=True):
        params = params or {}
        p_str = params.get("parameters", "T2M")
        var_name = p_str.split(",")[0]
        # Return 24 months of simulated observations for requested parameter
        data_vals = {
            f"{yr}{m:02d}": 20.0 + m
            for yr in (2020, 2021)
            for m in range(1, 13)
        }
        return {"properties": {"parameter": {var_name: data_vals}}}

    with patch("app.data.nasa_client.nasa_client.get_with_retry", side_effect=mock_get):
        for cat in ["temperature", "rain", "wind", "ocean", "vegetation", "storms"]:
            pts, meta, unit = await ObservationService.get_observations(
                cat, 19.0760, 72.8777, "2020-01-01", "2021-12-31"
            )
            assert meta.organization == "NASA"
            assert len(pts) == 24
            assert unit != ""

        # Test Polar Ice
        pts_ice, meta_ice, _ = await ObservationService.get_observations(
            "ice", 78.0, 15.0, "2020-01-01", "2021-12-31"  # Polar Svalbard
        )
        assert len(pts_ice) == 24
        assert "NSIDC" in meta_ice.dataset_name

        # Test Non-Polar Ice
        pts_non_polar_ice, _, _ = await ObservationService.get_observations(
            "ice", 0.0, 0.0, "2020-01-01", "2021-12-31"
        )
        assert len(pts_non_polar_ice) == 0
