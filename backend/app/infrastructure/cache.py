from hashlib import sha256
from time import monotonic
from typing import Generic, Iterable, TypeVar


def build_cache_key(parts: Iterable[str | None]) -> str:
    normalized = "\n".join(part or "" for part in parts)
    return sha256(normalized.encode("utf-8")).hexdigest()


T = TypeVar("T")


class MemoryTTLCache(Generic[T]):
    def __init__(self, *, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < monotonic():
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T) -> None:
        self._items[key] = (monotonic() + self.ttl_seconds, value)

    def clear(self) -> None:
        self._items.clear()
