import timeit


class Stopwatch(object):
    """
    Simple stopwatch that measures duration of block of code in [ms]

    Example:
        >>> import time
        >>>
        >>> with Stopwatch() as stopwatch:
        ...    time.sleep(1)
        >>> assert stopwatch.duration_ms >= 1000
    """
    def __init__(self):
        self.start = 0
        self.end = 0

    def __enter__(self):
        self.start = timeit.default_timer()
        return self

    def __exit__(self, *args):
        self.end = timeit.default_timer()
        return False

    @property
    def duration_ms(self):
        return (self.end - self.start) * 1000
