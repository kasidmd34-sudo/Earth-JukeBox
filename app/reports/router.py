
"""FastAPI routes for Earth Jukebox PDF reports."""

import logging
from io import BytesIO
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.reports.report_service import ReportService
from app.reports.chart_generator import ChartGenerator
from app.reports.pdf_generator import PDFGenerator


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["Environmental Reports"],
)


@router.get("/{condition}/pdf")
async def download_pdf_report(
    condition: Literal[
        "temperature",
        "rain",
        "wind",
        "fires",
        "ocean",
        "ice",
        "storms",
        "vegetation",
    ],
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    report_format: Literal["compact", "detailed"] = Query("compact"),
):
    """Generate and download a NASA-based environmental PDF report."""

    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date.",
        )

    try:
        # 1. Retrieve NASA observations and build report context.
        report = await ReportService.generate_report(
            condition=condition,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        # 2. Generate charts from the returned NASA observations.
        charts = ChartGenerator.generate_charts(report)

        # 3. Generate PDF.
        pdf_generator = PDFGenerator()

        pdf_buffer = pdf_generator.generate_pdf(
            report_data=report,
            charts=charts,
            report_format=report_format,
        )

        pdf_buffer.seek(0)

        filename = (
            f"earth_jukebox_{condition}_{report_format}_report.pdf"
        )

        # 4. Return downloadable PDF.
        return StreamingResponse(
            BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Earth Jukebox PDF generation failed")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while generating the PDF report.",
        ) from exc
