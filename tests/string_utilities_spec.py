from seveno_pyutil import is_blank


class DescribeIsBlank(object):
    def it_works_for_strings_numbers_and_iterables(self):
        assert is_blank("") == True
        assert is_blank("     ") == True
        assert is_blank("  \t \n \r   ") == True
        assert is_blank(None) == True
        assert is_blank(0) == True
        assert is_blank([]) == True
        assert is_blank([None, None]) == True

        assert is_blank(42) == False
        assert is_blank("42") == False
        assert is_blank([None, 42]) == False
