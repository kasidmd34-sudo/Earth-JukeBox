
"""Report orchestration service for Earth Jukebox.

Retrieves NASA observations, calculates descriptive statistics,
generates deterministic sonification parameters, and creates an
AI-assisted report summary.

NASA remains the only source of environmental observations.
Gemini is used only to summarize supplied NASA-derived results.

Performance improvements:
- Gemini timeout to prevent indefinite waiting.
- Representative observation sampling for Gemini.
- Deterministic fallback when Gemini is unavailable.
- Stage-level timing logs for performance diagnosis.
"""

import asyncio
import logging
import time

from datetime import datetime, date, timezone
from math import isfinite
from statistics import mean, median, pstdev, stdev
from typing import Any, Dict, List

from app.services.observation_service import ObservationService
from app.services.sonification_service import SonificationService
from app.reports.summary_generator import generate_ai_summary


logger = logging.getLogger(__name__)

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

# Gemini performance settings
GEMINI_SUMMARY_TIMEOUT = 10.0
GEMINI_MAX_OBSERVATIONS = 40


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
                f"Supported conditions: "
                f"{', '.join(sorted(SUPPORTED_CATEGORIES))}"
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
            raise ValueError(
                "start_date cannot be later than end_date."
            )

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

        if isinstance(value, (list, tuple)):
            return [
                ReportService._model_to_dict(item)
                for item in value
            ]

        return value

    @staticmethod
    def _calculate_statistics(
        observations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate descriptive statistics from actual observations."""

        values = []

        for item in observations:
            raw_value = item.get("value")

            if raw_value is None:
                continue

            try:
                numeric_value = float(raw_value)

                if isfinite(numeric_value):
                    values.append(numeric_value)

            except (ValueError, TypeError):
                continue

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
            "population_standard_deviation": round(
                pstdev(values), 4
            ),
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
    def _sample_observations(
        observations: List[Dict[str, Any]],
        max_points: int = GEMINI_MAX_OBSERVATIONS,
    ) -> List[Dict[str, Any]]:
        """Select evenly spaced observations for Gemini.

        The complete observation list is retained in the final report.
        Only the AI summary receives this smaller representative sample.
        """

        if len(observations) <= max_points:
            return observations

        if max_points <= 0:
            return []

        if max_points == 1:
            return [observations[0]]

        indexes = [
            round(
                i * (len(observations) - 1) / (max_points - 1)
            )
            for i in range(max_points)
        ]

        return [observations[index] for index in indexes]

    @staticmethod
    def _get_scientific_limitations(
        condition: str,
    ) -> List[str]:
        """Return category-specific scientific safeguards."""

        limitations = [
            (
                "This report summarizes observations returned by the "
                "configured NASA data adapters. It is not a substitute "
                "for local ground-station measurements."
            ),
            (
                "The requested date range is passed to the data adapters "
                "as start and end years. Some adapters may return "
                "observations at their native temporal resolution rather "
                "than exact daily coverage."
            ),
            (
                "Descriptive statistics describe retrieved observations "
                "only. They do not establish causation or guarantee "
                "future environmental conditions."
            ),
            (
                "Sonification parameters are deterministic mappings of "
                "retrieved values. They are not additional scientific "
                "measurements."
            ),
        ]

        category_limitations = {
            "temperature": [
                "NASA POWER temperature is gridded/model-assimilated data "
                "and may differ from nearby weather-station measurements."
            ],
            "rain": [
                "Precipitation values alone are not flash-flood warnings "
                "or local flood forecasts."
            ],
            "wind": [
                "Gridded 10-meter wind-speed values should not be "
                "interpreted as local instantaneous gust measurements."
            ],
            "fires": [
                "NASA FIRMS detections are active-fire observations. "
                "They do not predict future fire ignition or spread.",
                "Fire observations are event-based and may be irregularly "
                "spaced in time."
            ],
            "ocean": [
                "Sea-surface temperature products have their own spatial "
                "and temporal resolution and may not represent conditions "
                "at a specific coastal location."
            ],
            "ice": [
                "The current adapter reports values with the units supplied "
                "by its returned time-series points. Values must not be "
                "labelled sea-ice extent or area without supporting data.",
                "The current cryosphere adapter may be geographically "
                "restricted to polar regions."
            ],
            "storms": [
                "Storm-related precipitation observations do not constitute "
                "cyclone track, intensity, landfall or future storm forecasts.",
                "Storm observations may be irregularly spaced in time."
            ],
            "vegetation": [
                "The current adapter reports values in MJ/m²/day. These "
                "values must not automatically be interpreted as NDVI.",
                "Photosynthetically active radiation and vegetation-index "
                "measurements are different variables."
            ],
        }

        limitations.extend(
            category_limitations.get(condition, [])
        )

        return limitations

    @classmethod
    def _prepare_gemini_context(
        cls,
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
        """Prepare a constrained context for Gemini."""

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
            "observations": cls._sample_observations(
                observations
            ),
            "data_source": data_source,
            "scientific_limitations": limitations,
            "instructions": (
                "Summarize only the supplied NASA-derived observations "
                "and statistics. Do not invent measurements, locations, "
                "dates, causes, forecasts or scientific conclusions. "
                "Clearly state when observation count or temporal "
                "coverage is limited. Respect supplied units and "
                "scientific limitations."
            ),
        }

    @staticmethod
    def _fallback_summary(
        condition: str,
        statistics: Dict[str, Any],
        limitations: List[str],
        reason: str,
    ) -> Dict[str, Any]:
        """Create a deterministic summary without external AI."""

        count = statistics["observation_count"]

        if count == 0:
            summary = (
                f"No usable NASA-derived observations were returned "
                f"for {condition} in the requested date range."
            )
        else:
            summary = (
                f"The report contains {count} NASA-derived observations "
                f"for {condition}. The average value was "
                f"{statistics['mean']}, with a minimum of "
                f"{statistics['minimum']} and maximum of "
                f"{statistics['maximum']}. "
            )

            if statistics["change"] is not None:
                direction = (
                    "increased"
                    if statistics["change"] > 0
                    else "decreased"
                    if statistics["change"] < 0
                    else "remained unchanged"
                )

                summary += (
                    f"The first-to-last observed value {direction} "
                    f"by {abs(statistics['change'])}."
                )

        return {
            "summary": summary,
            "key_findings": [],
            "limitations": limitations,
            "generation_method": "statistical_fallback",
            "fallback_reason": reason,
        }

    @classmethod
    async def _generate_summary(
        cls,
        gemini_context: Dict[str, Any],
        condition: str,
        statistics: Dict[str, Any],
        limitations: List[str],
    ) -> Dict[str, Any]:
        """Generate an AI summary with a strict timeout."""

        try:
            ai_summary = await asyncio.wait_for(
                generate_ai_summary(gemini_context),
                timeout=GEMINI_SUMMARY_TIMEOUT,
            )

            if isinstance(ai_summary, dict):
                ai_summary.setdefault(
                    "limitations",
                    limitations,
                )
                ai_summary.setdefault(
                    "generation_method",
                    "gemini",
                )
                return ai_summary

            return {
                "summary": str(ai_summary),
                "key_findings": [],
                "limitations": limitations,
                "generation_method": "unknown",
            }

        except asyncio.TimeoutError:
            logger.warning(
                "Gemini summary timed out for %s.",
                condition,
            )

            return cls._fallback_summary(
                condition,
                statistics,
                limitations,
                "Gemini request timed out.",
            )

        except Exception as exc:
            logger.exception(
                "Gemini summary failed for %s.",
                condition,
            )

            return cls._fallback_summary(
                condition,
                statistics,
                limitations,
                f"AI summary unavailable: {type(exc).__name__}",
            )

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

        total_started = time.perf_counter()

        condition = condition.lower().strip()

        cls._validate_inputs(
            condition=condition,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        # -------------------------------------------------
        # 1. Retrieve NASA observations
        # -------------------------------------------------

        stage_started = time.perf_counter()

        points, source_metadata, unit = (
            await ObservationService.get_observations(
                category=condition,
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
            )
        )

        logger.info(
            "NASA observation retrieval for %s took %.2f seconds.",
            condition,
            time.perf_counter() - stage_started,
        )

        # -------------------------------------------------
        # 2. Convert observations
        # -------------------------------------------------

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
            if point.value is not None
        ]

        observations.sort(
            key=lambda item: item["timestamp"]
        )

        # -------------------------------------------------
        # 3. Calculate statistics
        # -------------------------------------------------

        stage_started = time.perf_counter()

        statistics = cls._calculate_statistics(
            observations
        )

        logger.info(
            "Statistics calculation took %.3f seconds.",
            time.perf_counter() - stage_started,
        )

        # -------------------------------------------------
        # 4. Preserve NASA metadata
        # -------------------------------------------------

        data_source = cls._model_to_dict(
            source_metadata
        )

        # -------------------------------------------------
        # 5. Generate sonification
        # -------------------------------------------------

        stage_started = time.perf_counter()

        sonification = (
            SonificationService.generate_sonification_series(
                category=condition,
                series=points,
            )
        )

        sonification_data = cls._model_to_dict(
            sonification
        )

        logger.info(
            "Sonification generation took %.3f seconds.",
            time.perf_counter() - stage_started,
        )

        # -------------------------------------------------
        # 6. Scientific limitations
        # -------------------------------------------------

        limitations = cls._get_scientific_limitations(
            condition
        )

        if not observations:
            limitations.append(
                "No observations were returned for this query. "
                "Statistical conclusions cannot be drawn."
            )

        # -------------------------------------------------
        # 7. Prepare Gemini context
        # -------------------------------------------------

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

        # -------------------------------------------------
        # 8. Generate AI summary with timeout
        # -------------------------------------------------

        stage_started = time.perf_counter()

        ai_summary = await cls._generate_summary(
            gemini_context=gemini_context,
            condition=condition,
            statistics=statistics,
            limitations=limitations,
        )

        logger.info(
            "AI summary generation took %.2f seconds.",
            time.perf_counter() - stage_started,
        )

        # -------------------------------------------------
        # 9. Assemble final report
        # -------------------------------------------------

        report = {
            "application": "Earth Jukebox",
            "report_title": (
                f"{condition.capitalize()} Environmental Report"
            ),
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
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),
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

        logger.info(
            "Complete report generation for %s took %.2f seconds. "
            "Observations: %d",
            condition,
            time.perf_counter() - total_started,
            len(observations),
        )

        return report
