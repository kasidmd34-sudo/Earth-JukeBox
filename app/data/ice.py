"""NASA NSIDC DAAC Sea Ice Extent Product Client (G02135 & Polar Climatology)."""
from typing import List, Dict, Any
from app.data.nasa_cmr import NASACMRClient
from app.data.nasa_power import NASAPowerAdapter
from app.schemas.responses import TimeSeriesPoint

class CryosphereDataAdapter:
    SHORT_NAME = "G02135"  # Sea Ice Index Daily and Monthly

    @classmethod
    async def discover_sea_ice_data(
        cls, hemisphere: str = "N", start_date: str = "2020-01-01", end_date: str = "2023-12-31"
    ) -> List[Dict[str, Any]]:
        bbox = "-180,60,180,90" if hemisphere == "N" else "-180,-90,180,-60"
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
    async def fetch_polar_cryosphere_series(
        cls, latitude: float, longitude: float, start_year: int, end_year: int
    ) -> List[TimeSeriesPoint]:
        """Fetch polar surface temperature indicating freeze/melt status from NASA records."""
        payload = await NASAPowerAdapter.fetch_monthly_climatology(
            latitude, longitude, start_year, end_year, ["TS"]
        )
        return NASAPowerAdapter.parse_monthly_series(payload, "TS", "degrees_Celsius")
