from datetime import date, datetime
from typing import AnyStr, Iterable, Union

try:
    import simplejson as json
except Exception:
    import json


def is_blank(obj: Union[AnyStr, Iterable, None]):
    """
    True if line is empty string, None, string that contains only spaces and
    space like characters, or line is iterable that contains only these kinds
    of strings/objects
    """
    if not obj:
        return True

    if isinstance(obj, (str, bytes)):
        return not obj.strip()

    retv = False
    try:
        retv = all(is_blank(x) for x in obj)
    except TypeError:
        # ... not iterable
        retv = False

    return retv
