"""
This provides a dictionary with English text on key and Odia text as value
@author: Soumendra Kumar Sahoo
@license: MIT
"""
import json
from typing import Dict


def get_dictionary(
    file_location: str = "openodia/corpus/En-Or_word_pairs_v2.json",
) -> Dict[str, str]:
    with open(file_location) as dh:
        dictionary_data = json.load(dh)
        return dictionary_data
