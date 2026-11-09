
"""Report orchestration service for Earth Jukebox.

Retrieves NASA observations, calculates descriptive statistics,
generates deterministic sonification parameters, and creates an
AI-assisted report summary.

NASA remains the only source of environmental observations.
Gemini is used only to summarize the supplied NASA-derived results.
"""

from datetime import datetime, date, timezone
from math import isfinite
from statistics import mean, median, pstdev, stdev
from typing import Any, Dict, List, Optional

from app.services.observation_service import ObservationService
from app.services.sonification_service import SonificationService
from app.reports.summary_generator import generate_ai_summary


SUPPORTED_CATEGORIES = {
    "temperature",
    "rain",
    "wind",
    "fires",
    "ocean",
    "ice",
    "storms",
    "vegetation",
}


class ReportService:
    """Builds structured environmental reports from NASA observations."""

    @staticmethod
    def _validate_inputs(
        condition: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> None:
        condition = condition.lower().strip()

        if condition not in SUPPORTED_CATEGORIES:
            raise ValueError(
                f"Unsupported condition '{condition}'. "
                f"Supported conditions: {', '.join(sorted(SUPPORTED_CATEGORIES))}"
            )

        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")

        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
        except ValueError as exc:
            raise ValueError(
                "Dates must use YYYY-MM-DD format."
            ) from exc

        if start > end:
            raise ValueError("start_date cannot be later than end_date.")

    @staticmethod
    def _model_to_dict(value: Any) -> Any:
        """Convert Pydantic models and nested values to JSON-compatible data."""

        if value is None:
            return None

        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")

        if isinstance(value, dict):
            return {
                key: ReportService._model_to_dict(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                ReportService._model_to_dict(item)
                for item in value
            ]

        return value

    @staticmethod
    def _calculate_statistics(
        observations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate descriptive statistics from actual returned observations."""

        values = [
            float(item["value"])
            for item in observations
            if item.get("value") is not None
            and isfinite(float(item["value"]))
        ]

        if not values:
            return {
                "observation_count": 0,
                "mean": None,
                "median": None,
                "minimum": None,
                "maximum": None,
                "range": None,
                "standard_deviation": None,
                "population_standard_deviation": None,
                "first_value": None,
                "last_value": None,
                "change": None,
                "change_percent": None,
            }

        first_value = values[0]
        last_value = values[-1]
        change = last_value - first_value

        change_percent = (
            (change / abs(first_value)) * 100
            if first_value != 0 and len(values) > 1
            else None
        )

        return {
            "observation_count": len(values),
            "mean": round(mean(values), 4),
            "median": round(median(values), 4),
            "minimum": round(min(values), 4),
            "maximum": round(max(values), 4),
            "range": round(max(values) - min(values), 4),
            "standard_deviation": (
                round(stdev(values), 4)
                if len(values) > 1
                else 0.0
            ),
            "population_standard_deviation": round(pstdev(values), 4),
            "first_value": round(first_value, 4),
            "last_value": round(last_value, 4),
            "change": round(change, 4),
            "change_percent": (
                round(change_percent, 2)
                if change_percent is not None
                else None
            ),
        }

    @staticmethod
    def _get_scientific_limitations(condition: str) -> List[str]:
        """Return category-specific interpretation safeguards."""

        limitations = [
            (
                "This report summarizes the observations returned by the "
                "configured NASA data adapters. It is not a substitute for "
                "local ground-station measurements."
            ),
            (
                "The requested date range is passed to the data adapters as "
                "start and end years. Some adapters may return observations "
                "at their native temporal resolution rather than exact daily "
                "coverage of the requested dates."
            ),
            (
                "Descriptive statistics describe the retrieved observations "
                "only. They do not establish causation or guarantee future conditions."
            ),
            (
                "Sonification parameters are deterministic mappings of the "
                "retrieved values. They are not additional scientific measurements."
            ),
        ]

        category_limitations = {
            "temperature": [
                "NASA POWER temperature is gridded/model-assimilated data and "
                "may differ from measurements at a nearby weather station."
            ],
            "rain": [
                "Precipitation values are not, by themselves, flash-flood "
                "warnings or local flood forecasts."
            ],
            "wind": [
                "Gridded 10-meter wind-speed values should not be interpreted "
                "as local instantaneous gust measurements."
            ],
            "fires": [
                "NASA FIRMS detections are active-fire observations. They do "
                "not predict future fire ignition or fire spread.",
                "Fire observations are event-based and may be irregularly "
                "spaced in time; they should not be interpreted as a regular "
                "continuous time series."
            ],
            "ocean": [
                "Sea-surface temperature products have their own spatial and "
                "temporal resolution and may not represent conditions at a "
                "specific coastal location."
            ],
            "ice": [
                "The current adapter reports values with the unit supplied by "
                "its returned time-series points. This report does not label "
                "those values as sea-ice extent or area unless the returned "
                "measurements explicitly support that interpretation.",
                "The current cryosphere adapter is geographically restricted "
                "to polar regions."
            ],
            "storms": [
                "Storm-related precipitation observations do not constitute "
                "cyclone track, intensity, landfall, or future storm forecasts.",
                "Storm observations may be irregularly spaced in time."
            ],
            "vegetation": [
                "The current adapter reports its time-series values in "
                "MJ/m²/day. These values must not automatically be interpreted "
                "as NDVI, even though NDVI appears in the dataset metadata.",
                "Photosynthetically active radiation and vegetation-index "
                "measurements are different variables and must not be treated "
                "as interchangeable."
            ],
        }

        limitations.extend(category_limitations.get(condition, []))
        return limitations

    @staticmethod
    def _prepare_gemini_context(
        condition: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        unit: str,
        statistics: Dict[str, Any],
        observations: List[Dict[str, Any]],
        data_source: Dict[str, Any],
        limitations: List[str],
    ) -> Dict[str, Any]:
        """Prepare a constrained context for Gemini.

        Gemini receives NASA-derived values and metadata only.
        It is not asked to retrieve or invent environmental measurements.
        """

        return {
            "application": "Earth Jukebox",
            "condition": condition,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "time_window": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "unit": unit,
            "statistics": statistics,
            "observations": observations,
            "data_source": data_source,
            "scientific_limitations": limitations,
            "instructions": (
                "Summarize only the supplied NASA-derived observations and "
                "statistics. Do not invent measurements, locations, dates, "
                "causes, forecasts, or scientific conclusions. Clearly state "
                "when the observation count or temporal coverage is limited. "
                "Respect the supplied units and scientific limitations."
            ),
        }

    @classmethod
    async def generate_report(
        cls,
        condition: str,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Retrieve NASA observations and build the report context."""

        condition = condition.lower().strip()

        cls._validate_inputs(
            condition=condition,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # 1. Retrieve observations from the existing NASA data pipeline.
        points, source_metadata, unit = (
            await ObservationService.get_observations(
                category=condition,
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
            )
        )

        # 2. Convert observations into JSON-compatible dictionaries.
        observations = [
            {
                "timestamp": point.timestamp,
                "value": float(point.value),
                "unit": point.unit,
                "anomaly": point.anomaly,
                "lower_bound": point.lower_bound,
                "upper_bound": point.upper_bound,
            }
            for point in points
        ]

        # Keep the observations chronologically ordered.
        observations.sort(key=lambda item: item["timestamp"])

        # 3. Calculate descriptive statistics.
        statistics = cls._calculate_statistics(observations)

        # 4. Preserve the metadata returned by the NASA adapter.
        data_source = cls._model_to_dict(source_metadata)

        # 5. Generate sonification parameters using the existing engine.
        sonification = SonificationService.generate_sonification_series(
            category=condition,
            series=points,
        )
        sonification_data = cls._model_to_dict(sonification)

        # 6. Add scientific interpretation limitations.
        limitations = cls._get_scientific_limitations(condition)

        if not observations:
            limitations.append(
                "No observations were returned for this query. "
                "Statistical conclusions cannot be drawn from an empty dataset."
            )

        # 7. Prepare the data Gemini is allowed to summarize.
        gemini_context = cls._prepare_gemini_context(
            condition=condition,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
            statistics=statistics,
            observations=observations,
            data_source=data_source,
            limitations=limitations,
        )

        # 8. Generate the AI summary.
        # The summary generator should return a deterministic fallback
        # if Gemini is unavailable.
        try:
            ai_summary = await generate_ai_summary(gemini_context)

            if not isinstance(ai_summary, dict):
                ai_summary = {
                    "summary": str(ai_summary),
                    "key_findings": [],
                    "limitations": limitations,
                    "generation_method": "unknown",
                }

        except Exception:
            # A summary-generation failure must not prevent PDF creation.
            ai_summary = {
                "summary": (
                    f"The report contains {statistics['observation_count']} "
                    f"NASA-derived observations for {condition}. "
                    "An AI-generated summary was unavailable."
                ),
                "key_findings": [],
                "limitations": limitations,
                "generation_method": "statistical_fallback",
            }

        # 9. Assemble the complete report context.
        return {
            "application": "Earth Jukebox",
            "report_title": f"{condition.capitalize()} Environmental Report",
            "condition": condition,
            "location": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "time_window": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "unit": unit,
            "statistics": statistics,
            "observations": observations,
            "observation_type": (
                "event_based"
                if condition == "fires"
                else "time_series"
            ),
            "data_source": data_source,
            "sonification": sonification_data,
            "ai_summary": ai_summary,
            "limitations": limitations,
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "observation_count": len(observations),
                "data_provider": "NASA",
                "summary_provider": ai_summary.get(
                    "generation_method",
                    "unknown",
                ),
                "environmental_data_source_policy": (
                    "NASA datasets and NASA data adapters only"
                ),
            },
        }
