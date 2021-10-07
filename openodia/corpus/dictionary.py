"""
This provides a dictionary with English text on key and Odia text as value
@author: Soumendra Kumar Sahoo
@license: MIT
"""
import json
import os
from typing import Dict
from openodia.common.utility import LOGGER


def get_dictionary() -> Dict[str, str]:
    dict_file = os.path.join(os.path.dirname(__file__), "En-Or_word_pairs_v2.json")
    LOGGER.debug(f"Getting offline dictionary data from: {dict_file}")
    with open(dict_file, encoding="utf8") as dh:
        dictionary_data = json.load(dh)
        return dictionary_data
