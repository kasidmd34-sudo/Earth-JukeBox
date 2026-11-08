"""Prediction Service managing model execution, uncertainty bounds, and scientific limitations."""
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
from app.services.observation_service import ObservationService
from app.services.sonification_service import SonificationService
from app.models.registry import model_registry
from app.preprocessing.cleaning import DataCleaner
from app.preprocessing.validation import GeoValidator
from app.schemas.responses import (
    ModuleResponse, TimeSeriesPoint, UncertaintyInfo
)
from app.schemas.common import (
    GeoLocation, ResultType, ModelMetadata
)

# Strict scientific limitations registry
CATEGORY_LIMITATIONS: Dict[str, List[str]] = {
    "temperature": [
        "Statistical climate forecast based on lag-autoregressive historical NASA POWER observations.",
        "Does not simulate synoptic weather systems or rapid microclimate fluctuations.",
    ],
    "rain": [
        "Precipitation projection based on statistical seasonal autoregression.",
        "Cannot be used as an operational convective storm or flood warning system.",
    ],
    "wind": [
        "10-meter wind speed projection represents spatial cell average (0.5 x 0.625 degrees).",
        "Local topographic turbulence or gust dynamics are not resolved.",
    ],
    "fires": [
        "SCIENTIFIC RESTRICTION: Active fire detections cannot be extrapolated into future dates.",
        "Future fire risk forecast is marked UNAVAILABLE per project scientific governance.",
        "Thermal anomalies represent near-real-time observations, not predictive ignition models.",
    ],
    "storms": [
        "SCIENTIFIC RESTRICTION: Satellite precipitation observations do not support deterministic cyclone track forecasts.",
        "Cyclone track, intensity, and landfall predictions are marked UNAVAILABLE per scientific standards.",
    ],
    "ocean": [
        "Historical sea surface temperature analysis from GHRSST MUR and NASA POWER TS climatology.",
        "Coastal boundaries may be subject to land-mask contamination.",
    ],
    "ice": [
        "Sea ice monitoring from NSIDC DAAC Sea Ice Index and polar cryosphere observations.",
        "Applicable exclusively to polar regions (|latitude| >= 60.0 degrees).",
    ],
    "vegetation": [
        "Biophysical vegetation seasonality and photosynthetically active radiation (PAR).",
        "Cloud cover and atmospheric aerosols introduce temporal gaps in optical sensors.",
    ],
}


class PredictionService:
    @classmethod
    async def execute_prediction(
        cls,
        category: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        horizon: int,
    ) -> ModuleResponse:
        # Validate coordinates first
        valid, msg = GeoValidator.validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(msg)

        pts, meta, unit = await ObservationService.get_observations(
            category, latitude, longitude, start_date, end_date
        )

        limitations = CATEGORY_LIMITATIONS.get(
            category,
            ["General physical observation limitations apply. Satellite sensor resolution applies."]
        )

        # NASA Worldview deep link URL for spatial verification
        min_lon = max(-180.0, longitude - 2.0)
        max_lon = min(180.0, longitude + 2.0)
        min_lat = max(-90.0, latitude - 2.0)
        max_lat = min(90.0, latitude + 2.0)
        worldview_url = f"https://worldview.earthdata.nasa.gov/?v={min_lon:.2f},{min_lat:.2f},{max_lon:.2f},{max_lat:.2f}&t={end_date}"

        # 1. Scientific Restriction: FIRES must NEVER produce synthetic future forecasts
        if category == "fires":
            sonif = SonificationService.generate_sonification_series(category, pts)
            return ModuleResponse(
                status="success",
                condition=category,
                result_type=ResultType.OBSERVATION if pts else ResultType.UNAVAILABLE,
                location=GeoLocation(latitude=latitude, longitude=longitude),
                unit=unit,
                data_source=meta,
                model=None,
                historical_data=pts,
                predictions=[],
                uncertainty=UncertaintyInfo(
                    available=False,
                    description="Future active fire forecasting is scientifically unsupported; thermal hotspots indicate observed anomalies only.",
                ),
                sonification=sonif,
                nasa_worldview_url=worldview_url,
                limitations=limitations,
            )

        # 2. Scientific Restriction: STORMS must NEVER produce deterministic future track forecasts
        if category == "storms":
            sonif = SonificationService.generate_sonification_series(category, pts)
            return ModuleResponse(
                status="success",
                condition=category,
                result_type=ResultType.HISTORICAL_ANALYSIS if pts else ResultType.UNAVAILABLE,
                location=GeoLocation(latitude=latitude, longitude=longitude),
                unit=unit,
                data_source=meta,
                model=None,
                historical_data=pts,
                predictions=[],
                uncertainty=UncertaintyInfo(
                    available=False,
                    description="Cyclone tracks and landfall forecasts are marked UNAVAILABLE per scientific standard.",
                ),
                sonification=sonif,
                nasa_worldview_url=worldview_url,
                limitations=limitations,
            )

        # 3. Scientific Restriction: ICE is strictly polar (|lat| >= 60)
        if category == "ice":
            is_polar = GeoValidator.is_polar_region(latitude)
            if not is_polar or not pts:
                return ModuleResponse(
                    status="success",
                    condition=category,
                    result_type=ResultType.UNAVAILABLE,
                    location=GeoLocation(latitude=latitude, longitude=longitude),
                    unit=unit,
                    data_source=meta,
                    model=None,
                    historical_data=[],
                    predictions=[],
                    uncertainty=UncertaintyInfo(
                        available=False,
                        description="Cryosphere sea ice monitoring is restricted to polar latitudes (|lat| >= 60.0 deg).",
                    ),
                    sonification=SonificationService.generate_sonification_series(category, []),
                    nasa_worldview_url=worldview_url,
                    limitations=limitations + ["Non-polar coordinates: Cryospheric ice pack absent."],
                )
            # Polar historical analysis
            return ModuleResponse(
                status="success",
                condition=category,
                result_type=ResultType.HISTORICAL_ANALYSIS,
                location=GeoLocation(latitude=latitude, longitude=longitude),
                unit=unit,
                data_source=meta,
                model=None,
                historical_data=pts,
                predictions=[],
                uncertainty=UncertaintyInfo(
                    available=False,
                    description="Polar ice sheet / SST historical analysis.",
                ),
                sonification=SonificationService.generate_sonification_series(category, pts),
                nasa_worldview_url=worldview_url,
                limitations=limitations,
            )

        # 4. Modules supporting HISTORICAL_ANALYSIS / PROJECTION (ocean, vegetation)
        if category in ("ocean", "vegetation") and horizon == 0:
            return ModuleResponse(
                status="success",
                condition=category,
                result_type=ResultType.HISTORICAL_ANALYSIS if pts else ResultType.UNAVAILABLE,
                location=GeoLocation(latitude=latitude, longitude=longitude),
                unit=unit,
                data_source=meta,
                model=None,
                historical_data=pts,
                predictions=[],
                uncertainty=UncertaintyInfo(
                    available=False,
                    description=f"{category.capitalize()} historical analysis.",
                ),
                sonification=SonificationService.generate_sonification_series(category, pts),
                nasa_worldview_url=worldview_url,
                limitations=limitations,
            )

        # 5. Continuous Forecasting Targets (temperature, rain, wind, and optionally ocean/vegetation when horizon > 0)
        if len(pts) < 24:
            return ModuleResponse(
                status="success",
                condition=category,
                result_type=ResultType.OBSERVATION if pts else ResultType.UNAVAILABLE,
                location=GeoLocation(latitude=latitude, longitude=longitude),
                unit=unit,
                data_source=meta,
                model=None,
                historical_data=pts,
                predictions=[],
                uncertainty=UncertaintyInfo(
                    available=False,
                    description=f"Insufficient historical samples ({len(pts)}/24 required for statistical model training).",
                ),
                sonification=SonificationService.generate_sonification_series(category, pts),
                nasa_worldview_url=worldview_url,
                limitations=limitations + ["Insufficient historical records to train a validated predictive model."],
            )

        # Clean historical records
        records = [{"timestamp": p.timestamp, "value": p.value} for p in pts]
        df_hist = DataCleaner.clean_time_series(records, value_col="value")

        model = model_registry.get_or_create_model(category)
        train_metrics = model.fit(df_hist, "value")
        pred_vals, intervals = model.predict_forward(df_hist, "value", steps=horizon)

        # Generate future timestamps
        last_dt = pd.to_datetime(df_hist["timestamp"].iloc[-1])
        prediction_points: List[TimeSeriesPoint] = []
        for i, val in enumerate(pred_vals):
            step_dt = last_dt + pd.DateOffset(months=i + 1)
            lower, upper = intervals[i]
            prediction_points.append(
                TimeSeriesPoint(
                    timestamp=step_dt.strftime("%Y-%m-%d"),
                    value=round(val, 2),
                    unit=unit,
                    lower_bound=round(lower, 2),
                    upper_bound=round(upper, 2),
                )
            )

        model_meta = ModelMetadata(
            name=model.name,
            version=model.version,
            status="validated",
            validation_method="Chronological Holdout (80/20 train/validation split)",
            metrics=train_metrics,
            trained_at=datetime.utcnow().isoformat() + "Z",
            baseline_algorithm="Seasonal-Naive (Lag-12)",
        )

        all_points = pts + prediction_points
        sonification_data = SonificationService.generate_sonification_series(category, all_points)

        result_type = ResultType.FORECAST if category in ("temperature", "rain", "wind") else ResultType.PROJECTION

        return ModuleResponse(
            status="success",
            condition=category,
            result_type=result_type,
            location=GeoLocation(latitude=latitude, longitude=longitude),
            unit=unit,
            data_source=meta,
            model=model_meta,
            historical_data=pts,
            predictions=prediction_points,
            uncertainty=UncertaintyInfo(
                available=True,
                method="Empirical Residual Bootstrapping",
                confidence_level=0.95,
                description="95% prediction intervals computed from chronological validation residuals.",
            ),
            sonification=sonification_data,
            nasa_worldview_url=worldview_url,
            limitations=limitations,
        )
