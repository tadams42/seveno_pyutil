from __future__ import annotations

import contextlib
import enum
import json
import logging
import timeit
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pygments
import sqlparse

# from pygments.formatters import TerminalTrueColorFormatter
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

HAS_PSYCOPG2 = False

with contextlib.suppress(Exception):
    HAS_PSYCOPG2 = True


HAS_PSYCOPG3 = True
try:
    import psycopg

except Exception:
    HAS_PSYCOPG3 = False

HAS_FLASK = True
try:
    import flask

except Exception:
    HAS_FLASK = False


class SQLFilter(logging.Filter):
    """
    Filter for SQLAlchemy SQL loggers. Optionally reformats and colorizes queries.

    To use it with Flask and SQLAlchemy:

    - configure Flask app
    - configure SQLAlchemy engine events (call `:meth:register_sqlalchemy_logging_events`)
    - configure logging

    All three steps are presented in example below. After it has been configured,
    provides following logging placeholders:

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

        import flask
        from seveno_pyutil import FlaskSQLStats, SQLFilter

        dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "app": {"format": "lvl=%(levelname)s msg=%(message)s"},
                    "app.db": {
                        "format": "lvl=%(levelname)s, sqld=%(sql_duration)s sql=%(sql)s msg=%(message)s"
                    },
                },
                "filters": {
                    "colored_sql": {
                        "()": "seveno_pyutil.SQLFilter",
                        "colorize_queries": True,
                        "multiline_queries": True,
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "app",
                        "stream": "ext://sys.stdout",
                    },
                    "console_sqlalchemy": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "db",
                        "filters": ["colored_sql"],
                        "stream": "ext://sys.stdout",
                    },
                },
                "loggers": {
                    "myapp": {
                        "level": "INFO",
                        "propagate": False,
                        "handlers": ["console"],
                    },
                    "myapp.db": {
                        "level": "DEBUG",
                        "propagate": False,
                        "handlers": ["console_sqlalchemy"],
                    },
                },
            }
        )


        class RequestLoggingMiddleware:
            def __init__(self, sql_logger_name, app=None):
                self.sql_logger_name = sql_logger_name
                if app:
                    self.init_app(app)

            def init_app(self, app: flask.Flask):
                SQLFilter.register_sqlalchemy_logging_events(self.sql_logger_name)

                @app.before_request
                def log_current_request():
                    FlaskSQLStats.open()

                    @flask.after_this_request
                    def log_current_response(response):
                        logger.info("Some HTTP request was processed :)")
                        FlaskSQLStats.close()
                        return response


        logger = logging.getLogger(__name__)
        app = flask.Flask(__name__)
        RequestLoggingMiddleware("myapp.db").init_app(app)
    """

    @classmethod
    def register_sqlalchemy_logging_events(cls, logger: str | logging.Logger):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        connection_enricher = ConnectionEnricher(logger)

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(  # noqa: PLR0913
            conn,
            cursor,
            statement: str,
            parameters: dict,
            context,
            executemany: bool,  # noqa: FBT001
        ):
            connection_enricher.start(conn)

        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(  # noqa: PLR0913
            conn,
            cursor,
            statement: str,
            parameters: dict,
            context,
            executemany: bool,  # noqa: FBT001
        ):
            connection_enricher.end(conn, cursor, statement, parameters)

        @event.listens_for(Engine, "handle_error")
        def receive_handle_error(exception_context):
            connection_enricher.error(exception_context)

    def __init__(
        self,
        *args,
        colorize_queries=False,
        multiline_queries=False,
        shorten_logs=True,
        **kwargs,
    ):
        self.enricher = RecordEnricher(
            colorize_queries=colorize_queries,
            multiline_queries=multiline_queries,
            shorten_logs=shorten_logs,
        )
        super().__init__(*args, **kwargs)

    def filter(self, record: logging.LogRecord):
        self.enricher.add_attributes(record)
        return super().filter(record)


class ConnectionEnricher:
    _ATTR_START_TIME = "query_start_time"

    def __init__(self, lgr: str | logging.Logger):
        self.lgr: logging.Logger
        if isinstance(lgr, str):
            self.lgr = logging.getLogger(lgr)
        else:
            self.lgr = lgr

    def start(self, conn):
        if conn:
            conn.info.setdefault(self._ATTR_START_TIME, []).append(
                timeit.default_timer()
            )

    def end(self, conn, cursor, statement: str, parameters: dict):
        statement_duration = self._execution_duration(conn)
        FlaskSQLStats.incr_stats(self.lgr, statement_duration)

        compiled = self._compiled_sql(conn, cursor, statement, parameters)

        self.lgr.debug(
            "",
            extra={
                RecordEnricher.ATTR_DATA: SQLRecordedQuery(
                    statement=str(statement),
                    parameters=parameters,
                    duration=statement_duration,
                    compiled=compiled,
                )
            },
        )

    def error(self, exception_context):
        msg = "SQL engine exception detected."

        try:
            msg = msg + " " + str(exception_context.original_exception).strip()
        except Exception:
            msg = "SQL engine exception detected. "

        self.lgr.critical(
            msg,
            extra={
                RecordEnricher.ATTR_DATA: SQLRecordedQuery(
                    statement=str(exception_context.statement),
                    parameters=exception_context.parameters,
                    duration=self._execution_duration(exception_context.connection),
                )
            },
        )

    @classmethod
    def _compiled_sql(cls, conn, cursor, statement, parameters):
        compiled = None

        if HAS_PSYCOPG2:
            with contextlib.suppress(Exception):
                compiled = cursor.mogrify(statement, parameters).decode()

        elif HAS_PSYCOPG3:
            with contextlib.suppress(Exception):
                cc = psycopg.ClientCursor(connection=conn.connection.dbapi_connection)
                compiled = cc.mogrify(statement, parameters)

        # Other drivers would need their own implementation. Since we are not using
        # them, we don't provide one. Returning None here means SQL will be logged
        # separately from it's parameters, ie.
        #   sql=SELECT id, foo FROM foos where foo = %(bar)s; with params {"bar": baz}
        # instead of
        #   sql=SELECT id, foo FROM foos where foo = 'baz'

        return compiled

    @classmethod
    def _execution_duration(cls, conn) -> timedelta:
        data: list[float] = getattr(conn, "info", {}).get(cls._ATTR_START_TIME, [])
        started_at = data.pop(-1) if data else 0
        return timedelta(milliseconds=(timeit.default_timer() - started_at) * 1000.0)


@dataclass
class SQLRecordedQuery:
    statement: str
    parameters: dict
    duration: timedelta
    compiled: str | None = None
    duration_ms: float = field(init=False, default=0)

    def __post_init__(self):
        td = None
        if isinstance(self.duration, int | float | str):
            td = timedelta(microseconds=float(self.duration))
        elif isinstance(self.duration, timedelta):
            td = self.duration
        else:
            td = timedelta()
        self.duration_ms = td.total_seconds() * 1000


class RecordEnricher:
    ATTR_DATA = "_sql"
    ATTR_SQL = "sql"
    ATTR_DURATION = "sql_duration"

    def __init__(
        self, *, colorize_queries=False, multiline_queries=False, shorten_logs=True
    ):
        self.colorize_queries = colorize_queries
        self.multiline_queries = multiline_queries
        self.shorten_logs = shorten_logs

    def add_attributes(self, record: logging.LogRecord):
        setattr(record, self.ATTR_SQL, "")
        setattr(record, self.ATTR_DURATION, "")

        recorded_query: SQLRecordedQuery | None = getattr(record, self.ATTR_DATA, None)
        if not recorded_query:
            return

        query_str = self._format_query_string(recorded_query)
        setattr(record, self.ATTR_SQL, query_str)

        duration_str = self._format_duration_string(recorded_query)
        setattr(record, self.ATTR_DURATION, duration_str)

    def _format_query_string(self, recorded_query: SQLRecordedQuery) -> str:
        if recorded_query.compiled:
            return self._format_compiled(recorded_query.compiled)

        return self._format_statement_and_params(
            recorded_query.statement, recorded_query.parameters
        )

    _SQL_FORMAT_OPTS = {
        "reindent": True,
        "keyword_case": "upper",
        "truncate_strings": 25,
        "reindent_aligned": True,
        "wrap_after": 88,
    }

    def _maybe_multiline(self, sql: str) -> str:
        if sql:
            if self.multiline_queries:
                sql = "\n".join(
                    _.rstrip()
                    for _ in sqlparse.format(sql, **self._SQL_FORMAT_OPTS).splitlines()
                    if _.strip()
                ).strip()
            else:
                sql = " ".join(
                    _.strip()
                    for _ in sqlparse.format(sql, **self._SQL_FORMAT_OPTS).splitlines()
                    if _.strip()
                ).strip()

            if sql and not sql.endswith(";"):
                sql = sql + ";"

        return sql or ""

    def _maybe_colorized(self, sql: str) -> str:
        if self.colorize_queries and sql:
            sql = pygments.highlight(
                sql, SqlLexer(), Terminal256Formatter(style="monokai")
            ).strip()

        return sql or ""

    def _format_compiled(self, compiled: str | None) -> str:
        sql = compiled or ""

        sql = self._maybe_multiline(sql)
        sql = self._maybe_colorized(sql)

        if self.shorten_logs:
            (sql or " SQL")[:1300]

        return sql

    def _format_statement_and_params(
        self, statement: str | None, parameters: dict | None
    ) -> str:
        sql: str = statement or ""

        sql = self._maybe_multiline(sql)
        sql = self._maybe_colorized(sql)

        if parameters:
            params_dict = parameters
            params = json.dumps(params_dict, cls=JSONEncoder).strip()
        else:
            params_dict = {}
            params = ""

        if self.colorize_queries and params:
            params = pygments.highlight(
                params,
                pygments.lexers.get_lexer_for_mimetype("application/json"),
                Terminal256Formatter(style="monokai"),
            ).strip()

        # rsyslogd limits to 2048 bytes per message by default
        # We prefer to lose some params when shortening log line than to lose some SQL
        # statement content. Either way, it is not possible to guarantee both will
        # be fully logged in all contexts and log sinks
        if params and params_dict:
            if self.shorten_logs:
                sql = f"{sql[:1500]} with params {params[:500]}"
            else:
                # params should always be shortened because they can be huge in when
                # for exmple we are inserting into PostgreSQL JSONB columns
                sql = f"{sql} with params {params[:500]}"
        else:
            sql = (sql or " SQL")[:1300]

        return sql

    def _format_duration_string(self, recorded_query: SQLRecordedQuery) -> str:
        dur = "_.___ ms"
        if recorded_query.duration_ms:
            dur = f"{recorded_query.duration_ms:.2f} ms"
        return dur


class FlaskSQLStats:
    _KEY_REQUEST_SQL_STATS = "sqlalchemy_statistics"
    _KEY_SQL_CUMULATIVE_DURATION = "cumulative_duration"
    _KEY_SQL_COUNT = "statements_count"

    @classmethod
    def get_statements_count(cls) -> int:
        stats = cls.get()
        if stats:
            return stats[cls._KEY_SQL_COUNT] or 0
        return 0

    @classmethod
    def get_cumulative_statements_duration(cls) -> timedelta:
        stats = FlaskSQLStats.get()
        if stats:
            return stats[cls._KEY_SQL_CUMULATIVE_DURATION]
        return timedelta()

    @classmethod
    def open(cls) -> dict | None:
        if HAS_FLASK:
            return flask.g.setdefault(cls._KEY_REQUEST_SQL_STATS, {})
        return None

    @classmethod
    def close(cls):
        if HAS_FLASK:
            flask.g.pop(cls._KEY_REQUEST_SQL_STATS)

    @classmethod
    def get(cls) -> dict | None:
        if HAS_FLASK:
            return flask.g.get(cls._KEY_REQUEST_SQL_STATS)
        return None

    @classmethod
    def incr_stats(cls, lgr: logging.Logger, statement_duration: timedelta):
        if HAS_FLASK:
            try:
                data = cls.open()
                data.setdefault(cls._KEY_SQL_CUMULATIVE_DURATION, timedelta())
                data.setdefault(cls._KEY_SQL_COUNT, 0)
                data[cls._KEY_SQL_CUMULATIVE_DURATION] += statement_duration
                data[cls._KEY_SQL_COUNT] += 1

            except Exception:
                lgr.error("Failed to collect SQL statistics!", exc_info=True)


class JSONEncoder(json.JSONEncoder):
    _DATES_TIMES = (date, datetime)

    def default(self, obj):
        if isinstance(obj, self._DATES_TIMES):
            return obj.isoformat()
        if isinstance(obj, enum.Enum):
            return obj.name
        if isinstance(obj, UUID | Decimal | Path):
            return str(obj)
        # return json.JSONEncoder.default(self, obj)
        return str(obj)
