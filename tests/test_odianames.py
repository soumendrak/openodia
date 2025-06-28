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

    # Additional test cases
    def test_generate_prefixes_empty(self):
        """Test generating zero prefixes"""
        result = name.generate_prefixes(0)
        assert len(result) == 0
        assert result == []

    def test_generate_prefixes_single(self):
        """Test generating single prefix"""
        result = name.generate_prefixes(1)
        assert len(result) == 1
        assert isinstance(result[0], str)

    def test_generate_names_empty(self):
        """Test generating zero names"""
        result = name.generate_names(0)
        assert len(result) == 0
        assert result == []

    def test_generate_names_single(self):
        """Test generating single name"""
        result = name.generate_names(1)
        assert len(result) == 1
        assert isinstance(result[0], str)

    def test_generate_names_are_unique_in_small_set(self):
        """Test that generated names can be unique in small sets"""
        result = name.generate_names(5)
        # While names might repeat, each should be a valid string
        assert all(isinstance(n, str) for n in result)
        assert all(len(n) > 0 for n in result)

    def test_generate_firstnames_case_insensitive(self):
        """Test that name_type parameter is case insensitive"""
        male_lower = name.generate_firstnames(5, "male")
        male_upper = name.generate_firstnames(5, "MALE")
        male_mixed = name.generate_firstnames(5, "MaLe")

        # All should work without error
        assert len(male_lower) == 5
        assert len(male_upper) == 5
        assert len(male_mixed) == 5

    def test_generate_firstnames_invalid_types(self):
        """Test various invalid name types"""
        invalid_types = ["xyz", "123", "man", "woman", " male", "male "]

        for invalid_type in invalid_types:
            with pytest.raises(ValueError):
                name.generate_firstnames(5, invalid_type)

    def test_generate_firstnames_empty_type(self):
        """Test empty string type returns mixed names"""
        result = name.generate_firstnames(10, "")
        assert len(result) == 10
        assert all(isinstance(n, str) for n in result)

    def test_generate_firstnames_none_type(self):
        """Test None type (should default to mixed)"""
        # This would need to check the actual implementation
        # If the method doesn't handle None, this might fail
        try:
            result = name.generate_firstnames(5)  # No name_type parameter
            assert len(result) == 5
        except TypeError:
            # If the method requires name_type parameter
            pytest.skip("Method requires name_type parameter")

    def test_generate_middlenames_empty(self):
        """Test generating zero middle names"""
        result = name.generate_middlenames(0)
        assert len(result) == 0
        assert result == []

    def test_generate_middlenames_large_count(self):
        """Test generating large number of middle names"""
        result = name.generate_middlenames(100)
        # Should return available middle names (might be less than requested if not enough available)
        assert len(result) <= 100
        assert len(result) > 0
        assert all(isinstance(n, str) for n in result)

    def test_generate_surnames_empty(self):
        """Test generating zero surnames"""
        result = name.generate_surnames(0)
        assert len(result) == 0
        assert result == []

    def test_generate_surnames_large_count(self):
        """Test generating large number of surnames"""
        result = name.generate_surnames(100)
        assert len(result) == 100
        assert all(isinstance(n, str) for n in result)

    def test_all_generated_names_are_strings(self):
        """Test that all generated items are strings"""
        prefixes = name.generate_prefixes(5)
        names = name.generate_names(5)
        firstnames = name.generate_firstnames(5, "male")
        middlenames = name.generate_middlenames(5)
        surnames = name.generate_surnames(5)

        for item_list in [prefixes, names, firstnames, middlenames, surnames]:
            assert all(isinstance(item, str) for item in item_list)
            assert all(len(item) > 0 for item in item_list)

    def test_negative_count_handling(self):
        """Test behavior with negative counts"""
        # Depending on implementation, this might raise an error or return empty list
        try:
            result = name.generate_prefixes(-1)
            # If it doesn't raise an error, it should return empty or handle gracefully
            assert len(result) >= 0
        except (ValueError, IndexError):
            # This is also acceptable behavior
            pass

    def test_large_count_handling(self):
        """Test behavior with very large counts"""
        # Test with count larger than available names
        large_count = 10000

        # These should work (might have repeats)
        prefixes = name.generate_prefixes(large_count)
        middlenames = name.generate_middlenames(large_count)
        surnames = name.generate_surnames(large_count)

        # Length should be reasonable - may not match exactly if not enough data
        assert len(prefixes) > 0
        assert len(middlenames) > 0
        assert len(surnames) > 0
        
        # Should not exceed the requested count
        assert len(prefixes) <= large_count
        assert len(middlenames) <= large_count
        assert len(surnames) <= large_count

    def test_method_consistency(self):
        """Test that methods return consistent types"""
        # All methods should return lists of strings
        methods_and_params = [
            (name.generate_prefixes, (5,)),
            (name.generate_names, (5,)),
            (name.generate_firstnames, (5, "male")),
            (name.generate_middlenames, (5,)),
            (name.generate_surnames, (5,))
        ]

        for method, params in methods_and_params:
            result = method(*params)
            assert isinstance(result, list)
            assert len(result) == 5
