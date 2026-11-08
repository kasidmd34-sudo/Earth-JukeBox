"""Geographic location resolution and multi-hazard observation summary."""
from typing import Dict, Any
from app.preprocessing.validation import GeoValidator
from app.services.observation_service import ObservationService

class LocationService:
    @classmethod
    async def analyze_location(
        cls, latitude: float, longitude: float, location_name: str = "Target"
    ) -> Dict[str, Any]:
        is_valid, msg = GeoValidator.validate_coordinates(latitude, longitude)
        if not is_valid:
            raise ValueError(msg)

        is_polar = GeoValidator.is_polar_region(latitude)
        
        # Test temperature observation
        t_pts, _, _ = await ObservationService.get_observations(
            "temperature", latitude, longitude, "2022-01-01", "2023-12-31"
        )
        
        return {
            "location_name": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "is_polar_region": is_polar,
            "cryosphere_monitoring_active": is_polar,
            "observations_available": len(t_pts) > 0,
            "sample_point_count": len(t_pts),
            "recommended_spatial_grid": "0.5 x 0.625 degrees (NASA POWER standard grid)"
        }