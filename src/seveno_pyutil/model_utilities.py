from collections import defaultdict

from marshmallow import ValidationError, fields

from .metaprogramming_helpers import import_string


class IsoTimeField(fields.DateTime):
    def __init__(self, **kwargs):
        kwargs = dict([(k, v) for k, v in kwargs.items() if k != 'format'])
        super().__init__(format='iso', **kwargs)

    def _serialize(self, value, attr, obj):
        if value and hasattr(value, 'microsecond'):
            value = value.replace(microsecond=0)

        return super()._serialize(value, attr, obj)


class ValidateableMixin(object):
    """
    Mixin for objects supporting validation through marshmallow schema.

    Child classes must define ``SCHEMA_CLASS`` as either `str` of `class`
    """

    #: str or class designating marshmallow schema that should be use to
    #: validate instances of this class
    SCHEMA_CLASS = None
    _SCHEMA_INSTANCE = None

    def __init__(self, *args, **kwargs):
        self._errors = None
        super(ValidateableMixin, self).__init__(*args, **kwargs)

    @property
    def errors(self):
        """Errors dictionary from last validation."""
        return self._errors

    @property
    def is_valid(self):
        """Calls :meth:`validate` and returns validation result."""
        self.validate()
        return not self._errors

    @property
    def _schema(self):
        """Instance of marshmallow Schema used to validate self."""
        if not self.SCHEMA_CLASS:
            raise NotImplementedError(
                "SCHEMA_CLASS is not defined. Can't validate {}!".format(
                    self.__class__.__name__
                )
            )

        if not self.__class__._SCHEMA_INSTANCE:
            if isinstance(self.SCHEMA_CLASS, str):
                klass = import_string(self.SCHEMA_CLASS)
            else:
                klass = self.SCHEMA_CLASS
            self.__class__._SCHEMA_INSTANCE = klass()

        return self._SCHEMA_INSTANCE

    def validate(self):
        """
        Validates instance using schema.

        Returns:
            dict: Errors dictionary.
        """
        self._errors = defaultdict(list)

        json_str = None
        try:
            json_str = self._schema.dumps(self)
        except Exception:
            # Ignoring dump_errors because they don't contain all validations -
            # this is marshmallows' by-design feature. Instead, we'll try to
            # load dumped data and use result of that for errors dict
            pass

        try:
            self._schema.loads(json_str)

        except ValidationError as exception:
            self._errors = exception.messages

        except Exception as e:
            self._errors[self.__class__.__name__].append(str(e))

        return self._errors


class RepresentableMixin(object):
    """
    Mixin provides generic __repr__ implementation for value objects (for
    example: models).

    - prints only public attributes
    - date values are printed as ISO8601
    """

    _ONLY_REPR_ATTRIBUTES = None
    _SKIP_REPR_ATTRIBUTES = None

    def _repr_it(self, name, value):
        return "{}={}".format(
            name, repr(getattr(value, "isoformat", lambda: value)())
        )

    @property
    def _attrs_to_repr(self):
        return sorted([
            attr for attr in (
                set(self._ONLY_REPR_ATTRIBUTES or [])
                or (
                    set(vars(self).keys()) -
                    set(self._SKIP_REPR_ATTRIBUTES or [])
                )
            )
            if not attr.startswith('_')
        ])

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__, ", ".join([
                self._repr_it(attr, getattr(self, attr))
                for attr in self._attrs_to_repr
            ])
        )
