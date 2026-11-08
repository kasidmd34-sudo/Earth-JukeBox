"""Module status discovery and capability audit endpoint."""
from fastapi import APIRouter
from typing import List
from app.schemas.responses import ModuleCapability
from app.schemas.common import ModuleOperationalStatus, ResultType

router = APIRouter(prefix="/modules", tags=["Discovery"])

@router.get("", response_model=List[ModuleCapability])
def get_modules():
    return [
        ModuleCapability(
            category="temperature",
            operational_status=ModuleOperationalStatus.FULLY_WORKING,
            dataset_name="NASA POWER Monthly Climate Surface Temperatures",
            provider_daac="NASA Langley ASDC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.FORECAST, ResultType.HISTORICAL_ANALYSIS],
            spatial_coverage="Global (0.5 x 0.625 degrees)",
            limitations=["Lag-autoregressive time-series; does not resolve turbulent urban microclimates."]
        ),
        ModuleCapability(
            category="rain",
            operational_status=ModuleOperationalStatus.FULLY_WORKING,
            dataset_name="NASA POWER Precipitation / GPM IMERG Calibrated",
            provider_daac="NASA GES DISC / Langley ASDC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.FORECAST, ResultType.HISTORICAL_ANALYSIS],
            spatial_coverage="Global (0.5 x 0.625 degrees)",
            limitations=["Monthly aggregated precipitation; not suitable for flash-flood early warning."]
        ),
        ModuleCapability(
            category="wind",
            operational_status=ModuleOperationalStatus.FULLY_WORKING,
            dataset_name="NASA POWER 10-Meter Wind Speed",
            provider_daac="NASA Langley ASDC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.FORECAST, ResultType.HISTORICAL_ANALYSIS],
            spatial_coverage="Global (0.5 x 0.625 degrees)",
            limitations=["Grid-averaged scalar speed; topographic gust dynamics omitted."]
        ),
        ModuleCapability(
            category="fires",
            operational_status=ModuleOperationalStatus.OBSERVATION_ONLY,
            dataset_name="NASA FIRMS VIIRS Active Fire Detections",
            provider_daac="NASA LANCE / MODAPS",
            supported_result_types=[ResultType.OBSERVATION, ResultType.HISTORICAL_ANALYSIS],
            spatial_coverage="Global 375m",
            limitations=["Future prediction marked UNAVAILABLE. Active fire hotspots cannot predict future ignitions."]
        ),
        ModuleCapability(
            category="vegetation",
            operational_status=ModuleOperationalStatus.HISTORICAL_ANALYSIS,
            dataset_name="NASA MODIS MOD13A2 / MOD13Q1 NDVI",
            provider_daac="NASA LP DAAC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.HISTORICAL_ANALYSIS, ResultType.PROJECTION],
            spatial_coverage="Global 250m - 1km",
            limitations=["Cloud cover and atmospheric aerosols introduce temporal gaps."]
        ),
        ModuleCapability(
            category="ocean",
            operational_status=ModuleOperationalStatus.HISTORICAL_ANALYSIS,
            dataset_name="GHRSST Level 4 MUR Global Sea Surface Temperature",
            provider_daac="NASA PO.DAAC / OB.DAAC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.HISTORICAL_ANALYSIS, ResultType.PROJECTION],
            spatial_coverage="Global Oceans (0.01 - 0.25 degrees)",
            limitations=["Coastal boundaries subject to land-mask contamination."]
        ),
        ModuleCapability(
            category="ice",
            operational_status=ModuleOperationalStatus.HISTORICAL_ANALYSIS,
            dataset_name="NSIDC Sea Ice Index (G02135)",
            provider_daac="NASA NSIDC DAAC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.HISTORICAL_ANALYSIS, ResultType.PROJECTION],
            spatial_coverage="Polar Cryosphere (25km)",
            limitations=["Limited to polar regions; melt ponds introduce passive microwave uncertainty."]
        ),
        ModuleCapability(
            category="storms",
            operational_status=ModuleOperationalStatus.OBSERVATION_ONLY,
            dataset_name="NASA GES DISC GPM 3IMERGM Storm Observations",
            provider_daac="NASA GES DISC",
            supported_result_types=[ResultType.OBSERVATION, ResultType.HISTORICAL_ANALYSIS],
            spatial_coverage="Global 0.1 degree (60N - 60S)",
            limitations=["Cyclone track and intensity forecasting marked UNAVAILABLE per scientific guidelines."]
        )
    ]