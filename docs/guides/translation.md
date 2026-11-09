# Translation and cache

Translate between Odia and other languages. English to Odia tries a bundled offline dictionary first and only then calls Google Translate. Results that come from Google are kept in a cache.

Examples that need the network have no output shown and are not run by the test suite, because Google can rate limit or change its answers. Everything else on this page is run by the suite.

## Functions

| Function | Direction | Default |
| --- | --- | --- |
| `other_lang_to_odia(text, source_language_code="en")` | any language to Odia | English source |
| `odia_to_other_lang(text, dest_language_code="en")` | Odia to any language | English target |
| `universal_translation(text, source_language_code="en", dest_language_code="or")` | any to any | English to Odia |

Language codes are the ones Google Translate uses, for example `hi`, `de`, `or`.

```python
from openodia import other_lang_to_odia, odia_to_other_lang, universal_translation

other_lang_to_odia("शेयर बाज़ार", source_language_code="hi")
odia_to_other_lang("ନମସ୍କାର", dest_language_code="de")
universal_translation("Guten Morgen", source_language_code="de", dest_language_code="en")
```

## The offline dictionary

When the source is `"en"`, `other_lang_to_odia` looks the text up in an English to Odia dictionary that ships with the package. The lookup is case-insensitive and needs no network.

```pycon
>>> from openodia import other_lang_to_odia
>>> other_lang_to_odia("good morning")
'ଶୁଭ ସକାଳ'
>>> other_lang_to_odia("Good Morning")
'ଶୁଭ ସକାଳ'
>>> from openodia.corpus.dictionary import get_dictionary
>>> dictionary = get_dictionary()
>>> len(dictionary) > 100_000
True
>>> dictionary["a bad apple"]
'ଏକ ଖରାପ ଆପଲ୍'
```

The dictionary is loaded once per process, so the first call pays for reading the JSON file and later calls reuse it.

!!! note "Gotchas"
    - The key is lowercased but not stripped. `"good morning "` with a trailing space misses the dictionary and goes to Google.
    - A non-English source never uses the dictionary, even for a word that is in it.
    - `odia_to_other_lang` and `universal_translation` always go to Google, never to the dictionary.

## The translation cache

Every Google answer is stored under the key `(text, source_code, destination_code)` in an in-memory LRU cache of 10,000 entries. `cache.stats()` reports hits, misses and sizes, and the same call repeated later is served from memory.

You can seed the cache yourself, which is also how to see a hit without the network:

```pycon
>>> from openodia import cache, odia_to_other_lang
>>> cache.clear()
>>> cache.get_cache().set(("ନମସ୍କାର", "or", "en"), "Hello")
>>> odia_to_other_lang("ନମସ୍କାର")
'Hello'
>>> cache.stats()
{'hits': 1, 'misses': 0, 'size': 1, 'max_size': 10000, 'disk_size': 0}
```

`cache.get_cache().get(key)` returns `None` on a miss and counts it:

```pycon
>>> cache.get_cache().get(("ଅଜଣା", "or", "en")) is None
True
>>> cache.stats()["misses"]
1
```

### Size and eviction

`cache.configure(max_size=n)` sets the capacity. The least recently used entry is evicted first, and reading an entry makes it the most recent.

```pycon
>>> _ = cache.configure(max_size=2)
>>> c = cache.get_cache()
>>> c.set("a", "1"); c.set("b", "2"); c.set("c", "3")
>>> c.get("a") is None, c.get("c")
(True, '3')
>>> cache.stats()["size"]
2
>>> cache.configure(max_size=0)
Traceback (most recent call last):
  ...
ValueError: max_size must be >= 1, got 0
```

!!! note "Gotcha: `configure` starts a new cache"
    `configure` installs a fresh cache. Entries and hit counters from the old one are gone, and `disk_path` is dropped unless you pass it again.

### Persist across runs

Install the extra and give `configure` a directory:

```bash
pip install "openodia[cache]"
```

```python
from openodia import cache

cache.configure(max_size=50_000, disk_path="~/.cache/openodia/translate")
```

Reads check memory first, then disk. You can also set the defaults before the process starts with the environment variables `OPENODIA_CACHE_MAX_SIZE` and `OPENODIA_CACHE_DISK`. An invalid size raises `ValueError` the first time the cache is used.

## Next

- [Command-line interface](cli.md) for the `translate` command.
- [API reference: translation and cache](../api/translation.md) and [offline dictionary](../api/corpus.md).
