"""Async translation over the existing synchronous Google path, with bounded concurrency."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from deep_translator.exceptions import RequestError, TooManyRequests

from openodia._translate import odia_to_other_lang, other_lang_to_odia, universal_translation

_TRANSIENT_ERRORS = (TooManyRequests, RequestError, OSError)


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


def _require(name: str, value: float, minimum: float) -> None:
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


async def translate_batch(
    texts: Sequence[str],
    *,
    source: str = "or",
    to: str = "en",
    concurrency: int = 8,
    retries: int = 0,
    backoff: float = 0.5,
    return_exceptions: bool = False,
) -> list[str | BaseException]:
    """Translate ``texts`` concurrently and return the results in input order.

    Each distinct text is translated once, through the same path and cache as the sync functions:
    ``source="or"`` and ``to="or"`` behave like :func:`odia_to_other_lang` and
    :func:`other_lang_to_odia` (so English to Odia uses the offline dictionary first); any other pair
    behaves like :func:`universal_translation`.

    At most ``concurrency`` requests run at once, on a thread pool private to this call.
    A request that fails with a rate limit, a request error or a network error is retried up to
    ``retries`` times, sleeping ``backoff * 2**attempt`` seconds between attempts. Other errors,
    such as an unsupported language code, are never retried.

    By default the first failure is raised, queued texts are never started, and requests already
    running finish in the background. With ``return_exceptions=True`` every text gets an entry, either
    its translation or the exception it failed with. Cancelling the call stops queued texts the same
    way. A translation is cached only once it has succeeded, so neither case leaves a partial entry.

    Raises:
        ValueError: If ``concurrency`` < 1, ``retries`` < 0 or ``backoff`` < 0.
    """
    _require("concurrency", concurrency, 1)
    _require("retries", retries, 0)
    _require("backoff", backoff, 0)
    distinct = list(dict.fromkeys(texts))
    if not distinct:
        return []
    translate = _translator_for(source, to)
    loop = asyncio.get_running_loop()
    pool = ThreadPoolExecutor(max_workers=min(concurrency, len(distinct)))

    async def translate_with_retries(text: str) -> str:
        attempt = 0
        while True:
            try:
                return await loop.run_in_executor(pool, translate, text)
            except _TRANSIENT_ERRORS:
                if attempt == retries:
                    raise
                await asyncio.sleep(backoff * 2**attempt)
                attempt += 1

    tasks = [asyncio.ensure_future(translate_with_retries(text)) for text in distinct]
    try:
        outcomes = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    finally:
        for task in tasks:
            task.cancel()
        pool.shutdown(wait=False, cancel_futures=True)
    by_text = dict(zip(distinct, outcomes, strict=True))
    return [by_text[text] for text in texts]
