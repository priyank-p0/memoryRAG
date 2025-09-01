"""DiskCache wrapper utility."""

from typing import Any, Callable, Optional
from contextlib import contextmanager
from diskcache import Cache
from ..config import settings


class CacheService:
    """Simple cache service using diskcache with optional enable flag."""

    def __init__(self, directory: Optional[str] = None, ttl_seconds: Optional[int] = None, enabled: Optional[bool] = None):
        self.enabled = settings.enable_cache if enabled is None else enabled
        self.directory = directory or settings.cache_dir
        self.ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        self._cache = Cache(self.directory) if self.enabled else None

    def get(self, key: str) -> Any:
        if not self.enabled or not self._cache:
            return None
        return self._cache.get(key, default=None)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.enabled or not self._cache:
            return
        self._cache.set(key, value, expire=(ttl if ttl is not None else self.ttl))

    def memoize(self, ttl: Optional[int] = None) -> Callable:
        """Decorator to cache function results."""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                key = f"{func.__module__}.{func.__name__}:{repr(args)}:{repr(sorted(kwargs.items()))}"
                cached = self.get(key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                self.set(key, result, ttl=ttl)
                return result
            return wrapper
        return decorator

    def close(self):
        if self._cache:
            self._cache.close()


# Global cache instance
cache_service = CacheService()


