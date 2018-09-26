import itertools


def in_batches(iterable, of_size=1):
    """
    Generator that yields generator slices of iterable.

    Since it is elegant and working flawlessly, it is shameles C/P from
    https://stackoverflow.com/a/8998040/2219433

    Warning:
        Each returned batch should be completely consumed before next batch
        is yielded. See example below to better understand what that means.

    Example:

        >>> from seveno_pyutil import in_batches
        >>> g = (o for o in range(10))
        >>> for batch in in_batches(g, of_size=3):
        ...     print(list(batch))
        ...
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]
        >>> g = list(range(10))
        >>> for batch in in_batches(g, of_size=3):
        ...     print(list(batch))
        ...
        [0, 1, 2]
        [3, 4, 5]
        [6, 7, 8]
        [9]
        >>> # And now a demo what happens if don't consume whole batch before
        >>> # yielding another one
        >>> g = list(range(10))
        >>> g
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> for batch in in_batches(g, of_size=3):
        ...     print( [next(batch), next(batch)] )
        ...
        [0, 1]
        [2, 3]
        [4, 5]
        [6, 7]
        [8, 9]
    """
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, of_size)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)