def is_blank(line):
    """
    True if string is empty, None or contains only spaces and space like
    characters.
    """
    return line is None or not str(line).strip()
