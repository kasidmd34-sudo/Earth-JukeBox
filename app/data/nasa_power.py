"""NASA POWER API adapter (Prediction Of Worldwide Energy Resources).
Provides validated, analysis-ready solar, meteorological, and surface data.
"""
from datetime import datetime
from typing import Dict, Any, List
from app.data.nasa_client import nasa_client
from app.schemas.responses import TimeSeriesPoint

class NASAPowerAdapter:
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    @classmethod
    async def fetch_monthly_climatology(
        cls,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        variables: List[str]
    ) -> Dict[str, Any]:
        params = {
            "parameters": ",".join(variables),
            "community": "AG",
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": str(start_year),
            "end": str(end_year),
            "format": "JSON"
        }
        return await nasa_client.get_with_retry(cls.BASE_URL, params=params)

    @classmethod
    def parse_monthly_series(
        cls,
        payload: Dict[str, Any],
        variable_name: str,
        unit: str
    ) -> List[TimeSeriesPoint]:
        points: List[TimeSeriesPoint] = []
        try:
            param_dict = payload["properties"]["parameter"][variable_name]
        except KeyError:
            return points

        for date_key, val in sorted(param_dict.items()):
            # POWER monthly format is YYYYMM; 13th month is annual average
            if len(date_key) == 6 and not date_key.endswith("13"):
                year = date_key[:4]
                month = date_key[4:]
                timestamp = f"{year}-{month}-01"
                float_val = float(val)
                # NASA POWER uses -999.0 as missing value flag
                if float_val != -999.0:
                    points.append(
                        TimeSeriesPoint(
                            timestamp=timestamp,
                            value=float_val,
                            unit=unit
                        )
                    )
        return points