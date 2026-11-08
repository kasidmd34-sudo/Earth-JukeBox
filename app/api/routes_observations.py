"""NASA environmental observation retrieval route."""
from fastapi import APIRouter, HTTPException, Query
from app.schemas.requests import ObservationRequest
from app.schemas.responses import ModuleResponse, UncertaintyInfo
from app.schemas.common import GeoLocation, ResultType, EnvironmentalCategory
from app.services.observation_service import ObservationService
from app.services.sonification_service import SonificationService

router = APIRouter(tags=["Observations"])


async def _handle_observation_query(category: str, latitude: float, longitude: float, start_date: str, end_date: str) -> ModuleResponse:
    try:
        pts, meta, unit = await ObservationService.get_observations(
            category=category,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )
        sonification_data = SonificationService.generate_sonification_series(category, pts)
        
        # Result type classification
        result_type = ResultType.OBSERVATION
        if not pts:
            result_type = ResultType.UNAVAILABLE

        return ModuleResponse(
            status="success",
            condition=category,
            result_type=result_type,
            location=GeoLocation(latitude=latitude, longitude=longitude),
            unit=unit,
            data_source=meta,
            model=None,
            historical_data=pts,
            predictions=[],
            uncertainty=UncertaintyInfo(
                available=False,
                description="Raw NASA satellite and reanalysis observations contain sensor measurement uncertainty.",
            ),
            sonification=sonification_data,
            limitations=[
                "Observations are provided directly from NASA missions and reanalysis records.",
                "Subject to spatial resolution and instrument calibration thresholds.",
            ],
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Observation retrieval error: {str(exc)}")


@router.post("/observations", response_model=ModuleResponse)
async def get_observations(request: ObservationRequest):
    return await _handle_observation_query(
        category=request.category.value,
        latitude=request.latitude,
        longitude=request.longitude,
        start_date=request.start_date,
        end_date=request.end_date,
    )


@router.get("/observations", response_model=ModuleResponse)
async def get_observations_get(
    category: str = Query(..., description="Environmental category (e.g. temperature, rain, wind, fires, ocean, ice, storms, vegetation)"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    start_date: str = Query("2022-01-01"),
    end_date: str = Query("2023-12-31"),
):
    try:
        cat_enum = EnvironmentalCategory(category.lower())
    except ValueError:
        valid_cats = [e.value for e in EnvironmentalCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environmental category '{category}'. Supported: {valid_cats}",
        )
    req = ObservationRequest(
        category=cat_enum,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
    )
    return await get_observations(req)
