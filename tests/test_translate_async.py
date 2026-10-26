import asyncio
import threading
from collections.abc import Callable
from unittest import mock

import pytest
from deep_translator.exceptions import LanguageNotSupportedException, TooManyRequests

import openodia
from openodia import _translate, cache

DICTIONARY = {"watch": "ଦେଖନ୍ତୁ"}


class FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.active = 0
        self.peak = 0
        self.gate: Callable[[str], None] = lambda text: None
        self.failures: dict[str, list[Exception]] = {}
        self._lock = threading.Lock()

    def translator(self, source: str, target: str) -> object:
        service = self

        class Translator:
            def translate(self, text: str) -> str:
                with service._lock:
                    service.calls.append((text, source, target))
                    service.active += 1
                    service.peak = max(service.peak, service.active)
                try:
                    service.gate(text)
                    queued = service.failures.get(text)
                    if queued:
                        raise queued.pop(0)
                    return f"{text}:{source}>{target}"
                finally:
                    with service._lock:
                        service.active -= 1

        return Translator()


@pytest.fixture
def service():
    cache.clear()
    fake = FakeService()
    with (
        mock.patch.object(_translate, "GoogleTranslator", fake.translator),
        mock.patch.object(_translate, "get_dictionary", lambda: DICTIONARY),
    ):
        yield fake
    cache.clear()


def test_public_names_are_exported() -> None:
    for name in ("odia_to_other_lang_async", "other_lang_to_odia_async", "universal_translation_async", "translate_batch"):
        assert getattr(openodia, name) is not None


def test_single_async_calls_match_the_sync_calls(service: FakeService) -> None:
    async def scenario() -> list[str]:
        return [
            await openodia.odia_to_other_lang_async("କଣ", "en"),
            await openodia.other_lang_to_odia_async("watch"),
            await openodia.other_lang_to_odia_async("hello", "en"),
            await openodia.universal_translation_async("hi", "en", "or"),
        ]

    sync = [
        openodia.odia_to_other_lang("କଣ", "en"),
        openodia.other_lang_to_odia("watch"),
        openodia.other_lang_to_odia("hello", "en"),
        openodia.universal_translation("hi", "en", "or"),
    ]
    cache.clear()
    assert asyncio.run(scenario()) == sync


def test_async_and_sync_share_the_cache(service: FakeService) -> None:
    asyncio.run(openodia.odia_to_other_lang_async("କଣ", "en"))
    openodia.odia_to_other_lang("କଣ", "en")
    assert service.calls == [("କଣ", "or", "en")]


def test_batch_preserves_order_and_defaults_to_odia_to_english(service: FakeService) -> None:
    texts = [f"t{i}" for i in range(20)]
    result = asyncio.run(openodia.translate_batch(texts, concurrency=5))
    assert result == [f"t{i}:or>en" for i in range(20)]


def test_batch_of_nothing_is_empty(service: FakeService) -> None:
    assert asyncio.run(openodia.translate_batch([])) == []
    assert service.calls == []


def test_batch_translates_a_repeated_text_once(service: FakeService) -> None:
    result = asyncio.run(openodia.translate_batch(["a", "b", "a", "a"]))
    assert result == ["a:or>en", "b:or>en", "a:or>en", "a:or>en"]
    assert sorted(service.calls) == [("a", "or", "en"), ("b", "or", "en")]


@pytest.mark.parametrize(
    ("source", "to", "expected"),
    [
        ("or", "en", "watch:or>en"),
        ("hi", "or", "watch:hi>or"),
        ("en", "hi", "watch:en>hi"),
        ("en", "or", "ଦେଖନ୍ତୁ"),
    ],
)
def test_batch_routes_each_language_pair_like_the_sync_api(service: FakeService, source: str, to: str, expected: str) -> None:
    assert asyncio.run(openodia.translate_batch(["watch"], source=source, to=to)) == [expected]


def test_concurrency_is_bounded_and_reached(service: FakeService) -> None:
    barrier = threading.Barrier(4, timeout=5)
    service.gate = lambda text: barrier.wait()
    asyncio.run(openodia.translate_batch([f"t{i}" for i in range(12)], concurrency=4))
    assert service.peak == 4


def test_first_error_is_raised_and_queued_work_never_starts(service: FakeService) -> None:
    service.failures["bad"] = [LanguageNotSupportedException("xx")]
    with pytest.raises(LanguageNotSupportedException):
        asyncio.run(openodia.translate_batch(["bad", "a", "b", "c"], concurrency=1))
    assert [call[0] for call in service.calls] == ["bad"]


def test_return_exceptions_keeps_every_slot(service: FakeService) -> None:
    failure = LanguageNotSupportedException("xx")
    service.failures["bad"] = [failure]
    result = asyncio.run(openodia.translate_batch(["a", "bad", "b"], return_exceptions=True))
    assert result == ["a:or>en", failure, "b:or>en"]


def test_transient_errors_are_retried_with_exponential_backoff(service: FakeService, monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def record(delay: float) -> None:
        sleeps.append(delay)
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", record)
    service.failures["a"] = [TooManyRequests(), ConnectionError("reset")]
    result = asyncio.run(openodia.translate_batch(["a"], retries=2, backoff=0.5))
    assert result == ["a:or>en"]
    assert sleeps == [0.5, 1.0]
    assert len(service.calls) == 3


def test_retries_run_out_and_raise_the_last_error(service: FakeService) -> None:
    service.failures["a"] = [TooManyRequests(), TooManyRequests(), TooManyRequests()]
    with pytest.raises(TooManyRequests):
        asyncio.run(openodia.translate_batch(["a"], retries=1, backoff=0))
    assert len(service.calls) == 2


def test_permanent_errors_are_not_retried(service: FakeService) -> None:
    service.failures["a"] = [LanguageNotSupportedException("xx")] * 3
    with pytest.raises(LanguageNotSupportedException):
        asyncio.run(openodia.translate_batch(["a"], retries=3, backoff=0))
    assert len(service.calls) == 1


@pytest.mark.parametrize("option", [{"concurrency": 0}, {"retries": -1}, {"backoff": -0.1}])
def test_bad_options_are_rejected(option: dict[str, float]) -> None:
    with pytest.raises(ValueError, match="must be"):
        asyncio.run(openodia.translate_batch(["a"], **option))


def test_cancelling_a_batch_stops_queued_work_and_leaves_the_cache_usable(service: FakeService) -> None:
    started = threading.Event()
    release = threading.Event()

    def gate(text: str) -> None:
        started.set()
        release.wait(5)

    service.gate = gate

    async def scenario() -> None:
        task = asyncio.ensure_future(openodia.translate_batch(["a", "b", "c", "d"], concurrency=1))
        await asyncio.to_thread(started.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()

    asyncio.run(scenario())
    assert [call[0] for call in service.calls] == ["a"]
    service.gate = lambda text: None
    assert openodia.odia_to_other_lang("a", "en") == "a:or>en"
    assert openodia.odia_to_other_lang("b", "en") == "b:or>en"
