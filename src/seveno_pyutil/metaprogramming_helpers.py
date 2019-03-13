import sys
from collections import abc
from importlib import import_module
from typing import Mapping, Union


class LeafSubclassRetriever:
    """
    http://code.activestate.com/recipes/577858-concrete-class-finder/
    """

    def __init__(self, base_class):
        self.base_class = base_class

    def value(self):
        direct_subclasses = self.base_class.__subclasses__()
        leaf_subclasses = list()
        for klass in direct_subclasses:
            if (len(klass.__subclasses__()) > 0):
                leaf_subclasses += LeafSubclassRetriever(klass).value()
            else:
                leaf_subclasses.append(klass)

        return leaf_subclasses


def leaf_subclasses(klass):
    """
    Returns all leaf subclasses of given ``klass``
    """
    return LeafSubclassRetriever(klass).value()


def all_subclasses(klass):
    subclasses = set(klass.__subclasses__())

    for subklass in subclasses:
        subclasses = subclasses.union(all_subclasses(subklass))

    return subclasses


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as e:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from e

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class' % (
                module_path, class_name)
        ) from e


def getval(src: Union[Mapping, object], attr: object, default=None):
    """
    Companion of `dict.get` and `getattr` which ensures default value even when
    original method would had returned `None`

    Example::

        d1 = {}
        d2 = {"foo": None}
        d3 = {"foo": "bar"}

        d1.get("foo", 42)  # => 42
        d2.get("foo", 42)  # => None
        d3.get("foo", 42)  # => "bar"

        getval(d1, "foo", 42)  # => 42
        getval(d2, "foo", 42)  # => 42
        getval(d3, "foo", 42)  # => "bar"

        # and also

        getval({"a": ""}, "a", None) is None  # => True

        # and with objects other than dicts

        class Foo:
            def __init__(self, foo=None):
                self.foo = foo

        class Bar:
            pass

        o1 = Bar()
        o2 = Foo()
        o3 = Foo("bar")

        getattr(o1, "foo", 42)  # => 42
        getattr(o2, "foo", 42)  # => None
        getattr(o3, "foo", 42)  # => "bar"

        getval(o1, "foo", 42)  # => 42
        getval(o2, "foo", 42)  # => 42
        getval(o3, "foo", 42)  # => "bar"
    """

    if isinstance(src, abc.Mapping):
        return src.get(attr, None) or default
    else:
        return getattr(src, attr, None) or default
