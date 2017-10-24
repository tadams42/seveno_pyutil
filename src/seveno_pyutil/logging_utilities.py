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

import pytz
import tzlocal

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
#: This is to be used as a prefix for your custom logging formats for
#: :class:`logging.handlers.SysLogHandler`.
RFC5424_PREFIX = '1 %(isotime)s %(hostname)s {application_name} %(process)d - - [%(levelname)s]'

#: Logging format prefix suitable for non-syslog loggers.
#: Doesn't use log coloring.
COLORLESS_FILELOG_PREFIX = '%(isotime)s %(hostname)s {application_name}[%(process)d] [%(levelname)s]'

#: Colored logging format prefix suitable for non-syslog loggers.
#: Requires ``colorlog.ColoredFormatter`` to be used as formatter class.
COLORED_FILELOG_PREFIX = '%(isotime)s %(hostname)s {application_name}[%(process)d] [%(log_color)s%(levelname)s%(reset)s]'


class DynamicContextFormatter(logging.Formatter):
    """
    Formatter that prepends logging message with logging context data, but only
    with values in context dict that are not blank.

    Logging context is stored in thread local storage.

    Example:
        >>> import logging
        >>> import sys
        >>> from seveno_pyutil.logging_utilities import DynamicContextFormatter
        >>>
        >>> logger = logging.getLogger('console')
        >>> handler = logging.StreamHandler(stream=sys.stdout)
        >>> handler.setFormatter(
        ...     DynamicContextFormatter(
        ...         fmt=DynamicContextFormatter.PLACEHOLDER + ' %(message)s'
        ...     )
        ... )
        >>> handler.setLevel('DEBUG')
        >>> logger.setLevel('DEBUG')
        >>> logger.addHandler(handler)
        >>>
        >>> DynamicContextFormatter.context()['foo'] = 42
        >>> DynamicContextFormatter.context()['bar'] = 'baz'
        >>> logger.info("Message with context")
         foo: 42, bar: baz, Message with context
        >>>
        >>> DynamicContextFormatter.context()['foo'] = None
        >>> DynamicContextFormatter.context()['bar'] = None
        >>> logger.info("Message without context")
         Message without context
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

    #: Logging format string placeholder
    PLACEHOLDER = '%(dynamic_context_data)s'

    #: When context is logged, add this suffix to it.
    SUFFIX = ','
    PREFIX = ' '

    @property
    def dynamic_context_data(self):
        """Generates data for ``record.dynamic_context_data`` attribute."""
        if reduce(or_, [
            not string_utilities.is_blank(value)
            for value in self.context().values()
        ], False) and self.context():
            return self.PREFIX + ', '.join([
                '{}: {}'.format(key, value)
                for key, value in self.context().items()
                if not string_utilities.is_blank(value)
            ]) + self.SUFFIX
        return ''

    def format(self, record):
        record.dynamic_context_data = self.dynamic_context_data
        return super(DynamicContextFormatter, self).format(record)


def log_http_request(request):
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
    logger.debug(
        "HTTP request headers: %s",
        "{}".format(request.headers).replace("\r\n", " ")
    )

    if (
        getattr(request, "is_json", None) or
        request.headers.get('Content-Type', None) == 'application/json'
    ):
        logger.info("HTTP request payload: %s", request.json)


def log_http_response(for_request, response):
    """
    Log some stuff from HTTP request.

    Known to work with Flask and Django request objects.
    """
    logger.debug(
        "HTTP response headers: %s",
        "{}".format(response.headers).replace("\r\n", " ")
    )

    if (
        getattr(response, 'content_type', None) == 'application/json' or
        response.headers.get('Content-Type', None) == 'application/json'
    ):
        payload = getattr(response, 'json', ''
                         ) or response.data.decode('UTF-8')
        if callable(payload):
            payload = payload()

        if isinstance(payload, str):
            payload = json.loads(payload)

        logger.info("HTTP response payload: %s", payload)

    logger.info(
        "Finished HTTP request: %s %s %s", for_request.method,
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


class SQLFormatter(logging.Formatter):
    """
    Formatter for Django's SQL loggers. Reformats and colorizes queries.
    """
    def __init__(self, colorize_queries=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: not for now
        self.reformat_queries = False
        self.colorize_queries = colorize_queries

    def format(self, record):
        if self.colorize_queries:
            # Check if Pygments is available for coloring
            try:
                import pygments
                from pygments.lexers import SqlLexer
                # from pygments.formatters import TerminalTrueColorFormatter
                from pygments.formatters import Terminal256Formatter
            except ImportError:
                pygments = None
        else:
            pygments = None

        if self.reformat_queries:
            # Check if sqlparse is available for indentation
            try:
                import sqlparse
            except ImportError:
                sqlparse = None
        else:
            sqlparse = None

        # Remove leading and trailing whitespaces
        sql = record.sql.strip()

        if sqlparse:
            # Indent the SQL query
            sql = sqlparse.format(sql, reindent=True)

        if pygments:
            # Highlight the SQL query
            sql = pygments.highlight(
                sql,
                SqlLexer(),
                # TerminalTrueColorFormatter(style='monokai')
                Terminal256Formatter(style='monokai')
            )

        # Set the record's statement to the formatted query

        if not hasattr(record, 'duration'):
            # DDL statements don't have `duration` attribute set by Django
            # loggers. Not much we can do about that
            record.duration = 0

        record.statement = sql.strip()
        return super().format(record)


class ColoredSQLFormatter(SQLFormatter):
    """
    Formatter for Django's SQL logger that colorizes SQL in log. Don't use with
    ``syslog``, it is ugly and wrong. And remember to use ``less -R`` to enjoy.

    Example logging dict config::

        {
            'colored_sql': {
                '()': 'ColoredSQLFormatter',
                'format': '(%(duration).3f) %(statement)s'
            }
        }

    """
    def __init__(self, *args, **kwargs):
        kwargs.pop('colorize_queries', None)
        super().__init__(colorize_queries=True, *args, **kwargs)


class ColorlessSQLFormatter(SQLFormatter):
    """
    Formatter for Django's SQL logger that produces colorless SQL in log.
    Suitable for use with ``syslog``. Example logging dict config::

        {
            'syslog_sql': {
                '()': 'ColorlessSQLFormatter',
                'format': RFC5424_PREFIX + '(%(duration).3f) %(statement)s'
            }
        }

    """
    def __init__(self, *args, **kwargs):
        kwargs.pop('colorize_queries', None)
        super().__init__(colorize_queries=False, *args, **kwargs)


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
