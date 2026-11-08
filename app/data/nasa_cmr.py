"""NASA Common Metadata Repository (CMR) Client for dataset granule discovery."""
from typing import Dict, Any, List
from app.data.nasa_client import nasa_client

class NASACMRClient:
    CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

    @classmethod
    async def discover_granules(
        cls,
        short_name: str,
        bounding_box: str,
        start_date: str,
        end_date: str,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        params = {
            "short_name": short_name,
            "bounding_box": bounding_box,
            "temporal": f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
            "page_size": page_size
        }
        res = await nasa_client.get_with_retry(cls.CMR_SEARCH_URL, params=params)
        return res.get("feed", {}).get("entry", [])