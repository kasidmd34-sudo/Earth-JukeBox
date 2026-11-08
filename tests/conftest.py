"""Pytest fixtures and mock NASA responses."""
import pytest
from typing import Dict, Any

@pytest.fixture
def mock_nasa_power_temperature_response() -> Dict[str, Any]:
    # Mock 36 months of NASA POWER monthly temperature observations
    params = {}
    for year in range(2020, 2023):
        for m in range(1, 13):
            # Monthly variation simulating seasonal curve
            month_str = f"{m:02d}"
            key = f"{year}{month_str}"
            val = 25.0 + 5.0 * ((m - 6) / 6.0) ** 2
            params[key] = round(val, 2)
    return {
        "properties": {
            "parameter": {
                "T2M": params
            }
        }
    }

@pytest.fixture
def mock_nasa_power_rain_response() -> Dict[str, Any]:
    params = {}
    for year in range(2020, 2023):
        for m in range(1, 13):
            month_str = f"{m:02d}"
            key = f"{year}{month_str}"
            val = 3.5 + (2.0 if m in (6, 7, 8) else 0.5)
            params[key] = round(val, 2)
    return {
        "properties": {
            "parameter": {
                "PRECTOTCORR": params
            }
        }
    }