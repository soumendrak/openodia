"""Lookup tables for Odia number words.

The 0..99 list below is the package's single source of truth for irregular
Odia counts. Any correction by a native-speaker reviewer should land here
and be reflected in :func:`openodia.numbers.to_words` automatically.
"""

from __future__ import annotations

# Numbers 0..99 in their standard Odia forms.
# Index N is the word for the integer N.
UNDER_HUNDRED: tuple[str, ...] = (
    "ଶୂନ୍ୟ",  # 0
    "ଏକ",  # 1
    "ଦୁଇ",  # 2
    "ତିନି",  # 3
    "ଚାରି",  # 4
    "ପାଞ୍ଚ",  # 5
    "ଛଅ",  # 6
    "ସାତ",  # 7
    "ଆଠ",  # 8
    "ନଅ",  # 9
    "ଦଶ",  # 10
    "ଏଗାର",  # 11
    "ବାର",  # 12
    "ତେର",  # 13
    "ଚଉଦ",  # 14
    "ପନ୍ଦର",  # 15
    "ଷୋହଳ",  # 16
    "ସତର",  # 17
    "ଅଠର",  # 18
    "ଊଣେଇଶ",  # 19
    "କୋଡ଼ିଏ",  # 20
    "ଏକୋଇଶ",  # 21
    "ବାଇଶ",  # 22
    "ତେଇଶ",  # 23
    "ଚବିଶ",  # 24
    "ପଚିଶ",  # 25
    "ଛବିଶ",  # 26
    "ସତାଇଶ",  # 27
    "ଅଠାଇଶ",  # 28
    "ଅଣତିରିଶ",  # 29
    "ତିରିଶ",  # 30
    "ଏକତିରିଶ",  # 31
    "ବତିଶ",  # 32
    "ତେତିଶ",  # 33
    "ଚଉତିରିଶ",  # 34
    "ପଇଁତିରିଶ",  # 35
    "ଛତିଶ",  # 36
    "ସଇଁତିରିଶ",  # 37
    "ଅଠତିରିଶ",  # 38
    "ଅଣଚାଳିଶ",  # 39
    "ଚାଳିଶ",  # 40
    "ଏକଚାଳିଶ",  # 41
    "ବୟାଳିଶ",  # 42
    "ତେୟାଳିଶ",  # 43
    "ଚଉରାଳିଶ",  # 44
    "ପଞ୍ଚଚାଳିଶ",  # 45
    "ଛୟାଳିଶ",  # 46
    "ସତଚାଳିଶ",  # 47
    "ଅଠଚାଳିଶ",  # 48
    "ଅଣଚାଶ",  # 49
    "ପଚାଶ",  # 50
    "ଏକାବନ",  # 51
    "ବାବନ",  # 52
    "ତେପନ",  # 53
    "ଚଉପନ",  # 54
    "ପଞ୍ଚାବନ",  # 55
    "ଛପନ",  # 56
    "ସତାବନ",  # 57
    "ଅଠାବନ",  # 58
    "ଅଣଷଠି",  # 59
    "ଷାଠିଏ",  # 60
    "ଏକଷଠି",  # 61
    "ବାଷଠି",  # 62
    "ତେଷଠି",  # 63
    "ଚଉଷଠି",  # 64
    "ପଞ୍ଚଷଠି",  # 65
    "ଛଅଷଠି",  # 66
    "ସତଷଠି",  # 67
    "ଅଠଷଠି",  # 68
    "ଅଣସତୁରୀ",  # 69
    "ସତୁରୀ",  # 70
    "ଏକସତୁରୀ",  # 71
    "ବାସତୁରୀ",  # 72
    "ତେସତୁରୀ",  # 73
    "ଚଉସତୁରୀ",  # 74
    "ପଞ୍ଚସତୁରୀ",  # 75
    "ଛଅସତୁରୀ",  # 76
    "ସତସତୁରୀ",  # 77
    "ଅଠସତୁରୀ",  # 78
    "ଅଣାଅଶି",  # 79
    "ଅଶୀ",  # 80
    "ଏକାଅଶି",  # 81
    "ବାଆଶି",  # 82
    "ତିରାଅଶି",  # 83
    "ଚଉରାଅଶି",  # 84
    "ପଞ୍ଚାଅଶି",  # 85
    "ଛଅଆଶି",  # 86
    "ସତାଅଶି",  # 87
    "ଅଠାଅଶି",  # 88
    "ଅଣେଇଶ",  # 89
    "ନବେ",  # 90
    "ଏକାନବେ",  # 91
    "ବାନେ",  # 92
    "ତିରାନେ",  # 93
    "ଚଉରାନେ",  # 94
    "ପଞ୍ଚାନେ",  # 95
    "ଛଅନେ",  # 96
    "ସତାନେ",  # 97
    "ଅଠାନେ",  # 98
    "ଅନେଶ",  # 99
)

# Place-value multipliers in increasing order. Used by the composition
# algorithm: walk multipliers high → low, divmod at each step.
INDIAN_MULTIPLIERS: tuple[tuple[int, str], ...] = (
    (10**7, "କୋଟି"),  # crore
    (10**5, "ଲକ୍ଷ"),  # lakh
    (1_000, "ହଜାର"),  # thousand
    (100, "ଶହ"),  # hundred
)

SHORT_MULTIPLIERS: tuple[tuple[int, str], ...] = (
    (10**12, "ଟ୍ରିଲିୟନ"),  # trillion
    (10**9, "ବିଲିୟନ"),  # billion
    (10**6, "ମିଲିୟନ"),  # million
    (1_000, "ହଜାର"),  # thousand
    (100, "ଶହ"),  # hundred
)

# Irregular ordinals (1st..10th); higher ordinals are formed by suffixing
# ``ତମ`` to the cardinal form.
ORDINALS_IRREGULAR: dict[int, str] = {
    1: "ପ୍ରଥମ",
    2: "ଦ୍ୱିତୀୟ",
    3: "ତୃତୀୟ",
    4: "ଚତୁର୍ଥ",
    5: "ପଞ୍ଚମ",
    6: "ଷଷ୍ଠ",
    7: "ସପ୍ତମ",
    8: "ଅଷ୍ଟମ",
    9: "ନବମ",
    10: "ଦଶମ",
}
ORDINAL_SUFFIX: str = "ତମ"

# Words used in compound output.
NEGATIVE_WORD: str = "ଋଣାତ୍ମକ"

# Currency vocabulary.
CURRENCY_RUPEE: str = "ଟଙ୍କା"
CURRENCY_PAISA: str = "ପଇସା"

# Month names — Gregorian, transliterated. Keep simple.
GREGORIAN_MONTHS: tuple[str, ...] = (
    "ଜାନୁଆରୀ",
    "ଫେବ୍ରୁଆରୀ",
    "ମାର୍ଚ୍ଚ",
    "ଏପ୍ରିଲ",
    "ମଇ",
    "ଜୁନ",
    "ଜୁଲାଇ",
    "ଅଗଷ୍ଟ",
    "ସେପ୍ଟେମ୍ବର",
    "ଅକ୍ଟୋବର",
    "ନଭେମ୍ବର",
    "ଡିସେମ୍ବର",
)
