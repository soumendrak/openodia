from openodia.corpus.dictionary import get_dictionary


def test_get_dictionary():
    assert len(get_dictionary()) == 208177
