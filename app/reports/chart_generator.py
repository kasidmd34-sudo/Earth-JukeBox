"""Chart generation for Earth Jukebox environmental PDF reports.

Charts are generated in memory as PNG images. No external environmental
data is retrieved here. All plotted values come from the supplied NASA
report context.
"""

from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


class ChartGenerator:
    """Creates report-ready charts from NASA-derived observations."""

    CATEGORY_TITLES = {
        "temperature": "Surface Temperature",
        "rain": "Precipitation",
        "wind": "10-Meter Wind Speed",
        "fires": "Active Fire Radiative Power",
        "ocean": "Sea Surface Temperature",
        "ice": "Cryosphere Returned Measurements",
        "storms": "Storm-Related Precipitation Observations",
        "vegetation": "Vegetation Adapter Returned Measurements",
    }

    # Presentation-only unit labels.
    # Original NASA adapter metadata remains unchanged.
    UNIT_DISPLAY_LABELS = {
        "degrees_Celsius": "°C",
        "degree_Celsius": "°C",
        "degrees_Fahrenheit": "°F",
        "degree_Fahrenheit": "°F",
        "meters_per_second": "m/s",
        "meter_per_second": "m/s",
        "millimeters": "mm",
        "millimeter": "mm",
        "millimetres": "mm",
        "millimetre": "mm",
        "kilometers": "km",
        "kilometer": "km",
        "kilometres": "km",
        "kilometre": "km",
        "percent": "%",
        "percentage": "%",
    }

    # Event-based categories must not be drawn as continuous time series.
    EVENT_BASED_CATEGORIES = {"fires", "storms"}

    @staticmethod
    def _normalise_datetime(value: datetime) -> datetime:
        """Return a timezone-naive datetime whose clock is expressed in UTC."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return value.replace(tzinfo=None)

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        """Parse common NASA date/timestamp formats and normalize to UTC."""
        if value is None or value == "":
            return None

        value = str(value).strip()

        formats = (
            "%Y-%m-%d",
            "%Y%m%d",
            "%Y-%m",
            "%Y%m",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        )

        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                return ChartGenerator._normalise_datetime(parsed)
            except ValueError:
                continue

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
            return ChartGenerator._normalise_datetime(parsed)
        except ValueError:
            return None

    @classmethod
    def _extract_observations(
        cls,
        report_data: Dict[str, Any],
    ) -> Tuple[List[datetime], List[float], List[str]]:
        """Extract valid timestamp/value pairs from report data."""

        observations = report_data.get("observations", []) or []
        valid_records: List[Tuple[datetime, float]] = []

        for item in observations:
            if not isinstance(item, dict):
                continue

            timestamp = cls._parse_timestamp(
                item.get("timestamp")
            )

            value = item.get("value")

            if (
                timestamp is None
                or value is None
                or isinstance(value, bool)
            ):
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError, OverflowError):
                continue

            if not np.isfinite(numeric_value):
                continue

            valid_records.append(
                (timestamp, numeric_value)
            )

        # Retain duplicate timestamps:
        # multiple event observations may be valid.
        valid_records.sort(
            key=lambda record: record[0]
        )

        dates = [
            record[0] for record in valid_records
        ]

        values = [
            record[1] for record in valid_records
        ]

        labels = [
            date.strftime("%Y-%m-%d")
            for date in dates
        ]

        return dates, values, labels

    @staticmethod
    def _figure_to_buffer(fig: plt.Figure) -> BytesIO:
        """Save a Matplotlib figure as an in-memory PNG."""

        buffer = BytesIO()

        fig.savefig(
            buffer,
            format="png",
            dpi=180,
            bbox_inches="tight",
            facecolor="white",
        )

        buffer.seek(0)
        plt.close(fig)

        return buffer

    @classmethod
    def _create_empty_chart(
        cls,
        title: str,
        message: str = "No valid observations available for this chart.",
    ) -> BytesIO:
        """Create a placeholder chart when observations are unavailable."""

        fig, ax = plt.subplots(
            figsize=(9, 4.5)
        )

        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
        )

        ax.text(
            0.5,
            0.5,
            message,
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=11,
        )

        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        return cls._figure_to_buffer(fig)

    @classmethod
    def _format_unit(cls, unit: Any) -> str:
        """Return a readable display unit without changing source metadata."""

        raw_unit = str(unit or "").strip()

        return cls.UNIT_DISPLAY_LABELS.get(
            raw_unit,
            raw_unit,
        )

    @classmethod
    def _get_measurement_label(
        cls,
        condition: str,
        report_data: Dict[str, Any],
    ) -> str:
        """Build a cautious label using the unit returned by the adapter."""

        unit = cls._format_unit(
            report_data.get("unit")
        )

        unit_label = (
            unit if unit else "unit not supplied"
        )

        if condition == "fires":
            return f"Fire Radiative Power ({unit_label})"

        if condition == "storms":
            return (
                "Returned precipitation measurement "
                f"({unit_label})"
            )

        if condition == "ice":
            return (
                "Returned cryosphere measurement "
                f"({unit_label})"
            )

        if condition == "vegetation":
            return (
                "Returned adapter measurement "
                f"({unit_label})"
            )

        title = cls.CATEGORY_TITLES.get(
            condition,
            condition.capitalize(),
        )

        return f"{title} ({unit_label})"

    @classmethod
    def _is_event_based(
        cls,
        condition: str,
        report_data: Dict[str, Any],
    ) -> bool:
        """Use event plots for event categories or explicitly irregular data."""

        if condition in cls.EVENT_BASED_CATEGORIES:
            return True

        source = report_data.get(
            "data_source", {}
        ) or {}

        if not isinstance(source, dict):
            return False

        temporal_resolution = str(
            source.get("temporal_resolution", "") or ""
        ).lower()

        irregular_terms = (
            "event-based",
            "event based",
            "irregular",
            "as available",
        )

        return any(
            term in temporal_resolution
            for term in irregular_terms
        )

    @classmethod
    def _get_time_axis_label(
        cls,
        condition: str,
        report_data: Dict[str, Any],
    ) -> str:
        """Choose an appropriate label for the observation time axis."""

        if cls._is_event_based(condition, report_data):
            return "Observation Date (UTC)"

        source = report_data.get(
            "data_source", {}
        ) or {}

        temporal_resolution = ""

        if isinstance(source, dict):
            temporal_resolution = str(
                source.get("temporal_resolution", "") or ""
            ).strip().lower()

        if "monthly" in temporal_resolution:
            return "Observation Month"

        return "Observation Date (UTC)"

    @classmethod
    def create_observation_chart(
        cls,
        report_data: Dict[str, Any],
    ) -> BytesIO:
        """Create a time-based chart with category-appropriate visualization."""

        condition = report_data.get(
            "condition", "unknown"
        )

        dates, values, _ = cls._extract_observations(
            report_data
        )

        title = cls.CATEGORY_TITLES.get(
            condition,
            condition.capitalize(),
        )

        if not values:
            return cls._create_empty_chart(
                f"{title} Observations"
            )

        measurement_label = cls._get_measurement_label(
            condition,
            report_data,
        )

        fig, ax = plt.subplots(
            figsize=(10, 4.8)
        )

        if cls._is_event_based(
            condition,
            report_data,
        ):
            ax.scatter(
                dates,
                values,
                alpha=0.75,
                s=30,
                label="NASA observations",
            )

            ax.set_title(
                f"{title} — Individual Observations",
                fontsize=14,
                fontweight="bold",
            )

        else:
            ax.plot(
                dates,
                values,
                marker="o",
                markersize=3.5,
                linewidth=1.6,
                label="NASA observations",
            )

            ax.set_title(
                f"{title} Over Time",
                fontsize=14,
                fontweight="bold",
            )

        ax.set_xlabel(
            cls._get_time_axis_label(
                condition,
                report_data,
            )
        )

        ax.set_ylabel(
            measurement_label
        )

        ax.grid(
            True,
            linestyle="--",
            alpha=0.35,
        )

        ax.legend(
            loc="best"
        )

        locator = mdates.AutoDateLocator()

        formatter = mdates.ConciseDateFormatter(
            locator
        )

        ax.xaxis.set_major_locator(
            locator
        )

        ax.xaxis.set_major_formatter(
            formatter
        )

        fig.autofmt_xdate()
        fig.tight_layout()

        return cls._figure_to_buffer(fig)

    @classmethod
    def create_distribution_chart(
        cls,
        report_data: Dict[str, Any],
    ) -> BytesIO:
        """Create a histogram of retrieved observation values."""

        condition = report_data.get(
            "condition", "unknown"
        )

        _, values, _ = cls._extract_observations(
            report_data
        )

        title = cls.CATEGORY_TITLES.get(
            condition,
            condition.capitalize(),
        )

        if not values:
            return cls._create_empty_chart(
                f"{title} Distribution"
            )

        measurement_label = cls._get_measurement_label(
            condition,
            report_data,
        )

        fig, ax = plt.subplots(
            figsize=(9, 4.5)
        )

        if len(values) == 1:
            ax.axvline(
                values[0],
                linewidth=2,
                label=f"Observed value: {values[0]:.4f}",
            )

            ax.legend(
                loc="best"
            )

            ax.set_title(
                f"{title} — Single Observation",
                fontsize=14,
                fontweight="bold",
            )

        else:
            bins = min(
                20,
                max(5, int(np.sqrt(len(values)))),
            )

            ax.hist(
                values,
                bins=bins,
                edgecolor="black",
                alpha=0.8,
            )

            ax.set_title(
                f"{title} Value Distribution",
                fontsize=14,
                fontweight="bold",
            )

        ax.set_xlabel(
            measurement_label
        )

        ax.set_ylabel(
            "Observation Frequency"
        )

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.35,
        )

        fig.tight_layout()

        return cls._figure_to_buffer(fig)

    @classmethod
    def generate_charts(
        cls,
        report_data: Dict[str, Any],
    ) -> Dict[str, BytesIO]:
        """Generate all charts required by the PDF generator."""

        return {
            "observation_chart": cls.create_observation_chart(
                report_data
            ),
            "distribution_chart": cls.create_distribution_chart(
                report_data
            ),
        }
