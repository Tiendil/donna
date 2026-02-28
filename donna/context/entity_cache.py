from __future__ import annotations

import time
from abc import ABC

from donna.domain.types import Milliseconds
from donna.workspaces.config import config


class TimedCacheValue:
    __slots__ = ("loaded_at_ms", "checked_at_ms")

    def __init__(self, loaded_at_ms: Milliseconds, checked_at_ms: Milliseconds) -> None:
        self.loaded_at_ms = loaded_at_ms
        self.checked_at_ms = checked_at_ms


class TimedCache(ABC):
    @staticmethod
    def _now_ms() -> Milliseconds:
        return Milliseconds(time.time_ns() // 1_000_000)

    @staticmethod
    def _cache_lifetime_ms() -> Milliseconds:
        return Milliseconds(max(0, int(config().cache_lifetime * 1000)))

    def _is_within_lifetime(self, cached: TimedCacheValue, now_ms: Milliseconds) -> bool:
        return (now_ms - cached.checked_at_ms) < self._cache_lifetime_ms()

    @staticmethod
    def _mark_checked(cached: TimedCacheValue, now_ms: Milliseconds) -> None:
        cached.checked_at_ms = now_ms
