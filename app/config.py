"""Central application configuration using Pydantic Settings."""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080,null"
    
    # NASA Credentials
    NASA_EARTHDATA_TOKEN: str = ""
    NASA_FIRMS_MAP_KEY: str = ""

    # Gemini AI - report summaries only
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_TIMEOUT_SECONDS: float = 30.0

    # Storage & Network
    CACHE_DIR: str = "./data/cache"
    MODEL_ARTIFACTS_DIR: str = "./artifacts/models"
    EVALUATION_DIR: str = "./artifacts/evaluations"
    HTTP_TIMEOUT_SECONDS: float = 30.0
    HTTP_MAX_RETRIES: int = 3

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.MODEL_ARTIFACTS_DIR, exist_ok=True)
os.makedirs(settings.EVALUATION_DIR, exist_ok=True)