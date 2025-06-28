"""
This provides a dictionary with English text on key and Odia text as value
@author: Soumendra Kumar Sahoo
@license: MIT
"""

import json
import os
from typing import Dict
from functools import lru_cache

from openodia.common.utility import LOGGER


@lru_cache(maxsize=1)
def get_dictionary() -> Dict[str, str]:
    """Return the offline dictionary.

    The dictionary file is quite large and reading it multiple times slows down
    the translation utilities.  Cache the loaded content so subsequent calls are
    served from memory.
    """
    dict_file = os.path.join(os.path.dirname(__file__), "En-Or_word_pairs_v3.json")
    LOGGER.debug(f"Getting offline dictionary data from: {dict_file}")
    with open(dict_file, mode="rt", encoding="utf-8") as dh:
        return json.load(dh)
