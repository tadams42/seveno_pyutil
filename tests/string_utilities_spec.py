from seveno_pyutil import is_blank


class DescribeIsBlank:
    def it_works_for_strings_numbers_and_iterables(self):
        assert is_blank("") is True
        assert is_blank("     ") is True
        assert is_blank("  \t \n \r   ") is True
        assert is_blank(None) is True
        assert is_blank(0) is True
        assert is_blank([]) is True
        assert is_blank([None, None]) is True

        assert is_blank(42) is False
        assert is_blank("42") is False
        assert is_blank([None, 42]) is False
