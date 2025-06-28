import pytest

from openodia import ud


class TestUnderstandData:
    def test_word_tokenizer(self):
        assert ud.word_tokenizer(
            "କ୍ୱାଣ୍ଟମ କମ୍ପ୍ୟୁଟିଙ୍ଗ, ହେଉଛି ଏକ ଉଦୀୟମାନ ହାର୍ଡ଼ୱେର ଏବଂ ସଫ୍ଟୱେରର ପ୍ରଯୁକ୍ତିବିଦ୍ୟା, ଯାହା କଠିନ ଗାଣିତିକ ସମସ୍ୟାଗୁଡ଼ିକର ସମାଧାନ ପାଇଁ ଉପ-ପାରମାଣବିକ ଘଟଣାଗୁଡ଼ିକର ଉପଯୋଗ କରିଥାଏ ।[୧]"
        ) == [
            "କ୍ୱାଣ୍ଟମ",
            "କମ୍ପ୍ୟୁଟିଙ୍ଗ",
            "ହେଉଛି",
            "ଏକ",
            "ଉଦୀୟମାନ",
            "ହାର୍ଡ଼ୱେର",
            "ଏବଂ",
            "ସଫ୍ଟୱେରର",
            "ପ୍ରଯୁକ୍ତିବିଦ୍ୟା",
            "ଯାହା",
            "କଠିନ",
            "ଗାଣିତିକ",
            "ସମସ୍ୟାଗୁଡ଼ିକର",
            "ସମାଧାନ",
            "ପାଇଁ",
            "ଉପ",
            "ପାରମାଣବିକ",
            "ଘଟଣାଗୁଡ଼ିକର",
            "ଉପଯୋଗ",
            "କରିଥାଏ",
            "।",
            "୧",
        ]

    def test_sentence_tokenizer(self):
        assert ud.sentence_tokenizer(
            "ଏହି ଭବନଟିକୁ, ନ୍ୟାୟର ନିକିତିକୁ ପ୍ରଦର୍ଶନ କରୁଥିବା ଆକୃତି ଦିଆଯାଇଛି । ଏହାର ମଧ୍ଯ ଭାଗ ନିକିତିର ଦଣ୍ଡ, ତଥା ଦୁଇ ପଟେ ଦୁଇଟି ନ୍ୟାୟକକ୍ଷ ନିକିତିର ଦୁଇ ଭାରକୁ ଦର୍ଶାଉଛି । ଭବନର ମଧ୍ଯ ଭାଗରେ ମୁଖ୍ଯ ବିଚାରପତିଙ୍କ ନ୍ୟାୟକକ୍ଷ ଅବସ୍ଥିତ"
        ) == [
            "ଏହି ଭବନଟିକୁ, ନ୍ୟାୟର ନିକିତିକୁ ପ୍ରଦର୍ଶନ କରୁଥିବା ଆକୃତି ଦିଆଯାଇଛି",
            " ଏହାର ମଧ୍ଯ ଭାଗ ନିକିତିର ଦଣ୍ଡ, ତଥା ଦୁଇ ପଟେ ଦୁଇଟି ନ୍ୟାୟକକ୍ଷ ନିକିତିର ଦୁଇ ଭାରକୁ ଦର୍ଶାଉଛି",
            " ଭବନର ମଧ୍ଯ ଭାଗରେ ମୁଖ୍ଯ ବିଚାରପତିଙ୍କ ନ୍ୟାୟକକ୍ଷ ଅବସ୍ଥିତ",
        ]

    def test_remove_stopwords(self):
        assert ud.remove_stopwords("ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି") == [
            "ରାମ",
            "ସୀତା",
            "ଆମକୁ",
            "ଆଶୀର୍ବାଦ",
        ]
        assert ud.remove_stopwords("ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି ", get_str=True) == "ରାମ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ"

    @pytest.mark.parametrize(
        "text, threshold, output",
        [
            (
                "hey how are you?",
                0.5,
                {"language": "non-odia", "confidence_score": 1.0},
            ),
            (
                "hey how are you? ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ",
                0.5,
                {"language": "odia", "confidence_score": 0.67},
            ),
            (
                "hey how are you? ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ",
                0.7,
                {"language": "non-odia", "confidence_score": 0.33},
            ),
            (
                "ନ୍ୟାଚୁରାଲ ଲାଙ୍ଗୁଏଜ ପ୍ରୋସେସିଂ ବା ପ୍ରାକୃତିକ ଭାଷା ପ୍ରକ୍ରିୟାକରଣ କଂପ୍ୟୁଟର ବିଜ୍ଞାନ ଏବଂ ଆର୍ଟିଫିସିଆଲ ଇଣ୍ଟେଲିଜେନ୍ସର ସେହି ବିଭାଗକୁ କୁହାଯ ାଏ ଯାହା ମନୁଷ୍ୟର ଭାଷାଗୁଡ଼ିକ ସହ କମ୍ପ୍ୟୁଟରର କଥାବାର୍ତ୍ତାକୁ ବୁଝାଇଥାଏ। ",
                0.5,
                {"language": "odia", "confidence_score": 0.99},
            ),
        ],
    )
    def test_detect_language(self, text, threshold, output):
        assert ud.detect_language(text, threshold=threshold) == output

    # Additional test cases for edge cases
    def test_word_tokenizer_empty_string(self):
        """Test word tokenizer with empty string"""
        assert ud.word_tokenizer("") == []

    def test_word_tokenizer_single_word(self):
        """Test word tokenizer with single word"""
        assert ud.word_tokenizer("ନମସ୍କାର") == ["ନମସ୍କାର"]

    def test_word_tokenizer_with_numbers(self):
        """Test word tokenizer with numbers"""
        result = ud.word_tokenizer("ଏହା ୨୦୨୪ ସାଲ")
        assert "୨୦୨୪" in result
        assert "ଏହା" in result
        assert "ସାଲ" in result

    def test_sentence_tokenizer_empty_string(self):
        """Test sentence tokenizer with empty string"""
        result = ud.sentence_tokenizer("")
        assert result == [] or result == [""]

    def test_sentence_tokenizer_single_sentence(self):
        """Test sentence tokenizer with single sentence"""
        result = ud.sentence_tokenizer("ଏହା ଏକ ବାକ୍ୟ")
        assert len(result) == 1
        assert result[0] == "ଏହା ଏକ ବାକ୍ୟ"

    def test_sentence_tokenizer_no_punctuation(self):
        """Test sentence tokenizer without punctuation"""
        result = ud.sentence_tokenizer("ଏହା ପ୍ରଥମ ଏହା ଦ୍ୱିତୀୟ")
        assert len(result) == 1
        assert result[0] == "ଏହା ପ୍ରଥମ ଏହା ଦ୍ୱିତୀୟ"

    def test_remove_stopwords_with_list_input(self):
        """Test remove_stopwords with list input"""
        token_list = ["ରାମ", "ଓ", "ସୀତା", "ଆମକୁ", "ଦେଇଛନ୍ତି"]
        result = ud.remove_stopwords(token_list)
        expected = ["ରାମ", "ସୀତା", "ଆମକୁ"]
        assert result == expected

    def test_remove_stopwords_with_extra_stopwords(self):
        """Test remove_stopwords with user supplied stopwords"""
        text = "ରାମ ଓ ସୀତା ଆମକୁ ଆଶୀର୍ବାଦ ଦେଇଛନ୍ତି"
        result = ud.remove_stopwords(text, extra_stopwords=["ଆମକୁ"])
        assert "ଆମକୁ" not in result
        assert result == ["ରାମ", "ସୀତା", "ଆଶୀର୍ବାଦ"]

    def test_remove_stopwords_empty_string(self):
        """Test remove_stopwords with empty string"""
        assert ud.remove_stopwords("") == []
        assert ud.remove_stopwords("", get_str=True) == ""

    def test_remove_stopwords_all_stopwords(self):
        """Test remove_stopwords with all stopwords"""
        result = ud.remove_stopwords("ଏହା । ପାଇଁ ଦେଇଛନ୍ତି")
        assert len(result) == 0

    def test_detect_language_empty_string(self):
        """Test detect_language with empty string"""
        result = ud.detect_language("")
        assert result == {}

    def test_detect_language_pure_odia(self):
        """Test detect_language with pure Odia text"""
        result = ud.detect_language("ନମସ୍କାର କେମିତି ଅଛନ୍ତି", threshold=0.5)
        assert result["language"] == "odia"
        assert result["confidence_score"] > 0.9

    def test_detect_language_pure_english(self):
        """Test detect_language with pure English text"""
        result = ud.detect_language("Hello how are you", threshold=0.5)
        assert result["language"] == "non-odia"
        assert result["confidence_score"] == 1.0

    def test_detect_language_mixed_with_spaces(self):
        """Test detect_language with mixed text and spaces"""
        result = ud.detect_language("   hello   ନମସ୍କାର   ", threshold=0.5)
        assert "language" in result
        assert "confidence_score" in result

    def test_detect_language_different_thresholds(self):
        """Test detect_language with different threshold values"""
        text = "hello ନମସ୍କାର"  # 50% Odia

        result_low = ud.detect_language(text, threshold=0.3)
        result_high = ud.detect_language(text, threshold=0.7)

        assert result_low["language"] == "odia"
        assert result_high["language"] == "non-odia"
