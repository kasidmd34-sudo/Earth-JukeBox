"""Common domain enumerations and metadata models for Earth Jukebox."""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class EnvironmentalCategory(str, Enum):
    TEMPERATURE = "temperature"
    RAIN = "rain"
    WIND = "wind"
    FIRES = "fires"
    VEGETATION = "vegetation"
    OCEAN = "ocean"
    ICE = "ice"
    STORMS = "storms"

class ResultType(str, Enum):
    OBSERVATION = "observation"
    FORECAST = "forecast"
    PROJECTION = "projection"
    RISK_ESTIMATE = "risk_estimate"
    HISTORICAL_ANALYSIS = "historical_analysis"
    UNAVAILABLE = "unavailable"

class ModuleOperationalStatus(str, Enum):
    FULLY_WORKING = "fully_working"
    OBSERVATION_ONLY = "observation_only"
    HISTORICAL_ANALYSIS = "historical_analysis"
    EXPERIMENTAL = "experimental"
    UNAVAILABLE = "unavailable"

class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude")
    location_name: Optional[str] = Field(default=None, description="Human-readable location identifier")

class DataSourceMetadata(BaseModel):
    organization: str = "NASA"
    dataset_name: str
    dataset_identifier: str
    provider_daac: str
    api_endpoint: str
    retrieved_at: str
    variables: List[str]
    spatial_resolution: str
    temporal_resolution: str
    license_or_access: str

class ModelMetadata(BaseModel):
    name: str
    version: str
    status: str
    validation_method: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    trained_at: Optional[str] = None
    baseline_algorithm: Optional[str] = None