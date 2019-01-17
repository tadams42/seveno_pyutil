try:
    import simplejson as json
except Exception:
    import json

import logging
import timeit

import pygments
import sqlparse
# from pygments.formatters import TerminalTrueColorFormatter
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

from .. import string_utilities


class SQLFilter(logging.Filter):
    """
    Filter for Django's and SQLAlchemy SQL loggers. Reformats and colorizes
    queries.

    To use it with Django:

    - add it to ``django.db.backends`` and ``django.db.backends.schema``
      loggers
    - remove ``%(message)s`` from log format because it will cause to double
      emit each SQL statement. Use this filter's placeholder's instead.

    To use it with SQLAlchemy:

    - add it to ``sqlalchemy.engine`` logger and call
      `:meth:register_sqlalchemy_logging_events`

    Supports following loging placeholders:

    +-------------------+----------------------------------------------+
    | placeholder       | description                                  |
    +-------------------+----------------------------------------------+
    | %(sql)s           | Formatted SQL statement that was executed    |
    +-------------------+----------------------------------------------+
    | %(sql_duration)s  | Formatted duration of SQL execution          |
    +-------------------+----------------------------------------------+

    Arguments:
        colorize_queries(bool): Should apply shell coloring escape sequences to
            formatted SQL?
        multiline_queries(bool): Should emit SQL as indented, multiline of
            single line log statements? In development it is usually nice to
            have it be `True`. In production environments, multiline logs are
            pain and should be avoided.

    Example::

        import logging
        from logging.config import dictConfig

        from seveno_pyutil import SQLFilter

        try:
            import sqlalchemy
            SQLFilter.register_sqlalchemy_logging_events('myapp.db')
        except ImportError:
            pass

        dictConfig({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'django_sql': {'format': '(%(sql_duration)s) %(sql)s'},
                'sqlalchemy_sql': {'format': '(%(sql_duration)s) %(sql)s %(message)s'}
            },
            'filters': {
                'colored_sql': {
                    '()': 'seveno_pyutil.SQLFilter'
                    'colorize_queries': True,
                    'multiline_queries': True,
                }
            },
            'handlers': {
                'console_django': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'django_sql',
                    'filters': ['colored_sql'],
                    'stream': 'ext://sys.stdout'
                },
                'console_sqlalchemy': {
                    'class': 'logging.StreamHandler',
                    'level': 'DEBUG',
                    'formatter': 'sqlalchemy_sql',
                    'filters': ['colored_sql'],
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'myapp.db': {
                    'level': 'DEBUG',
                    'propagate': False,
                    'handlers': ['console_sqlalchemy']
                },
                'django.db.backends': {
                    'level': 'DEBUG',
                    'propagate': False,
                    'handlers': ['console_django']
                },
                'django.db.backends.schema': {
                    'level': 'DEBUG',
                    'propagate': False,
                    'handlers': ['console_django']
                }
            }
        })

    """
    @classmethod
    def register_sqlalchemy_logging_events(cls, logger):
        """Must be called when logging SQLAlchemy statements and durations."""

        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        _logger = logger
        if isinstance(logger, str):
            _logger = logging.getLogger(logger)

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault(
                'query_start_time', []).append(timeit.default_timer()
            )

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            _logger.debug("", extra={
                'sql_statement': statement,
                'sql_parameters': parameters,
                'sql_duration_ms': (
                    timeit.default_timer()
                    - conn.info['query_start_time'].pop(-1)
                ) * 1000
            })

        @event.listens_for(Engine, "handle_error")
        def receive_handle_error(exception_context):
            _logger.critical("", extra={
                'sql_statement': exception_context.statement,
                'sql_parameters': exception_context.parameters,
                'sql_duration_ms': (
                    timeit.default_timer()
                    - exception_context.connection.info['query_start_time'].pop(-1)
                ) * 1000
            })

    def __init__(
        self, colorize_queries=False, multiline_queries=False, *args, **kwargs
    ):
        self.colorize_queries = colorize_queries
        self.multiline_queries = multiline_queries
        super(SQLFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        sql = (
            # SQLAlchemy
            getattr(record, 'sql_statement', None)
            # Django
            or getattr(record, 'sql', None)
            or ""
        )

        if sql:
            if self.multiline_queries:
                sql = sqlparse.format(
                    sql, reindent=True, keyword_case='upper'
                ).strip()
            else:
                sql = ' '.join(
                    l.strip()
                    for l in sqlparse.format(
                        sql, reindent=True, keyword_case='upper'
                    ).splitlines()
                ).strip()

            if sql and not sql.endswith(';'):
                sql = sql + ';'

        if hasattr(record, 'sql_parameters'):
            params_dict = record.sql_parameters
            params = json.dumps(
                record.sql_parameters,
                cls=string_utilities.JSONEncoderWithDateTime
            ).strip()
        else:
            params_dict = {}
            params = ""

        if self.colorize_queries:
            if sql:
                sql = pygments.highlight(
                    sql, SqlLexer(), Terminal256Formatter(style='monokai')
                ).strip()

            if params:
                params = pygments.highlight(
                    params,
                    pygments.lexers.get_lexer_for_mimetype('application/json'),
                    Terminal256Formatter(style='monokai')
                ).strip()

        if params and params_dict:
            record.sql = "{} with params {}".format(sql, params)
        else:
            record.sql = sql or 'SQL'

        duration = (
            getattr(record, 'sql_duration_ms', None)
            or getattr(record, 'duration', None)
        )

        if duration:
            record.sql_duration = "{:.3f} ms".format(duration)
        else:
            record.sql_duration = '_.___ ms'

        return super().filter(record)
