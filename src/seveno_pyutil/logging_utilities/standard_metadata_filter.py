import logging
import socket
from datetime import datetime

import pytz
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
