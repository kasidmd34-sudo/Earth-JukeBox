"""Dataset provenance, catalog metadata, and model registry endpoints."""
from fastapi import APIRouter, HTTPException
from app.data.dataset_registry import DATASET_INVENTORY
from app.utils.provenance import ProvenanceAuditor
from app.models.registry import model_registry

router = APIRouter(tags=["Metadata"])


@router.get("/datasets")
def list_datasets():
    """Retrieve full catalog inventory of verified NASA environmental datasets."""
    return DATASET_INVENTORY


@router.get("/metadata/{condition}")
def get_condition_metadata(condition: str):
    """Retrieve NASA product specification, DAAC archive, and resolution for a module."""
    cond_clean = condition.lower()
    if cond_clean not in DATASET_INVENTORY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown category '{condition}'. Available: {list(DATASET_INVENTORY.keys())}",
        )
    return DATASET_INVENTORY[cond_clean]


@router.get("/provenance/{condition}")
def get_provenance(condition: str):
    """Retrieve strict data provenance lineage, mission citation, and DAAC archive info."""
    cond_clean = condition.lower()
    return ProvenanceAuditor.get_provenance(cond_clean)


@router.get("/models")
def list_models():
    """List operational ML models and supported statistical estimation algorithms."""
    supported = ["temperature", "rain", "wind", "ocean", "vegetation"]
    info = {}
    for cat in supported:
        m = model_registry.get_or_create_model(cat)
        info[cat] = {
            "model_name": m.name,
            "version": m.version,
            "algorithm": "Ridge Regressor with Lag Auto-regression [1, 2, 12] + Cyclical Calendar Features",
            "is_trained": m.is_trained,
            "metrics": m.metrics,
            "validation": "80/20 Chronological Holdout Split (Zero Future Leakage)",
            "uncertainty": "Empirical Residual Bootstrapping (95% Confidence Interval)",
            "baseline": "Seasonal-Naive (Lag-12)",
        }
    return info


@router.get("/models/{condition}")
def get_model_metadata(condition: str):
    """Retrieve model specification for a specific environmental condition."""
    cond_clean = condition.lower()
    if cond_clean in ("fires", "storms"):
        return {
            "condition": cond_clean,
            "status": "UNAVAILABLE",
            "reason": (
                "Predictive ML modeling is strictly disabled for active fires and storm tracks "
                "per NASA scientific governance standards."
            ),
        }
    m = model_registry.get_or_create_model(cond_clean)
    return {
        "condition": cond_clean,
        "model_name": m.name,
        "version": m.version,
        "is_trained": m.is_trained,
        "metrics": m.metrics,
        "validation_strategy": "Chronological 80/20 Holdout",
        "baseline_comparison": "Seasonal-Naive (Lag-12)",
    }
