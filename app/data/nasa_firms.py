"""NASA FIRMS API adapter (Fire Information for Resource Management System).
Adheres strictly to NASA guidelines: active fire observations only, never predicting wildfire events.
"""
from typing import Dict, Any, List
from app.data.nasa_client import nasa_client
from app.config import settings

class NASAFirmsAdapter:
    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    @classmethod
    async def fetch_active_fires(
        cls,
        latitude: float,
        longitude: float,
        delta_deg: float = 1.0,
        days: int = 10
    ) -> List[Dict[str, Any]]:
        # Compute bounding box
        min_lat = max(-90.0, latitude - delta_deg)
        max_lat = min(90.0, latitude + delta_deg)
        min_lon = max(-180.0, longitude - delta_deg)
        max_lon = min(180.0, longitude + delta_deg)
        
        map_key = settings.NASA_FIRMS_MAP_KEY
        if not map_key:
            # Fallback metadata reporting if MAP_KEY is not set
            return []

        endpoint = f"https://firms.modaps.eosdis.nasa.gov/api/area/json/{map_key}/VIIRS_SNPP_NRT/{min_lon},{min_lat},{max_lon},{max_lat}/{days}"
        try:
            data = await nasa_client.get_with_retry(endpoint, use_cache=True)
            return data if isinstance(data, list) else []
        except Exception:
            return []