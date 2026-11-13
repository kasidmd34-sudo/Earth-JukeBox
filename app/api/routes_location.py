"""Location environmental analysis endpoint."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.location_service import LocationService
import httpx

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

@router.get("/location/search")
async def search_location(q: str = Query(..., min_length=2, max_length=160)):
    """Resolve a place name to coordinates using OpenStreetMap Nominatim."""
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Enter a place name.")
    headers = {"User-Agent": "EarthJukebox/1.0 (NASA Space Apps educational project)"}
    try:
        async with httpx.AsyncClient(timeout=12.0, headers=headers) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1},
            )
            response.raise_for_status()
            results = response.json()
        return {
            "query": query,
            "results": [
                {
                    "display_name": item.get("display_name", ""),
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                    "type": item.get("type"),
                    "osm_type": item.get("osm_type"),
                    "osm_id": item.get("osm_id"),
                }
                for item in results if item.get("lat") and item.get("lon")
            ],
            "attribution": "© OpenStreetMap contributors, Nominatim",
        }
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Place search is temporarily unavailable: {exc}") from exc
