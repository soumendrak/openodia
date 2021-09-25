#!/usr/local/bin/python
# -*- coding: utf-8 -*-
"""
This module is regarding automatic text summarization
Date: 25 Sep 2021
Author: Soumendra Kumar Sahoo
Reference: Automatic Text Summarization for Oriya language by Sujata Dash et al
"""
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import List

from openodia._understandData import UnderstandData as ud
from openodia.common.utility import LOGGER


@dataclass
class SummarizationBaseMethod(ABC):
    text: str = ""
    token_list: List[str] = field(default_factory=list)
    sentence_list: List[str] = field(default_factory=list)

    def get_tokens(self) -> None:
        """Get tokens from the text of the entire webpage"""
        self.token_list = ud.word_tokenizer(self.text)

    def get_sentences(self):
        """Get ordered sentences list from the text of the entire webpage"""
        self.sentence_list = ud.sentence_tokenizer(self.text)

    def remove_stopwords(self):
        """Remove stopwords from the provided token list"""
        self.token_list = ud.remove_stopwords(self.token_list)

    def _number_of_words_in_text(self) -> int:
        """Count the number of words in the provided"""
        return len(self.token_list)

    def _number_of_unique_words_in_text(self) -> int:
        """Count the number of UNIQUE words in the provided text"""
        return len(set(self.token_list))

    def _get_threshold_value(self) -> float:
        """Get the threshold value
        It is calculated as
        number_of_words_in_text / number_of_unique_words_in_text
        Therefore, it will be always be greater than 1.0
        """
        return self._number_of_words_in_text() / self._number_of_unique_words_in_text()

    def words_having_higher_threshold(self, threshold_value: float = 1.0) -> set[str]:
        """Get the list of tokens having higher threshold value
        That means the words which are significant for the given text
        """
        threshold_value = threshold_value or self._get_threshold_value()
        LOGGER.debug(f"{threshold_value=}")
        token_ctr = Counter(self.token_list)
        LOGGER.debug(f"{token_ctr=}")
        frequent_token_set = set(
            [word for word in self.token_list if token_ctr[word] > threshold_value]
        )
        return frequent_token_set

    def get_sentence_having_frequent_words(self, frequent_token_list: set[str]) -> str:
        """Get the sentences having the frequent words"""
        summarized_text = []
        for sentence in self.sentence_list:
            for token in frequent_token_list:
                if token in sentence:
                    summarized_text.append(sentence)
                    break
        LOGGER.debug(f"{len(summarized_text)} number of sentences found in summarized text.")
        summarized_text = " ".join(summarized_text)
        return summarized_text

    @abstractmethod
    def get_summary(self) -> str:
        """Main orchestrator"""
        raise NotImplementedError


@dataclass
class WordFrequency(SummarizationBaseMethod, ABC):
    """Get summarized text based on word frequency method"""

    def get_summary(self, threshold: float = None) -> str:
        """Main function to orchestrate the summarization
        :param threshold: The more the value the lesser the summary text
        """
        self.get_tokens()
        LOGGER.debug(f"{len(self.token_list)} number of tokens found.")
        LOGGER.debug(f"{self.token_list=}")
        self.get_sentences()
        LOGGER.debug(f"{len(self.sentence_list)} number of sentences found.")
        self.remove_stopwords()
        LOGGER.debug("stopwords removed")
        frequent_token_list = self.words_having_higher_threshold(threshold)
        LOGGER.debug(f"{len(frequent_token_list)} number of frequent tokens found.")
        LOGGER.debug(f"{frequent_token_list=}")
        summary = self.get_sentence_having_frequent_words(frequent_token_list)
        LOGGER.debug(f"{summary=}")
        return summary
