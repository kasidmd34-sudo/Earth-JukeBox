"""Unified Environmental Intelligence Layer.
Synthesizes observations across all eight environmental modules into a coherent environmental report.
"""
import asyncio
from typing import Dict, Any, List
from app.services.observation_service import ObservationService
from app.schemas.responses import IntelligenceReport
from app.schemas.common import GeoLocation
from app.preprocessing.validation import GeoValidator


class IntelligenceService:
    ALL_MODULES = [
        "temperature",
        "rain",
        "wind",
        "fires",
        "ocean",
        "ice",
        "storms",
        "vegetation",
    ]

    @classmethod
    async def synthesize(
        cls,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        location_name: str = "Target Coordinates",
    ) -> IntelligenceReport:
        # Validate coordinates first
        valid, msg = GeoValidator.validate_coordinates(latitude, longitude)
        if not valid:
            raise ValueError(msg)

        is_polar = GeoValidator.is_polar_region(latitude)
        module_results: Dict[str, Dict[str, Any]] = {}
        anomalies: List[Dict[str, Any]] = []

        # Concurrently query all 8 environmental modules via asyncio.gather
        async def _fetch_mod(cat: str):
            try:
                pts, meta, unit = await ObservationService.get_observations(
                    cat, latitude, longitude, start_date, end_date
                )
                return cat, pts, meta, unit, None
            except Exception as e:
                return cat, [], None, None, str(e)

        tasks = [_fetch_mod(cat) for cat in cls.ALL_MODULES]
        results = await asyncio.gather(*tasks)

        available_count = 0
        applicable_count = 0

        for cat, pts, meta, unit, err in results:
            # Special domain rule: Ice is only geographically applicable in polar regions
            if cat == "ice" and not is_polar:
                module_results[cat] = {
                    "status": "not_applicable_non_polar",
                    "notes": "Cryosphere ice pack monitoring is restricted to polar latitudes (|lat| >= 60°).",
                }
                continue

            applicable_count += 1

            if err:
                module_results[cat] = {"status": "error", "message": err}
                continue

            if pts:
                available_count += 1
                vals = [p.value for p in pts]
                mean_val = sum(vals) / len(vals)
                max_val = max(vals)
                min_val = min(vals)

                # Detect anomalies exceeding 2 standard deviations
                variance = sum((x - mean_val) ** 2 for x in vals) / len(vals)
                std_val = variance ** 0.5

                if std_val > 0.001:
                    for p in pts:
                        if abs(p.value - mean_val) > 2.0 * std_val:
                            anomalies.append({
                                "category": cat,
                                "timestamp": p.timestamp,
                                "value": round(p.value, 2),
                                "mean": round(mean_val, 2),
                                "unit": unit,
                                "deviation": round((p.value - mean_val) / std_val, 2),
                            })

                module_results[cat] = {
                    "status": "available",
                    "count": len(pts),
                    "unit": unit,
                    "mean": round(mean_val, 2),
                    "min": round(min_val, 2),
                    "max": round(max_val, 2),
                    "dataset": meta.dataset_name if meta else "NASA",
                }
            else:
                module_results[cat] = {
                    "status": "no_data_for_location_window",
                    "dataset": meta.dataset_name if meta else "NASA",
                }

        completeness = available_count / max(1, applicable_count)

        # Calculate Compound Scientific Indices
        compound_indices: Dict[str, float] = {}
        if (
            "temperature" in module_results and module_results["temperature"]["status"] == "available"
            and "rain" in module_results and module_results["rain"]["status"] == "available"
        ):
            t_mean = module_results["temperature"]["mean"]
            r_mean = module_results["rain"]["mean"]
            # Evaporative stress / thermal aridity ratio
            compound_indices["evaporative_aridity_factor"] = round(float(t_mean / (r_mean + 0.1)), 2)

        if (
            "wind" in module_results and module_results["wind"]["status"] == "available"
            and "rain" in module_results and module_results["rain"]["status"] == "available"
        ):
            w_mean = module_results["wind"]["mean"]
            r_max = module_results["rain"]["max"]
            # Convective storm kinetic energy index
            compound_indices["convective_storm_index"] = round(float(w_mean * r_max), 2)

        # Synthesize professional, scientifically sound narrative
        narrative_parts = [
            f"Multi-hazard environmental intelligence assessment for {location_name} ({latitude:.4f}, {longitude:.4f}).",
            f"Analysis period: {start_date} to {end_date}.",
            f"Overall data completeness: {completeness * 100:.1f}% across {applicable_count} applicable environmental domains.",
        ]

        if "temperature" in module_results and module_results["temperature"]["status"] == "available":
            t = module_results["temperature"]
            narrative_parts.append(f"Surface temperature averaged {t['mean']} {t['unit']} (range: {t['min']} to {t['max']}).")

        if "rain" in module_results and module_results["rain"]["status"] == "available":
            r = module_results["rain"]
            narrative_parts.append(f"Precipitation averaged {r['mean']} {r['unit']} (peak: {r['max']} {r['unit']}).")

        if "wind" in module_results and module_results["wind"]["status"] == "available":
            w = module_results["wind"]
            narrative_parts.append(f"10-meter wind velocity averaged {w['mean']} {w['unit']}.")

        if "fires" in module_results and module_results["fires"]["status"] == "available":
            f = module_results["fires"]
            narrative_parts.append(f"Active fire hotspots detected: {f['count']} records within query window.")

        if "ocean" in module_results and module_results["ocean"]["status"] == "available":
            o = module_results["ocean"]
            narrative_parts.append(f"Sea surface temperature averaged {o['mean']} {o['unit']}.")

        if "vegetation" in module_results and module_results["vegetation"]["status"] == "available":
            v = module_results["vegetation"]
            narrative_parts.append(f"Vegetation photosynthetic flux (PAR) averaged {v['mean']} {v['unit']}.")

        if anomalies:
            narrative_parts.append(
                f"Statistical screening flagged {len(anomalies)} severe anomalous observations (>2 sigma variance) across telemetry series."
            )
        else:
            narrative_parts.append("No statistical anomalies exceeding the 2-sigma baseline threshold were detected.")

        narrative = " ".join(narrative_parts)

        # NASA Worldview deep link URL for spatial verification
        min_lon = max(-180.0, longitude - 2.0)
        max_lon = min(180.0, longitude + 2.0)
        min_lat = max(-90.0, latitude - 2.0)
        max_lat = min(90.0, latitude + 2.0)
        worldview_url = f"https://worldview.earthdata.nasa.gov/?v={min_lon:.2f},{min_lat:.2f},{max_lon:.2f},{max_lat:.2f}&t={end_date}"

        return IntelligenceReport(
            status="success",
            application="Earth Jukebox",
            location=GeoLocation(latitude=latitude, longitude=longitude, location_name=location_name),
            time_window={"start_date": start_date, "end_date": end_date},
            unified_narrative=narrative,
            anomalies_detected=anomalies,
            modules_aggregated=module_results,
            compound_indices=compound_indices,
            nasa_worldview_url=worldview_url,
            data_completeness_ratio=round(completeness, 3),
            scientific_disclaimer=(
                "Synthesized exclusively from NASA Earth-observation platforms, mission instruments, "
                "and reanalysis models. Multi-indicator syntheses represent empirical correlations and "
                "must not be interpreted as causal guarantees or operational disaster warnings."
            ),
        )
