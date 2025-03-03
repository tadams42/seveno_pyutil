import itertools
from collections.abc import Generator, Iterable
from typing import TypeVar

T = TypeVar("T")  # Declare type variable


def in_batches(iterable: Iterable[T], of_size: int = 1) -> Generator[Iterable[T]]:
    """
    Generator that yields generator slices of iterable.

    Since it is elegant and working flawlessly, it is shameless C/P from
    https://stackoverflow.com/questions/8991506/iterate-an-iterator-by-chunks-of-n-in-python/8998040#8998040

    Warning:
        Each returned batch should be completely consumed before next batch
        is yielded. See example below to better understand what that means.

    Example::

        from seveno_pyutil import in_batches

        g = (o for o in range(10))
        for batch in in_batches(g, of_size=3):
            print(list(batch))
        # [0, 1, 2]
        # [3, 4, 5]
        # [6, 7, 8]
        # [9]

        # And this happens if whole batch is not consumed before yielding another one...

        g = list(range(10))
        for batch in in_batches(g, of_size=3):
            print( [next(batch), next(batch)] )
        # [0, 1]
        # [2, 3]
        # [4, 5]
        # [6, 7]
        # [8, 9]
    """
    it = iter(iterable)
    while True:
        chunk_it = itertools.islice(it, of_size)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield itertools.chain((first_el,), chunk_it)
