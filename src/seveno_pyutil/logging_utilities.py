import json
import logging
import socket
import sys
import threading
import time
import traceback
from collections import OrderedDict
from datetime import datetime
from functools import reduce
from logging import NullHandler
from operator import or_

import colorlog
import pygments
import pytz
import sqlparse
import tzlocal
# from pygments.formatters import TerminalTrueColorFormatter
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

from . import string_utilities

logger = logging.getLogger(__name__)


class StandardMetadataFilter(logging.Filter):
    """
    Filter that adds few more attributes to log records.

    +-------------------+----------------------------------------------+
    | placeholder       | description                                  |
    +-------------------+----------------------------------------------+
    | %(hostname)s      | hostname                                     |
    +-------------------+----------------------------------------------+
    | %(isotime)s       | Local time represented as ISO8601            |
    +-------------------+----------------------------------------------+
    | %(isotime_utc)s   | local time converted to UTC and represented  |
    |                   | as ISO8601 string                            |
    +-------------------+----------------------------------------------+
    """

    try:
        _HOSTNAME = socket.gethostname()
    except Exception as exception:
        _HOSTNAME = '-'

    _LOCAL_TZ = tzlocal.get_localzone()

    def filter(self, record):
        # Note that naive datetime will not be exported correctly to isoformat:
        #   datetime.now().isoformat()
        #   '2017-05-22T13:51:49.336335'
        # but we don't have this problem because we make sure that here we
        # always have tzinfo on datetime object
        dt = self._LOCAL_TZ.localize(datetime.fromtimestamp(record.created))
        record.isotime = dt.isoformat()
        record.isotime_utc = dt.astimezone(pytz.utc).isoformat()

        record.hostname = self._HOSTNAME

        return super(StandardMetadataFilter, self).filter(record)


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


def _colored_json(data):
    try:
        if isinstance(data, dict):
            json_str = json.dumps(data)
        else:
            json_str = None
    except Exception:
        json_str = None

    if not json_str:
        return data

    return pygments.highlight(
        json_str,
        pygments.lexers.get_lexer_for_mimetype('application/json'),
        Terminal256Formatter(style='monokai')
    )

    return data


def log_http_request(request, colorized=False):
    """
    Log some stuff from HTTP request.

    Known to work with Flask and Django request objects.
    """

    # Requests received by local Flask will have "path" and "url".
    # Requests outgoing from local Flask to some other service will have only
    # "url".
    destination = (
        getattr(request, "path", None) or getattr(request, "url", None)
    )

    logger.info("Started HTTP request %s: %s", request.method, destination)

    headers = ((k.strip(), v.strip()) for k, v in request.headers)

    logger.debug(
        "HTTP request headers: %s", (
            _colored_json(dict(headers))
            if colorized else json.dumps(dict(headers))
        ).strip()
    )

    if (
        getattr(request, "is_json", None)
        or request.headers.get('Content-Type', None) == 'application/json'
    ):
        logger.info(
            "HTTP request payload: %s",
            _colored_json(request.json).strip() if colorized
            else str(request.json).strip()
        )


def log_http_response(
    for_request, response, colorized=False, response_metrics=None
):
    """
    Log some stuff from HTTP request.

    Known to work with Flask and Django request objects.
    """

    headers = ((k.strip(), v.strip()) for k, v in response.headers)

    logger.debug(
        "HTTP response headers: %s", (
            _colored_json(dict(headers))
            if colorized else json.dumps(dict(headers))
        ).strip()
    )

    if (
        getattr(response, 'content_type', None) == 'application/json'
        or response.headers.get('Content-Type', None) == 'application/json'
    ):
        payload = getattr(response, 'json', ''
                         ) or response.data.decode('UTF-8')

        if callable(payload):
            payload = payload()

        if isinstance(payload, str):
            payload = json.loads(payload)

        logger.info(
            "HTTP response payload: %s", (
                _colored_json(dict(payload))
                if colorized else json.dumps(dict(payload))
            ).strip()
        )

    if response_metrics:
        logger.info(
            "Completed %s %s %s %s", for_request.method,
            getattr(for_request, "path", None)
            or getattr(for_request, "url", None),
            getattr(response, 'status', None)
            or getattr(response, 'status_code', None),
            (
                _colored_json(dict(response_metrics))
                if colorized else json.dumps(dict(response_metrics))
            ).strip()
        )
    else:
        logger.info(
            "Completed %s %s %s", for_request.method,
            getattr(for_request, "path", None)
            or getattr(for_request, "url", None),
            getattr(response, 'status', None)
            or getattr(response, 'status_code', None)
        )

    return response


def silence_logger(logger):
    """
    For given logger, replaces all its handlers with
    :class:`logging.NullHandler`.
    """
    while logger.handlers:
        logger.removeHandler(logger.handlers[0])

    logger.addHandler(NullHandler())


def log_traceback_single_log(logger_callable):
    logger_callable(
        traceback.format_exc().replace('\n', '\\n')
    )


def log_traceback_multiple_logs(logger_callable):
    for line in traceback.format_exc().split('\n'):
        logger_callable(line)


class SQLFilter(logging.Filter):
    """
    Filter for Django's and SQLAlchemy SQL loggers. Reformats and colorizes
    queries.

    To use it with Django, add it to ``django.db.backends`` and
    ``django.db.backends.schema`` loggers.

    To use it with SQLAlchemy, add it to ``sqlalchemy.engine`` logger.

    For convenience and for use in ``logging.config.dictConfig`` there are also
    `.ColoredSQLFilter` and `.ColorlessSQLFilter`

    Filter supports following loging placeholders:

    +-------------------+----------------------------------------------+
    | placeholder       | description                                  |
    +-------------------+----------------------------------------------+
    | %(statement)s     | SQL statement being executed (SQLAlchemy)    |
    |                   | or that was executed (Django)                |
    +-------------------+----------------------------------------------+
    | %(duration)s      | Duration of SQL execution in [ms]            |
    +-------------------+----------------------------------------------+
    """
    def __init__(self, colorize_queries=True, *args, **kwargs):
        super(SQLFilter, self).__init__(*args, **kwargs)
        self.colorize_queries = colorize_queries

    def filter(self, record):
        if not hasattr(record, 'sql'):
            # SQLAlchemy logger puts SQL statements into ``record.msg``.
            sql = record.getMessage().strip()
        else:
            # Django ORM logger puts SQL statements into ``record.sql``.
            sql = record.sql.strip()

        # SQLAlchemy logger creates two types of log records: one with SQL
        # statements which is followed by another that has query parameters
        if sql.startswith('{'):
            try:
                params_json = json.loads(sql.replace("'", '"'))
            except Exception:
                params_json = None

            if self.colorize_queries and params_json:
                sql = 'Query parameters: ' + _colored_json(params_json)
            else:
                sql = 'Query parameters: ' + sql
        else:
            sql = ' '.join(
                l.strip()
                for l in sqlparse.format(
                    sql, reindent=True, keyword_case='upper'
                ).splitlines()
            )

            if self.colorize_queries:
                sql = pygments.highlight(
                    sql, SqlLexer(), Terminal256Formatter(style='monokai')
                )

        record.statement = sql.strip()

        # Django ORM only measures DML statements SQLAlchemy doesn't measure
        # any statemens - it logs them before they are executed.
        if hasattr(record, 'duration'):
            record.duration = "{:.3f}ms".format(record.duration)
        else:
            record.duration = '_.___ms'

        return super(SQLFilter, self).filter(record)


class ColoredSQLFilter(SQLFilter):
    """Filter for Django's SQL logger that colorizes SQL in log.

    Don't use with ``syslog``, it is ugly and wrong. And remember to use
    ``less -R`` to enjoy.

    Example:

        # logging.config.dictConfig
        {"filters": {"sql": {'()': 'ColoredSQLFilter'}}}
    """
    def __init__(self, *args, **kwargs):
        kwargs.pop('colorize_queries', None)
        super(ColoredSQLFilter, self).__init__(
            colorize_queries=True, *args, **kwargs
        )


class ColorlessSQLFilter(SQLFilter):
    """Filter for Django's SQL logger that produces colorless SQL in log.

    Suitable for use with ``syslog``.

    Example:

        # logging.config.dictConfig
        {"filters": {"sql": {'()': 'ColorlessSQLFilter'}}}
    """
    def __init__(self, *args, **kwargs):
        kwargs.pop('colorize_queries', None)
        super(ColorlessSQLFilter, self).__init__(
            colorize_queries=False, *args, **kwargs
        )


def log_to_console_for(logger_name):
    """
    Sometimes, usually during development, we want to quickly see output of
    some particular package logger. This method will configure such logger
    to spit stuff out to console.
    """

    logger = logging.getLogger(logger_name)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)


def log_to_tmp_file_for(logger_name, file_path='/tmp/seveno_pyutil.log'):
    """
    Quick setup for given logger directing it to ``/tmp/seveno_pyutil.log``
    This is of course mainly used during development, especially when playing
    with things in Python console.
    """

    logger = logging.getLogger(logger_name)

    handler = logging.FileHandler(filename=file_path)
    handler.setLevel(logging.DEBUG)

    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)


class SingleLineFormatter(logging.Formatter):
    """
    logging.Formatter that escapes all new lines forcing log record to be
    logged as single line.
    """
    def format(self, record):
        return super(SingleLineFormatter, self).format(record).replace(
            '\n', '\\n'
        )


class SingleLineColoredFormatter(colorlog.ColoredFormatter):
    """
    logging.Formatter that escapes all new lines forcing log record to be
    logged as single line.
    """
    def format(self, record):
        return super(SingleLineColoredFormatter, self).format(record).replace(
            '\n', '\\n'
        )
