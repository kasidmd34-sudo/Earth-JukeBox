"""Tests for 8 parameter pages, chord hierarchy, chart-marker sync, PDF, and media analysis."""
from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.reports.chart_generator import ChartGenerator
from app.reports.pdf_generator import PDFGenerator
from app.schemas.responses import TimeSeriesPoint
from app.services.sonification_service import SonificationService

client = TestClient(app)


def test_eight_dedicated_parameter_pages():
    for cat in ("temperature", "rain", "wind", "fires", "ocean", "ice", "storms", "vegetation"):
        res = client.get(f"/explore/{cat}")
        assert res.status_code == 200
        assert cat.upper() in res.text


def test_chord_hierarchy_and_chart_marker_alignment():
    pts = [TimeSeriesPoint(timestamp=f"2023-{m:02d}-01", value=20.0 + m, unit="degrees_Celsius") for m in range(1, 13)]
    sonif = SonificationService.generate_sonification_series("temperature", pts)
    assert "level_3_register_tiers" in sonif.chord_hierarchy
    assert sonif.parameters[-1].pitch_direction in ("higher", "unchanged", "lower")

    report = {
        "report_title": "Temperature Test Report",
        "condition": "temperature",
        "location": {"latitude": 19.076, "longitude": 72.8777},
        "time_window": {"start_date": "2023-01-01", "end_date": "2023-12-01"},
        "unit": "degrees_Celsius",
        "statistics": {"observation_count": 12, "mean": 26.5, "minimum": 21.0, "maximum": 32.0},
        "observations": [{"timestamp": p.timestamp, "value": p.value, "unit": p.unit} for p in pts],
        "sonification": sonif.model_dump(mode="json"),
        "ai_summary": {"summary": "Test summary.", "key_findings": ["Rising step"], "limitations": [], "generation_method": "statistical_fallback"},
        "limitations": ["Test limitation."],
        "data_source": {"organization": "NASA", "dataset_name": "POWER", "temporal_resolution": "Monthly"},
        "report_metadata": {"generated_at": "2026-01-01T00:00:00Z"},
    }
    charts = ChartGenerator.generate_charts(report)
    assert charts["observation_chart"].getvalue()[:8] == b"\x89PNG\r\n\x1a\n"

    pdf_bytes = PDFGenerator().generate_pdf(report, charts=charts, report_format="detailed").getvalue()
    assert pdf_bytes.startswith(b"%PDF")


def test_media_image_analyze_and_pdf():
    img = Image.new("RGB", (64, 64), color=(220, 80, 40))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        "/media/analyze",
        data={"category": "temperature", "location_name": "Test Photo"},
        files={"file": ("sample.png", buf, "image/png")},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["observation_type"] == "media_sequence"
    assert len(payload["sonification"]["parameters"]) > 0

    pdf_res = client.post("/media/report/pdf?report_format=compact", json=payload)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF")