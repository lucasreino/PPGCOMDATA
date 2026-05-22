"""Cache TTL simples em memória (por processo/worker)."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

_lock = Lock()
_store: Dict[str, Tuple[float, Any]] = {}


def cache_get(key: str, ttl_sec: float) -> Optional[Any]:
    now = time.time()
    with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        ts, value = entry
        if now - ts >= ttl_sec:
            del _store[key]
            return None
        return value


def cache_set(key: str, value: Any) -> None:
    with _lock:
        _store[key] = (time.time(), value)


def cache_clear_prefix(prefix: str = "") -> int:
    with _lock:
        if not prefix:
            n = len(_store)
            _store.clear()
            return n
        keys = [k for k in _store if k.startswith(prefix)]
        for k in keys:
            del _store[k]
        return len(keys)


def cached_call(key: str, ttl_sec: float, factory: Callable[[], Any]) -> Any:
    hit = cache_get(key, ttl_sec)
    if hit is not None:
        return hit
    value = factory()
    cache_set(key, value)
    return value
