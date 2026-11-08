"""NASA LP DAAC MODIS Vegetation Product (MOD13A2 / MOD13Q1) Discovery Adapter."""
from typing import List, Dict, Any
from app.data.nasa_cmr import NASACMRClient
from app.data.nasa_power import NASAPowerAdapter
from app.schemas.responses import TimeSeriesPoint

class NASAModisAdapter:
    SHORT_NAME = "MOD13A2"  # Terra 16-Day 1km NDVI

    @classmethod
    async def discover_ndvi_granules(
        cls, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        bbox = f"{longitude - 0.2:.3f},{latitude - 0.2:.3f},{longitude + 0.2:.3f},{latitude + 0.2:.3f}"
        try:
            return await NASACMRClient.discover_granules(
                short_name=cls.SHORT_NAME,
                bounding_box=bbox,
                start_date=start_date,
                end_date=end_date,
                page_size=10
            )
        except Exception:
            return []

    @classmethod
    async def fetch_vegetation_biophysical_series(
        cls, latitude: float, longitude: float, start_year: int, end_year: int
    ) -> List[TimeSeriesPoint]:
        """Fetch photosynthetically active radiation (ALLSKY_SFC_PAR_TOT) from NASA POWER."""
        payload = await NASAPowerAdapter.fetch_monthly_climatology(
            latitude, longitude, start_year, end_year, ["ALLSKY_SFC_PAR_TOT"]
        )
        return NASAPowerAdapter.parse_monthly_series(payload, "ALLSKY_SFC_PAR_TOT", "MJ/m^2/day")
