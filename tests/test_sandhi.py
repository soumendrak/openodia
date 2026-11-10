"""Sandhi and compound splitting."""

import openodia
from openodia import sandhi

COMPOUNDS: list[tuple[str, list[str]]] = [
    ("ବିଦ୍ୟାଳୟ", ["ବିଦ୍ୟା", "ଆଳୟ"]),
    ("ମହାତ୍ମା", ["ମହା", "ଆତ୍ମା"]),
    ("ପୁସ୍ତକାଳୟ", ["ପୁସ୍ତକ", "ଆଳୟ"]),
    ("ହିମାଳୟ", ["ହିମ", "ଆଳୟ"]),
    ("ଦେବାଳୟ", ["ଦେବ", "ଆଳୟ"]),
    ("ବିଦ୍ୟାର୍ଥୀ", ["ବିଦ୍ୟା", "ଅର୍ଥୀ"]),
    ("ଶିକ୍ଷାନୁଷ୍ଠାନ", ["ଶିକ୍ଷା", "ଅନୁଷ୍ଠାନ"]),
    ("ଗଙ୍ଗାରତି", ["ଗଙ୍ଗା", "ଆରତି"]),
    ("ଗିରୀନ୍ଦ୍ର", ["ଗିରି", "ଇନ୍ଦ୍ର"]),
    ("କବୀନ୍ଦ୍ର", ["କବି", "ଇନ୍ଦ୍ର"]),
    ("ନଦୀଶ", ["ନଦୀ", "ଈଶ"]),
    ("ଭାନୂଦୟ", ["ଭାନୁ", "ଉଦୟ"]),
    ("ସିନ୍ଧୂର୍ମି", ["ସିନ୍ଧୁ", "ଊର୍ମି"]),
    ("ମହେଶ", ["ମହା", "ଈଶ"]),
    ("ରମେଶ", ["ରମା", "ଈଶ"]),
    ("ଗଙ୍ଗେଶ", ["ଗଙ୍ଗା", "ଈଶ"]),
    ("ରାଜେନ୍ଦ୍ର", ["ରାଜା", "ଇନ୍ଦ୍ର"]),
    ("ଦେବେନ୍ଦ୍ର", ["ଦେବ", "ଇନ୍ଦ୍ର"]),
    ("ପରମେନ୍ଦ୍ର", ["ପରମ", "ଇନ୍ଦ୍ର"]),
    ("ସୂର୍ଯ୍ୟୋଦୟ", ["ସୂର୍ଯ୍ୟ", "ଉଦୟ"]),
    ("ଚନ୍ଦ୍ରୋଦୟ", ["ଚନ୍ଦ୍ର", "ଉଦୟ"]),
    ("ମହୋତ୍ସବ", ["ମହା", "ଉତ୍ସବ"]),
    ("ଜଳୋତ୍ସବ", ["ଜଳ", "ଉତ୍ସବ"]),
    ("ସଦୈବ", ["ସଦା", "ଏବ"]),
    ("ମହୈଶ୍ୱର୍ଯ୍ୟ", ["ମହା", "ଐଶ୍ୱର୍ଯ୍ୟ"]),
    ("ମହୌଷଧ", ["ମହା", "ଔଷଧ"]),
    ("ଦେବୌଷଧ", ["ଦେବ", "ଔଷଧ"]),
    ("ଇତ୍ୟାଦି", ["ଇତି", "ଆଦି"]),
    ("ସ୍ୱାଗତ", ["ସୁ", "ଆଗତ"]),
    ("ଅତ୍ୟନ୍ତ", ["ଅତି", "ଅନ୍ତ"]),
    ("ପ୍ରତ୍ୟେକ", ["ପ୍ରତି", "ଏକ"]),
    ("ଅଧ୍ୟକ୍ଷ", ["ଅଧି", "ଅକ୍ଷ"]),
    ("ନମସ୍ତେ", ["ନମଃ", "ତେ"]),
    ("ନିଶ୍ଚଳ", ["ନିଃ", "ଚଳ"]),
    ("ନିସ୍ତାର", ["ନିଃ", "ତାର"]),
    ("ଉଚ୍ଚାରଣ", ["ଉତ୍", "ଚାରଣ"]),
    ("ସନ୍ତୋଷ", ["ସମ୍", "ତୋଷ"]),
    ("ସଙ୍କଳ୍ପ", ["ସମ୍", "କଳ୍ପ"]),
    ("ସଞ୍ଚୟ", ["ସମ୍", "ଚୟ"]),
    ("ଉଜ୍ଜ୍ୱଳ", ["ଉତ୍", "ଜ୍ୱଳ"]),
    ("ରାଜ୍ୟପାଳ", ["ରାଜ୍ୟ", "ପାଳ"]),
    ("ଗୃହକାର୍ଯ୍ୟ", ["ଗୃହ", "କାର୍ଯ୍ୟ"]),
    ("ଜନସେବା", ["ଜନ", "ସେବା"]),
    ("ଲୋକସଭା", ["ଲୋକ", "ସଭା"]),
    ("ଗ୍ରାମପଞ୍ଚାୟତ", ["ଗ୍ରାମ", "ପଞ୍ଚାୟତ"]),
    ("ଜଳପଥ", ["ଜଳ", "ପଥ"]),
    ("ରାଜଧାନୀ", ["ରାଜ", "ଧାନୀ"]),
    ("ଦେଶସେବା", ["ଦେଶ", "ସେବା"]),
    ("ଧର୍ମଶାଳା", ["ଧର୍ମ", "ଶାଳା"]),
    ("ସୂର୍ଯ୍ୟକିରଣ", ["ସୂର୍ଯ୍ୟ", "କିରଣ"]),
]


def test_curated_set_has_fifty_compounds() -> None:
    assert len(COMPOUNDS) >= 50
    assert len({word for word, _parts in COMPOUNDS}) == len(COMPOUNDS)


def test_top1_accuracy_meets_acceptance() -> None:
    hits = sum(sandhi.split(word) == parts for word, parts in COMPOUNDS)
    assert hits / len(COMPOUNDS) >= 0.70


def test_issue_examples() -> None:
    assert sandhi.split("ବିଦ୍ୟାଳୟ") == ["ବିଦ୍ୟା", "ଆଳୟ"]
    assert sandhi.split("ସୂର୍ଯ୍ୟୋଦୟ") == ["ସୂର୍ଯ୍ୟ", "ଉଦୟ"]
    assert sandhi.split("ରାଜ୍ୟପାଳ") == ["ରାଜ୍ୟ", "ପାଳ"]
    assert sandhi.join(["ବିଦ୍ୟା", "ଆଳୟ"]) == "ବିଦ୍ୟାଳୟ"


def test_round_trip_for_every_compound() -> None:
    for word, parts in COMPOUNDS:
        assert sandhi.split(word) == parts
        assert sandhi.join(parts) == word
        assert sandhi.join(sandhi.split(word)) == word


def test_unchanged_when_no_valid_split() -> None:
    for word in ("", "ରାମ", "ବିଦ୍ୟା", "ପୁସ୍ତକ", "ବକବକବକ", "hello", "ବିଦ୍ୟା ଆଳୟ"):
        assert sandhi.split(word) == [word]
        assert sandhi.join(sandhi.split(word)) == word


def test_candidates_prefer_the_longer_left_part() -> None:
    assert sandhi.split("ରାଜେନ୍ଦ୍ର", candidates=True) == [
        ["ରାଜା", "ଇନ୍ଦ୍ର"],
        ["ରାଜ", "ଇନ୍ଦ୍ର"],
    ]
    assert sandhi.split("ବିଦ୍ୟାଳୟ", candidates=True) == [["ବିଦ୍ୟା", "ଆଳୟ"]]
    assert sandhi.split("ରାମ", candidates=True) == []
    assert sandhi.split("ବକବକବକ", candidates=True) == []


def test_edges_outside_the_compound_list() -> None:
    assert sandhi.join(["ଆ", "ଆଳୟ"]) == "ଆଳୟ"
    assert sandhi.join(["ଉତ୍", "ପାଳ"]) == "ଉତ୍ପାଳ"
    assert sandhi.join(["", "ରାମ"]) == "ରାମ"
    assert sandhi.join(["ରାମ", ""]) == "ରାମ"
    assert sandhi.split("ବିଦ୍ୟାଆଳୟ") == ["ବିଦ୍ୟାଆଳୟ"]
    assert sandhi.split("ାଳୟ") == ["ାଳୟ"]


def test_join_folds_a_three_part_compound() -> None:
    assert sandhi.join(["ଲୋକ", "ସଭା", "ଗୃହ"]) == "ଲୋକସଭାଗୃହ"
    assert sandhi.join([]) == ""
    assert sandhi.join(["ରାମ"]) == "ରାମ"


def test_package_exports_sandhi() -> None:
    assert "sandhi" in openodia.__all__
    assert openodia.sandhi.split is sandhi.split
    assert openodia.sandhi.join is sandhi.join
