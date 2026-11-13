"""NASA PO.DAAC / OB.DAAC Ocean Observation Client (GHRSST MUR SST & NASA POWER TS)."""
from typing import List, Dict, Any, Tuple
from app.data.nasa_cmr import NASACMRClient
from app.data.nasa_power import NASAPowerAdapter
from app.schemas.responses import TimeSeriesPoint

class OceanDataAdapter:
    COLLECTION_SHORT_NAME = "MUR-JPL-L4-GLOB-v4.1"

    @classmethod
    async def discover_sst_granules(
        cls, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        bbox = f"{longitude - 0.5:.2f},{latitude - 0.5:.2f},{longitude + 0.5:.2f},{latitude + 0.5:.2f}"
        try:
            return await NASACMRClient.discover_granules(
                short_name=cls.COLLECTION_SHORT_NAME,
                bounding_box=bbox,
                start_date=start_date,
                end_date=end_date,
                page_size=5
            )
        except Exception:
            return []

    @classmethod
    async def fetch_sst_series(
        cls, latitude: float, longitude: float, start_year: int, end_year: int
    ) -> List[TimeSeriesPoint]:
        """Return NASA POWER surface temperature (TS) as a proxy.

        This is NOT the GHRSST MUR analysed_sst product. Use
        discover_sst_granules to locate actual MUR granules.
        """
        payload = await NASAPowerAdapter.fetch_monthly_climatology(
            latitude, longitude, start_year, end_year, ["TS"]
        )
        return NASAPowerAdapter.parse_monthly_series(payload, "TS", "degrees_Celsius")
