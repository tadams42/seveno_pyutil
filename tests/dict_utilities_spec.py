from seveno_pyutil import dict_utilities


class describe_inverted(object):
    def it_inverts_dict_keys_and_values(self):
        d = {'a': 1, 'b': 2}

        assert dict_utilities.inverted(d) == {1: 'a', 2: 'b'}
