import enum
from collections import abc
from datetime import date, datetime
from typing import Callable, Iterator, List, Mapping, Optional, Sequence, Union

from .metaprogramming_helpers import getval
from .string_utilities import is_blank


class ExceptionsAsErrors:
    """
    Context manager that swallows exceptions and stores them as structured error dict
    that can later be added to `marshmallow.ValidationError`.

    It uses `add_error_to` to update provided ``errors_store`` with caught exceptions.

    Example::

        errors = {}
        with ExceptionsAsErrors(errors) as e:
            raise RuntimeError("ZOMG!")
        errors == {'_schema': ['ZOMG!']}

        errors = {}
        with ExceptionsAsErrors(errors, subkey="some_name") as e:
            raise RuntimeError("ZOMG!")
        errors == {'some_name': ['ZOMG!']}
    """

    def __init__(self, errors_store: Union[Mapping, object], subkey=None):
        self.subkey = subkey if not is_blank(subkey) else None
        self.errors_store = errors_store

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        if exc_val:
            if self.subkey:
                add_error_to(self.errors_store, {self.subkey: exc_val})
            else:
                add_error_to(self.errors_store, exc_val)
        return True


def _normalize_error_data(error):
    if isinstance(error, str):
        return error

    if isinstance(error, (abc.Sequence, abc.Set)):
        return [_normalize_error_data(obj) for obj in error]

    if isinstance(error, abc.Mapping):
        return {k: _normalize_error_data(v) for k, v in error.items()}

    if hasattr(error, "normalized_messages"):
        return _normalize_error_data(error.normalized_messages())

    return str(error)


def add_error_to(
    errors_store: Union[Mapping, object],
    error: Union[str, Sequence, object, Mapping, Exception],
):
    """
    Updates error store, merging messages from ``error``

    Example::

        errors_store = {
            "person": {
                "email": ["is not an email"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"]
            },
            "job": ["is not from allowed values list"]
        }

        add_error_to(errors_store, {"person": {"email": "is from illegal domain"}})

        errors_store == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"]
            },
            "job": ["is not from allowed values list"]
        }

    But, trying to do this::

        add_error_to(errors_store, {"person": "is illegally formed"})

    will add/update ``_schema`` key because ``person`` has child keys and replacing
    them with ``["is illegally formed"]`` would loose that data. Thus,
    ``errors_store`` will look like this now::

        errors_store == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"]
            },
            "job": ["is not from allowed values list"]
        }

    Another example of this behavior::

        add_error_to(errors_store, {"job": {"title": "can't be blank"}})

    will result in::

        errors_store == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"]
            },
            "job": {
                "_schema": ["is not from allowed values list"],
                "title": ["can't be blank"]
            }
        }

    Also, method is smart enough to correctly update errors store with either one or
    a sequence of messages. So both of these are valid::

        add_error_to(errors_store, {"job": {"title": "is overpaid"}})
        add_error_to(errors_store, {"job": {"title": ["is forbiden", "doesn't exist"]}})

        errors_store == {
            "person": {
                "email": ["is not an email", "is from illegal domain"],
                "name": ["is too long"],
                "date_of_birth": ["is not a date"],
                "_schema": ["is illegally formed"]
            },
            "job": {
                "_schema": ["is not from allowed values list"],
                "title": [
                    "can't be blank", "is overpaid", "is forbiden", "doesn't exist"
                ]
            }
        }

    Arguments:

        errors_store: either a dict into which errors will be added or an object. If
            object we expect it to have attribute ``errors`` and that these are a dict.
            If no such attribute exists on given object, we will attach our own.
    """
    _SELF_ERRORS_KEY = "_schema"

    dest = None
    if errors_store is None:
        raise RuntimeError(
            "errors_store can't be None! errors_store must be a dict or object onto "
            "which dict can be attached!"
        )
    elif isinstance(errors_store, abc.Mapping):
        dest = errors_store
    else:
        errors_store.errors = getval(errors_store, "errors", dict())
        dest = errors_store.errors

    data = _normalize_error_data(error)

    if is_blank(data):
        return dest

    if isinstance(data, str):
        dest[_SELF_ERRORS_KEY] = getval(dest, _SELF_ERRORS_KEY, [])
        dest[_SELF_ERRORS_KEY].append(data)
        return dest

    if isinstance(data, list):
        dest[_SELF_ERRORS_KEY] = getval(dest, _SELF_ERRORS_KEY, [])
        dest[_SELF_ERRORS_KEY].extend(data)
        return dest

    for k, v in data.items():
        if is_blank(v):
            continue

        if k in dest:
            if isinstance(dest[k], list):
                if isinstance(v, str):
                    dest[k].append(v)

                elif isinstance(v, list):
                    dest[k].extend(v)

                elif isinstance(v, dict):
                    dest[k] = {_SELF_ERRORS_KEY: dest[k]}
                    add_error_to(dest[k], v)

                else:
                    dest[k].append(str(v))

            else:
                if isinstance(v, str):
                    dest[k][_SELF_ERRORS_KEY] = getval(dest[k], _SELF_ERRORS_KEY, [])
                    dest[k][_SELF_ERRORS_KEY].append(v)

                elif isinstance(v, list):
                    dest[k][_SELF_ERRORS_KEY] = getval(dest[k], _SELF_ERRORS_KEY, [])
                    dest[k][_SELF_ERRORS_KEY].extend(v)

                elif isinstance(v, dict):
                    add_error_to(dest[k], v)

                else:
                    dest[k][_SELF_ERRORS_KEY] = getval(dest[k], _SELF_ERRORS_KEY, [])
                    dest[k][_SELF_ERRORS_KEY].append(str(v))

        else:
            if isinstance(v, str):
                dest[k] = [v]

            elif isinstance(v, list):
                dest[k] = v

            elif isinstance(v, dict):
                dest[k] = dict()
                add_error_to(dest[k], v)

            else:
                dest[k] = [str(v)]

    return dest
