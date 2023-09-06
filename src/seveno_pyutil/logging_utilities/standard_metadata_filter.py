import logging
import socket
from datetime import datetime
from zoneinfo import ZoneInfo

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
    except Exception:
        _HOSTNAME = "-"

    _LOCAL_TZ = ZoneInfo(tzlocal.get_localzone_name())

    def filter(self, record):
        dt = datetime.fromtimestamp(record.created).replace(  # noqa: DTZ006
            tzinfo=self._LOCAL_TZ
        )

        record.isotime = dt.isoformat()
        record.isotime_utc = dt.astimezone(ZoneInfo("UTC")).isoformat()
        record.hostname = self._HOSTNAME

        return super().filter(record)
