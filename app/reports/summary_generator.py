"""
AI-assisted summaries for Earth Jukebox PDF reports.

Important:
- Environmental measurements come exclusively from NASA-backed services.
- Gemini only interprets the supplied report context.
- No web search or external environmental datasets are used.
- A deterministic statistical fallback is returned if Gemini is unavailable.
"""

import asyncio
import json
import logging
import random

from typing import Any, Dict

import httpx

from app.config import settings


logger = logging.getLogger(__name__)

GEMINI_INTERACTIONS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/interactions"
)

MAX_RETRY_ATTEMPTS = 3

RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


# ---------------------------------------------------------
# 1. SAFE NUMBER CONVERSION
# ---------------------------------------------------------

def _safe_number(value: Any) -> float | None:
    """Convert a value to a finite float, otherwise return None."""

    try:
        number = float(value)

        if number != number:
            return None

        if number in (float("inf"), float("-inf")):
            return None

        return number

    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------
# 2. GEMINI RESPONSE EXTRACTION
# ---------------------------------------------------------

def _extract_gemini_text(response: Dict[str, Any]) -> str:
    """Extract text from Gemini Interactions API responses."""

    # First preference: direct output_text.
    output_text = response.get("output_text")

    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    text_parts = []

    # Extract text from model output steps.
    steps = response.get("steps", [])

    if not isinstance(steps, list):
        return ""

    for step in steps:

        if not isinstance(step, dict):
            continue

        if step.get("type") != "model_output":
            continue

        content = step.get("content", [])

        if isinstance(content, str):
            text_parts.append(content)
            continue

        if not isinstance(content, list):
            continue

        for part in content:

            if isinstance(part, str):
                text_parts.append(part)
                continue

            if not isinstance(part, dict):
                continue

            if part.get("type") == "text":

                text = part.get("text", "")

                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())

    return "\n".join(text_parts).strip()


# ---------------------------------------------------------
# 3. JSON RESPONSE PARSING
# ---------------------------------------------------------

def _parse_json_response(raw_text: str) -> Dict[str, Any]:
    """Extract a JSON object from Gemini text, tolerating fences and prose."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned = raw_text.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            result, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(result, dict):
            return result

    preview = cleaned[:300].replace("\\n", " ")
    raise ValueError(
        "Gemini did not return a valid JSON object. "
        f"Response preview: {preview!r}"
    )


def _normalise_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Keep generated summaries within the expected report structure."""

    summary = data.get("summary", "")
    findings = data.get("key_findings", [])
    limitations = data.get("limitations", [])

    if not isinstance(summary, str):
        summary = ""

    if not isinstance(findings, list):
        findings = []

    if not isinstance(limitations, list):
        limitations = []

    return {
        "summary": summary.strip(),

        "key_findings": [
            str(item).strip()
            for item in findings
            if str(item).strip()
        ][:6],

        "limitations": [
            str(item).strip()
            for item in limitations
            if str(item).strip()
        ][:6],
    }


# ---------------------------------------------------------
# 5. STATISTICAL FALLBACK
# ---------------------------------------------------------

def _display_unit(unit: Any) -> str:
    """Convert common machine-readable units to readable summary units."""
    text = str(unit or "units")
    return {
        "degrees_Celsius": "°C",
        "degree_Celsius": "°C",
        "degrees_Fahrenheit": "°F",
        "degree_Fahrenheit": "°F",
    }.get(text, text)


def _build_fallback_summary(
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a factual, deterministic summary from supplied report data."""
    category = str(
        context.get("condition", "environmental")
    ).replace("_", " ").title()
    unit = _display_unit(context.get("unit", "units"))
    statistics = context.get("statistics") or {}
    observations = context.get("observations") or []
    time_window = context.get("time_window") or {}

    sample_count = context.get(
        "sample_count",
        statistics.get("observation_count", len(observations)),
    )
    try:
        sample_count = int(sample_count or 0)
    except (TypeError, ValueError, OverflowError):
        sample_count = len(observations)

    mean_value = _safe_number(statistics.get("mean"))
    min_value = _safe_number(statistics.get("minimum", statistics.get("min")))
    max_value = _safe_number(statistics.get("maximum", statistics.get("max")))
    std_value = _safe_number(
        statistics.get("standard_deviation", statistics.get("std"))
    )
    first_value = _safe_number(statistics.get("first_value"))
    last_value = _safe_number(statistics.get("last_value"))
    change_value = _safe_number(statistics.get("change"))
    change_percent = _safe_number(statistics.get("change_percent"))

    start_date = time_window.get("start_date")
    end_date = time_window.get("end_date")
    date_phrase = (
        f" for the requested period from {start_date} to {end_date}"
        if start_date and end_date else ""
    )

    if sample_count <= 0:
        summary_text = (
            f"No usable {category.lower()} observations were available"
            f"{date_phrase}. A statistical interpretation cannot be "
            "produced from an empty observation set."
        )
        findings = [
            "No usable observations were returned by the NASA data service."
        ]
    else:
        summary_text = (
            f"The report contains {sample_count} {category.lower()} "
            f"observations reported in {unit}{date_phrase}. "
        )
        if mean_value is not None:
            summary_text += f"The mean reported value is {mean_value:.2f} {unit}. "
        if min_value is not None and max_value is not None:
            summary_text += (
                f"Values range from {min_value:.2f} to "
                f"{max_value:.2f} {unit}. "
            )
        if std_value is not None:
            summary_text += f"The standard deviation is {std_value:.2f} {unit}. "

        if change_value is None and first_value is not None and last_value is not None:
            change_value = last_value - first_value

        if change_value is not None:
            summary_text += f"The first-to-last change is {change_value:+.2f} {unit}"
            if change_percent is not None:
                summary_text += f" ({change_percent:+.2f}%)."
            else:
                summary_text += "."
            summary_text += " "

        summary_text += (
            "These statistics describe only the retrieved observations; "
            "they do not establish causation or predict future conditions."
        )

        findings = [f"Number of observations: {sample_count}."]
        if mean_value is not None:
            findings.append(f"Mean reported value: {mean_value:.2f} {unit}.")
        if min_value is not None and max_value is not None:
            findings.append(
                f"Observed range: {min_value:.2f} to {max_value:.2f} {unit}."
            )
        if std_value is not None:
            findings.append(f"Standard deviation: {std_value:.2f} {unit}.")
        if first_value is not None and last_value is not None:
            change_text = (
                f"First observation: {first_value:.2f} {unit}; "
                f"last observation: {last_value:.2f} {unit}"
            )
            if change_value is not None:
                change_text += f"; net change: {change_value:+.2f} {unit}"
            if change_percent is not None:
                change_text += f" ({change_percent:+.2f}%)"
            findings.append(change_text + ".")

    return {
        "summary": summary_text,
        "key_findings": findings[:6],
        "limitations": [
            "This summary is generated deterministically from the supplied descriptive statistics.",
            "The reported observations do not establish causation or provide a future forecast.",
            "Interpretation is limited by the coverage and resolution of the underlying NASA dataset.",
        ],
        "generation_method": "statistical_fallback",
    }


# ---------------------------------------------------------

async def _request_gemini(
    headers: Dict[str, str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Send a Gemini request with retry handling."""

    timeout = httpx.Timeout(
        settings.GEMINI_TIMEOUT_SECONDS
    )

    async with httpx.AsyncClient(timeout=timeout) as client:

        for attempt in range(MAX_RETRY_ATTEMPTS):

            try:

                response = await client.post(
                    GEMINI_INTERACTIONS_URL,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as exc:

                status_code = exc.response.status_code

                if (
                    status_code in RETRYABLE_STATUS_CODES
                    and attempt < MAX_RETRY_ATTEMPTS - 1
                ):

                    delay = (
                        2 ** (attempt + 1)
                        + random.uniform(0, 1)
                    )

                    logger.warning(
                        "Gemini returned HTTP %s. "
                        "Retrying in %.2f seconds "
                        "(attempt %s/%s).",
                        status_code,
                        delay,
                        attempt + 1,
                        MAX_RETRY_ATTEMPTS,
                    )

                    await asyncio.sleep(delay)

                    continue

                raise

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
            ) as exc:

                if attempt < MAX_RETRY_ATTEMPTS - 1:

                    delay = (
                        2 ** (attempt + 1)
                        + random.uniform(0, 1)
                    )

                    logger.warning(
                        "Gemini network error: %s. "
                        "Retrying in %.2f seconds "
                        "(attempt %s/%s).",
                        repr(exc),
                        delay,
                        attempt + 1,
                        MAX_RETRY_ATTEMPTS,
                    )

                    await asyncio.sleep(delay)

                    continue

                raise

    raise ValueError(
        "Gemini did not return a response after all retry attempts."
    )


# ---------------------------------------------------------
# 7. MAIN AI SUMMARY FUNCTION
# ---------------------------------------------------------

async def generate_ai_summary(
    report_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate an AI-assisted explanation of verified report statistics.

    Gemini interprets supplied NASA observations and statistics.
    If Gemini is unavailable, a deterministic statistical summary
    is returned instead.
    """

    fallback = _build_fallback_summary(report_context)

    # Check API key.
    if not settings.GEMINI_API_KEY:

        logger.warning(
            "GEMINI_API_KEY is not configured. "
            "Using statistical report summary."
        )

        return fallback

    # -----------------------------------------------------
    # SYSTEM INSTRUCTION
    # -----------------------------------------------------

    system_instruction = """
You are the scientific report-writing assistant for Earth Jukebox.

Your task is to explain environmental observations using ONLY the
structured report context supplied by the application.

STRICT RULES:

1. Environmental measurements originate from NASA datasets.
2. Do not introduce measurements from any other source.
3. Do not browse the internet or use external information.
4. Do not invent values, dates, locations, trends, causes, or events.
5. Do not claim that an observation proves climate change or causation.
6. Do not describe historical observations as a forecast.
7. If sample size or data coverage is insufficient, say so clearly.
8. Respect the supplied units and dataset description.
9. Do not relabel one environmental variable as another.
10. Explain uncertainty and limitations honestly.
11. If observations are present, do not claim that the dataset is empty.
12. Use the supplied statistics accurately.

Return ONLY a valid JSON object with these keys:

{
    "summary": "A concise scientific explanation.",
    "key_findings": ["Finding 1", "Finding 2"],
    "limitations": ["Limitation 1"]
}

Use clear language understandable to a general audience.
"""

    # -----------------------------------------------------
    # USER INPUT
    # -----------------------------------------------------

    user_input = (
        "Create an environmental report summary from this verified "
        "report context. Do not add any new measurements.\n\n"
        + json.dumps(
            report_context,
            ensure_ascii=False,
            default=str,
        )
    )

    # -----------------------------------------------------
    # GEMINI REQUEST PAYLOAD
    # -----------------------------------------------------

    payload = {
        "model": settings.GEMINI_MODEL,

        "input": user_input,

        "system_instruction": system_instruction,

        "store": False,

        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": {
                "type": "object",

                "properties": {
                    "summary": {
                        "type": "string"
                    },

                    "key_findings": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },

                    "limitations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },
                },

                "required": [
                    "summary",
                    "key_findings",
                    "limitations",
                ],
            },
        },

        "generation_config": {
            "temperature": 0.2,
            "max_output_tokens": 1200,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.GEMINI_API_KEY,
    }

    # -----------------------------------------------------
    # SEND REQUEST
    # -----------------------------------------------------

    try:

        response_data = await _request_gemini(
            headers=headers,
            payload=payload,
        )

        logger.info(
            "Gemini response status: %s",
            response_data.get("status"),
            )

        logger.info(
            "Gemini response keys: %s",
            list(response_data.keys()),
            )

        logger.info(
            "Gemini response steps: %s",
            json.dumps(
                response_data.get("steps", []),
                ensure_ascii=False,
                default=str,
            )[:4000],
        )

        generated_text = _extract_gemini_text(response_data)

        logger.info(
            "Extracted Gemini text preview: %r",
            generated_text[:1500] if generated_text else None,
        )

        if not generated_text:

            raise ValueError(
                "Gemini returned an empty summary."
            )

        parsed = _parse_json_response(
            generated_text
        )

        result = _normalise_summary(
            parsed
        )

        if not result["summary"]:

            raise ValueError(
                "Gemini summary was empty."
            )

        result["generation_method"] = "gemini"

        logger.info(
            "Gemini summary generated successfully."
        )

        return result

    # -----------------------------------------------------
    # ERROR HANDLING
    # -----------------------------------------------------

    except httpx.HTTPStatusError as exc:

        logger.error(
            "Gemini API HTTP error: status=%s, response=%s",
            exc.response.status_code,
            exc.response.text[:2000],
        )

        logger.warning(
            "Using deterministic statistical fallback."
        )

        return fallback

    except httpx.RequestError as exc:

        logger.error(
            "Gemini network error: %s",
            repr(exc),
        )

        logger.warning(
            "Using deterministic statistical fallback."
        )

        return fallback

    except (
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:

        logger.exception(
            "Gemini response processing failed: %s",
            repr(exc),
        )

        logger.warning(
            "Using deterministic statistical fallback."
        )

        return fallback
