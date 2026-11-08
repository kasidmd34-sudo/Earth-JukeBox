"""NASA GES DISC Tropical Cyclone and Extreme Rain Extraction Adapter."""
from typing import List, Dict, Any
from app.data.nasa_cmr import NASACMRClient
from app.data.nasa_power import NASAPowerAdapter
from app.schemas.responses import TimeSeriesPoint

class StormsDataAdapter:
    SHORT_NAME = "GPM_3IMERGDF"  # Daily Calibrated Precipitation (0.1 deg)

    @classmethod
    async def discover_storm_precipitation(
        cls, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        bbox = f"{longitude - 1.0:.2f},{latitude - 1.0:.2f},{longitude + 1.0:.2f},{latitude + 1.0:.2f}"
        try:
            return await NASACMRClient.discover_granules(
                short_name=cls.SHORT_NAME,
                bounding_box=bbox,
                start_date=start_date,
                end_date=end_date,
                page_size=5
            )
        except Exception:
            return []

    @classmethod
    async def fetch_extreme_storm_series(
        cls, latitude: float, longitude: float, start_year: int, end_year: int
    ) -> List[TimeSeriesPoint]:
        """Fetch GPM-calibrated precipitation records to identify severe convective storm precipitation."""
        payload = await NASAPowerAdapter.fetch_monthly_climatology(
            latitude, longitude, start_year, end_year, ["PRECTOTCORR"]
        )
        return NASAPowerAdapter.parse_monthly_series(payload, "PRECTOTCORR", "mm/day")
