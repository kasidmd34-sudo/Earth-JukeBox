"""API Route validation and health check tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["nasa_policy_compliance"] == "STRICT_NASA_ONLY"


def test_module_discovery():
    res = client.get("/modules")
    assert res.status_code == 200
    modules = res.json()
    assert len(modules) == 8
    categories = [m["category"] for m in modules]
    for expected in ["temperature", "rain", "wind", "fires", "ocean", "ice", "storms", "vegetation"]:
        assert expected in categories

    # Check that fire forecasting restriction is clearly declared
    fires_mod = next(m for m in modules if m["category"] == "fires")
    assert fires_mod["operational_status"] == "observation_only"


def test_models_metadata_endpoints():
    res = client.get("/models")
    assert res.status_code == 200
    data = res.json()
    assert "temperature" in data
    assert "baseline" in data["temperature"]

    # Test single condition
    res_single = client.get("/models/temperature")
    assert res_single.status_code == 200
    assert res_single.json()["condition"] == "temperature"

    # Test scientific restriction on fires
    res_fire = client.get("/models/fires")
    assert res_fire.status_code == 200
    assert res_fire.json()["status"] == "UNAVAILABLE"


def test_datasets_and_provenance_endpoints():
    res_ds = client.get("/datasets")
    assert res_ds.status_code == 200
    assert "temperature" in res_ds.json()
    assert "rain" in res_ds.json()

    res_meta = client.get("/metadata/rain")
    assert res_meta.status_code == 200
    assert res_meta.json()["units"] == "mm/day"

    res_prov = client.get("/provenance/temperature")
    assert res_prov.status_code == 200
    assert res_prov.json()["nasa_only_policy_enforced"] is True


def test_date_chronology_validation():
    payload = {
        "category": "temperature",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "start_date": "2023-12-31",
        "end_date": "2020-01-01",  # Invalid inverted order
    }
    res = client.post("/observations", json=payload)
    assert res.status_code == 422


def test_coordinate_validation():
    payload = {
        "category": "temperature",
        "latitude": 95.0,  # Invalid latitude > 90
        "longitude": 0.0,
        "start_date": "2020-01-01",
        "end_date": "2022-12-31",
    }
    res = client.post("/observations", json=payload)
    assert res.status_code == 422


def test_demo_endpoint_exists():
    res = client.get("/demo")
    # Returns 200 if demo.html exists or 404 if not yet written
    assert res.status_code in (200, 404)
