"""Location environmental analysis endpoint."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.location_service import LocationService

router = APIRouter(tags=["Location"])


class LocationQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    location_name: str = "Selected Location"


@router.post("/location/analyze")
async def analyze_location(query: LocationQuery):
    try:
        return await LocationService.analyze_location(query.latitude, query.longitude, query.location_name)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/location/analyze")
async def analyze_location_get(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    location_name: str = Query("Selected Location"),
):
    query = LocationQuery(latitude=latitude, longitude=longitude, location_name=location_name)
    return await analyze_location(query)
