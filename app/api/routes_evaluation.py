"""Model performance evaluation endpoint."""
from fastapi import APIRouter, HTTPException, Query
from app.services.evaluation_service import EvaluationService

router = APIRouter(tags=["Evaluation"])


@router.get("/evaluate/{condition}")
async def evaluate_condition(
    condition: str,
    lat: float = Query(19.0760, ge=-90.0, le=90.0),
    lon: float = Query(72.8777, ge=-180.0, le=180.0),
    start_date: str = Query("2018-01-01"),
    end_date: str = Query("2023-12-31"),
):
    cond_clean = condition.lower()
    if cond_clean in ("fires", "storms"):
        return {
            "category": cond_clean,
            "status": "not_applicable",
            "message": f"Predictive modeling is strictly restricted for {cond_clean} per project scientific guidelines.",
            "beats_baseline": False,
        }
    try:
        return await EvaluationService.evaluate_module(cond_clean, lat, lon, start_date, end_date)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(exc)}")
