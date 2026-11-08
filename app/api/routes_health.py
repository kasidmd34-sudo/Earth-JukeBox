"""System health, service readiness, and root endpoints."""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["System"])

@router.get("/")
def get_root():
    return {
        "application": "Earth Jukebox",
        "description": "NASA-Powered Environmental Intelligence, Prediction & Sonification Engine",
        "version": "2.0.0",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nasa_policy_compliance": "STRICT_NASA_ONLY"
    }