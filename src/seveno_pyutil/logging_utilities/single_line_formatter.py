import logging
import socket
from datetime import datetime
from zoneinfo import ZoneInfo

import colorlog
import tzlocal


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
        _HOSTNAME = "-"

    _LOCAL_TZ = ZoneInfo(tzlocal.get_localzone_name())

    def filter(self, record):
        # Note that naive datetime will not be exported correctly to isoformat:
        #   datetime.now().isoformat()
        #   '2017-05-22T13:51:49.336335'
        # but we don't have this problem because we make sure that here we
        # always have tzinfo on datetime object
        dt = datetime.fromtimestamp(record.created).replace(tzinfo=self._LOCAL_TZ)

        record.isotime = dt.isoformat()
        record.isotime_utc = dt.astimezone(ZoneInfo("UTC")).isoformat()
        record.hostname = self._HOSTNAME

        return super().filter(record)


class SingleLineFormatter(logging.Formatter):
    """
    logging.Formatter that escapes all new lines forcing log record to be
    logged as single line.
    """

    def format(self, record):
        return super().format(record).replace("\n", "\\n")


class SingleLineColoredFormatter(colorlog.ColoredFormatter):
    """
    logging.Formatter that escapes all new lines forcing log record to be
    logged as single line but it also preserves colored log sequences.
    """

    def format(self, record):
        return super().format(record).replace("\n", "\\n")
