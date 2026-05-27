"""Translation cache implementation."""

from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any, TypedDict

DEFAULT_MAX_SIZE: int = 10_000

_ENV_MAX_SIZE: str = "OPENODIA_CACHE_MAX_SIZE"
_ENV_DISK: str = "OPENODIA_CACHE_DISK"


class CacheStats(TypedDict):
    """Snapshot of cache counters."""

    hits: int
    misses: int
    size: int
    max_size: int
    disk_size: int


class TranslationCache:
    """LRU cache for translation results, with optional disk persistence.

    Keys are arbitrary hashable tuples; the package uses
    ``(text, source_lang, dest_lang)`` triples. Values are translated strings.

    Args:
        max_size: Maximum number of entries to keep in memory. Must be ≥ 1.
        disk_path: Optional directory for persistent storage. Requires
            ``diskcache`` (install with ``pip install openodia[cache]``).
    """

    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        disk_path: Path | str | None = None,
    ) -> None:
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")
        self._max_size = max_size
        self._memory: OrderedDict[Any, str] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._disk: Any | None = None
        if disk_path is not None:
            self._disk = _open_diskcache(disk_path)

    # ------------------------------------------------------------------
    # Get / set
    # ------------------------------------------------------------------

    def get(self, key: Any) -> str | None:
        """Return a cached value or ``None`` if missing.

        Hits in memory are moved to the most-recently-used position. Hits
        on disk are promoted to memory.
        """
        if key in self._memory:
            self._memory.move_to_end(key)
            self._hits += 1
            return self._memory[key]
        if self._disk is not None:
            value = self._disk.get(key)
            if value is not None:
                self._store_memory(key, value)
                self._hits += 1
                return value
        self._misses += 1
        return None

    def set(self, key: Any, value: str) -> None:
        """Insert into memory (and disk, if configured)."""
        self._store_memory(key, value)
        if self._disk is not None:
            self._disk[key] = value

    def _store_memory(self, key: Any, value: str) -> None:
        self._memory[key] = value
        self._memory.move_to_end(key)
        while len(self._memory) > self._max_size:
            self._memory.popitem(last=False)

    # ------------------------------------------------------------------
    # Reporting / control
    # ------------------------------------------------------------------

    def stats(self) -> CacheStats:
        """Return current hit/miss/size counters."""
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            size=len(self._memory),
            max_size=self._max_size,
            disk_size=len(self._disk) if self._disk is not None else 0,
        )

    def clear(self) -> None:
        """Drop all entries (memory + disk) and reset counters."""
        self._memory.clear()
        self._hits = 0
        self._misses = 0
        if self._disk is not None:
            self._disk.clear()

    @property
    def max_size(self) -> int:
        """Configured LRU capacity."""
        return self._max_size

    @property
    def disk_enabled(self) -> bool:
        """Whether disk persistence is currently active."""
        return self._disk is not None


def _open_diskcache(disk_path: Path | str) -> Any:
    try:
        from diskcache import Cache
    except ImportError as exc:
        raise ImportError("Disk caching requires the 'diskcache' package. Install with: pip install openodia[cache]") from exc
    return Cache(str(Path(disk_path).expanduser()))


def _build_from_env() -> TranslationCache:
    max_size = int(os.environ.get(_ENV_MAX_SIZE, DEFAULT_MAX_SIZE))
    disk_path = os.environ.get(_ENV_DISK) or None
    return TranslationCache(max_size=max_size, disk_path=disk_path)


# ---------------------------------------------------------------------------
# Module-level singleton + convenience helpers
# ---------------------------------------------------------------------------

_cache: TranslationCache | None = None


def get_cache() -> TranslationCache:
    """Return the active cache instance, building it lazily on first use."""
    global _cache
    if _cache is None:
        _cache = _build_from_env()
    return _cache


def configure(
    max_size: int | None = None,
    disk_path: Path | str | None = None,
) -> TranslationCache:
    """Replace the active cache with a new configuration.

    Args:
        max_size: New LRU capacity. ``None`` keeps the current value.
        disk_path: Path for disk persistence; ``None`` disables disk
            persistence. To keep the existing disk path, pass it again.

    Returns:
        The newly-installed cache instance.
    """
    global _cache
    current = get_cache()
    new_max_size = max_size if max_size is not None else current.max_size
    _cache = TranslationCache(max_size=new_max_size, disk_path=disk_path)
    return _cache


def stats() -> CacheStats:
    """Snapshot of the active cache's counters."""
    return get_cache().stats()


def clear() -> None:
    """Drop all entries and reset counters in the active cache."""
    get_cache().clear()
