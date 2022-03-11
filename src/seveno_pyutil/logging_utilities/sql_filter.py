import enum
import logging
import timeit
from datetime import date, datetime, timedelta

import pygments
import sqlparse

# from pygments.formatters import TerminalTrueColorFormatter
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

try:
    import simplejson as json
except Exception:
    import json


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, enum.Enum):
            return o.name
        return super().default(o)


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

    KEY_SQL_CUMULATIVE_DURATION = "cumulative_duration"
    KEY_SQL_COUNT = "statements_count"

    @classmethod
    def register_sqlalchemy_logging_events(
        cls, logger, duration_threshold_ms=None, statistics_ctx_get=None
    ):
        """
        Must be called when logging SQLAlchemy statements and durations.

        Arguments:
            logger: name of logger or logging.Logger instance that will be used to log
                SQL messages.
            duration_threshold_ms: If given, only queries lasting longer than this
                threshold will be logged.
            statistics_ctx_get: callable that returns mutable dict. If given, then each
                time SQL query is executes, this dict will be updated.

                It can be used for example in Flask to track SQL execution statistics
                during one HTTP request::

                    import flask
                    from seveno_pyutil import register_sqlalchemy_logging_events

                    def sqlalchemy_stats():
                        return flask.g.setdefault("sqlalchemy_statistics", {})

                    register_sqlalchemy_logging_events(
                        "may_app_sql_logger", statistics_ctx_get=sqlalchemy_stats
                    )

                    @flask.before_request
                    def track_sqlalchemy():
                        @flask.after_this_request
                        def log_sqlalchemy_stats(response):
                            logger.info(
                                "SQLAlchemy statistics for request %s",
                                sqlalchemy_stats()
                            )
                            flask.g["sqlalchemy_statistics"] = {}
        """

        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        _logger = logger
        if isinstance(logger, str):
            _logger = logging.getLogger(logger)

        if duration_threshold_ms is not None and not isinstance(
            duration_threshold_ms, timedelta
        ):
            duration_threshold_ms = timedelta(milliseconds=duration_threshold_ms)

        def duration_ms(conn):
            return timedelta(
                milliseconds=(
                    timeit.default_timer() - conn.info["query_start_time"].pop(-1)
                )
                * 1000.0
            )

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(timeit.default_timer())

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            statement_duration = duration_ms(conn)

            warned = False
            if (
                duration_threshold_ms is not None
                and statement_duration >= duration_threshold_ms
            ):
                _logger.warning(
                    "Detected SQL query running longer than {:.2f} ms! ".format(
                        duration_threshold_ms.total_seconds() * 1000
                    ),
                    extra={
                        "sql_statement": str(statement),
                        "sql_parameters": str(parameters),
                        "sql_duration_ms": statement_duration.total_seconds() * 1000,
                    },
                )
                warned = True

            if not warned and statement_duration is not None:
                _logger.debug(
                    "",
                    extra={
                        "sql_statement": str(statement),
                        "sql_parameters": str(parameters),
                        "sql_duration_ms": statement_duration.total_seconds() * 1000,
                    },
                )

            if statistics_ctx_get:
                try:
                    data = statistics_ctx_get()
                    data.setdefault(cls.KEY_SQL_CUMULATIVE_DURATION, timedelta())
                    data.setdefault(cls.KEY_SQL_COUNT, 0)
                    data[cls.KEY_SQL_CUMULATIVE_DURATION] += statement_duration
                    data[cls.KEY_SQL_COUNT] += 1

                except Exception:
                    _logger.error("Failed to collect SQL statistics!", exc_info=True)

        @event.listens_for(Engine, "handle_error")
        def receive_handle_error(exception_context):
            _logger.critical(
                "",
                extra={
                    "sql_statement": str(exception_context.statement),
                    "sql_parameters": str(exception_context.parameters),
                    "sql_duration_ms": duration_ms(
                        exception_context.connection
                    ).total_seconds()
                    * 1000,
                },
            )

    def __init__(
        self,
        colorize_queries=False,
        multiline_queries=False,
        shorten_logs=True,
        *args,
        **kwargs
    ):
        self.colorize_queries = colorize_queries
        self.multiline_queries = multiline_queries
        self.shorten_logs = shorten_logs
        super().__init__(*args, **kwargs)

    def filter(self, record):
        sql = (
            # SQLAlchemy
            getattr(record, "sql_statement", None)
            # Django
            or getattr(record, "sql", None)
            or ""
        )

        if sql:
            if self.multiline_queries:
                sql = sqlparse.format(sql, reindent=True, keyword_case="upper").strip()
            else:
                sql = " ".join(
                    l.strip()
                    for l in sqlparse.format(
                        sql, reindent=True, keyword_case="upper"
                    ).splitlines()
                ).strip()

            if sql and not sql.endswith(";"):
                sql = sql + ";"

        if hasattr(record, "sql_parameters"):
            params_dict = record.sql_parameters
            params = json.dumps(record.sql_parameters, cls=JsonEncoder).strip()
        else:
            params_dict = {}
            params = ""

        if self.colorize_queries:
            if sql:
                sql = pygments.highlight(
                    sql, SqlLexer(), Terminal256Formatter(style="monokai")
                ).strip()

            if params:
                params = pygments.highlight(
                    params,
                    pygments.lexers.get_lexer_for_mimetype("application/json"),
                    Terminal256Formatter(style="monokai"),
                ).strip()

        # rsyslogd limits to 2048 bytes per message by default
        # We prefer to lose some params when shortening log line than to lose some SQL
        # statement content. Either way, it is not possible to guarnatee both will
        # be fully logged in all contexts and log sinks
        if params and params_dict:
            if self.shorten_logs:
                record.sql = "{} with params {}".format(sql[:1500], params[:500])
            else:
                # params should always be shortened because they can be huge in when
                # for exmple we are inserting into PostgreSQL JSONB columns
                record.sql = "{} with params {}".format(sql, params[:500])
        else:
            record.sql = (sql or "SQL")[:1300]

        duration = getattr(record, "sql_duration_ms", None) or getattr(
            record, "duration", None
        )

        if duration:
            record.sql_duration = "{:.2f} ms".format(duration)
        else:
            record.sql_duration = "_.___ ms"

        return super().filter(record)
