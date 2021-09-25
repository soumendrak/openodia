from openodia import name


class TestOdiaNames:
    def test_generate_prefixes(self):
        assert len(name.generate_prefixes(3)) == 3

    def test_generate_names(self):
        assert len(name.generate_names(153)) == 153

    def test_generate_firstnames(self):
        assert len(name.generate_firstnames(42)) == 42

    def test_generate_middlenames(self):
        assert len(name.generate_middlenames(9)) == 9

    def test_generate_surnames(self):
        assert len(name.generate_surnames(25)) == 25
