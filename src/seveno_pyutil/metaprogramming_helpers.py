import sys
from importlib import import_module

import six


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
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])
