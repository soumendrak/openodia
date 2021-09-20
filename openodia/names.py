from random import shuffle
from typing import List

from faker import Faker

from openodia.constants import (
    PREFIXES,
    FIRST_NAMES_MALE,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_UNISEX,
    FIRST_NAMES,
    MIDDLE_NAMES,
    LAST_NAMES,
)


class Names:
    """Names in Odia"""

    @classmethod
    def generate_prefixes(cls, count: int = 10) -> List[str]:
        """Generate prefixes
        :param count: number of prefixes to generate
        """
        shuffle(PREFIXES)
        return PREFIXES[:count]

    @classmethod
    def generate_names(cls, count: int = 10) -> List[str]:
        """Generate Odia names
        :param count: number of names to generate
        """
        fake = Faker("or_IN")
        name_list = [fake.name() for _ in range(count)]
        return name_list

    @classmethod
    def generate_firstnames(cls, count: int = 10, type: str = "") -> List[str]:
        """Generate first names
        :param count: number of names to generate
        :param type: types of name to give
        """
        valid_types = ("female", "male", "unisex")
        if type.lower() == "male":
            shuffle(FIRST_NAMES_MALE)
            return FIRST_NAMES_MALE[:count]
        elif type.lower() == "female":
            shuffle(FIRST_NAMES_FEMALE)
            return FIRST_NAMES_FEMALE[:count]
        elif type.lower() == "unisex":
            shuffle(FIRST_NAMES_UNISEX)
            return FIRST_NAMES_UNISEX[:count]
        elif len(type) > 0:
            print(f"Invalid {type=} provided.\n Please provide one of these {valid_types=}")
        else:
            # send mix of all first names
            shuffle(FIRST_NAMES)
            return FIRST_NAMES[:count]

    @classmethod
    def generate_middlenames(cls, count: int = 10) -> List[str]:
        """Generate middle names
        :param count: number of middle names to generate
        """
        shuffle(MIDDLE_NAMES)
        return MIDDLE_NAMES[:count]

    @classmethod
    def generate_surnames(cls, count: int = 10) -> List[str]:
        """Generate surnames
        :param count: number of surnames to generate
        """
        shuffle(LAST_NAMES)
        return LAST_NAMES[:count]
