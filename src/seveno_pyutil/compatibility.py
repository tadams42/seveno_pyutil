"""
Backports some of Python 3 things that can't be found in other compatibility
packages.
"""

def py34_min(iterable, key=None, default=None):
    """
    Implements ``min`` builtin with new ``default`` keyword arument introduced
    in Python 3.4
    """
    try:
        if key:
            retv = min(iterable, key=key)
        else:
            retv = min(iterable)
    except ValueError as e:
        # 'min() arg is an empty sequence'
        retv = default

    return retv

def py34_max(iterable, key=None, default=None):
    """
    Implements ``max`` builtin with new ``default`` keyword arument introduced
    in Python 3.4
    """
    try:
        if key:
            retv = max(iterable, key=key)
        else:
            retv = max(iterable)
    except ValueError as e:
        # 'max() arg is an empty sequence'
        retv = default

    return retv
