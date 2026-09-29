"""Small in-process rate limiter for auth endpoints.

This is intentionally dependency-free so the project works without an extra
rate-limit package. For a multi-instance production deployment, replace this
with a shared Redis-backed limiter.
"""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class AuthRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = AuthRateLimiter()


def client_key(ip: str | None, identifier: str = "") -> str:
    return f"{ip or 'unknown'}:{identifier.strip().lower()}"
