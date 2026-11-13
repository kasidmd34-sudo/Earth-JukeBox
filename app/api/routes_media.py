"""Routes for uploaded photo & video frame analysis, sonification, and PDF reports."""
from io import BytesIO
from typing import List
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.reports.chart_generator import ChartGenerator
from app.reports.pdf_generator import PDFGenerator
from app.schemas.common import EnvironmentalCategory
from app.schemas.responses import TimeSeriesPoint
from app.services.media_service import MediaAnalysisService

router = APIRouter(prefix="/media", tags=["Media Lab"])


class MediaFramesRequest(BaseModel):
    category: EnvironmentalCategory = EnvironmentalCategory.TEMPERATURE
    filename: str = "uploaded_video.mp4"
    location_name: str = "Uploaded Video"
    frames: List[str]


@router.post("/analyze")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    category: EnvironmentalCategory = Form(EnvironmentalCategory.TEMPERATURE),
    location_name: str = Form("Uploaded Photo"),
):
    content_type = (file.content_type or "").lower()
    if content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail="Send video frames to /media/analyze-frames (handled automatically by the web UI).",
        )
    raw = await file.read()
    if not raw or len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Upload an image under 15 MB.")
    try:
        points = MediaAnalysisService.extract_image_series(raw, category.value)
        return await MediaAnalysisService.build_media_report(
            category=category.value,
            filename=file.filename or "photo.png",
            media_kind="image",
            points=points,
            location_name=location_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process image: {exc}") from exc


@router.post("/analyze-frames")
async def analyze_video_frames(payload: MediaFramesRequest):
    if not payload.frames:
        raise HTTPException(status_code=400, detail="No video frames supplied.")
    try:
        points = MediaAnalysisService.extract_frames_series(payload.frames, payload.category.value)
        return await MediaAnalysisService.build_media_report(
            category=payload.category.value,
            filename=payload.filename,
            media_kind="video",
            points=points,
            location_name=payload.location_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process video frames: {exc}") from exc


@router.post("/report/pdf")
async def download_media_pdf(report_data: dict, report_format: str = "compact"):
    try:
        charts = ChartGenerator.generate_charts(report_data)
        pdf_buf = PDFGenerator().generate_pdf(report_data, charts=charts, report_format=report_format)
        pdf_buf.seek(0)
        cond = str(report_data.get("condition", "media")).lower()
        return StreamingResponse(
            BytesIO(pdf_buf.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="earth_jukebox_media_{cond}_{report_format}.pdf"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Media PDF generation failed: {exc}") from exc
