"""Media Visual Analysis & Sonification Service for Earth Jukebox.

Note: Media-derived indices measure pixel/color/luminance properties of uploaded
photos or video frames. They are NOT calibrated NASA satellite retrievals.
"""
import base64
from datetime import datetime, timezone
from io import BytesIO
from statistics import mean, median, pstdev, stdev
from typing import Any, Dict, List

import numpy as np
from PIL import Image

from app.reports.summary_generator import generate_ai_summary
from app.schemas.responses import TimeSeriesPoint
from app.services.sonification_service import SonificationService


class MediaAnalysisService:
    @staticmethod
    def _compute_image_signal(arr: np.ndarray, category: str) -> float:
        """Compute a single scalar visual-environmental proxy index from an RGB array."""
        r = arr[:, :, 0].astype(np.float32)
        g = arr[:, :, 1].astype(np.float32)
        b = arr[:, :, 2].astype(np.float32)

        if category == "vegetation":
            # Excess Greenness Index (ExG) normalized to [0, 100]
            exg = (2.0 * g - r - b) / (2.0 * g + r + b + 1e-5)
            return float(np.clip((np.mean(exg) + 0.5) * 100.0, 0.0, 100.0))
        if category == "temperature":
            # Warmth (Red - Blue) balance normalized to [0, 100]
            warmth = (r - b) / (r + b + 1e-5)
            return float(np.clip((np.mean(warmth) + 1.0) * 50.0, 0.0, 100.0))
        if category == "fires":
            # High-intensity ember / orange-red saturation ratio (%)
            ember = ((r > 185) & (r > g * 1.25) & (r > b * 1.6)).astype(np.float32)
            return float(np.mean(ember) * 100.0)
        if category == "ocean":
            # Blue dominance index
            blue_idx = (b - 0.5 * (r + g)) / (r + g + b + 1e-5)
            return float(np.clip((np.mean(blue_idx) + 0.5) * 100.0, 0.0, 100.0))
        if category == "ice":
            # High-albedo brightness / neutral whiteness (%)
            bright = ((r + g + b) / 3.0) / 255.0 * 100.0
            return float(np.mean(bright))
        if category in ("rain", "storms"):
            # Cloud contrast / storm texture standard deviation
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return float(np.std(lum))
        # Wind / general visual energy (spatial gradient magnitude)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        gx = np.abs(np.diff(lum, axis=1))
        return float(np.mean(gx))

    @classmethod
    def extract_image_series(cls, image_bytes: bytes, category: str, slices: int = 16) -> List[TimeSeriesPoint]:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((320, 320))
        arr = np.asarray(img)
        h, w, _ = arr.shape
        slices = max(4, min(slices, w))
        edges = np.linspace(0, w, slices + 1, dtype=int)

        points: List[TimeSeriesPoint] = []
        for i in range(slices):
            strip = arr[:, edges[i]:max(edges[i] + 1, edges[i + 1]), :]
            val = round(cls._compute_image_signal(strip, category), 3)
            points.append(TimeSeriesPoint(
                timestamp=f"Slice {i + 1:02d}",
                value=val,
                unit="visual_index",
            ))
        return points

    @classmethod
    def extract_frames_series(cls, frame_data_urls: List[str], category: str) -> List[TimeSeriesPoint]:
        points: List[TimeSeriesPoint] = []
        for idx, item in enumerate(frame_data_urls[:48]):
            raw_b64 = item.split(",", 1)[1] if "," in item else item
            raw_bytes = base64.b64decode(raw_b64)
            img = Image.open(BytesIO(raw_bytes)).convert("RGB")
            img.thumbnail((240, 240))
            val = round(cls._compute_image_signal(np.asarray(img), category), 3)
            points.append(TimeSeriesPoint(
                timestamp=f"Frame {idx + 1:02d}",
                value=val,
                unit="visual_index",
            ))
        return points

    @classmethod
    async def build_media_report(
        cls,
        category: str,
        filename: str,
        media_kind: str,
        points: List[TimeSeriesPoint],
        location_name: str = "Uploaded Media",
    ) -> Dict[str, Any]:
        values = [float(p.value) for p in points]
        statistics = {
            "observation_count": len(values),
            "mean": round(mean(values), 4) if values else None,
            "median": round(median(values), 4) if values else None,
            "minimum": round(min(values), 4) if values else None,
            "maximum": round(max(values), 4) if values else None,
            "range": round(max(values) - min(values), 4) if values else None,
            "standard_deviation": round(stdev(values), 4) if len(values) > 1 else 0.0,
            "population_standard_deviation": round(pstdev(values), 4) if values else None,
            "first_value": round(values[0], 4) if values else None,
            "last_value": round(values[-1], 4) if values else None,
            "change": round(values[-1] - values[0], 4) if len(values) > 1 else 0.0,
            "change_percent": round(((values[-1] - values[0]) / abs(values[0])) * 100, 2) if len(values) > 1 and values[0] != 0 else None,
        }

        sonification = SonificationService.generate_sonification_series(category, points).model_dump(mode="json")
        limitations = [
            "Values represent visual pixel-derived indices extracted from the uploaded media, NOT calibrated NASA satellite measurements.",
            "Lighting, camera exposure, and color balance strongly affect visual indices.",
            "Sonification chords reflect visual intensity variation across spatial slices or video frames.",
        ]

        observations = [{"timestamp": p.timestamp, "value": p.value, "unit": p.unit} for p in points]
        context = {
            "application": "Earth Jukebox",
            "condition": f"{category} (media visual signal)",
            "location": {"name": location_name, "source_file": filename},
            "time_window": {"start_date": points[0].timestamp if points else "N/A", "end_date": points[-1].timestamp if points else "N/A"},
            "unit": "visual_index",
            "statistics": statistics,
            "observations": observations,
            "scientific_limitations": limitations,
        }
        ai_summary = await generate_ai_summary(context)

        return {
            "application": "Earth Jukebox",
            "report_title": f"{category.capitalize()} Media Visual Analysis Report",
            "condition": category,
            "location": {"latitude": location_name, "longitude": media_kind},
            "time_window": {"start_date": points[0].timestamp if points else "N/A", "end_date": points[-1].timestamp if points else "N/A"},
            "unit": "visual_index",
            "statistics": statistics,
            "observations": observations,
            "observation_type": "media_sequence",
            "data_source": {
                "organization": "User-Uploaded Media",
                "dataset_name": f"{media_kind.capitalize()} Visual Scan ({filename})",
                "dataset_identifier": "MEDIA_VISUAL_INDEX",
                "provider_daac": "Local Upload Analysis (Non-NASA)",
                "api_endpoint": "/media/analyze",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "variables": [f"{category}_visual_index"],
                "spatial_resolution": "Media pixel grid",
                "temporal_resolution": "Frame / Horizontal Slice Sequence",
                "license_or_access": "User-provided media",
            },
            "sonification": sonification,
            "ai_summary": ai_summary,
            "limitations": limitations,
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "observation_count": len(observations),
                "data_provider": "User Media",
                "summary_provider": ai_summary.get("generation_method", "unknown"),
            },
        }
