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
genitive ର, except when the remainder would end in ା, so ବିଚାର stays
ବିଚାର, or would be one akshara without candrabindu, so ଫେର stays ଫେର
while ଗାଁର is ଗାଁ plus ର. Short verbal tails (େ, ଇ, ବା) apply only to
listed roots. Longer verbal tails apply to any well-formed remainder.
A bare ଥିଲା / ଥିଲେ after a conjunctive is perfect, and ିଁଥିଲା / ୁଁଥିଲା
keep the root, so ଚାହିଁଥିଲା is ଚାହ. An infinitive the dictionary does not
list is the root plus ିବା after a consonant, ବା after େ (ଦେବା), and ଇବା
after any other vowel sign (ଖାଇବା, ପିଇବା, ଶୁଇବା, ଧୋଇବା). A finite ହୋ form
(ହୋଇଥିଲା) is the verb ହେ, with infinitive ହେବା. Suppletive pasts (କଲା,
ଗଲା, ଦେଲା, ନେଲା, ହେଲା, ଥିଲା), the infinitives ଯିବା, ଥିବା and ଚାହିଁବା,
and the future forms ଯିବ, ଯିବି, ଯିବେ, ଥିବ, ଥିବି and ଥିବେ
are a dictionary, not a cut. Nasalized present-progressive endings
ୁଁଛି, ୁଁଛୁ and ୁଁଛନ୍ତି keep the root, so ଚାହୁଁଛି is ଚାହ.

Each string has one reading. ଲେ and ଥିଲେ are stored as third person plural,
which is also the polite form. କୁ is dative and also the accusative marker;
the ending does not distinguish them.

The ending list follows Neukom and Patnaik 2003, A Grammar of Oriya;
Mohapatra 1997 on number and case; Jena and Rautaray 2020 (IJITEE nominal
and verbal tables); Sethi 2013, the lightweight Odia stemmer; and
Chaupattnaik, Nanda and Mohanty 2012, the suffix-stripping Odia stemmer.
``suffixes()`` is that list. A perfect ``ଇଥିଲା`` / ``ଇଛି`` ending keeps the
conjunctive vowel with the suffix, so the stem is the root. Genitive ``ର``
is stripped only when at least two aksharas remain and the remainder is
not an unlisted stem ending in ``ା``.

Endings:

ର (nominal): ର
କୁ (nominal): କୁ
ରେ (nominal): ରେ, େ
ରୁ (nominal): ରୁ
ଠାରୁ (nominal): ଠାରୁ
ଠୁ (nominal): ଠୁ
ଠାରେ (nominal): ଠାରେ
ଦ୍ୱାରା (nominal): ଦ୍ୱାରା
ଦେଇ (nominal): ଦେଇ
ଟି (nominal): ଟି
ଟା (nominal): ଟା
ଟେ (nominal): ଟେ
ଟିଏ (nominal): ଟିଏ
ମାନେ (nominal): ମାନେ
ମାନଙ୍କ (nominal): ମାନଙ୍କ
ଗୁଡ଼ିକ (nominal): ଗୁଡ଼ିକ
ଗୁଡ଼ା (nominal): ଗୁଡ଼ା
ଗୁଡ଼ାକ (nominal): ଗୁଡ଼ାକ
ଗୁଡ଼ିଏ (nominal): ଗୁଡ଼ିଏ
ଙ୍କ (nominal): ଙ୍କ
େ (nominal): େ
ମାନଙ୍କୁ (nominal): ମାନଙ୍କୁ
ଙ୍କୁ (nominal): ଙ୍କୁ
ଗୁଡ଼ିକୁ (nominal): ଗୁଡ଼ିକୁ
ଉଥିଲେ (verbal): ୁଁଥିଲେ, ୁଥିଲେ, ଉଥିଲେ
ଉଥିଲା (verbal): ୁଁଥିଲା, ୁଥିଲା, ଉଥିଲା
ଉଥିଲି (verbal): ୁଥିଲି, ଉଥିଲି
ଉଛି (verbal): ୁଁଛି, ୁଛି, ଉଛି
ଉଛୁ (verbal): ୁଁଛୁ, ୁଛୁ, ଉଛୁ
ଉଛନ୍ତି (verbal): ୁଁଛନ୍ତି, ୁଛନ୍ତି, ଉଛନ୍ତି
ଇଛି (verbal): ିଛି, ଇଛି
ଇଲା (verbal): ିଲା, ଇଲା
ଇଲେ (verbal): ିଲେ, ଇଲେ
ଇଲି (verbal): ିଲି, ଇଲି
ଇବ (verbal): ିବ, ଇବ, ବ
ଇବି (verbal): ିବି, ଇବି, ବି
ଇବେ (verbal): ିବେ, ଇବେ, ବେ
ଥାଏ (verbal): ିଥାଏ, ଥାଏ
ଇଥିଲେ (verbal): ିଁଥିଲେ, ିଥିଲେ, ଇଥିଲେ, ଥିଲେ
ଇଥିଲା (verbal): ିଁଥିଲା, ିଥିଲା, ଇଥିଲା, ଥିଲା
ଇଛନ୍ତି (verbal): ିଛନ୍ତି, ଇଛନ୍ତି
ନ୍ତି (verbal): ନ୍ତି
ଏ (verbal): େ, ଏ
ଇବା (verbal): ିବା, ଇବା, ବା
ଇ (verbal): ି, ଇ
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
