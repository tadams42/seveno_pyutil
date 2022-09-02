from typing import Any


def is_blank(obj: Any) -> bool:
    """
    True if obj is empty string, None, string that contains only spaces and space like
    characters, or iterable that contains only these kinds of strings/objects
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
