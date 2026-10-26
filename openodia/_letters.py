"""Letters in Odia language
@author: Soumendra Kumar Sahoo
@date: 19-Sep-2021
"""

from string import punctuation


class Letters:
    """Letters in Odia language

    Exposed as ``openodia.alphabet``. Every attribute is a class-level
    constant, so no instance is needed.

    Attributes:
        all_letters: Every Odia letter, modifier, sign and digit, in code point order by group.
        vowels: Independent vowels.
        consonants: Consonants.
        matras: Dependent vowel signs, modifiers, nukta, halant and the Odia isshar sign.
        numbers: Odia digits ``୦`` to ``୯``.
        punctuations: ASCII punctuation characters plus the Odia full stop ``୲``.
    """

    all_letters = [
        "ଁ",
        "ଂ",
        "ଃ",
        "ଅ",
        "ଆ",
        "ଇ",
        "ଈ",
        "ଉ",
        "ଊ",
        "ଋ",
        "ଌ",
        "ଏ",
        "ଐ",
        "ଓ",
        "ଔ",
        "କ",
        "ଖ",
        "ଗ",
        "ଘ",
        "ଙ",
        "ଚ",
        "ଛ",
        "ଜ",
        "ଝ",
        "ଞ",
        "ଟ",
        "ଠ",
        "ଡ",
        "ଢ",
        "ଣ",
        "ତ",
        "ଥ",
        "ଦ",
        "ଧ",
        "ନ",
        "ପ",
        "ଫ",
        "ବ",
        "ଭ",
        "ମ",
        "ଯ",
        "ର",
        "ଲ",
        "ଳ",
        "ଵ",
        "ଶ",
        "ଷ",
        "ସ",
        "ହ",
        "଼",
        "ଽ",
        "ା",
        "ି",
        "ୀ",
        "ୁ",
        "ୂ",
        "ୃ",
        "ୄ",
        "େ",
        "ୈ",
        "ୋ",
        "ୌ",
        "୍",
        "ୖ",
        "ୗ",
        "ଡ଼",
        "ଢ଼",
        "ୟ",
        "ୠ",
        "ୡ",
        "ୢ",
        "ୣ",
        "୦",
        "୧",
        "୨",
        "୩",
        "୪",
        "୫",
        "୬",
        "୭",
        "୮",
        "୯",
        "୰",
        "ୱ",
        "୲",
    ]

    vowels = ["ଅ", "ଆ", "ଇ", "ଈ", "ଉ", "ଊ", "ଋ", "ଌ", "ଏ", "ଐ", "ଓ", "ଔ"]

    numbers = ["୦", "୧", "୨", "୩", "୪", "୫", "୬", "୭", "୮", "୯"]

    consonants = [
        "କ",
        "ଖ",
        "ଗ",
        "ଘ",
        "ଙ",
        "ଚ",
        "ଛ",
        "ଜ",
        "ଝ",
        "ଞ",
        "ଟ",
        "ଠ",
        "ଡ",
        "ଢ",
        "ଣ",
        "ତ",
        "ଥ",
        "ଦ",
        "ଧ",
        "ନ",
        "ପ",
        "ଫ",
        "ବ",
        "ଭ",
        "ମ",
        "ଯ",
        "ର",
        "ଲ",
        "ଳ",
        "ଵ",
        "ଶ",
        "ଷ",
        "ସ",
        "ହ",
    ]

    matras = [
        "ଁ",
        "ଂ",
        "ଃ",
        "଼",
        "ଽ",
        "ା",
        "ି",
        "ୀ",
        "ୁ",
        "ୂ",
        "ୃ",
        "ୄ",
        "େ",
        "ୈ",
        "ୋ",
        "ୌ",
        "୍",
        "ୖ",
        "ୗ",
        "୰",
        "ୱ",
        "୲",
    ]

    punctuations = tuple(f"{punctuation}୲")
