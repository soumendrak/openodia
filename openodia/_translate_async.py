"""Async translation over the existing synchronous Google path, with bounded concurrency."""

from __future__ import annotations

import asyncio
import math
import threading
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Literal, overload

from deep_translator.exceptions import TooManyRequests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from openodia._translate import odia_to_other_lang, other_lang_to_odia, universal_translation

_CONNECTION_ERRORS = (ConnectionError, TimeoutError, RequestsConnectionError, RequestsTimeout)


async def odia_to_other_lang_async(text: str, dest_language_code: str = "en") -> str:
    """Async :func:`openodia.odia_to_other_lang`; runs in a worker thread."""
    return await asyncio.to_thread(odia_to_other_lang, text, dest_language_code)


async def other_lang_to_odia_async(text: str, source_language_code: str = "en") -> str:
    """Async :func:`openodia.other_lang_to_odia`; runs in a worker thread."""
    return await asyncio.to_thread(other_lang_to_odia, text, source_language_code)


async def universal_translation_async(text: str, source_language_code: str = "en", dest_language_code: str = "or") -> str:
    """Async :func:`openodia.universal_translation`; runs in a worker thread."""
    return await asyncio.to_thread(universal_translation, text, source_language_code, dest_language_code)


def _translator_for(source: str, to: str) -> Callable[[str], str]:
    if source == "or":
        return partial(odia_to_other_lang, dest_language_code=to)
    if to == "or":
        return partial(other_lang_to_odia, source_language_code=source)
    return partial(universal_translation, source_language_code=source, dest_language_code=to)


def _is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int):
        return status == 429 or 500 <= status < 600
    return isinstance(exc, (TooManyRequests, *_CONNECTION_ERRORS))


def _unless_stopped(
    translate: Callable[[str], str], stopped: threading.Event, retries: int, return_exceptions: bool
) -> Callable[[str, int], str]:
    def run(text: str, attempt: int) -> str:
        if stopped.is_set():
            return ""
        try:
            return translate(text)
        except Exception as exc:
            if not return_exceptions and not (_is_retryable(exc) and attempt < retries):
                stopped.set()
            raise

    return run


def _validate_options(texts: object, concurrency: object, retries: object, backoff: object) -> None:
    if isinstance(texts, str | bytes):
        raise TypeError("texts must be a list of strings, not a single str or bytes; wrap it in a list")
    for name, value, minimum in (("concurrency", concurrency, 1), ("retries", retries, 0)):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}, got {value!r}")
    if isinstance(backoff, bool) or not isinstance(backoff, int | float) or not math.isfinite(backoff) or backoff < 0:
        raise ValueError(f"backoff must be a finite number >= 0, got {backoff!r}")


@overload
async def translate_batch(
    texts: Sequence[str],
    *,
    source: str = ...,
    to: str = ...,
    concurrency: int = ...,
    retries: int = ...,
    backoff: float = ...,
    return_exceptions: Literal[False] = ...,
) -> list[str]: ...


@overload
async def translate_batch(
    texts: Sequence[str],
    *,
    source: str = ...,
    to: str = ...,
    concurrency: int = ...,
    retries: int = ...,
    backoff: float = ...,
    return_exceptions: Literal[True],
) -> list[str | BaseException]: ...


async def translate_batch(
    texts: Sequence[str],
    *,
    source: str = "or",
    to: str = "en",
    concurrency: int = 8,
    retries: int = 0,
    backoff: float = 0.5,
    return_exceptions: bool = False,
) -> list[str] | list[str | BaseException]:
    """Translate ``texts`` concurrently and return the results in input order.

    Each distinct text is translated once, through the same path and cache as the sync functions:
    ``source="or"`` and ``to="or"`` behave like :func:`odia_to_other_lang` and
    :func:`other_lang_to_odia` (so English to Odia uses the offline dictionary first); any other pair
    behaves like :func:`universal_translation`.

    At most ``concurrency`` requests run at once, on a thread pool private to this call.
    A request is retried up to ``retries`` times, sleeping ``backoff * 2**attempt`` seconds between
    attempts, only when it fails with a rate limit (HTTP 429), an HTTP 5xx status, or a connection
    or timeout error. Anything else is raised at once: other statuses, ``OSError`` subclasses such as
    ``PermissionError``, and errors such as an unsupported language code. deep-translator reports a
    failed HTTP response as a ``RequestError`` that carries no status, so that error is not retried;
    only exceptions that expose ``status_code`` (or ``response.status_code``) can count as 5xx.

    Texts of 5000 characters or more raise ``NotValidLength``, which aborts the whole batch unless
    ``return_exceptions=True``. Identical texts are translated once per call, not across calls; the
    shared cache covers repeats across calls.

    By default the first failure is raised, texts not yet started are skipped, and requests already
    running finish in the background. With ``return_exceptions=True`` every text gets an entry, either
    its translation or the exception it failed with. Cancelling the call stops queued texts the same
    way. A translation is cached only once it has succeeded, so neither case leaves a partial entry.

    Raises:
        TypeError: If ``texts`` is a single ``str`` or ``bytes``.
        ValueError: If ``concurrency`` is not an integer >= 1, ``retries`` is not an integer >= 0, or
            ``backoff`` is not a finite number >= 0.
    """
    _validate_options(texts, concurrency, retries, backoff)
    distinct = list(dict.fromkeys(texts))
    if not distinct:
        return []
    translate = _translator_for(source, to)
    loop = asyncio.get_running_loop()
    pool = ThreadPoolExecutor(max_workers=min(concurrency, len(distinct)))
    stopped = threading.Event()
    run_unless_stopped = _unless_stopped(translate, stopped, retries, return_exceptions)

    async def translate_with_retries(text: str) -> str:
        attempt = 0
        while True:
            try:
                return await loop.run_in_executor(pool, run_unless_stopped, text, attempt)
            except Exception as exc:
                if not _is_retryable(exc):
                    raise
                if attempt == retries:
                    raise
                await asyncio.sleep(backoff * 2**attempt)
                attempt += 1

    tasks = [asyncio.ensure_future(translate_with_retries(text)) for text in distinct]
    try:
        outcomes = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    finally:
        stopped.set()
        for task in tasks:
            task.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
    by_text = dict(zip(distinct, outcomes, strict=True))
    return [by_text[text] for text in texts]
