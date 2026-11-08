"""Robust NASA HTTP Client with retries, exponential backoff, connection pooling, and disk caching."""
import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, Optional
import httpx
from app.config import settings
from app.utils.caching import disk_cache

logger = logging.getLogger("earth_jukebox.nasa_client")


class NASAClient:
    def __init__(self):
        self.timeout = httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS, connect=10.0)
        self.max_retries = settings.HTTP_MAX_RETRIES
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Reuse persistent AsyncClient with HTTP connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Gracefully close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        serialized = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        return f"nasa_api_{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"

    async def get_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
        ttl_seconds: int = 86400,
    ) -> Dict[str, Any]:
        """Perform an asynchronous GET request to a NASA API endpoint with backoff and caching.

        Strict NASA Only Policy: Requests are routed exclusively to verified NASA endpoints.
        """
        params = params or {}
        headers = headers or {}

        # Earthdata token inclusion if configured
        if settings.NASA_EARTHDATA_TOKEN and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {settings.NASA_EARTHDATA_TOKEN}"

        cache_key = self._generate_cache_key(endpoint, params)

        if use_cache:
            cached_data = disk_cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Retrieved cached response for NASA endpoint: {endpoint}")
                return cached_data

        client = await self.get_client()
        backoff = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"NASA API Request -> {endpoint} (Attempt {attempt}/{self.max_retries})")
                response = await client.get(endpoint, params=params, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        # Some NASA endpoints return raw text/CSV
                        data = {"raw_content": response.text}

                    if use_cache:
                        disk_cache.set(cache_key, data, ttl=ttl_seconds)
                    return data

                elif response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        f"NASA upstream status {response.status_code}. Backing off {backoff:.1f}s (Attempt {attempt})..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

                elif response.status_code in (401, 403):
                    msg = (
                        f"NASA authentication failure (HTTP {response.status_code}) for {endpoint}. "
                        "Verify NASA_EARTHDATA_TOKEN or NASA_FIRMS_MAP_KEY."
                    )
                    logger.error(msg)
                    raise PermissionError(msg)

                elif response.status_code == 404:
                    logger.warning(f"NASA resource not found (HTTP 404) at {endpoint}")
                    raise FileNotFoundError(f"NASA data resource not found at endpoint {endpoint}")

                else:
                    response.raise_for_status()

            except httpx.RequestError as exc:
                logger.warning(f"Network transport error on attempt {attempt}: {exc}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"NASA API connection failed after {self.max_retries} attempts: {exc}")
                await asyncio.sleep(backoff)
                backoff *= 2.0

        raise RuntimeError(f"Unable to retrieve data from NASA endpoint {endpoint} after {self.max_retries} attempts.")


nasa_client = NASAClient()
