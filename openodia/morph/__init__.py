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
genitive ର, except when the remainder would end in ା and is neither a peeled nominal nor an infinitive, so ବିଚାର stays
ବିଚାର while ଘରଟାର is ଘର plus definite genitive and କରିବାର is the infinitive କରିବା, or would be one akshara without candrabindu, so ଫେର stays ଫେର
while ଗାଁର is ଗାଁ plus ର. Short verbal tails (େ, ଇ, ବା) apply only to
listed roots. Longer verbal tails apply to any well-formed remainder.
A bare ଥିଲା / ଥିଲେ after a conjunctive is perfect. A negative perfect (କରିନଥିଲେ) is the
same perfect reading with the root କର; the features do not mark negation. An infinitive the dictionary does not
list is the root plus ିବା after a consonant, ବା after the listed େ roots
(ଦେବା, ନେବା, ହେବା), and ଇବା after any other vowel sign (ଖାଇବା, ପିଇବା,
ଶୁଇବା, ଧୋଇବା, ବାଡ଼େଇବା). A finite ହୋ form
(ହୋଇଥିଲା) and the conjunctive ହୋଇ are the verb ହେ, with infinitive ହେବା. Suppletive pasts (କଲା,
ଗଲା, ଦେଲା, ନେଲା, ହେଲା, ଥିଲା, with first person ଲି and ଲୁ such as ଦେଲି and ଥିଲୁ), the infinitives ଯିବା, ଥିବା and ଚାହିଁବା,
the future forms ଯିବ, ଯିବି, ଯିବେ, ଥିବ, ଥିବି and ଥିବେ, and the presents
ଦିଏ, ଦିଅନ୍ତି, ନିଏ, ନିଅନ୍ତି, ହୁଏ, ହୁଅନ୍ତି and ଚାହାନ୍ତି are a dictionary, not a cut.
A vowel-final root takes present plural ଆନ୍ତି (ଖାଆନ୍ତି is ଖା, ଧୋଆନ୍ତି is ଧୋ).
ଚାହ has the nasal stem ଚାହିଁ-: a candrabindu right after the vowel sign
that follows ଚାହ belongs to the stem, so every ending reads the same with
it (ଚାହିଁବି, ଚାହିଁଲା, ଚାହୁଁଛି, ଚାହିଁଛନ୍ତି, ଚାହେଁ and ଚାହିଁ are all ଚାହ).

Each string has one reading. ଲେ and ଥିଲେ are stored as third person plural,
which is also the polite form. କୁ is dative and also the accusative marker;
the ending does not distinguish them.

The ending list follows Neukom and Patnaik 2003, A Grammar of Oriya;
Mohapatra 1997 on number and case; Jena and Rautaray 2020 (IJITEE nominal
and verbal tables); Sethi 2013, the lightweight Odia stemmer; and
Chaupattnaik, Nanda and Mohanty 2012, the suffix-stripping Odia stemmer.
``suffixes()`` is that list. A perfect ``ଇଥିଲା`` / ``ଇଛି`` ending keeps the
conjunctive vowel with the suffix, so the stem is the root. Genitive ``ର``
is stripped only when the remainder has at least two aksharas or ends in
candrabindu (ଗାଁର is ଗାଁ), and is not an unlisted stem ending in ``ା``
other than an infinitive.

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
ଉଥିଲେ (verbal): ୁଥିଲେ, ଉଥିଲେ
ଉଥିଲା (verbal): ୁଥିଲା, ଉଥିଲା
ଉଥିଲି (verbal): ୁଥିଲି, ଉଥିଲି
ଉଛି (verbal): ୁଛି, ଉଛି
ଉଛୁ (verbal): ୁଛୁ, ଉଛୁ
ଉଛନ୍ତି (verbal): ୁଛନ୍ତି, ଉଛନ୍ତି
ଇଛି (verbal): ିଛି, ଇଛି
ଇଲା (verbal): ିଲା, ଇଲା
ଇଲେ (verbal): ିଲେ, ଇଲେ
ଇଲି (verbal): ିଲି, ଇଲି
ଇବ (verbal): ିବ, ଇବ, ବ
ଇବି (verbal): ିବି, ଇବି, ବି
ଇବେ (verbal): ିବେ, ଇବେ, ବେ
ଥାଏ (verbal): ିଥାଏ, ଇଥାଏ, ଥାଏ
ଇଥିଲେ (verbal): ିନଥିଲେ, ଇନଥିଲେ, ିଥିଲେ, ଇଥିଲେ, ଥିଲେ
ଇଥିଲା (verbal): ିନଥିଲା, ଇନଥିଲା, ିଥିଲା, ଇଥିଲା, ଥିଲା
ଇଥିଲି (verbal): ିନଥିଲି, ଇନଥିଲି, ିଥିଲି, ଇଥିଲି, ଥିଲି
ଇଛନ୍ତି (verbal): ିଛନ୍ତି, ଇଛନ୍ତି
ନ୍ତି (verbal): ଆନ୍ତି, ନ୍ତି
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
