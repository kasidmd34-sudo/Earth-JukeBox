"""NASA environmental observation retrieval route."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
import csv, io, json
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


@router.get("/data/export/{category}")
async def export_historical_data(
    category: str,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: str = Query("2001-01-01"),
    end_date: str = Query("2025-12-31"),
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Export exactly the observations returned by the configured adapter."""
    try:
        cat_enum = EnvironmentalCategory(category.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported category: {category}")
    try:
        points, metadata, unit = await ObservationService.get_observations(
            category=cat_enum.value,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not retrieve source observations: {exc}") from exc
    records = [
        {"timestamp": point.timestamp, "value": point.value, "unit": point.unit or unit}
        for point in points
    ]
    payload = {
        "category": cat_enum.value,
        "location": {"latitude": latitude, "longitude": longitude},
        "requested_period": {"start_date": start_date, "end_date": end_date},
        "unit": unit,
        "data_source": metadata.model_dump(mode="json"),
        "record_count": len(records),
        "records": records,
        "notice": "Contains only records returned by the configured adapter; coverage and resolution are defined by source metadata. No missing periods are fabricated.",
    }
    safe_category = cat_enum.value
    if format == "json":
        return Response(
            content=json.dumps(payload, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="earthjukebox_{safe_category}_history.json"'},
        )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["timestamp", "value", "unit"])
    writer.writeheader()
    writer.writerows(records)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="earthjukebox_{safe_category}_history.csv"'},
    )
