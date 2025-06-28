from openodia import stem_word, stem_text


def test_stem_word_examples():
    assert stem_word("ପିଲାମାନେ") == "ପିଲା"
    assert stem_word("ବଇଗୁଡ଼ିକ") == "ବଇ"
    assert stem_word("କଲେ") == "କ"


def test_stem_text():
    text = "ପିଲାମାନେ ବଇଗୁଡ଼ିକ ପଢ଼ୁଛନ୍ତି"
    assert stem_text(text) == "ପିଲା ବଇ ପଢ଼ୁଛ"

