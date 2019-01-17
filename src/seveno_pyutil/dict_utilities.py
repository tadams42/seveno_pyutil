def inverted(dct):
    """
    Converts::

        d = {'a': 1, 'b': 2}

    To::

        {1: 'a', 2: 'b'}
    """
    return {v: k for k, v in dct.items()}
