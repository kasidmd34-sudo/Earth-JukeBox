"""Filesystem caching utility with TTL support."""
import hashlib
import json
import logging
import os
import time
from typing import Any, Optional
from app.config import settings

logger = logging.getLogger("earth_jukebox.cache")


class DiskCache:
    def __init__(self, cache_dir: str = settings.CACHE_DIR, ttl_seconds: int = 86400):
        self.cache_dir = cache_dir
        self.ttl = ttl_seconds
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create cache dir {cache_dir}: {e}")

    def _file_path(self, key: str) -> str:
        # Use SHA-256 for uniform filename length and collision prevention
        hashed_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self._file_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                item = json.load(f)
            saved_at = item.get("saved_at", 0)
            item_ttl = item.get("ttl", self.ttl)
            if time.time() - saved_at > item_ttl:
                try:
                    os.remove(path)
                except OSError:
                    pass
                return None
            return item.get("data")
        except Exception as e:
            logger.warning(f"Cache read error for {path}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        path = self._file_path(key)
        item_ttl = ttl if ttl is not None else self.ttl
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"saved_at": time.time(), "ttl": item_ttl, "data": value}, f)
        except Exception as e:
            logger.warning(f"Cache write error for {path}: {e}")

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        path = self._file_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False

    def clear(self) -> int:
        count = 0
        if not os.path.exists(self.cache_dir):
            return count
        for fname in os.listdir(self.cache_dir):
            if fname.endswith(".json"):
                try:
                    os.remove(os.path.join(self.cache_dir, fname))
                    count += 1
                except OSError:
                    pass
        return count


disk_cache = DiskCache()
