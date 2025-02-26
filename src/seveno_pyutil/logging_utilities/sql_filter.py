from __future__ import annotations

import contextlib
import enum
import json
import logging
import timeit
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pygments
import sqlglot

# from pygments.formatters import TerminalTrueColorFormatter
from pygments.formatters import Terminal256Formatter
from pygments.lexers import SqlLexer

HAS_PSYCOPG2 = True
try:
    import psycopg2  # noqa: F401
except Exception:
    HAS_PSYCOPG2 = False

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

HAS_SQLALCHEMY = True
try:
    import sqlalchemy  # noqa: F401
    from sqlalchemy import event
    from sqlalchemy.engine import Connection, Engine
except Exception:
    HAS_SQLALCHEMY = False


def _raise_if_missing_dependencies():
    missing_deps = []
    if not HAS_PSYCOPG2 and not HAS_PSYCOPG3:
        missing_deps.append("psycopg2 or psycopg")
    if not HAS_FLASK:
        missing_deps.append("flask")
    if not HAS_SQLALCHEMY:
        missing_deps.append("sqlalchemy")
    if missing_deps:
        raise ImportError(f"SQLFilter requires following packages: {[missing_deps]}!")


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
        connection_enricher = ConnectionEnricher(logger)

        # https://docs.sqlalchemy.org/en/20/core/events.html#sqlalchemy.events.ConnectionEvents.before_cursor_execute
        @event.listens_for(Engine, "before_cursor_execute")  # type: ignore
        def before_cursor_execute(  # noqa: PLR0913
            conn: Connection,
            cursor,
            statement: str,
            parameters: dict | tuple | list | None,
            context,
            executemany: bool,  # noqa: FBT001
        ):
            connection_enricher.on_start(conn=conn, statement=statement)

        @event.listens_for(Engine, "after_cursor_execute")  # type: ignore
        def after_cursor_execute(  # noqa: PLR0913
            conn: Connection,
            cursor,
            statement: str,
            parameters: dict | tuple | list | None,
            context,
            executemany: bool,  # noqa: FBT001
        ):
            connection_enricher.on_end(conn, cursor, statement, parameters, executemany)

        @event.listens_for(Engine, "handle_error")  # type: ignore
        def receive_handle_error(exception_context):
            connection_enricher.on_error(exception_context)

    def __init__(
        self,
        *args,
        colorize_queries=False,
        multiline_queries=False,
        shorten_logs=True,
        **kwargs,
    ):
        _raise_if_missing_dependencies()

        self.enricher = RecordEnricher(
            colorize_queries=colorize_queries,
            multiline_queries=multiline_queries,
            shorten_logs=shorten_logs,
        )
        super().__init__(*args, **kwargs)

    def filter(self, record: logging.LogRecord):
        self.enricher.add_attributes(record)
        return super().filter(record)


@dataclass
class SQLRecordedQuery:
    # Compiled SQL statement
    duration_ms: float
    compiled_sql: str | None = None
    statement: str | None = None
    parameters: list | tuple | dict | None = None


class ConnectionEnricher:
    _KEY_CONNECTION_INFO_STORAGE = "sql_filter_data"
    _KEY_STARTED_AT = "query_start_time"

    def __init__(self, lgr: str | logging.Logger):
        self.lgr: logging.Logger
        if isinstance(lgr, str):
            self.lgr = logging.getLogger(lgr)
        else:
            self.lgr = lgr

    def on_start(self, conn: Connection, statement: str):
        if conn:
            conn.info.setdefault(self._KEY_CONNECTION_INFO_STORAGE, {})
            key = self._statement_hash(statement)
            conn.info[self._KEY_CONNECTION_INFO_STORAGE][key] = {
                self._KEY_STARTED_AT: timeit.default_timer()
            }

    def on_end(
        self,
        conn: Connection,
        cursor,
        statement: str,
        parameters: dict | tuple | list | None,
        executemany: bool,  # noqa: FBT001
    ):
        key = self._statement_hash(statement)
        duration = self._execution_duration(conn, key)
        FlaskSQLStats.incr_stats(self.lgr, duration)

        if self.lgr.level <= logging.DEBUG:
            compiled = None
            with contextlib.suppress(Exception):
                compiled = self._compiled_sql(
                    conn=conn, cursor=cursor, statement=statement, parameters=parameters
                )

            self.lgr.debug(
                "",
                extra={
                    RecordEnricher.ATTR_DATA: SQLRecordedQuery(
                        compiled_sql=compiled,
                        duration_ms=duration.total_seconds() * 1000,
                        statement=statement,
                        parameters=parameters,
                    )
                },
            )

    def on_error(self, exception_context):
        msg = "SQL engine exception detected."
        with contextlib.suppress(Exception):
            msg = msg + " " + str(exception_context.original_exception).strip()

        connection: Connection | None = None
        with contextlib.suppress(Exception):
            connection = exception_context.connection

        statement: str | None = None
        with contextlib.suppress(Exception):
            statement = exception_context.statement

        parameters: list | tuple | dict | None = None
        with contextlib.suppress(Exception):
            parameters = exception_context.parameters

        cursor = None
        with contextlib.suppress(Exception):
            cursor = exception_context.cursor

        key = None
        if statement:
            key = self._statement_hash(statement)

        duration = timedelta(milliseconds=0)
        if key and connection:
            duration = self._execution_duration(connection, key)
            FlaskSQLStats.incr_stats(self.lgr, duration)

        compiled: str | None = None
        with contextlib.suppress(Exception):
            compiled = self._compiled_sql(
                conn=connection,
                cursor=cursor,
                statement=statement,
                parameters=parameters,
            )

        self.lgr.critical(
            msg,
            extra={
                RecordEnricher.ATTR_DATA: SQLRecordedQuery(
                    compiled_sql=compiled,
                    duration_ms=duration.total_seconds() * 1000,
                    statement=statement,
                    parameters=parameters,
                )
            },
        )

    @classmethod
    def _statement_hash(cls, statement: str):
        # Good enough
        return hash(statement)

    @classmethod
    def _execution_duration(cls, conn: Connection, key) -> timedelta:
        data: dict = conn.info.get(cls._KEY_CONNECTION_INFO_STORAGE, {})
        started_at_data = data.pop(key, {})
        started_at = started_at_data.get(cls._KEY_STARTED_AT, 0)
        return timedelta(milliseconds=(timeit.default_timer() - started_at) * 1000.0)

    @classmethod
    def _compiled_sql(
        cls,
        conn: Connection | None,
        cursor,
        statement: str | None,
        parameters: list | tuple | dict | None,
    ) -> str | None:
        compiled = None

        if HAS_PSYCOPG2 and conn and statement:
            with contextlib.suppress(Exception):
                if not cursor:
                    # happens when DB driver encounters errors ...
                    # ... but we'd still like to try to compile statement
                    new_conn = conn.engine.pool.connect()
                    compiled = new_conn.cursor().mogrify(statement, parameters).decode()
                    # returns connection to pool
                    new_conn.close()

                else:
                    compiled = cursor.mogrify(statement, parameters).decode()

        elif HAS_PSYCOPG3 and conn and statement:
            with contextlib.suppress(Exception):
                cc = psycopg.ClientCursor(connection=conn.connection.dbapi_connection)  # type: ignore
                compiled = cc.mogrify(statement, parameters)  # type: ignore

        return compiled


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
        if recorded_query.compiled_sql:
            return self._format_compiled(recorded_query.compiled_sql)

        return self._format_non_compiled(
            recorded_query.statement, recorded_query.parameters
        )

    def _format_compiled(self, compiled: str) -> str:
        if self.multiline_queries:
            formatted = None
            # Avoid stuff that sqlglot still doesn't support
            # ie. `RELEASE SAVEPOINT foobar` in PostgreSQL
            with contextlib.suppress(Exception):
                formatted = sqlglot.transpile(
                    compiled,
                    read="postgres",
                    write="postgres",
                    pretty=True,
                    normalize_functions="upper",
                    leading_comma=True,
                    max_text_width=240,
                    comments=False,
                )[0]
            if formatted:
                compiled = formatted

        if self.colorize_queries:
            compiled = pygments.highlight(
                compiled, SqlLexer(), Terminal256Formatter(style="monokai")
            ).strip()

        if self.shorten_logs:
            (compiled or " SQL")[:1300]

        return compiled

    def _format_non_compiled(
        self, statement: str | None, parameters: list | tuple | dict | None
    ) -> str:
        sql: str = statement or ""

        if self.colorize_queries:
            sql = pygments.highlight(
                sql, SqlLexer(), Terminal256Formatter(style="monokai")
            ).strip()

        parameters_str: str = ""
        if parameters:
            parameters_str = json.dumps(parameters, cls=JSONEncoder)

            if self.colorize_queries:
                parameters_str = pygments.highlight(
                    parameters_str,
                    pygments.lexers.get_lexer_for_mimetype("application/json"),  # type: ignore
                    Terminal256Formatter(style="monokai"),
                ).strip()

        # rsyslogd limits to 2048 bytes per message by default We prefer to lose some
        # params when shortening log line than to lose some SQL statement content.
        # Either way, it is not possible to guarantee both will be fully logged in all
        # contexts and log sinks
        if self.shorten_logs:
            if len(parameters_str) > 202:  # noqa: PLR2004
                parameters_str = parameters_str[:100] + " ... " + parameters_str[-100:]

            if len(sql) > 1500:  # noqa: PLR2004
                sql = sql[:1500]

        if sql and parameters_str:
            sql = f"{sql}; with params: {parameters_str}"

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
    def open(cls) -> dict:
        return flask.g.setdefault(cls._KEY_REQUEST_SQL_STATS, {})  # type: ignore

    @classmethod
    def close(cls):
        flask.g.pop(cls._KEY_REQUEST_SQL_STATS)  # type: ignore

    @classmethod
    def get(cls) -> dict | None:
        return flask.g.get(cls._KEY_REQUEST_SQL_STATS)  # type: ignore

    @classmethod
    def incr_stats(cls, lgr: logging.Logger, statement_duration: timedelta):
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

    def default(self, o) -> str:
        if isinstance(o, self._DATES_TIMES):
            return o.isoformat()
        if isinstance(o, enum.Enum):
            return o.name
        if isinstance(o, UUID | Decimal | Path):
            return str(o)
        return str(o)
