"""Cross-module Environmental Intelligence endpoint."""
from fastapi import APIRouter, HTTPException, Query
from app.schemas.requests import IntelligenceRequest
from app.schemas.responses import IntelligenceReport
from app.services.intelligence_service import IntelligenceService

router = APIRouter(tags=["Intelligence"])


@router.post("/intelligence/analyze", response_model=IntelligenceReport)
async def analyze_intelligence(request: IntelligenceRequest):
    try:
        return await IntelligenceService.synthesize(
            latitude=request.latitude,
            longitude=request.longitude,
            start_date=request.start_date,
            end_date=request.end_date,
            location_name=request.location_name or "Target Coordinates",
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Intelligence synthesis error: {str(exc)}")


@router.get("/intelligence/analyze", response_model=IntelligenceReport)
async def analyze_intelligence_get(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    start_date: str = Query("2020-01-01"),
    end_date: str = Query("2023-12-31"),
    location_name: str = Query("Target Coordinates"),
):
    req = IntelligenceRequest(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        location_name=location_name,
    )
    return await analyze_intelligence(req)
