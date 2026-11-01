import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
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
        c._memory.clear()
        assert c.get("persistent") == "yes"
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

        def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
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
        import deep_translator

        class FakeGoogleTranslator:
            def __init__(self, source: str, target: str) -> None:
                pass

            def translate(self, text: str) -> str:
                return "Hello! Sounds good?"

        with mock.patch.object(deep_translator, "GoogleTranslator", FakeGoogleTranslator):
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
    GUARDED = frozenset({"_hits", "_misses", "_generation"})

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
    for name in ("_lock", "_write_lock"):
        locks = [getattr(clone, name) for clone in clones] + [getattr(original, name) for original in originals]
        assert len({id(lock) for lock in locks}) == len(locks)


def test_a_shallow_copy_gets_its_own_memory_dict() -> None:
    import copy

    original = cache.TranslationCache(max_size=3)
    original.set(("a",), "x")
    clone = copy.copy(original)
    assert clone._memory is not original._memory
    clone.set(("b",), "y")
    assert original.get(("b",)) is None
    assert clone.get(("a",)) == "x"


def test_a_copy_reads_memory_under_the_lock(guarded: GuardedCache) -> None:
    import copy

    lock: RecordingLock = guarded._lock
    guarded.set(("a",), "x")
    before = lock.acquisitions
    clone = copy.deepcopy(guarded)
    assert lock.acquisitions == before + 1
    assert not lock.held
    assert dict(clone._memory) == {("a",): "x"}


class TestSingletonConstruction:
    THREADS = 8

    @pytest.fixture
    def unbuilt(self, monkeypatch: pytest.MonkeyPatch) -> tuple[list[cache.TranslationCache], threading.Event]:
        from openodia.cache import _cache as cache_module

        built: list[cache.TranslationCache] = []
        release = threading.Event()

        def slow_factory() -> cache.TranslationCache:
            release.wait(timeout=5)
            instance = cache.TranslationCache(max_size=5)
            built.append(instance)
            return instance

        monkeypatch.setattr(cache_module, "_cache", None)
        monkeypatch.setattr(cache_module, "_build_from_env", slow_factory)
        return built, release

    def test_threads_making_the_first_call_together_share_one_instance(
        self, unbuilt: tuple[list[cache.TranslationCache], threading.Event]
    ) -> None:
        built, release = unbuilt
        gate = threading.Barrier(self.THREADS + 1)
        seen: list[cache.TranslationCache] = []

        def first_call() -> None:
            gate.wait(timeout=5)
            seen.append(cache.get_cache())

        workers = [threading.Thread(target=first_call) for _ in range(self.THREADS)]
        for worker in workers:
            worker.start()
        gate.wait(timeout=5)
        time.sleep(0.2)
        release.set()
        for worker in workers:
            worker.join(timeout=5)
        assert len(built) == 1
        assert len(seen) == self.THREADS
        assert all(instance is built[0] for instance in seen)
        assert cache.get_cache() is built[0]

    def test_a_built_singleton_is_returned_without_taking_the_lock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from openodia.cache import _cache as cache_module

        lock = RecordingLock()
        monkeypatch.setattr(cache_module, "_singleton_lock", lock)
        built = cache.get_cache()
        assert cache.get_cache() is built
        assert lock.acquisitions == 0

    def test_the_first_call_builds_under_the_module_lock_and_checks_again_inside_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from openodia.cache import _cache as cache_module

        winner = cache.TranslationCache(max_size=7)

        def rival_wins_the_race() -> cache.TranslationCache:
            raise AssertionError("built a second instance")

        class WinsWhileWaiting(RecordingLock):
            def __enter__(self) -> None:
                monkeypatch.setattr(cache_module, "_cache", winner)
                super().__enter__()

        monkeypatch.setattr(cache_module, "_cache", None)
        monkeypatch.setattr(cache_module, "_build_from_env", rival_wins_the_race)
        monkeypatch.setattr(cache_module, "_singleton_lock", WinsWhileWaiting())
        assert cache.get_cache() is winner


class PausingDisk:
    def __init__(self, pause_on: str, fail: bool = False, **entries: str) -> None:
        self.store: dict[object, str] = {(key,): value for key, value in entries.items()}
        self.pause_on = pause_on
        self.fail = fail
        self.entered = threading.Event()
        self.resume = threading.Event()
        self.reads = 0
        self.reread = threading.Event()

    def __reduce__(self) -> tuple[type[dict[object, str]], tuple[dict[object, str]]]:
        return dict, (dict(self.store),)

    def _pause(self, operation: str) -> None:
        if operation == self.pause_on and not self.entered.is_set():
            self.entered.set()
            assert self.resume.wait(timeout=5)

    def get(self, key: object) -> str | None:
        self.reads += 1
        if self.reads > 1:
            self.reread.set()
        value = self.store.get(key)
        self._pause("get")
        return value

    def _write(self, operation: str) -> None:
        self._pause(operation)
        if self.fail:
            raise OSError("disk full")

    def __setitem__(self, key: object, value: str) -> None:
        self._write("set")
        self.store[key] = value

    def clear(self) -> None:
        self._write("clear")
        self.store.clear()

    def __len__(self) -> int:
        return len(self.store)


class FlakyDisk(dict[object, str]):
    MAX_READS = 3

    def __init__(self, failures: int = 0) -> None:
        super().__init__()
        self.failures = failures
        self.reads = 0

    def get(self, key: object, default: str | None = None) -> str | None:
        self.reads += 1
        assert self.reads <= self.MAX_READS, "get keeps re-reading the disk"
        return super().get(key, default)

    def _fail(self) -> None:
        if self.failures:
            self.failures -= 1
            raise OSError("disk full")

    def __setitem__(self, key: object, value: str) -> None:
        self._fail()
        super().__setitem__(key, value)

    def clear(self) -> None:
        self._fail()
        super().clear()


class WatchedLock:
    def __init__(self, contended: threading.Event) -> None:
        self._lock = threading.Lock()
        self.contended = contended

    def __enter__(self) -> None:
        if not self._lock.acquire(blocking=False):
            self.contended.set()
            self._lock.acquire()

    def __exit__(self, *exc: object) -> None:
        self._lock.release()


class PauseAfterFirstRelease:
    def __init__(self, thread_name: str) -> None:
        self._lock = threading.Lock()
        self.thread_name = thread_name
        self.released = threading.Event()
        self.resume = threading.Event()

    def __enter__(self) -> None:
        self._lock.acquire()

    def __exit__(self, *exc: object) -> None:
        self._lock.release()
        if threading.current_thread().name == self.thread_name and not self.released.is_set():
            self.released.set()
            assert self.resume.wait(timeout=5)


class SlowToCopy:
    def __init__(self, name: str, entered: threading.Event | None = None, resume: threading.Event | None = None) -> None:
        self.name = name
        self.entered = entered
        self.resume = resume

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SlowToCopy) and other.name == self.name

    def __reduce__(self) -> tuple[type["SlowToCopy"], tuple[str]]:
        if self.entered is not None and self.resume is not None and not self.entered.is_set():
            self.entered.set()
            assert self.resume.wait(timeout=5)
        return SlowToCopy, (self.name,)


def _disk_cache(disk: object) -> cache.TranslationCache:
    instance = cache.TranslationCache(max_size=4)
    instance._disk = disk
    return instance


def _start(
    target: Callable[[], object], done: threading.Event | None = None, name: str | None = None
) -> tuple[threading.Thread, list[object]]:
    results: list[object] = []

    def run() -> None:
        try:
            results.append(target())
        except OSError as exc:
            results.append(exc)
        finally:
            if done is not None:
                done.set()

    thread = threading.Thread(target=run, daemon=True, name=name)
    thread.start()
    return thread, results


def _watch_writes(instance: cache.TranslationCache) -> threading.Event:
    parked = threading.Event()
    instance._write_lock = WatchedLock(parked)
    return parked


class TestRacesWithDiskIO:
    def test_clear_during_a_paused_disk_read_leaves_nothing_behind(self) -> None:
        disk = PausingDisk("get", k="old")
        shared = _disk_cache(disk)
        reader, returned = _start(lambda: shared.get(("k",)))
        assert disk.entered.wait(timeout=5)
        shared.clear()
        disk.resume.set()
        reader.join(timeout=5)
        assert returned == [None]
        assert dict(shared._memory) == {}
        assert disk.store == {}
        assert shared.get(("k",)) is None
        assert shared.stats() == {"hits": 0, "misses": 2, "size": 0, "max_size": 4, "disk_size": 0}

    def test_set_during_a_paused_disk_read_leaves_the_new_value_in_memory_and_on_disk(self) -> None:
        disk = PausingDisk("get", k="v1")
        shared = _disk_cache(disk)
        reader, returned = _start(lambda: shared.get(("k",)))
        assert disk.entered.wait(timeout=5)
        shared.set(("k",), "v2")
        disk.resume.set()
        reader.join(timeout=5)
        assert returned == ["v2"]
        assert dict(shared._memory) == {("k",): "v2"}
        assert disk.store == {("k",): "v2"}
        assert shared.get(("k",)) == "v2"
        assert shared.stats()["hits"] == 2

    @pytest.mark.parametrize("write", ["set", "clear"])
    def test_a_read_that_ends_just_after_a_write_releases_the_lock_is_not_promoted(self, write: str) -> None:
        disk = PausingDisk("get", k="old")
        shared = _disk_cache(disk)
        hook = PauseAfterFirstRelease("writer")
        shared._lock = hook
        parked = _watch_writes(shared)
        reader, returned = _start(lambda: shared.get(("k",)), done=parked)
        assert disk.entered.wait(timeout=5)
        operation: Callable[[], object] = (lambda: shared.set(("k",), "new")) if write == "set" else shared.clear
        writer, _ = _start(operation, name="writer")
        assert hook.released.wait(timeout=5)
        disk.resume.set()
        assert parked.wait(timeout=5)
        hook.resume.set()
        writer.join(timeout=5)
        reader.join(timeout=5)
        expected = {"set": {("k",): "new"}, "clear": {}}[write]
        assert returned == [expected.get(("k",))]
        assert dict(shared._memory) == expected
        assert disk.store == expected
        assert shared.get(("k",)) == expected.get(("k",))

    def test_a_disk_read_that_starts_during_a_clear_is_not_promoted(self) -> None:
        disk = PausingDisk("clear", k="old")
        shared = _disk_cache(disk)
        parked = _watch_writes(shared)
        clearer, _ = _start(shared.clear)
        assert disk.entered.wait(timeout=5)
        reader, returned = _start(lambda: shared.get(("k",)), done=parked)
        assert parked.wait(timeout=5)
        assert returned == []
        disk.resume.set()
        clearer.join(timeout=5)
        reader.join(timeout=5)
        assert returned == [None]
        assert dict(shared._memory) == {}
        assert disk.store == {}

    def test_a_get_during_a_disk_write_waits_for_it_instead_of_rereading_the_disk(self) -> None:
        disk = PausingDisk("set")
        shared = _disk_cache(disk)
        parked = _watch_writes(shared)
        disk.reread = parked
        writer, _ = _start(lambda: shared.set(("k",), "v"))
        assert disk.entered.wait(timeout=5)
        reader, returned = _start(lambda: shared.get(("other",)), done=parked)
        assert parked.wait(timeout=5)
        assert (disk.reads, returned) == (1, [])
        disk.resume.set()
        writer.join(timeout=5)
        reader.join(timeout=5)
        assert (disk.reads, returned) == (2, [None])

    def test_a_clear_waits_for_a_set_that_is_writing_to_disk(self) -> None:
        disk = PausingDisk("set")
        shared = _disk_cache(disk)
        parked = _watch_writes(shared)
        writer, _ = _start(lambda: shared.set(("k",), "v"))
        assert disk.entered.wait(timeout=5)
        clearer, _ = _start(shared.clear, done=parked)
        assert parked.wait(timeout=5)
        assert dict(shared._memory) == {("k",): "v"}
        disk.resume.set()
        writer.join(timeout=5)
        clearer.join(timeout=5)
        assert dict(shared._memory) == {}
        assert disk.store == {}

    def test_two_sets_of_one_key_leave_memory_and_disk_agreeing(self) -> None:
        disk = PausingDisk("set")
        shared = _disk_cache(disk)
        parked = _watch_writes(shared)
        first, _ = _start(lambda: shared.set(("k",), "a"))
        assert disk.entered.wait(timeout=5)
        second, _ = _start(lambda: shared.set(("k",), "b"), done=parked)
        assert parked.wait(timeout=5)
        disk.resume.set()
        first.join(timeout=5)
        second.join(timeout=5)
        assert disk.store == dict(shared._memory) == {("k",): "b"}

    @pytest.mark.parametrize("write", ["set", "clear"])
    def test_a_disk_write_that_raises_leaves_the_cache_usable(self, write: str) -> None:
        disk = FlakyDisk(failures=1)
        shared = _disk_cache(disk)
        operation: Callable[[], object] = (lambda: shared.set(("k",), "v1")) if write == "set" else shared.clear
        with pytest.raises(OSError, match="disk full"):
            operation()
        assert shared.get(("other",)) is None
        assert disk.reads == 1
        shared.set(("k",), "v2")
        assert dict(disk) == {("k",): "v2"}
        assert shared.get(("k",)) == "v2"
        assert disk.reads == 1
        assert shared.stats()["misses"] == 1

    def test_a_set_with_an_unhashable_key_leaves_the_cache_usable(self) -> None:
        disk = FlakyDisk()
        shared = _disk_cache(disk)
        with pytest.raises(TypeError):
            shared.set([], "v")
        assert shared.get(("other",)) is None
        assert disk.reads == 1
        assert dict(disk) == {}

    @pytest.mark.parametrize("write", ["set", "clear"])
    def test_a_get_waiting_on_a_disk_write_that_raises_finishes(self, write: str) -> None:
        disk = PausingDisk(write, fail=True)
        shared = _disk_cache(disk)
        parked = _watch_writes(shared)
        operation: Callable[[], object] = (lambda: shared.set(("k",), "v")) if write == "set" else shared.clear
        writer, failed = _start(operation)
        assert disk.entered.wait(timeout=5)
        reader, returned = _start(lambda: shared.get(("other",)), done=parked)
        assert parked.wait(timeout=5)
        disk.resume.set()
        writer.join(timeout=5)
        reader.join(timeout=5)
        assert [str(exc) for exc in failed] == ["disk full"]
        assert (disk.reads, returned) == (2, [None])


class TestCopiesDuringWrites:
    @staticmethod
    def _copies() -> list[Callable[[cache.TranslationCache], cache.TranslationCache]]:
        import copy
        import pickle

        return [lambda c: pickle.loads(pickle.dumps(c)), copy.deepcopy, copy.copy]

    def test_a_deepcopy_while_another_thread_sets_copies_a_snapshot(self) -> None:
        import copy

        entered, resume = threading.Event(), threading.Event()
        original = cache.TranslationCache(max_size=8)
        original.set(SlowToCopy("a", entered, resume), "x")
        original.set(SlowToCopy("b"), "y")
        copier, copies = _start(lambda: copy.deepcopy(original))
        assert entered.wait(timeout=5)
        original.set(SlowToCopy("c"), "z")
        resume.set()
        copier.join(timeout=5)
        assert len(copies) == 1
        clone = copies[0]
        assert isinstance(clone, cache.TranslationCache)
        assert [key.name for key in clone._memory] == ["a", "b"]
        assert clone.get(SlowToCopy("c")) is None
        assert original.get(SlowToCopy("c")) == "z"

    def test_a_clone_taken_during_a_paused_disk_write_works_on_its_own(self) -> None:
        for make in self._copies():
            original = cache.TranslationCache(max_size=4)
            original.set(("a",), "x")
            disk = PausingDisk("set")
            original._disk = disk
            writer, _ = _start(lambda: original.set(("b",), "y"))
            assert disk.entered.wait(timeout=5)
            clone = make(original)
            clone._disk = FlakyDisk()
            assert dict(clone._memory) == {("a",): "x", ("b",): "y"}
            assert clone.get(("missing",)) is None
            assert clone._disk.reads == 1
            clone.set(("c",), "z")
            assert clone.get(("c",)) == "z"
            disk.resume.set()
            writer.join(timeout=5)
            assert original.get(("c",)) is None

    def test_clones_writing_to_disk_do_not_block_each_other(self) -> None:
        from openodia.cache import _cache as cache_module

        original = cache.TranslationCache(max_size=4)
        for make in self._copies():
            first, second = make(original), make(original)
            locks = {id(instance._write_lock) for instance in (original, first, second)}
            assert len(locks | {id(cache_module._singleton_lock)}) == 4
            disk = PausingDisk("set")
            first._disk = disk
            writer, _ = _start(lambda: first.set(("k",), "a"))
            assert disk.entered.wait(timeout=5)
            other, done = _start(lambda: second.set(("k",), "b"))
            other.join(timeout=5)
            disk.resume.set()
            writer.join(timeout=5)
            assert done == [None]
            assert (first.get(("k",)), second.get(("k",))) == ("a", "b")
