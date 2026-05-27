"""Translation cache configuration and observability.

The package keeps an in-memory LRU of translation results. By default it
holds 10,000 entries and is hidden from callers.

Use the helpers in this module to:

* enlarge / shrink the LRU,
* enable a persistent disk cache (requires the ``[cache]`` extra),
* observe hit/miss counts,
* clear the cache.

Configuration may also be set via environment variables at import time:

* ``OPENODIA_CACHE_MAX_SIZE`` — integer LRU size (default ``10000``).
* ``OPENODIA_CACHE_DISK`` — path to a directory used for disk persistence.

Example:
    >>> from openodia import cache
    >>> cache.configure(max_size=50_000)
    >>> cache.stats()
    {'hits': 0, 'misses': 0, 'size': 0, 'max_size': 50000, 'disk_size': 0}
"""

from openodia.cache._cache import (
    CacheStats,
    TranslationCache,
    clear,
    configure,
    get_cache,
    stats,
)

__all__ = [
    "CacheStats",
    "TranslationCache",
    "clear",
    "configure",
    "get_cache",
    "stats",
]
