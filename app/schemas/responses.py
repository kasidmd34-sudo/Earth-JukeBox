"""Consistent API response contracts across all environmental modules."""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.common import (
    GeoLocation, DataSourceMetadata, ModelMetadata, ResultType, ModuleOperationalStatus
)
from app.schemas.sonification import SonificationSeries


class TimeSeriesPoint(BaseModel):
    timestamp: str
    value: float
    unit: str
    anomaly: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class UncertaintyInfo(BaseModel):
    available: bool
    method: Optional[str] = None
    confidence_level: Optional[float] = None
    description: str


class ModuleResponse(BaseModel):
    status: str = "success"
    application: str = "Earth Jukebox"
    condition: str
    result_type: ResultType
    location: GeoLocation
    unit: str
    data_source: DataSourceMetadata
    model: Optional[ModelMetadata] = None
    historical_data: List[TimeSeriesPoint]
    predictions: List[TimeSeriesPoint] = Field(default_factory=list)
    uncertainty: UncertaintyInfo
    sonification: Optional[SonificationSeries] = None
    nasa_worldview_url: Optional[str] = Field(
        default=None,
        description="Direct deep-link to NASA Worldview satellite observation for requested bounding box",
    )
    limitations: List[str]


class ModuleCapability(BaseModel):
    category: str
    operational_status: ModuleOperationalStatus
    dataset_name: str
    provider_daac: str
    supported_result_types: List[ResultType]
    spatial_coverage: str
    limitations: List[str]


class IntelligenceReport(BaseModel):
    status: str = "success"
    application: str = "Earth Jukebox"
    location: GeoLocation
    time_window: Dict[str, str]
    unified_narrative: str
    anomalies_detected: List[Dict[str, Any]]
    modules_aggregated: Dict[str, Dict[str, Any]]
    compound_indices: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Compound climate indices (e.g. evaporative stress, storm convective energy)",
    )
    nasa_worldview_url: Optional[str] = None
    data_completeness_ratio: float
    scientific_disclaimer: str
