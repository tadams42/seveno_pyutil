from __future__ import annotations

import logging
from typing import IO, TYPE_CHECKING, Any

from colorlog import ColoredFormatter as ColoredFormatterBase
from pretty_traceback.formatting import exc_to_traceback_str

if TYPE_CHECKING:
    from collections.abc import Mapping

    from colorlog.formatter import LogColors, SecondaryLogColors


class ColoredFormatter(ColoredFormatterBase):
    def formatException(self, ei) -> str:
        _, exc_value, traceback = ei
        return exc_to_traceback_str(exc_value, traceback, color=True)


class PrettyFormatter(logging.Formatter):
    """
    Logging formatter for pretty logs:

    - can optionally colorize output
    - can optionally force output to be single line
    - reformats logged tracebacks

    To colorize output:

    - instantiate formatter with `colorize = True`
    - use color placeholders in format string, ie `%(red)s text that will be red %(reset)s`

    Example YAML logging config to use it:

    .. code-block:: yaml

        ---
        version: 1

        loggers:
          my_app:
            handlers:
              - console
            level: INFO
            propagate: false

        handlers:
          console:
            class: logging.StreamHandler
            filters:
              - request_id
            stream: ext://sys.stdout
            formatter: colored_multiline

        formatters:
          colored_multiline:
            (): seveno_pyutil.PrettyFormatter
            force_single_line: false
            colorize: true
            format: >-
              lvl=%(log_color)s%(levelname)s%(reset)s
              ts=%(thin_white)s%(asctime)s%(reset)s
              msg=%(message)s

          colorless_single_line:
            (): seveno_pyutil.PrettyFormatter
            force_single_line: true
            colorize: false
            format: >-
              lvl=%(levelname)s
              ts=%(asctime)s
              msg=%(message)s

    Some of available colors are:

    .. code-block:: python

        [
            'black', 'bold_black', 'thin_black', 'red', 'bold_red', 'thin_red', 'green',
            'bold_green', 'thin_green', 'yellow', 'bold_yellow', 'thin_yellow', 'blue',
            'bold_blue', 'thin_blue', 'purple', 'bold_purple', 'thin_purple', 'cyan',
            'bold_cyan', 'thin_cyan', 'white', 'bold_white', 'thin_white', "..."
        ]

    Others can be retrieved via:

    .. code-block:: python

        colorlog.ColoredFormatter()._escape_code_map("DEBUG").keys()

    or check docs for `colorlog`.
    """

    def __init__(  # noqa: PLR0913
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: logging._FormatStyle = "%",
        validate: bool = True,  # noqa: FBT001, FBT002
        *,
        defaults: Mapping[str, Any] | None = None,
        force_single_line: bool = True,
        colorize: bool = False,
        log_colors: LogColors | None = None,
        secondary_log_colors: SecondaryLogColors | None = None,
        reset: bool = True,
        stream: IO | None = None,
    ):
        super().__init__(
            fmt=fmt, datefmt=datefmt, style=style, validate=validate, defaults=defaults
        )
        self.force_single_line = force_single_line
        self.colorize = colorize
        self._color_formatter: ColoredFormatter | None = None
        if self.colorize:
            self._color_formatter = ColoredFormatter(
                fmt=fmt,
                datefmt=datefmt,
                style=style,
                validate=validate,
                defaults=defaults,
                log_colors=log_colors,
                secondary_log_colors=secondary_log_colors,
                reset=reset,
                stream=stream,
                force_color=self.colorize,
                no_color=not self.colorize,
            )

    def formatException(self, ei) -> str:
        _, exc_value, traceback = ei
        return exc_to_traceback_str(exc_value, traceback, color=self.colorize)

    def format(self, record: logging.LogRecord) -> str:
        if self.colorize and self._color_formatter:
            retv = self._color_formatter.format(record)
        else:
            retv = super().format(record)

        if self.force_single_line:
            return retv.replace("\n", "\\n")

        return retv
