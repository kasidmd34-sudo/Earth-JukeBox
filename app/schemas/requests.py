"""Strict Pydantic request models with input validation."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.common import EnvironmentalCategory


def _validate_date_str(v: str) -> str:
    try:
        datetime.strptime(v, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Date '{v}' does not match expected format YYYY-MM-DD")
    return v


def _check_date_order(start_date: str, end_date: str):
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    if s > e:
        raise ValueError(f"start_date '{start_date}' cannot be chronologically after end_date '{end_date}'.")


class ObservationRequest(BaseModel):
    category: EnvironmentalCategory
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    start_date: str = Field(..., json_schema_extra={"example": "2022-01-01"})
    end_date: str = Field(..., json_schema_extra={"example": "2023-12-31"})

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        return _validate_date_str(v)

    @model_validator(mode="after")
    def validate_chronology(self) -> ObservationRequest:
        _check_date_order(self.start_date, self.end_date)
        return self


class PredictionRequest(BaseModel):
    category: EnvironmentalCategory
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    start_date: str = Field(default="2018-01-01")
    end_date: str = Field(default="2023-12-31")
    horizon: int = Field(default=12, ge=1, le=36, description="Prediction horizon steps (months)")
    interval: str = Field(default="monthly", pattern="^(daily|monthly)$")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        return _validate_date_str(v)

    @model_validator(mode="after")
    def validate_chronology(self) -> PredictionRequest:
        _check_date_order(self.start_date, self.end_date)
        return self


class IntelligenceRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: Optional[str] = "Selected Coordinates"
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        return _validate_date_str(v)

    @model_validator(mode="after")
    def validate_chronology(self) -> IntelligenceRequest:
        _check_date_order(self.start_date, self.end_date)
        return self


class SonificationGenerationRequest(BaseModel):
    category: EnvironmentalCategory
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    start_date: str = "2020-01-01"
    end_date: str = "2023-12-31"
    include_prediction: bool = True
    horizon: int = Field(default=12, ge=1, le=24)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        return _validate_date_str(v)

    @model_validator(mode="after")
    def validate_chronology(self) -> SonificationGenerationRequest:
        _check_date_order(self.start_date, self.end_date)
        return self
