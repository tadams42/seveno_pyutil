import logging
import threading
from collections import OrderedDict
from functools import reduce
from operator import or_

from .. import string_utilities

#: RFC-5424 compatible logging format.
#: This is to be used as a _PREFIX for your custom logging formats for
#: :class:`logging.handlers.SysLogHandler`.
RFC5424_PREFIX = '1 %(isotime)s %(hostname)s {application_name} %(process)d - - [%(levelname)s]'

#: Logging format _PREFIX suitable for non-syslog loggers.
#: Doesn't use log coloring.
COLORLESS_FILELOG_PREFIX = '%(isotime)s %(hostname)s {application_name}[%(process)d] [%(levelname)s]'

#: Colored logging format _PREFIX suitable for non-syslog loggers.
#: Requires ``colorlog.ColoredFormatter`` to be used as formatter class.
COLORED_FILELOG_PREFIX = '%(isotime)s %(hostname)s {application_name}[%(process)d] [%(log_color)s%(levelname)s%(reset)s]'


class DynamicContextFilter(logging.Filter):
    """
    Logging filter that renders ``cls.context()``.

    Logging context is stored in thread local storage so it can be modified
    in runtime by any thread.

    This is usefull for ie. prepending ``request_id`` to all messages in
    context of single http request. But, since it doesn't rely on any HTTP
    framework, it is not tied to context of HTTP request only but to any kind
    of repetitive multi step process that needs to connect produced log lines
    into single context.

    This filter will introduce following log format placeholders.

    +-------------------------------------+-----------------------------------+
    | placeholder                         | description                       |
    +-------------------------------------+-----------------------------------+
    | %(dynamic_context_keys_and_values)s | for given context::               |
    |                                     |                                   |
    |                                     |     {'foo': 'bar', 'baz': 42}     |
    |                                     |                                   |
    |                                     | will render placeholder as::      |
    |                                     |                                   |
    |                                     |    foo: bar, baz: 42              |
    |                                     |                                   |
    +-------------------------------------+-----------------------------------+
    | %(dynamic_context_values)s          | for given context::               |
    |                                     |                                   |
    |                                     |     {'foo': 'bar', 'baz': 42}     |
    |                                     |                                   |
    |                                     | will render placeholder as::      |
    |                                     |                                   |
    |                                     |     [bar] [42]                    |
    |                                     |                                   |
    +-------------------------------------+-----------------------------------+

    Example:

        >>> import logging
        >>> import sys
        >>> import uuid
        >>> from logging.config import dictConfig
        >>>
        >>> from seveno_pyutil import logging_utilities
        >>>
        >>> dictConfig({
        ...     'version': 1,
        ...     'disable_existing_loggers': False,
        ...     'formatters': {
        ...         'key_and_values': {
        ...             'format': '%(dynamic_context_keys_and_values)s %(message)s'
        ...         },
        ...         'only_values': {
        ...             'format': '%(dynamic_context_values)s %(message)s'
        ...         }
        ...     },
        ...     'filters': {
        ...         'dynamic_context': {
        ...             '()': logging_utilities.DynamicContextFilter
        ...         }
        ...     },
        ...     'handlers': {
        ...         'console_key_and_values': {
        ...             'class': 'logging.StreamHandler',
        ...             'level': 'DEBUG',
        ...             'formatter': 'key_and_values',
        ...             'filters': ['dynamic_context'],
        ...             'stream': 'ext://sys.stdout'
        ...         },
        ...         'console_only_values': {
        ...             'class': 'logging.StreamHandler',
        ...             'level': 'DEBUG',
        ...             'formatter': 'only_values',
        ...             'filters': ['dynamic_context'],
        ...             'stream': 'ext://sys.stdout'
        ...         },
        ...     },
        ...     'loggers': {
        ...         'foo': {
        ...             'level': 'INFO',
        ...             'propagate': True,
        ...             'handlers': ['console_key_and_values']
        ...         },
        ...         'bar': {
        ...             'level': 'INFO',
        ...             'propagate': True,
        ...             'handlers': ['console_only_values']
        ...         }
        ...     }
        ... })
        >>>
        >>> logger_foo = logging.getLogger('foo')
        >>> logger_bar = logging.getLogger('bar')
        >>>
        >>> logging_utilities.DynamicContextFilter.context().update({
        ...     # 'request_id': uuid.uuid4()
        ...     'request_id': 'f67d41a0-8188-4294-b8a4-d20d8edfdc95'
        ... })
        >>> logger_foo.info('Message1')
         request_id: f67d41a0-8188-4294-b8a4-d20d8edfdc95, Message1
        >>> logger_bar.info('Message2')
         [f67d41a0-8188-4294-b8a4-d20d8edfdc95] Message2
        >>> logging_utilities.DynamicContextFilter.clear_context()
        >>> logger_foo.info('Message3')
         Message3
        >>> logger_bar.info('Message4')
         Message4
        >>>

    Warning:
        This filter assumes and provides global logging context per thread. In cases
        where there are multiple context holders in single thread it won't work. In
        these cases it is necessary to utilize ordinary local context dict and use
        standard way of passing it to log records via::

            logger.foo(..., extra=context_dict)

        or via own filter and::

            logger = logging.getLogger(__name__)
            my_context_dict = {'foo': 'val'}
            logger = logging.LoggerAdapter(logger, context_dict)
    """

    _LOGGING_CONTEXT = threading.local()

    @classmethod
    def context(cls):
        """Thread local logging context storage."""
        if not hasattr(cls._LOGGING_CONTEXT, 'data'):
            cls._LOGGING_CONTEXT.data = OrderedDict()
        return cls._LOGGING_CONTEXT.data

    @classmethod
    def clear_context(cls):
        if hasattr(cls._LOGGING_CONTEXT, 'data'):
            for key in cls._LOGGING_CONTEXT.data.keys():
                cls._LOGGING_CONTEXT.data[key] = None

    LOG_TAGS_KEYS_AND_VALUES = '%(dynamic_context_keys_and_values)s'
    LOG_TAGS_ONLY_VALUES = '%(dynamic_context_values)s'

    #: When context is logged, add this _SUFFIX to it.
    _SUFFIX = ','
    _KEY_VALUE_SEPARATOR = ', '
    _PREFIX = ' '

    @property
    def has_any_context(self):
        return self.context() and reduce(
            or_,
            [
                not string_utilities.is_blank(value)
                for value in self.context().values()
            ], False
        )

    @property
    def dynamic_context_keys_and_values(self):
        """
        Generates data for ``record.dynamic_context_keys_and_values``
        attribute.
        """
        if self.has_any_context:
            return (
                self._PREFIX
                + self._KEY_VALUE_SEPARATOR.join(
                    '{}: {}'.format(key, value)
                    for key, value in self.context().items()
                    if not string_utilities.is_blank(value)
                )
                + self._SUFFIX
            )
        return ''

    @property
    def dynamic_context_values(self):
        if self.has_any_context:
            return (
                self._PREFIX
                + ' '.join(
                    '[' + str(value) + ']'
                    for value in self.context().values()
                    if not string_utilities.is_blank(value)
                )
            )
        return ''

    def filter(self, record):
        record.dynamic_context_keys_and_values = \
            self.dynamic_context_keys_and_values
        record.dynamic_context_values = self.dynamic_context_values

        return super(DynamicContextFilter, self).filter(record)
