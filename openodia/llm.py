"""
This module is for the upcoming LLM based features.
"""

import os
import litellm

class LLM:
    """
    This class provides access to Large Language Model (LLM) based features.
    It uses the litellm library to provide a consistent interface to various LLM providers.

    The model can be configured using the `OPENODIA_LLM_MODEL` environment variable.
    By default, it uses `gemini/gemini-pro`.

    API keys for the different services are expected to be in the environment.
    For example, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc.
    """
    def __init__(self):
        self.model = os.getenv("OPENODIA_LLM_MODEL", "gemini/gemini-pro")

    def _get_completion(self, messages):
        """
        A helper method to get a completion from the configured LLM.
        """
        return litellm.completion(model=self.model, messages=messages)

    def summarize(self, text: str) -> str:
        """
        Provides abstractive summarization for a given Odia text.

        This feature uses a transformer-based model to generate a concise,
        human-like summary of the input text.

        Args:
            text: The Odia text to be summarized.

        Returns:
            A string containing the abstractive summary.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes Odia text."},
            {"role": "user", "content": f"Please summarize the following Odia text:\n\n{text}"}
        ]
        response = self._get_completion(messages)
        return response.choices[0].message.content.strip()

    def named_entity_recognition(self, text: str) -> dict:
        """
        Performs Named Entity Recognition (NER) on a given Odia text.

        This feature will identify and categorize entities such as names of people,
        organizations, locations, dates, etc.

        Args:
            text: The Odia text to be analyzed.

        Returns:
            A dictionary containing the identified entities and their categories.
            Example: {"PERSON": ["ରାମ", "ସୀତା"], "LOCATION": ["ଅଯୋଧ୍ୟା"]}
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant that performs Named Entity Recognition on Odia text. Respond with a JSON object where keys are entity types (e.g., PERSON, LOCATION, ORGANIZATION) and values are lists of the identified entities."},
            {"role": "user", "content": f"Please perform Named Entity Recognition on the following Odia text:\n\n{text}"}
        ]
        response = self._get_completion(messages)
        try:
            import json
            return json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to decode the LLM response as JSON."}


    def sentiment_analysis(self, text: str) -> dict:
        """
        Analyzes the sentiment of a given Odia text.

        This feature will determine whether the sentiment of the text is positive,
        negative, or neutral.

        Args:
            text: The Odia text to be analyzed.

        Returns:
            A dictionary containing the sentiment classification and confidence score.
            Example: {"sentiment": "positive", "confidence": 0.95}
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant that performs sentiment analysis on Odia text. Respond with a JSON object containing the 'sentiment' (positive, negative, or neutral) and a 'confidence' score (0.0 to 1.0)."},
            {"role": "user", "content": f"Please perform sentiment analysis on the following Odia text:\n\n{text}"}
        ]
        response = self._get_completion(messages)
        try:
            import json
            return json.loads(response.choices[0].message.content.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to decode the LLM response as JSON."}
