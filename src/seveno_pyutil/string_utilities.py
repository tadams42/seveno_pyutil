import six


def is_blank(obj):
    """
    True if line is empty string, None, string that contains only spaces and
    space like characters, or line is iterable that contains only these kinds
    of strings/objects
    """
    if not obj:
        return True

    if isinstance(obj, six.string_types):
        return not obj.strip()

    retv = False
    try:
        retv = all(is_blank(x) for x in obj)
    except TypeError:
        # ... not iterable
        retv = False

    return retv
