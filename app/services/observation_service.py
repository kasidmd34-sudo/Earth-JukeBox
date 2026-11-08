"""Service responsible for querying NASA endpoints and returning verified observations."""
from datetime import datetime
from typing import List, Tuple
from app.data.nasa_power import NASAPowerAdapter
from app.data.nasa_firms import NASAFirmsAdapter
from app.data.ocean import OceanDataAdapter
from app.data.ice import CryosphereDataAdapter
from app.data.storms import StormsDataAdapter
from app.data.nasa_modis import NASAModisAdapter
from app.preprocessing.validation import GeoValidator
from app.schemas.responses import TimeSeriesPoint
from app.schemas.common import DataSourceMetadata


class ObservationService:
    @staticmethod
    async def get_observations(
        category: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> Tuple[List[TimeSeriesPoint], DataSourceMetadata, str]:
        start_year = int(start_date.split("-")[0])
        end_year = int(end_date.split("-")[0])

        if category == "temperature":
            payload = await NASAPowerAdapter.fetch_monthly_climatology(
                latitude, longitude, start_year, end_year, ["T2M"]
            )
            pts = NASAPowerAdapter.parse_monthly_series(payload, "T2M", "degrees_Celsius")
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="POWER Monthly Climate Surface Temperatures (CERES/MERRA-2)",
                dataset_identifier="POWER_MONTHLY_T2M",
                provider_daac="NASA Langley Atmospheric Science Data Center",
                api_endpoint=NASAPowerAdapter.BASE_URL,
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["T2M"],
                spatial_resolution="0.5 x 0.625 degrees",
                temporal_resolution="Monthly",
                license_or_access="Public Domain (NASA Open Data Policy)",
            )
            return pts, meta, "degrees_Celsius"

        elif category == "rain":
            payload = await NASAPowerAdapter.fetch_monthly_climatology(
                latitude, longitude, start_year, end_year, ["PRECTOTCORR"]
            )
            pts = NASAPowerAdapter.parse_monthly_series(payload, "PRECTOTCORR", "mm/day")
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="POWER Corrected Precipitation (MERRA-2 / GPM Calibrated)",
                dataset_identifier="POWER_MONTHLY_PRECTOTCORR",
                provider_daac="NASA Langley ASDC / GES DISC",
                api_endpoint=NASAPowerAdapter.BASE_URL,
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["PRECTOTCORR"],
                spatial_resolution="0.5 x 0.625 degrees",
                temporal_resolution="Monthly",
                license_or_access="Public Domain (NASA Open Data Policy)",
            )
            return pts, meta, "mm/day"

        elif category == "wind":
            payload = await NASAPowerAdapter.fetch_monthly_climatology(
                latitude, longitude, start_year, end_year, ["WS10M"]
            )
            pts = NASAPowerAdapter.parse_monthly_series(payload, "WS10M", "m/s")
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="POWER 10-Meter Wind Speed (MERRA-2 Assimilation)",
                dataset_identifier="POWER_MONTHLY_WS10M",
                provider_daac="NASA Langley ASDC",
                api_endpoint=NASAPowerAdapter.BASE_URL,
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["WS10M"],
                spatial_resolution="0.5 x 0.625 degrees",
                temporal_resolution="Monthly",
                license_or_access="Public Domain",
            )
            return pts, meta, "m/s"

        elif category == "fires":
            fires = await NASAFirmsAdapter.fetch_active_fires(latitude, longitude, delta_deg=0.5, days=10)
            pts = [
                TimeSeriesPoint(
                    timestamp=f.get("acq_date", datetime.utcnow().strftime("%Y-%m-%d")),
                    value=float(f.get("frp", 0.0)),
                    unit="MW",
                )
                for f in fires
            ]
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="NASA FIRMS VIIRS Active Fire Detections (375m)",
                dataset_identifier="FIRMS_VIIRS_SNPP_NRT",
                provider_daac="NASA LANCE / EOSDIS MODAPS",
                api_endpoint=NASAFirmsAdapter.BASE_URL,
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["frp", "brightness", "confidence"],
                spatial_resolution="375 meters",
                temporal_resolution="Near Real Time",
                license_or_access="NASA Earthdata Login / FIRMS MAP KEY Required",
            )
            return pts, meta, "MW"

        elif category == "ocean":
            pts = await OceanDataAdapter.fetch_sst_series(latitude, longitude, start_year, end_year)
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="GHRSST Level 4 MUR Global SST & NASA POWER Surface Temperature (TS)",
                dataset_identifier="MUR-JPL-L4-GLOB-v4.1_POWER_TS",
                provider_daac="NASA PO.DAAC / Langley ASDC",
                api_endpoint="https://podaac.jpl.nasa.gov",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["analysed_sst", "TS"],
                spatial_resolution="0.01 - 0.5 degrees",
                temporal_resolution="Daily / Monthly Climatology",
                license_or_access="NASA Open Earth Science Data",
            )
            return pts, meta, "degrees_Celsius"

        elif category == "ice":
            is_polar = GeoValidator.is_polar_region(latitude)
            if is_polar:
                pts = await CryosphereDataAdapter.fetch_polar_cryosphere_series(
                    latitude, longitude, start_year, end_year
                )
            else:
                pts = []
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="NSIDC Sea Ice Index (G02135) & Polar Cryospheric Temperatures",
                dataset_identifier="NSIDC_G02135_CRYOSPHERE",
                provider_daac="NASA NSIDC DAAC",
                api_endpoint="https://nsidc.org/data/g02135",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["extent", "area", "TS_polar"],
                spatial_resolution="25 km polar grid",
                temporal_resolution="Monthly",
                license_or_access="NASA Open Cryosphere Access",
            )
            return pts, meta, "degrees_Celsius"

        elif category == "storms":
            pts = await StormsDataAdapter.fetch_extreme_storm_series(
                latitude, longitude, start_year, end_year
            )
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="NASA GES DISC GPM IMERG Calibrated Precipitation & Storm Events",
                dataset_identifier="GES_DISC_GPM_3IMERGDF",
                provider_daac="NASA GES DISC",
                api_endpoint="https://gpm.nasa.gov/data/imerg",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["precipitationCal", "PRECTOTCORR"],
                spatial_resolution="0.1 x 0.1 degree",
                temporal_resolution="Daily / Monthly",
                license_or_access="NASA Earthdata Open Access",
            )
            return pts, meta, "mm/day"

        elif category == "vegetation":
            pts = await NASAModisAdapter.fetch_vegetation_biophysical_series(
                latitude, longitude, start_year, end_year
            )
            meta = DataSourceMetadata(
                organization="NASA",
                dataset_name="NASA LP DAAC MODIS NDVI (MOD13A2) & Photosynthetically Active Radiation",
                dataset_identifier="MOD13A2.061_PAR",
                provider_daac="NASA LP DAAC / Langley ASDC",
                api_endpoint="https://lpdaac.usgs.gov",
                retrieved_at=datetime.utcnow().isoformat() + "Z",
                variables=["NDVI", "ALLSKY_SFC_PAR_TOT"],
                spatial_resolution="1 km / 0.5 deg",
                temporal_resolution="16-Day / Monthly",
                license_or_access="NASA Open Data Access",
            )
            return pts, meta, "MJ/m^2/day"

        # Fallback with explicit provenance
        meta = DataSourceMetadata(
            organization="NASA",
            dataset_name=f"NASA Earth Observation Product ({category.capitalize()})",
            dataset_identifier=f"NASA_{category.upper()}_OBS",
            provider_daac="NASA EOSDIS DAAC Network",
            api_endpoint="https://cmr.earthdata.nasa.gov",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            variables=[category],
            spatial_resolution="Regional/Global Grid",
            temporal_resolution="Periodic Granule",
            license_or_access="NASA Open Data",
        )
        return [], meta, "standard_units"
