"""Geographic and spatial coordinate validation."""
from typing import Tuple

class GeoValidator:
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> Tuple[bool, str]:
        if not (-90.0 <= latitude <= 90.0):
            return False, f"Latitude {latitude} is outside valid WGS84 range [-90.0, 90.0]."
        if not (-180.0 <= longitude <= 180.0):
            return False, f"Longitude {longitude} is outside valid WGS84 range [-180.0, 180.0]."
        return True, "Coordinates are valid."

    @staticmethod
    def is_polar_region(latitude: float) -> bool:
        return abs(latitude) >= 60.0