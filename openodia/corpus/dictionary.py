"""
This provides a dictionary with English text on key and Odia text as value
@author: Soumendra Kumar Sahoo
@license: MIT
"""
import json
from typing import Dict


def get_dictionary() -> Dict[str, str]:
    with open("openodia/corpus/En-Or_word_pairs_v2.json", encoding="utf8") as dh:
        dictionary_data = json.load(dh)
        return dictionary_data
