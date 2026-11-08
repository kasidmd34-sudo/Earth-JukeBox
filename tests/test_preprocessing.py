"""Tests for cleaning and validation routines."""
from app.preprocessing.cleaning import DataCleaner
from app.preprocessing.validation import GeoValidator

def test_clean_fill_values():
    records = [
        {"timestamp": "2023-01-01", "value": 25.0},
        {"timestamp": "2023-02-01", "value": -999.0},  # NASA fill value
        {"timestamp": "2023-03-01", "value": 27.0}
    ]
    cleaned = DataCleaner.clean_time_series(records)
    # Value should be interpolated or forward-filled, not -999.0
    assert cleaned["value"].iloc[1] == 25.0

def test_geo_validator():
    ok, _ = GeoValidator.validate_coordinates(19.0760, 72.8777)
    assert ok is True
    bad, msg = GeoValidator.validate_coordinates(95.0, 0.0)
    assert bad is False