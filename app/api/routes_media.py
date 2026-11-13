from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.media_service import (
    MediaConfigurationError,
    MediaProviderError,
    MediaValidationError,
    interpret_media,
)

router = APIRouter(prefix="/media", tags=["Media Lab"])


@router.post("/analyze")
async def analyze_media(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        return await interpret_media(
            contents=contents,
            content_type=file.content_type or "",
            filename=file.filename,
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except MediaConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except MediaProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc