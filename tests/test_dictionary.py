from openodia.corpus.dictionary import get_dictionary


def test_get_dictionary():
    assert len(get_dictionary("../openodia/corpus/En-Or_word_pairs_v2.json")) == 208046
