import pytest

from openodia import name


class TestOdiaNames:
    def test_generate_prefixes(self):
        assert len(name.generate_prefixes(3)) == 3

    def test_generate_names(self):
        assert len(name.generate_names(153)) == 153

    @pytest.mark.parametrize(
        "count, name_type, output",
        [
            (14, "male", 14),
            (33, "Male", 33),
            (23, "feMale", 23),
            (3, "uniSEX", 3),
            (3, "I will not say", None),
            (10, "", 10),
        ],
    )
    def test_generate_firstnames(self, count, name_type, output):
        if name_type and name_type.lower() not in ("male", "female", "unisex"):
            with pytest.raises(ValueError):
                assert name.generate_firstnames(count, name_type)
        else:
            assert len(name.generate_firstnames(count, name_type)) == output

    def test_generate_middlenames(self):
        assert len(name.generate_middlenames(9)) == 9

    def test_generate_surnames(self):
        assert len(name.generate_surnames(25)) == 25
