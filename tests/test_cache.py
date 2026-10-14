from collections.abc import Iterator
from pathlib import Path
from unittest import mock

import pytest

from openodia import cache


@pytest.fixture(autouse=True)
def _isolated_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test gets a freshly-configured in-memory cache."""
    monkeypatch.delenv("OPENODIA_CACHE_MAX_SIZE", raising=False)
    monkeypatch.delenv("OPENODIA_CACHE_DISK", raising=False)
    cache.configure(max_size=100, disk_path=None)


class TestTranslationCacheBasics:
    def test_get_returns_none_for_miss(self) -> None:
        c = cache.get_cache()
        assert c.get("missing-key") is None

    def test_set_then_get(self) -> None:
        c = cache.get_cache()
        c.set("k", "v")
        assert c.get("k") == "v"

    def test_stats_counts_hits_and_misses(self) -> None:
        c = cache.get_cache()
        c.set("k", "v")
        c.get("k")  # hit
        c.get("k")  # hit
        c.get("missing")  # miss
        s = c.stats()
        assert s["hits"] == 2
        assert s["misses"] == 1

    def test_size_increases_on_set(self) -> None:
        c = cache.get_cache()
        assert c.stats()["size"] == 0
        c.set("a", "1")
        c.set("b", "2")
        assert c.stats()["size"] == 2

    def test_clear_resets_everything(self) -> None:
        c = cache.get_cache()
        c.set("a", "1")
        c.get("a")
        c.clear()
        s = c.stats()
        assert s == {"hits": 0, "misses": 0, "size": 0, "max_size": 100, "disk_size": 0}


class TestLRUEviction:
    def test_oldest_entry_evicted_when_full(self) -> None:
        cache.configure(max_size=3, disk_path=None)
        c = cache.get_cache()
        c.set("a", "1")
        c.set("b", "2")
        c.set("c", "3")
        c.set("d", "4")  # evicts "a"
        assert c.get("a") is None
        assert c.get("b") == "2"
        assert c.get("d") == "4"

    def test_access_promotes_entry(self) -> None:
        cache.configure(max_size=3, disk_path=None)
        c = cache.get_cache()
        c.set("a", "1")
        c.set("b", "2")
        c.set("c", "3")
        c.get("a")  # promote "a" to MRU
        c.set("d", "4")  # should evict "b", not "a"
        assert c.get("a") == "1"
        assert c.get("b") is None

    def test_repeated_set_overwrites_without_growing(self) -> None:
        c = cache.get_cache()
        c.set("k", "1")
        c.set("k", "2")
        assert c.stats()["size"] == 1
        assert c.get("k") == "2"


class TestConfigure:
    def test_configure_changes_max_size(self) -> None:
        cache.configure(max_size=42)
        assert cache.get_cache().max_size == 42

    def test_configure_with_none_keeps_max_size(self) -> None:
        cache.configure(max_size=42)
        cache.configure(max_size=None)
        assert cache.get_cache().max_size == 42

    def test_configure_replaces_instance(self) -> None:
        c1 = cache.get_cache()
        cache.configure(max_size=99)
        assert cache.get_cache() is not c1

    def test_configure_rejects_zero_max_size(self) -> None:
        with pytest.raises(ValueError, match="max_size must be >= 1"):
            cache.configure(max_size=0)


class TestEnvVars:
    def test_max_size_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Force fresh lazy build.
        monkeypatch.setenv("OPENODIA_CACHE_MAX_SIZE", "777")
        from openodia.cache import _cache as cache_module

        cache_module._cache = None
        try:
            assert cache.get_cache().max_size == 777
        finally:
            cache_module._cache = None  # avoid leaking to other tests

    def test_default_max_size_when_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from openodia.cache import _cache as cache_module

        monkeypatch.delenv("OPENODIA_CACHE_MAX_SIZE", raising=False)
        cache_module._cache = None
        try:
            assert cache.get_cache().max_size == 10_000
        finally:
            cache_module._cache = None


class TestModuleHelpers:
    def test_stats_proxy(self) -> None:
        c = cache.get_cache()
        c.set("k", "v")
        c.get("k")
        assert cache.stats() == c.stats()

    def test_clear_proxy(self) -> None:
        c = cache.get_cache()
        c.set("k", "v")
        cache.clear()
        assert c.stats()["size"] == 0


class TestDiskCache:
    """Disk caching requires the [cache] extra. Skip if unavailable."""

    pytest.importorskip("diskcache")

    def test_value_persists_across_clear_of_memory_only(self, tmp_path: Path) -> None:
        cache.configure(max_size=100, disk_path=tmp_path)
        c = cache.get_cache()
        c.set("persistent", "yes")
        # Clear in-memory by reconfiguring (this also clears disk... so
        # instead, manually evict in-memory and verify disk re-promotes).
        c._memory.clear()  # noqa: SLF001 — internal probe for the test
        assert c.get("persistent") == "yes"  # promoted back from disk
        assert c.stats()["disk_size"] >= 1

    def test_clear_clears_disk(self, tmp_path: Path) -> None:
        cache.configure(max_size=100, disk_path=tmp_path)
        c = cache.get_cache()
        c.set("k", "v")
        c.clear()
        assert c.get("k") is None
        assert c.stats()["disk_size"] == 0

    def test_disk_enabled_property(self, tmp_path: Path) -> None:
        cache.configure(max_size=100, disk_path=None)
        assert cache.get_cache().disk_enabled is False
        cache.configure(max_size=100, disk_path=tmp_path)
        assert cache.get_cache().disk_enabled is True

    def test_disk_path_accepts_string(self, tmp_path: Path) -> None:
        cache.configure(max_size=100, disk_path=str(tmp_path))
        assert cache.get_cache().disk_enabled is True

    def test_helpful_error_when_diskcache_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate the [cache] extra being missing."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "diskcache":
                raise ImportError("simulated")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ImportError, match=r"openodia\[cache\]"):
            cache.configure(max_size=10, disk_path=tmp_path)


class TestTranslationIntegration:
    """The translation path should route through the cache."""

    @pytest.fixture(autouse=True)
    def _fake_translator(self) -> Iterator[None]:
        """Keep these cache assertions off the live translation service.

        What is under test is the caching behaviour, not the wording Google
        returns, so a fixed reply is enough.
        """
        from openodia import _translate

        class FakeGoogleTranslator:
            def __init__(self, source: str, target: str) -> None:
                pass

            def translate(self, text: str) -> str:
                return "Hello! Sounds good?"

        with mock.patch.object(_translate, "GoogleTranslator", FakeGoogleTranslator):
            yield

    def test_first_lookup_is_a_miss(self) -> None:
        from openodia import odia_to_other_lang

        result = odia_to_other_lang("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?")
        assert result == "Hello! Sounds good?"
        # The reply was fetched and stored, so we now have one entry.
        assert cache.stats()["size"] == 1
        assert cache.stats()["misses"] == 1

    def test_second_lookup_is_a_hit(self) -> None:
        from openodia import odia_to_other_lang

        odia_to_other_lang("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?")
        odia_to_other_lang("ନମସ୍କାର!ଭଲ ଲାଗୁଛି?")
        assert cache.stats()["hits"] >= 1
