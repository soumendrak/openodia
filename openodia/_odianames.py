import random

from faker import Faker

from openodia.common.constants import (
    PREFIXES,
    FIRST_NAMES_MALE,
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_UNISEX,
    FIRST_NAMES,
    MIDDLE_NAMES,
    LAST_NAMES,
)
from openodia.common.utility import LOGGER


class Names:
    """Names in Odia"""

    @classmethod
    def generate_prefixes(cls, count: int = 10) -> list[str]:
        """Generate prefixes
        :param count: number of prefixes to generate
        """
        return random.sample(PREFIXES, min(count, len(PREFIXES)))

    @classmethod
    def generate_names(cls, count: int = 10) -> list[str]:
        """Generate Odia names
        :param count: number of names to generate
        """
        fake = Faker("or_IN")
        name_list = [fake.name() for _ in range(count)]
        LOGGER.debug(f"generated {len(name_list)} number of names.")
        return name_list

    @classmethod
    def generate_firstnames(cls, count: int = 10, name_type: str = "") -> list[str]:
        """Generate first names
        :param count: number of names to generate
        :param name_type: types of name to give
        """
        valid_types = ("female", "male", "unisex")
        if name_type.lower() == "male":
            return random.sample(FIRST_NAMES_MALE, min(count, len(FIRST_NAMES_MALE)))
        elif name_type.lower() == "female":
            return random.sample(FIRST_NAMES_FEMALE, min(count, len(FIRST_NAMES_FEMALE)))
        elif name_type.lower() == "unisex":
            return random.sample(FIRST_NAMES_UNISEX, min(count, len(FIRST_NAMES_UNISEX)))
        elif len(name_type) > 0:
            LOGGER.exception(f"Invalid {name_type=} provided.\n Please provide one of these {valid_types=}")
            raise ValueError("Invalid name_type provided")
        else:
            # send mix of all first names
            return random.sample(FIRST_NAMES, min(count, len(FIRST_NAMES)))

    @classmethod
    def generate_middlenames(cls, count: int = 10) -> list[str]:
        """Generate middle names
        :param count: number of middle names to generate
        """
        return random.sample(MIDDLE_NAMES, min(count, len(MIDDLE_NAMES)))

    @classmethod
    def generate_surnames(cls, count: int = 10) -> list[str]:
        """Generate surnames
        :param count: number of surnames to generate
        """
        return random.sample(LAST_NAMES, min(count, len(LAST_NAMES)))
