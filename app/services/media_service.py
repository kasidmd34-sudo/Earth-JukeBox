import base64
import os
import httpx

MAX_MEDIA_BYTES = 20 * 1024 * 1024  # 20 MB

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}
ALLOWED_MEDIA_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

SYSTEM_PROMPT = (
    "You are an environmental visual analyst for Earth Jukebox. "
    "Describe observable ecological, weather, landscape, water, vegetation, or atmospheric cues in the uploaded media. "
    "Important scientific integrity rule: visual interpretation is strictly separate from calibrated NASA satellite measurements. "
    "Do NOT claim or estimate calibrated satellite-derived temperature values, NDVI values, or fire radiative power."
)


class MediaValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class MediaConfigurationError(Exception):
    pass


class MediaProviderError(Exception):
    pass


def validate_media_upload(contents: bytes, content_type: str) -> str:
    normalized_type = (content_type or "").lower().strip()
    if normalized_type not in ALLOWED_MEDIA_TYPES:
        raise MediaValidationError(
            f"Unsupported media type '{normalized_type or 'unknown'}'. Upload an image or MP4/WebM/MOV video.",
            status_code=400,
        )
    if not contents:
        raise MediaValidationError("Uploaded file is empty.", status_code=400)
    if len(contents) > MAX_MEDIA_BYTES:
        raise MediaValidationError("Uploaded file exceeds 20 MB limit.", status_code=413)
    return normalized_type


async def _analyze_with_gemini(contents: bytes, content_type: str, api_key: str) -> str:
    model = os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    encoded = base64.b64encode(contents).decode("utf-8")

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": content_type,
                            "data": encoded,
                        }
                    },
                    {
                        "text": (
                            "Provide a concise, objective visual interpretation of this environmental image or video "
                            "and suggest what Earth Jukebox environmental signal "
                            "(temperature, rainfall, wind, fires, ocean, ice, storms, vegetation) it relates to."
                        )
                    },
                ]
            }
        ],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, params={"key": api_key}, json=payload)

    if resp.status_code >= 400:
        raise MediaProviderError(f"Gemini API error ({resp.status_code}): {resp.text}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise MediaProviderError("Unexpected response structure from Gemini API.") from exc


async def _analyze_with_openai(contents: bytes, content_type: str, api_key: str) -> str:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise MediaValidationError(
            "OpenAI fallback supports images only. Set GEMINI_API_KEY to analyze video files.",
            status_code=400,
        )

    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    encoded = base64.b64encode(contents).decode("utf-8")
    data_url = f"data:{content_type};base64,{encoded}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Provide a concise, objective visual interpretation of this environmental image "
                            "and suggest what Earth Jukebox signal it relates to."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "max_tokens": 450,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )

    if resp.status_code >= 400:
        raise MediaProviderError(f"OpenAI API error ({resp.status_code}): {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise MediaProviderError("Unexpected response structure from OpenAI API.") from exc


async def interpret_media(contents: bytes, content_type: str, filename: str | None = None) -> dict:
    normalized_type = validate_media_upload(contents, content_type)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if gemini_key:
        interpretation = await _analyze_with_gemini(contents, normalized_type, gemini_key)
        provider = "Gemini Vision"
    elif openai_key:
        interpretation = await _analyze_with_openai(contents, normalized_type, openai_key)
        provider = "OpenAI Vision"
    else:
        raise MediaConfigurationError(
            "Media interpretation is not configured on the server. "
            "Set GEMINI_API_KEY (images & video) or OPENAI_API_KEY (images)."
        )

    return {
        "filename": filename,
        "content_type": normalized_type,
        "provider": provider,
        "interpretation": interpretation,
    }
