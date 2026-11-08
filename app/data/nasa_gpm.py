"""NASA GPM / IMERG Precipitation Product Adapter (GES DISC)."""
from typing import Dict, Any, List
from app.data.nasa_power import NASAPowerAdapter
from app.schemas.responses import TimeSeriesPoint

class NASAGpmAdapter:
    """Uses GPM-calibrated PRECTOTCORR precipitation records from NASA."""
    
    @classmethod
    async def fetch_monthly_rainfall(
        cls, latitude: float, longitude: float, start_year: int, end_year: int
    ) -> List[TimeSeriesPoint]:
        payload = await NASAPowerAdapter.fetch_monthly_climatology(
            latitude, longitude, start_year, end_year, ["PRECTOTCORR"]
        )
        return NASAPowerAdapter.parse_monthly_series(payload, "PRECTOTCORR", "mm/day")