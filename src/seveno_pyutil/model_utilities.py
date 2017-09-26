from collections import defaultdict
from datetime import datetime

from marshmallow import ValidationError


class Validateable(object):
    """Mixin for objects supporting validation through marshmallow schema."""

    def __init__(self):
        self._errors = None

    @property
    def errors(self):
        """Errors dictionary from last validation or None"""
        if not self._errors:
            return None

        return dict(self._errors)

    @property
    def is_valid(self):
        """Calls :meth:`validate` and returns validation result."""

        self.validate()
        return not self._errors

    @property
    def _schema():
        """
        marshmallow Schema used to validate self.

        Note:
            It is allowed to return None in which case validation will report
            schema error.
        """
        raise NotImplementedError(
            "class {} is missing implementation of self._schema!".
            format(self.__class__.__name__)
        )

    def validate(self):
        """
        Validates instance using schema.

        Returns:
            dict: Errors dictionary.
        """
        self._errors = defaultdict(list)
        schema = self._schema
        if schema:
            try:
                json_str, dump_errors = schema.dumps(self)
                # Ignoring dump_errors because they don't contain all
                # validations - this is marshmallows' by-design feature.
                # Instead, we'll try to load it now and use that as errors dict
                data, self._errors = schema.loads(json_str)

            except ValidationError as e:
                for k, v in e.message.items():
                    self._errors[k] = v

            except Exception as e:
                self._errors[self.__class__.__name__].append(str(e))
        else:
            self._errors['{} schema'.format(self.__class__.__name__)
                        ].append('Invalid message_type!')

        return self._errors


class Representable(object):
    """
    Mixin provides generic __repr__ implementation for value object (
    for example: models).

    - prints only public attributes
    - date values are printed as ISO8601
    """

    def _repr_attribute(self, name, value):
        return "{}={}".format(
            name, repr(getattr(value, "isoformat", lambda: value)())
        )

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__, ", ".join([
                self._repr_attribute(name, value)
                for name, value in vars(self).items()
                if not name.startswith('_')
            ])
        )
