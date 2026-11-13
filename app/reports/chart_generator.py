"""Chart generation for Earth Jukebox environmental and media PDF reports."""

from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from app.services.sonification_service import SonificationService


class ChartGenerator:
    """Creates report-ready charts from NASA-derived or media-derived observations."""

    CATEGORY_TITLES = {
        "temperature": "Surface Temperature",
        "rain": "Precipitation",
        "wind": "10-Meter Wind Speed",
        "fires": "Active Fire Radiative Power",
        "ocean": "Sea Surface Temperature",
        "ice": "Cryosphere Returned Measurements",
        "storms": "Storm-Related Precipitation Observations",
        "vegetation": "Vegetation Adapter Returned Measurements",
        "media": "Uploaded Media Visual Profile",
    }

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

    EVENT_BASED_CATEGORIES = {"fires", "storms"}

    @staticmethod
    def _normalise_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.replace(tzinfo=None)

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
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
                return ChartGenerator._normalise_datetime(datetime.strptime(value, fmt))
            except ValueError:
                continue
        try:
            return ChartGenerator._normalise_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None

    @classmethod
    def _extract_observations(
        cls,
        report_data: Dict[str, Any],
    ) -> Tuple[List[Any], List[float], List[str], bool]:
        """Extract observations; supports both date-based and sequential media indices."""
        observations = report_data.get("observations", []) or []
        is_media = report_data.get("observation_type") == "media_sequence"

        if is_media:
            x_vals: List[int] = []
            y_vals: List[float] = []
            labels: List[str] = []
            for idx, item in enumerate(observations):
                if not isinstance(item, dict):
                    continue
                val = item.get("value")
                if val is None or isinstance(val, bool):
                    continue
                try:
                    num = float(val)
                except (TypeError, ValueError, OverflowError):
                    continue
                if np.isfinite(num):
                    x_vals.append(idx + 1)
                    y_vals.append(num)
                    labels.append(str(item.get("timestamp", f"Step {idx + 1}")))
            return x_vals, y_vals, labels, True

        valid_records: List[Tuple[datetime, float]] = []
        for item in observations:
            if not isinstance(item, dict):
                continue
            ts = cls._parse_timestamp(item.get("timestamp"))
            val = item.get("value")
            if ts is None or val is None or isinstance(val, bool):
                continue
            try:
                num = float(val)
            except (TypeError, ValueError, OverflowError):
                continue
            if np.isfinite(num):
                valid_records.append((ts, num))

        valid_records.sort(key=lambda r: r[0])
        dates = [r[0] for r in valid_records]
        values = [r[1] for r in valid_records]
        labels = [d.strftime("%Y-%m-%d") for d in dates]
        return dates, values, labels, False

    @staticmethod
    def _figure_to_buffer(fig: plt.Figure) -> BytesIO:
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight", facecolor="white")
        buffer.seek(0)
        plt.close(fig)
        return buffer

    @classmethod
    def _create_empty_chart(cls, title: str, message: str = "No valid observations available for this chart.") -> BytesIO:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        return cls._figure_to_buffer(fig)

    @classmethod
    def _format_unit(cls, unit: Any) -> str:
        raw_unit = str(unit or "").strip()
        return cls.UNIT_DISPLAY_LABELS.get(raw_unit, raw_unit)

    @classmethod
    def _get_measurement_label(cls, condition: str, report_data: Dict[str, Any]) -> str:
        unit = cls._format_unit(report_data.get("unit"))
        unit_label = unit if unit else "unit not supplied"
        if condition == "fires":
            return f"Fire Radiative Power ({unit_label})"
        if condition == "storms":
            return f"Returned precipitation measurement ({unit_label})"
        if condition == "ice":
            return f"Returned cryosphere measurement ({unit_label})"
        if condition == "vegetation":
            return f"Returned adapter measurement ({unit_label})"
        title = cls.CATEGORY_TITLES.get(condition, condition.capitalize())
        return f"{title} ({unit_label})"

    @classmethod
    def _is_event_based(cls, condition: str, report_data: Dict[str, Any]) -> bool:
        if condition in cls.EVENT_BASED_CATEGORIES:
            return True
        source = report_data.get("data_source", {}) or {}
        if not isinstance(source, dict):
            return False
        temporal_res = str(source.get("temporal_resolution", "") or "").lower()
        return any(term in temporal_res for term in ("event-based", "event based", "irregular", "as available"))

    @classmethod
    def _get_time_axis_label(cls, condition: str, report_data: Dict[str, Any], is_media: bool) -> str:
        if is_media:
            return "Media Frame / Spatial Scan Step"
        if cls._is_event_based(condition, report_data):
            return "Observation Date (UTC)"
        source = report_data.get("data_source", {}) or {}
        temporal_res = str(source.get("temporal_resolution", "") or "").strip().lower() if isinstance(source, dict) else ""
        if "monthly" in temporal_res:
            return "Observation Month"
        return "Observation Date (UTC)"

    @classmethod
    def create_observation_chart(cls, report_data: Dict[str, Any]) -> BytesIO:
        condition = report_data.get("condition", "unknown")
        x_vals, values, labels, is_media = cls._extract_observations(report_data)
        title = cls.CATEGORY_TITLES.get(condition, condition.capitalize())

        if not values:
            return cls._create_empty_chart(f"{title} Observations")

        measurement_label = cls._get_measurement_label(condition, report_data)
        fig, ax = plt.subplots(figsize=(10, 4.9))

        if not is_media and cls._is_event_based(condition, report_data):
            ax.scatter(x_vals, values, alpha=0.8, s=36, color="#2563EB", label="Observations")
            ax.set_title(f"{title} — Individual Observations & Chord Markers (A-Z)", fontsize=13.5, fontweight="bold")
        else:
            ax.plot(x_vals, values, marker="o", markersize=4, linewidth=1.9, color="#1D4ED8", label="Observed Values")
            ax.fill_between(x_vals, values, min(values), color="#3B82F6", alpha=0.10)
            ax.set_title(f"{title} Over Time — Annotated with Chord Markers (A-Z)", fontsize=13.5, fontweight="bold")

        mean_val = float(np.mean(values))
        ax.axhline(mean_val, color="#6B7280", linestyle=":", linewidth=1.2, label=f"Mean ({mean_val:.2f})")

        # Annotate up to 12 evenly spaced points A, B, C... matched strictly to sound_events[point_index]
        sonification = report_data.get("sonification", {}) or {}
        sound_events = sonification.get("parameters", []) or []
        chosen = SonificationService.sample_marker_indices(len(values), max_markers=12)

        for marker_idx, point_index in enumerate(chosen):
            letter = chr(65 + marker_idx)
            arrow = ""
            badge_fc = "#FEF3C7"
            badge_ec = "#B45309"
            if sound_events and point_index < len(sound_events):
                p_dir = sound_events[point_index].get("pitch_direction", "initial")
                if p_dir == "higher":
                    arrow = "↑"
                    badge_fc = "#DCFCE7"
                    badge_ec = "#15803D"
                elif p_dir == "lower":
                    arrow = "↓"
                    badge_fc = "#FEE2E2"
                    badge_ec = "#B91C1C"

            y_offset = 11 if (marker_idx % 2 == 0) else -16
            ax.annotate(
                f"{letter}{arrow}",
                (x_vals[point_index], values[point_index]),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="#111827",
                bbox={"boxstyle": "round,pad=0.22", "fc": badge_fc, "ec": badge_ec, "lw": 0.9},
            )

        ax.set_xlabel(cls._get_time_axis_label(condition, report_data, is_media), fontsize=10)
        ax.set_ylabel(measurement_label, fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(loc="best", fontsize=9)

        if is_media:
            ax.set_xticks(x_vals)
            ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        else:
            locator = mdates.AutoDateLocator()
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
            fig.autofmt_xdate()

        # Add extra vertical headroom so annotations never clip
        y_min, y_max = ax.get_ylim()
        pad = (y_max - y_min) * 0.14 if y_max > y_min else 1.0
        ax.set_ylim(y_min - pad * 0.7, y_max + pad)
        fig.tight_layout()
        return cls._figure_to_buffer(fig)

    @classmethod
    def create_distribution_chart(cls, report_data: Dict[str, Any]) -> BytesIO:
        condition = report_data.get("condition", "unknown")
        _, values, _, _ = cls._extract_observations(report_data)
        title = cls.CATEGORY_TITLES.get(condition, condition.capitalize())

        if not values:
            return cls._create_empty_chart(f"{title} Distribution")

        measurement_label = cls._get_measurement_label(condition, report_data)
        fig, ax = plt.subplots(figsize=(9, 4.3))

        if len(values) == 1:
            ax.axvline(values[0], linewidth=2, color="#2563EB", label=f"Observed value: {values[0]:.4f}")
            ax.legend(loc="best")
            ax.set_title(f"{title} — Single Observation", fontsize=13.5, fontweight="bold")
        else:
            bins = min(20, max(5, int(np.sqrt(len(values)))))
            ax.hist(values, bins=bins, color="#3B82F6", edgecolor="#1E3A8A", alpha=0.82)
            ax.axvline(float(np.mean(values)), color="#DC2626", linestyle="--", linewidth=1.4, label=f"Mean: {np.mean(values):.2f}")
            ax.legend(loc="best", fontsize=9)
            ax.set_title(f"{title} Value Distribution", fontsize=13.5, fontweight="bold")

        ax.set_xlabel(measurement_label, fontsize=10)
        ax.set_ylabel("Observation Frequency", fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        fig.tight_layout()
        return cls._figure_to_buffer(fig)

    @classmethod
    def generate_charts(cls, report_data: Dict[str, Any]) -> Dict[str, BytesIO]:
        return {
            "observation_chart": cls.create_observation_chart(report_data),
            "distribution_chart": cls.create_distribution_chart(report_data),
        }