"""Prediction execution endpoints."""
from fastapi import APIRouter, HTTPException, Query
from app.schemas.requests import PredictionRequest
from app.schemas.responses import ModuleResponse
from app.schemas.common import EnvironmentalCategory
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["Predictions"])


@router.post("/predict", response_model=ModuleResponse)
async def predict_general(request: PredictionRequest):
    try:
        return await PredictionService.execute_prediction(
            category=request.category.value,
            latitude=request.latitude,
            longitude=request.longitude,
            start_date=request.start_date,
            end_date=request.end_date,
            horizon=request.horizon,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(exc)}")


@router.post("/predict/{condition}", response_model=ModuleResponse)
async def predict_condition_post(condition: str, request: PredictionRequest):
    try:
        cat_enum = EnvironmentalCategory(condition.lower())
    except ValueError:
        valid_cats = [e.value for e in EnvironmentalCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environmental category '{condition}'. Supported: {valid_cats}",
        )
    request.category = cat_enum
    return await predict_general(request)


@router.get("/predict/{condition}", response_model=ModuleResponse)
async def predict_condition_get(
    condition: str,
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    start_date: str = Query("2018-01-01"),
    end_date: str = Query("2023-12-31"),
    horizon: int = Query(12, ge=1, le=36),
):
    try:
        cat_enum = EnvironmentalCategory(condition.lower())
    except ValueError:
        valid_cats = [e.value for e in EnvironmentalCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environmental category '{condition}'. Supported: {valid_cats}",
        )
    req = PredictionRequest(
        category=cat_enum,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        horizon=horizon,
    )
    return await predict_general(req)
