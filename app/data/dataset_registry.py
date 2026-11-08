"""NASA Dataset Inventory Catalog for Earth Jukebox."""
from typing import Dict, Any, List

DATASET_INVENTORY: Dict[str, Dict[str, Any]] = {
    "temperature": {
        "dataset_name": "NASA POWER Monthly Climate Temperatures (MERRA-2 / CERES)",
        "dataset_id": "POWER_MONTHLY_T2M",
        "daac": "NASA Langley ASDC",
        "variables": ["T2M", "T2M_MIN", "T2M_MAX"],
        "units": "degrees_Celsius",
        "spatial_res": "0.5 x 0.625 degrees",
        "temporal_res": "Monthly",
        "auth": "None (Open Access)"
    },
    "rain": {
        "dataset_name": "NASA POWER / GPM Corrected Precipitation",
        "dataset_id": "POWER_MONTHLY_PRECTOTCORR",
        "daac": "NASA GES DISC / Langley ASDC",
        "variables": ["PRECTOTCORR"],
        "units": "mm/day",
        "spatial_res": "0.5 x 0.625 degrees",
        "temporal_res": "Monthly",
        "auth": "None (Open Access)"
    },
    "wind": {
        "dataset_name": "NASA POWER 10-Meter Wind Speed & Direction",
        "dataset_id": "POWER_MONTHLY_WS10M",
        "daac": "NASA Langley ASDC",
        "variables": ["WS10M"],
        "units": "m/s",
        "spatial_res": "0.5 x 0.625 degrees",
        "temporal_res": "Monthly",
        "auth": "None (Open Access)"
    },
    "fires": {
        "dataset_name": "NASA FIRMS NRT Active Fire Hotspots (VIIRS 375m)",
        "dataset_id": "FIRMS_VIIRS_SNPP_NRT",
        "daac": "NASA LANCE / MODAPS",
        "variables": ["frp", "confidence", "brightness"],
        "units": "MW",
        "spatial_res": "375 meters",
        "temporal_res": "Near Real Time (NRT)",
        "auth": "FIRMS MAP_KEY"
    },
    "vegetation": {
        "dataset_name": "MODIS Terra Vegetation Indices 16-Day L3 (MOD13A2)",
        "dataset_id": "MOD13A2.061",
        "daac": "NASA LP DAAC",
        "variables": ["NDVI", "EVI"],
        "units": "dimensionless (scale 0.0001)",
        "spatial_res": "1 km",
        "temporal_res": "16-day",
        "auth": "NASA Earthdata Login"
    },
    "ocean": {
        "dataset_name": "GHRSST Level 4 MUR Global 0.01-deg SST Analysis",
        "dataset_id": "MUR-JPL-L4-GLOB-v4.1",
        "daac": "NASA PO.DAAC",
        "variables": ["analysed_sst", "sst_anomaly"],
        "units": "Kelvin / degrees_Celsius",
        "spatial_res": "0.01 degrees (~1km)",
        "temporal_res": "Daily",
        "auth": "NASA Earthdata Login"
    },
    "ice": {
        "dataset_name": "NSIDC Sea Ice Index (G02135)",
        "dataset_id": "G02135",
        "daac": "NASA NSIDC DAAC",
        "variables": ["extent", "area"],
        "units": "million_sq_km",
        "spatial_res": "25 km",
        "temporal_res": "Daily / Monthly",
        "auth": "None / Open Earthdata"
    },
    "storms": {
        "dataset_name": "GPM IMERG Final Precipitation (GPM_3IMERGDF)",
        "dataset_id": "GPM_3IMERGDF.07",
        "daac": "NASA GES DISC",
        "variables": ["precipitationCal"],
        "units": "mm/hr",
        "spatial_res": "0.1 degree",
        "temporal_res": "Daily",
        "auth": "NASA Earthdata Login"
    }
}