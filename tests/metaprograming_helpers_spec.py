from seveno_pyutil.metaprogramming_helpers import (all_subclasses,
                                                   leaf_subclasses)


class Base(object):
    pass


class DirectChild1(Base):
    pass


class DirectChild2(Base):
    pass


class Child(DirectChild1):
    pass


def test_leaf_subclasses_returns_correct_data():
    assert set(leaf_subclasses(Base)) == set([
        DirectChild2, Child
    ])


def test_all_subclasses_returns_correct_data():
    assert all_subclasses(Base) == set([
        DirectChild1, DirectChild2, Child
    ])
