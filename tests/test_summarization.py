from openodia import WordFrequency


class TestSummarization:
    def test_get_summary(self):
        wf = WordFrequency(
            text="ଭାରତୀୟ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ, ଭାରତର ଉଚ୍ଚତମ ନ୍ୟାୟିକ ଅନୁଷ୍ଠାନ ଅଟେ ଏବଂ ଭାରତୀୟ ସମ୍ବିଧାନ ଅଧୀନସ୍ଥ "
            "ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ ଅଟେ । "
            "ଏହା ସର୍ବ ବରିଷ୍ଠ ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ଅଟେ ଏବଂ ଏହି ନ୍ୟାୟିକ ପୁନରାବଲୋକନର କ୍ଷମତା ରହିଛି । "
            "ଭାରତର ମୁଖ୍ୟ ବିଚାରପତି ଏହାର ମୁଖ୍ୟ ଅଟନ୍ତି । ତତ୍ସହିତ ଏଥିରେ ସର୍ବାଧିକ ୩୪ ଜଣ ବିଚାରପତି ଅଛନ୍ତି । "
            "ମୁଖ୍ୟ, ଅପିଲୀୟ ତଥା ପରାମର୍ଶିକ ଆଦି ଅଧିକାରକ୍ଷେତ୍ର ମାଧ୍ୟମରେ ଏହାର ବିସ୍ତୃତ କ୍ଷମତା ରହିଛି । "
            "ଏହା ଭାରତରେ ସବୁଠାରୁ ଶକ୍ତିଶାଳୀ ଲୋକାନୁଷ୍ଠାନ ବୋଲି ଧରାଯାଇଅଛି । "
            "ଦେଶର ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ହୋଇଥିବାରୁ, ଏହା ମୁଖ୍ୟତଃ ସଙ୍ଘର ବିଭିନ୍ନ ଉଚ୍ଚ ନ୍ୟାୟାଳୟ ତଥା "
            "ଅନ୍ୟାନ୍ୟ ନ୍ୟାୟାଳୟ ଓ "
            "ଟ୍ରିବ୍ୟୁନାଲମାନଙ୍କର ରାୟ ବିରୁଦ୍ଧରେ ଅପିଲ୍ ନିଏ । "
            "ଏହା ନାଗରିକମାନଙ୍କର ମୌଳିକ ଅଧିକାରର ରକ୍ଷାକରେ ଏବଂ ବିଭିନ୍ନ ସରକାରୀ ଅଧିକାରୀ ତଥା "
            "ଦେଶରେ କେନ୍ଦ୍ର ସରକାର ବନାମ ରାଜ୍ୟ ସରକାର କିମ୍ବା ଗୋଟିଏ ରାଜ୍ୟ ସରକାର ବନାମ ଅନ୍ୟ ରାଜ୍ୟ ସରକାର "
            "ମଧ୍ୟରେ ବିବାଦର ସମାଧାନ କରେ । "
            "ଏକ ପରାମର୍ଶଦାତା ହିସାବରେ, ଏହା ଭାରତୀୟ ସମ୍ବିଧାନ ଅନୁସାରେ ରାଷ୍ଟ୍ରପତିଙ୍କଦ୍ୱାରା ସୂଚୀତ ବିଭିନ୍ନ ବିଷୟବସ୍ତୁ "
            "ଉପରେ ଶୁଣାଣି କରିଥାଏ । "
        )
        expected_output = "ଭାରତୀୟ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ, ଭାରତର ଉଚ୍ଚତମ ନ୍ୟାୟିକ ଅନୁଷ୍ଠାନ ଅଟେ ଏବଂ ଭାରତୀୟ ସମ୍ବିଧାନ ଅଧୀନସ୍ଥ ସର୍ବୋଚ୍ଚ ନ୍ୟାୟାଳୟ ଅଟେ  ଏହା ସର୍ବ ବରିଷ୍ଠ ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ଅଟେ ଏବଂ ଏହି ନ୍ୟାୟିକ ପୁନରାବଲୋକନର କ୍ଷମତା ରହିଛି  ଦେଶର ସାମ୍ବିଧାନିକ ନ୍ୟାୟାଳୟ ହୋଇଥିବାରୁ, ଏହା ମୁଖ୍ୟତଃ ସଙ୍ଘର ବିଭିନ୍ନ ଉଚ୍ଚ ନ୍ୟାୟାଳୟ ତଥା ଅନ୍ୟାନ୍ୟ ନ୍ୟାୟାଳୟ ଓ ଟ୍ରିବ୍ୟୁନାଲମାନଙ୍କର ରାୟ ବିରୁଦ୍ଧରେ ଅପିଲ୍ ନିଏ"
        assert wf.get_summary(4.0) == expected_output

    def test_get_tokens(self):
        """Test get_tokens method"""
        wf = WordFrequency(text="ଏହା ଏକ ପରୀକ୍ଷା ବାକ୍ୟ ।")
        wf.get_tokens()
        expected_tokens = ["ଏହା", "ଏକ", "ପରୀକ୍ଷା", "ବାକ୍ୟ", "।"]
        assert wf.token_list == expected_tokens

    def test_get_sentences(self):
        """Test get_sentences method"""
        wf = WordFrequency(text="ଏହା ପ୍ରଥମ ବାକ୍ୟ । ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ ।")
        wf.get_sentences()
        expected_sentences = ["ଏହା ପ୍ରଥମ ବାକ୍ୟ", " ଏହା ଦ୍ୱିତୀୟ ବାକ୍ୟ", ""]
        assert wf.sentence_list == expected_sentences

    def test_remove_stopwords_method(self):
        """Test remove_stopwords method"""
        wf = WordFrequency()
        wf.token_list = ["ଏହା", "ଏକ", "ପରୀକ୍ଷା", "ବାକ୍ୟ", "।"]
        wf.remove_stopwords()
        # "ଏହା" and "।" should be removed as they are stopwords
        expected_tokens = ["ଏକ", "ପରୀକ୍ଷା", "ବାକ୍ୟ"]
        assert wf.token_list == expected_tokens

    def test_number_of_words_in_text(self):
        """Test _number_of_words_in_text method"""
        wf = WordFrequency()
        wf.token_list = ["word1", "word2", "word3", "word1"]
        assert wf._number_of_words_in_text() == 4

    def test_number_of_unique_words_in_text(self):
        """Test _number_of_unique_words_in_text method"""
        wf = WordFrequency()
        wf.token_list = ["word1", "word2", "word3", "word1"]
        assert wf._number_of_unique_words_in_text() == 3

    def test_get_threshold_value(self):
        """Test _get_threshold_value method"""
        wf = WordFrequency()
        wf.token_list = ["word1", "word2", "word3", "word1"]
        # 4 total words / 3 unique words = 1.333...
        expected_threshold = 4 / 3
        assert abs(wf._get_threshold_value() - expected_threshold) < 0.01

    def test_words_having_higher_threshold(self):
        """Test words_having_higher_threshold method"""
        wf = WordFrequency()
        wf.token_list = ["word1", "word1", "word1", "word2", "word3"]
        # word1 appears 3 times, others appear 1 time
        # threshold of 2.0 should only return word1
        frequent_words = wf.words_having_higher_threshold(2.0)
        assert frequent_words == {"word1"}

    def test_words_having_higher_threshold_with_auto_threshold(self):
        """Test words_having_higher_threshold with automatic threshold"""
        wf = WordFrequency()
        wf.token_list = ["word1", "word1", "word2"]
        # Auto threshold = 3/2 = 1.5, so word1 (appears 2 times) should be returned
        frequent_words = wf.words_having_higher_threshold()
        assert frequent_words == {"word1"}

    def test_get_sentence_having_frequent_words(self):
        """Test get_sentence_having_frequent_words method"""
        wf = WordFrequency()
        wf.sentence_list = ["This has word1", "This has word2", "This has word3"]
        frequent_words = {"word1", "word3"}
        result = wf.get_sentence_having_frequent_words(frequent_words)
        expected = "This has word1 This has word3"
        assert result == expected

    def test_empty_text_handling(self):
        """Test handling of empty text"""
        wf = WordFrequency(text="")
        wf.get_tokens()
        assert wf.token_list == [] or wf.token_list == [""]
        wf.get_sentences()
        assert wf.sentence_list == [] or wf.sentence_list == [""]

    def test_text_with_only_stopwords(self):
        """Test text containing only stopwords"""
        wf = WordFrequency(text="ଏହା । ପାଇଁ")
        wf.get_tokens()
        wf.remove_stopwords()
        # All words should be removed
        assert len(wf.token_list) == 0
