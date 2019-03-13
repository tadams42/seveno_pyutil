from seveno_pyutil.metaprogramming_helpers import (all_subclasses, import_string,
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
    assert set(leaf_subclasses(Base)) == set([DirectChild2, Child])


def test_all_subclasses_returns_correct_data():
    assert all_subclasses(Base) == set([DirectChild1, DirectChild2, Child])


def test_import_string_imports_class_from_string():
    klass = import_string("seveno_pyutil.benchmarking_utilities.Stopwatch")
    assert klass.__name__ == "Stopwatch"
    assert klass.__module__ == "seveno_pyutil.benchmarking_utilities"
