import enum
from collections import abc
from datetime import date, datetime
from typing import Callable, Iterator, List, Mapping, Optional, Sequence, Union

from .metaprogramming_helpers import getval
from .string_utilities import is_blank


def filtered_children(
    root_element: "xml.etree.ElementTree.Element",
    predicate: Callable[["xml.etree.ElementTree.Element"], bool],
) -> Iterator["xml.etree.ElementTree.Element"]:
    """Filters node children by ``predicate``"""
    return (
        element
        for element in (root_element.getchildren() if root_element else [])
        if predicate(element)
    )


def element_text_or_none(element: "xml.etree.ElementTree.Element") -> Optional[str]:
    """
    Ensures that we either get contents of element or `None` (will not return blank
    strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return getval(element, "text", "").strip() or None


def child_text_or_none(
    root_element: "xml.etree.ElementTree.Element",
    predicate: Callable[["xml.etree.ElementTree.Element"], bool],
) -> Optional[str]:
    """
    Ensures that we either get contents of child element or `None` (will not return
    blank strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return element_text_or_none(next(filtered_children(root_element, predicate), None))


def child_by_tag_text_or_none(
    root_element: "xml.etree.ElementTree.Element", child_tag: str
) -> Optional[str]:
    """
    Ensures that we either get contents of child element or `None` (will not return
    blank strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return child_text_or_none(root_element, lambda child: child.tag == child_tag)


def xml_to_enum_by_val(xml_val, enum_):
    """Converts `xml_val` to `Enum` member or rises `ValueError`."""
    xml_val = str(xml_val).strip()

    converted_value = next(
        (our_val for our_val in enum_ if xml_val.lower() == str(our_val.value).lower()),
        None,
    )

    if xml_val and not converted_value:
        raise ValueError("Invalid value of '{}' for '{}'!".format(
            xml_val, enum_.__name__
        ))

    return converted_value


def xml_to_enum_by_name(xml_val, enum_):
    """Converts `xml_val` to `enum_` member or rises `ValueError`."""
    xml_val = str(xml_val).strip()

    converted_value = next(
        (our_val for our_val in enum_ if xml_val.lower() == our_val.name.lower()), None
    )

    if xml_val and not converted_value:
        raise ValueError(
            "Invalid value of '{}' for '{}'!".format(
                xml_val, enum_.__name__
            )
        )

    return converted_value


def element_attribute_or_none(
    element: "xml.etree.ElementTree.Element", attribute_name: str
) -> Optional[str]:
    """
    Ensures that we either get contents of element's attribute or `None` (will not
    return blank strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return getval(getval(element, "attrib", {}), attribute_name, "").strip() or None


def child_attribute_or_none(
    root_element: "xml.etree.ElementTree.Element",
    predicate: Callable[["xml.etree.ElementTree.Element"], bool],
    attribute_name: str,
) -> Optional[str]:
    """
    Ensures that we either get contents of child element's attribute or `None` (will
    not return blank strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return element_attribute_or_none(
        next(filtered_children(root_element, predicate), None), attribute_name
    )


def child_by_tag_attribute_or_none(
    root_element: "xml.etree.ElementTree.Element", child_tag: str, attribute_name: str
) -> Optional[str]:
    """
    Ensures that we either get contents of child element's attribute or `None` (will
    not return blank strings).

    Results of it are meant to be set on model's attributes and returning None
    guarantees that we will trigger NOT NULL constraint upon model INSERT/UPDATE.
    """
    return child_attribute_or_none(
        root_element, lambda child: child.tag == child_tag, attribute_name
    )
