"""Small in-memory sliding-window limiter for public read-only endpoints."""

from collections import deque
import math
import threading
import time


class SlidingWindowRateLimiter:
    """Limit requests per client and globally without persisting request data."""

    def __init__(self, *, requests, window_seconds, global_requests):
        self.requests = requests
        self.window_seconds = window_seconds
        self.global_requests_limit = global_requests
        self._lock = threading.Lock()
        self._client_requests = {}
        self._global_requests = deque()
        self._last_cleanup = 0

    @staticmethod
    def _prune(entries, cutoff):
        while entries and entries[0] <= cutoff:
            entries.popleft()

    def allow(self, client_key):
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._prune(self._global_requests, cutoff)
            if now - self._last_cleanup >= self.window_seconds:
                for existing_key, entries in list(self._client_requests.items()):
                    self._prune(entries, cutoff)
                    if not entries:
                        del self._client_requests[existing_key]
                self._last_cleanup = now

            client_entries = self._client_requests.setdefault(client_key, deque())
            self._prune(client_entries, cutoff)
            limit_reached = len(self._global_requests) >= self.global_requests_limit
            limit_reached = limit_reached or len(client_entries) >= self.requests
            if limit_reached:
                oldest = max(
                    self._global_requests[0] if self._global_requests else now,
                    client_entries[0] if client_entries else now,
                )
                retry_after = math.ceil(self.window_seconds - (now - oldest))
                return False, max(1, retry_after)

            client_entries.append(now)
            self._global_requests.append(now)
            return True, None

    def reset(self):
        with self._lock:
            self._client_requests.clear()
            self._global_requests.clear()
            self._last_cleanup = 0
