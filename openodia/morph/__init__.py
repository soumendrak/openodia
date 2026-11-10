"""Odia stemmer and lemmatizer.

``stem`` strips inflection to a noun stem or a verb root.
``lemma`` returns the citation form (noun stem, verb infinitive) and the
features of that one reading. Both NFC the word and leave an empty string
empty. They do not tokenize.

A verb stem is the root (ଆସ), not the infinitive (ଆସିବା). Finite endings are
one fusional tail. Noun plural and case peel from the right, so ଗୁଡ଼ିକର is
ଗୁଡ଼ିକ plus genitive ର. Locative ଘରେ keeps the stem-final ର and takes the
matra େ; that reading is used only for a listed consonant-final noun, which
is why ମନ୍ଦିରେ stays ମନ୍ଦିର and କରେ stays the verb କର. Listed nouns that end in
ର, such as ସରକାର, are not genitives. Unlisted nouns still lose a plain
genitive ର. Short verbal tails (େ, ଇ, ବା) apply only to listed roots. Longer
verbal tails apply to any well-formed remainder. Suppletive pasts (କଲା,
ଗଲା, ଦେଲା, ନେଲା, ହେଲା, ଥିଲା) and the vowel-changing infinitives ଯିବା and
ଥିବା are a dictionary, not a cut.

Each string has one reading. ଲେ and ଥିଲେ are stored as third person plural,
which is also the polite form. କୁ is dative and also the accusative marker;
the ending does not distinguish them.

The ending list follows Neukom and Patnaik 2003, A Grammar of Oriya;
Mohapatra 1997 on number and case; Jena and Rautaray 2020 (IJITEE nominal
and verbal tables); Sethi 2013, the lightweight Odia stemmer; and
Chaupattnaik, Nanda and Mohanty 2012, the suffix-stripping Odia stemmer.
``suffixes()`` is that list.
"""

from openodia.morph._engine import (
    FiniteVerb,
    Lemma,
    NonfiniteVerb,
    NounFeatures,
    Suffix,
    UnknownFeatures,
    lemma,
    stem,
    suffixes,
)

__all__ = [
    "FiniteVerb",
    "Lemma",
    "NonfiniteVerb",
    "NounFeatures",
    "Suffix",
    "UnknownFeatures",
    "lemma",
    "stem",
    "suffixes",
]


def _ending_catalog() -> str:
    lines = [f"{item.citation} ({item.kind}): {', '.join(item.tails)}" for item in suffixes()]
    return "Endings:\n\n" + "\n".join(lines)


__doc__ = (__doc__ or "") + "\n\n" + _ending_catalog() + "\n"
