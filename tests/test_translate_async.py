import asyncio
import inspect
import math
import threading
import time
import typing
from collections.abc import Callable
from unittest import mock

import pytest
import requests
from deep_translator.exceptions import LanguageNotSupportedException, RequestError, TooManyRequests

import openodia
from openodia import _translate, _translate_async, cache

DICTIONARY = {"watch": "ଦେଖନ୍ତୁ"}


def anything(value: object) -> typing.Any:
    return value


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


def test_stopped_worker_skips_the_network_call() -> None:
    stopped = threading.Event()
    stopped.set()
    calls: list[str] = []
    run = _translate_async._unless_stopped(calls.append, stopped, 0, False)
    assert run("a", 0) == ""
    assert calls == []


def test_first_failure_stops_a_single_worker_from_taking_the_next_text(service: FakeService) -> None:
    def gate(text: str) -> None:
        time.sleep(0.05)

    service.gate = gate
    service.failures["bad"] = [LanguageNotSupportedException("xx")]
    with pytest.raises(LanguageNotSupportedException):
        asyncio.run(openodia.translate_batch(["bad", "a", "b", "c", "d"], concurrency=1))
    assert [call[0] for call in service.calls] == ["bad"]


def test_a_retryable_failure_does_not_stop_the_other_texts(service: FakeService) -> None:
    service.failures["a"] = [TooManyRequests()]
    result = asyncio.run(openodia.translate_batch(["a", "b", "c"], concurrency=1, retries=1, backoff=0))
    assert result == ["a:or>en", "b:or>en", "c:or>en"]


def test_identical_texts_in_one_batch_are_translated_once_even_when_they_overlap(service: FakeService) -> None:
    service.gate = lambda text: time.sleep(0.05)
    result = asyncio.run(openodia.translate_batch(["same"] * 8, concurrency=8))
    assert result == ["same:or>en"] * 8
    assert len(service.calls) == 1


def test_default_concurrency_is_eight(service: FakeService) -> None:
    barrier = threading.Barrier(8, timeout=5)
    service.gate = lambda text: barrier.wait()
    asyncio.run(openodia.translate_batch([f"t{i}" for i in range(16)]))
    assert service.peak == 8


def http_error(status: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status
    return requests.HTTPError(f"{status}", response=response)


@pytest.mark.parametrize(
    "failure",
    [
        RequestError(),
        http_error(400),
        http_error(403),
        http_error(404),
        PermissionError("denied"),
        FileNotFoundError("missing"),
        OSError("disk"),
        ValueError("odd"),
    ],
    ids=lambda failure: type(failure).__name__ + str(getattr(getattr(failure, "response", None), "status_code", "")),
)
def test_failures_that_are_not_rate_limits_server_errors_or_connection_problems_are_not_retried(
    service: FakeService, failure: Exception
) -> None:
    service.failures["a"] = [failure] * 3
    with pytest.raises(type(failure)):
        asyncio.run(openodia.translate_batch(["a"], retries=2, backoff=0))
    assert len(service.calls) == 1


@pytest.mark.parametrize(
    "failure",
    [
        TooManyRequests(),
        http_error(429),
        http_error(500),
        http_error(503),
        http_error(599),
        requests.ConnectionError("reset"),
        requests.Timeout("slow"),
        requests.exceptions.ConnectTimeout("slow"),
        ConnectionResetError("reset"),
        TimeoutError("slow"),
    ],
    ids=lambda failure: type(failure).__name__ + str(getattr(getattr(failure, "response", None), "status_code", "")),
)
def test_rate_limits_server_errors_and_connection_problems_are_retried(service: FakeService, failure: Exception) -> None:
    service.failures["a"] = [failure]
    assert asyncio.run(openodia.translate_batch(["a"], retries=2, backoff=0)) == ["a:or>en"]
    assert len(service.calls) == 2


def test_status_is_read_from_the_exception_itself(service: FakeService) -> None:
    class Upstream(Exception):
        status_code = 502

    service.failures["a"] = [Upstream()]
    assert asyncio.run(openodia.translate_batch(["a"], retries=1, backoff=0)) == ["a:or>en"]


@pytest.mark.parametrize("value", [1.5, 2.0, True, False, 0, -1, None, "3", math.nan, math.inf])
def test_concurrency_must_be_a_positive_integer(value: object) -> None:
    with pytest.raises(ValueError, match="concurrency must be an integer >= 1"):
        asyncio.run(openodia.translate_batch(["a"], concurrency=anything(value)))


@pytest.mark.parametrize("value", [1.5, 1.0, True, False, -1, None, "1", math.nan, math.inf])
def test_retries_must_be_a_non_negative_integer(value: object) -> None:
    with pytest.raises(ValueError, match="retries must be an integer >= 0"):
        asyncio.run(openodia.translate_batch(["a"], retries=anything(value)))


@pytest.mark.parametrize("value", [-0.1, -1, math.nan, math.inf, -math.inf, True, None, "1"])
def test_backoff_must_be_a_finite_non_negative_number(value: object) -> None:
    with pytest.raises(ValueError, match="backoff must be a finite number >= 0"):
        asyncio.run(openodia.translate_batch(["a"], backoff=anything(value)))


def test_integer_backoff_and_zero_values_are_accepted(service: FakeService) -> None:
    assert asyncio.run(openodia.translate_batch(["a"], concurrency=1, retries=0, backoff=0)) == ["a:or>en"]
    assert asyncio.run(openodia.translate_batch(["b"], backoff=1)) == ["b:or>en"]


@pytest.mark.parametrize("value", ["abc", b"abc", bytearray(b"abc"), memoryview(b"abc")])
def test_a_bare_string_is_rejected_instead_of_being_split_into_characters(value: object) -> None:
    with pytest.raises(TypeError, match="texts must be a list of strings, not a single str or bytes"):
        asyncio.run(openodia.translate_batch(anything(value)))


def test_bad_options_are_rejected_before_any_work_even_for_an_empty_batch() -> None:
    with pytest.raises(ValueError, match="concurrency"):
        asyncio.run(openodia.translate_batch([], concurrency=0))


def test_return_exceptions_is_typed_so_callers_get_strings_by_default() -> None:
    hints = typing.get_overloads(openodia.translate_batch)
    returns = {inspect.signature(fn).return_annotation for fn in hints}
    assert returns == {"list[str]", "list[str | BaseException]"}


def test_a_generator_is_translated_and_not_silently_emptied(service: FakeService) -> None:
    assert asyncio.run(openodia.translate_batch(text for text in ["a", "b", "a"])) == ["a:or>en", "b:or>en", "a:or>en"]
    assert sorted(call[0] for call in service.calls) == ["a", "b"]


@pytest.mark.parametrize("texts", [iter(["a", "b"]), ("a", "b"), {"a": 1, "b": 2}.keys()])
def test_any_iterable_of_strings_is_accepted(service: FakeService, texts: typing.Iterable[str]) -> None:
    assert asyncio.run(openodia.translate_batch(texts)) == ["a:or>en", "b:or>en"]


@pytest.mark.parametrize(
    ("bad", "type_name"), [(None, "NoneType"), (1, "int"), (b"a", "bytes"), (["a"], "list"), (1.5, "float")]
)
def test_non_string_items_are_rejected_before_any_work(service: FakeService, bad: object, type_name: str) -> None:
    with pytest.raises(TypeError, match=rf"texts must contain only strings, got {type_name} at index 1$"):
        asyncio.run(openodia.translate_batch(["a", anything(bad), "c"]))
    assert service.calls == []


def test_the_item_error_names_the_type_and_does_not_echo_the_value(service: FakeService) -> None:
    with pytest.raises(TypeError) as caught:
        asyncio.run(openodia.translate_batch(["a", anything(b"secret")]))
    assert str(caught.value) == "texts must contain only strings, got bytes at index 1"


def test_a_non_iterable_is_a_type_error(service: FakeService) -> None:
    with pytest.raises(TypeError):
        asyncio.run(openodia.translate_batch(anything(5)))
