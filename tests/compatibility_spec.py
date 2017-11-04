from seveno_pyutil import max, min


class DescribeCompatibility(object):
    def test_min_has_default_parameter(self):
        assert min([], default=42) == 42

    def test_max_has_default_parameter(self):
        assert max([], default=42) == 42
