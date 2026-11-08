"""FastAPI common dependency injection providers."""
from typing import Generator
from app.config import settings

def get_settings():
    return settings

def verify_nasa_client_ready():
    # Health gate dependency for live endpoints
    return True