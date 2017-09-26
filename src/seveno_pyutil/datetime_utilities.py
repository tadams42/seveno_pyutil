from datetime import datetime

import pytz
import tzlocal


def ensure_tzinfo(val, tz=pytz.utc):
    """Ensures that val has ``tz_info`` attribute."""
    if isinstance(val, datetime):
        if isinstance(tz, str):
            tz = pytz.timezone(tz)

        if not val.tzinfo:
            val = tz.localize(val)
        else:
            val = val.astimezone(tz)

    return val
