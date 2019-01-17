import logging

import colorlog


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
    logged as single line but it also preserves colored log sequences.
    """
    def format(self, record):
        return super(SingleLineColoredFormatter, self).format(record).replace(
            '\n', '\\n'
        )
