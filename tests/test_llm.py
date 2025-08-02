import unittest
from unittest.mock import patch, MagicMock
from openodia.llm import LLM

class TestLLM(unittest.TestCase):
    def setUp(self):
        self.llm = LLM()

    @patch('litellm.completion')
    def test_summarize(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "ଏହା ଏକ ସାରାଂଶ।"
        mock_completion.return_value = mock_response

        summary = self.llm.summarize("A long odia text.")
        self.assertEqual(summary, "ଏହା ଏକ ସାରାଂଶ।")
        mock_completion.assert_called_once()

    @patch('litellm.completion')
    def test_named_entity_recognition(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"PERSON": ["ରାମ", "ସୀତା"], "LOCATION": ["ଅଯୋଧ୍ୟା"]}'
        mock_completion.return_value = mock_response

        entities = self.llm.named_entity_recognition("ରାମ ଓ ସୀତା ଅଯୋଧ୍ୟାରେ ବାସ କରୁଥିଲେ।")
        expected_entities = {"PERSON": ["ରାମ", "ସୀତା"], "LOCATION": ["ଅଯୋଧ୍ୟା"]}
        self.assertEqual(entities, expected_entities)
        mock_completion.assert_called_once()

    @patch('litellm.completion')
    def test_sentiment_analysis(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"sentiment": "positive", "confidence": 0.98}'
        mock_completion.return_value = mock_response

        sentiment = self.llm.sentiment_analysis("ଏହି ଫିଲ୍ମଟି ବହୁତ ଭଲ ଥିଲା।")
        expected_sentiment = {"sentiment": "positive", "confidence": 0.98}
        self.assertEqual(sentiment, expected_sentiment)
        mock_completion.assert_called_once()

    @patch('litellm.completion')
    def test_ner_json_decode_error(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not a valid JSON."
        mock_completion.return_value = mock_response

        result = self.llm.named_entity_recognition("Some text.")
        self.assertEqual(result, {"error": "Failed to decode the LLM response as JSON."})

    @patch('litellm.completion')
    def test_sentiment_json_decode_error(self, mock_completion):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is not a valid JSON."
        mock_completion.return_value = mock_response

        result = self.llm.sentiment_analysis("Some text.")
        self.assertEqual(result, {"error": "Failed to decode the LLM response as JSON."})

if __name__ == '__main__':
    unittest.main()
