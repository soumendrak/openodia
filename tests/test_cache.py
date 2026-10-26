from collections import OrderedDict
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


def test_concurrent_use_keeps_counters_exact_and_never_raises() -> None:
    import sys
    import threading

    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    shared = cache.TranslationCache(max_size=2)
    errors: list[BaseException] = []
    rounds = 3000

    def hammer() -> None:
        try:
            for i in range(rounds):
                key = (i % 3,)
                if shared.get(key) is None:
                    shared.set(key, "v")
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=hammer) for _ in range(8)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        sys.setswitchinterval(previous)
    stats = shared.stats()
    assert errors == []
    assert stats["hits"] + stats["misses"] == 8 * rounds
    assert stats["size"] <= 2


def test_cache_survives_pickle_and_deepcopy() -> None:
    import copy
    import pickle

    original = cache.TranslationCache(max_size=3)
    original.set(("a",), "x")
    for clone in (pickle.loads(pickle.dumps(original)), copy.deepcopy(original)):
        assert clone.get(("a",)) == "x"
        clone.set(("b",), "y")
        assert original.get(("b",)) is None


class RecordingLock:
    def __init__(self) -> None:
        self.held = False
        self.acquisitions = 0

    def __enter__(self) -> None:
        assert not self.held
        self.held = True
        self.acquisitions += 1

    def __exit__(self, *exc: object) -> None:
        self.held = False


class GuardedCache(cache.TranslationCache):
    GUARDED = frozenset({"_hits", "_misses"})

    def __getattribute__(self, name: str) -> object:
        if name in GuardedCache.GUARDED:
            lock = object.__getattribute__(self, "_lock")
            assert not isinstance(lock, RecordingLock) or lock.held, f"read {name} without the lock"
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: object) -> None:
        lock = self.__dict__.get("_lock")
        if name in GuardedCache.GUARDED and isinstance(lock, RecordingLock):
            assert lock.held, f"wrote {name} without the lock"
        super().__setattr__(name, value)


class GuardedMemory(OrderedDict[object, str]):
    def __init__(self, lock: RecordingLock) -> None:
        super().__init__()
        self.lock = lock

    def touch(self) -> None:
        assert self.lock.held, "memory touched without the lock"

    def __contains__(self, key: object) -> bool:
        self.touch()
        return super().__contains__(key)

    def __getitem__(self, key: object) -> str:
        self.touch()
        return super().__getitem__(key)

    def __setitem__(self, key: object, value: str) -> None:
        self.touch()
        super().__setitem__(key, value)

    def __len__(self) -> int:
        self.touch()
        return super().__len__()

    def move_to_end(self, key: object, last: bool = True) -> None:
        self.touch()
        super().move_to_end(key, last)

    def popitem(self, last: bool = True) -> tuple[object, str]:
        self.touch()
        return super().popitem(last)

    def clear(self) -> None:
        self.touch()
        super().clear()


class UnlockedDisk(dict[object, str]):
    def __init__(self, lock: RecordingLock) -> None:
        super().__init__()
        self.lock = lock

    def get(self, key: object, default: str | None = None) -> str | None:
        assert not self.lock.held, "disk read while holding the lock"
        return super().get(key, default)

    def __setitem__(self, key: object, value: str) -> None:
        assert not self.lock.held, "disk write while holding the lock"
        super().__setitem__(key, value)

    def __len__(self) -> int:
        assert not self.lock.held, "disk size read while holding the lock"
        return super().__len__()

    def clear(self) -> None:
        assert not self.lock.held, "disk clear while holding the lock"
        super().clear()


@pytest.fixture
def guarded() -> GuardedCache:
    instance = GuardedCache(max_size=2)
    lock = RecordingLock()
    instance._lock = lock
    instance._memory = GuardedMemory(lock)
    instance._disk = UnlockedDisk(lock)
    return instance


def test_get_set_stats_and_clear_each_take_the_lock_around_every_shared_access(guarded: GuardedCache) -> None:
    lock: RecordingLock = guarded._lock
    steps = [
        lambda: guarded.get(("miss",)),
        lambda: guarded.set(("a",), "x"),
        lambda: guarded.get(("a",)),
        lambda: guarded.set(("b",), "y"),
        lambda: guarded.set(("c",), "z"),
        lambda: guarded.stats(),
        lambda: guarded.clear(),
    ]
    for step in steps:
        before = lock.acquisitions
        step()
        assert lock.acquisitions > before
        assert not lock.held


def test_a_disk_hit_is_promoted_to_memory_under_the_lock(guarded: GuardedCache) -> None:
    guarded._disk["k"] = "v"
    assert guarded.get("k") == "v"
    assert guarded.get("k") == "v"
    assert guarded.stats() == {"hits": 2, "misses": 0, "size": 1, "max_size": 2, "disk_size": 1}


def test_disk_io_never_happens_while_the_lock_is_held(guarded: GuardedCache) -> None:
    guarded.set("a", "x")
    guarded.clear()
    guarded.get("a")
    guarded._disk["b"] = "y"
    guarded.get("b")
    assert guarded.stats()["disk_size"] == 1
    guarded.clear()


def test_every_instance_has_its_own_lock() -> None:
    first, second = cache.TranslationCache(), cache.TranslationCache()
    assert first._lock is not second._lock


def test_clones_get_their_own_lock() -> None:
    import copy
    import pickle

    original = cache.TranslationCache(max_size=3)
    original.set(("a",), "x")
    for clone in (pickle.loads(pickle.dumps(original)), copy.deepcopy(original), copy.copy(original)):
        assert clone._lock is not original._lock
        with original._lock:
            assert clone._lock.acquire(blocking=False)
            clone._lock.release()
        assert clone.get(("a",)) == "x"


def test_clones_do_not_share_a_lock_with_each_other() -> None:
    import copy
    import pickle

    originals = [cache.TranslationCache(), cache.TranslationCache()]
    clones = [
        make(original)
        for original in originals
        for make in (lambda c: pickle.loads(pickle.dumps(c)), copy.deepcopy, copy.copy, copy.copy)
    ]
    locks = [clone._lock for clone in clones] + [original._lock for original in originals]
    assert len({id(lock) for lock in locks}) == len(locks)


def test_a_shallow_copy_shares_the_memory_dict() -> None:
    import copy

    original = cache.TranslationCache(max_size=3)
    assert copy.copy(original)._memory is original._memory
