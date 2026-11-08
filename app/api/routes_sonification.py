"""Standalone Sonification Parameter Generator route."""
from fastapi import APIRouter, HTTPException, Query
from app.schemas.requests import SonificationGenerationRequest
from app.schemas.sonification import SonificationSeries
from app.schemas.common import EnvironmentalCategory
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["Sonification"])


@router.post("/sonification", response_model=SonificationSeries)
async def generate_sonification(request: SonificationGenerationRequest):
    try:
        response = await PredictionService.execute_prediction(
            category=request.category.value,
            latitude=request.latitude,
            longitude=request.longitude,
            start_date=request.start_date,
            end_date=request.end_date,
            horizon=request.horizon if request.include_prediction else 0,
        )
        if response.sonification:
            return response.sonification
        raise HTTPException(status_code=404, detail="Unable to compute sonification for requested range.")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sonification generation error: {str(exc)}")


@router.get("/sonification", response_model=SonificationSeries)
async def generate_sonification_get(
    category: str = Query(..., description="Environmental category (e.g. temperature, rain, wind, fires, ocean, ice, storms, vegetation)"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    start_date: str = Query("2020-01-01"),
    end_date: str = Query("2023-12-31"),
    include_prediction: bool = Query(True),
    horizon: int = Query(12, ge=1, le=24),
):
    try:
        cat_enum = EnvironmentalCategory(category.lower())
    except ValueError:
        valid_cats = [e.value for e in EnvironmentalCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environmental category '{category}'. Supported: {valid_cats}",
        )
    req = SonificationGenerationRequest(
        category=cat_enum,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        include_prediction=include_prediction,
        horizon=horizon,
    )
    return await generate_sonification(req)
