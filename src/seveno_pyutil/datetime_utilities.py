import re
from datetime import datetime, timedelta, tzinfo

import pytz
from dateutil.tz import tzoffset

_ISO_8601_OFFSET = re.compile(r"([+-]?)([0-9]{2})[:]?([0-9]{0,2})")


def timezone_or_offset(from_):
    """
    Given ``from_`` creates `datetime.tzinfo` or `dateutil.tz.tzoffset` as
    result.

    ``from_`` can be any of following:

    - `str` (ie. "-02:42", None, "", "Z", ...) which is ISO8601 offset
    - `str` (ie. "Europe/Zagreb") which is timezone name
    - `int` (ie. -9000) which is total number of seconds in time offset
    - `datetime.timedelta`
    - `datetime.tzinfo` or something that behaves like it

    Todo:
        In Python 3.7 there is finally datetime.timezone that behaves same as
        dateutil.tz.tzoffset so we should eventually use that.
    """
    offset_obj = None

    if from_ is None:
        offset_obj = pytz.utc

    elif isinstance(from_, str):
        try:
            offset_obj = pytz.timezone(from_)
        except pytz.exceptions.UnknownTimeZoneError:
            pass

        if not offset_obj:
            if from_.strip() in ['Z', '']:
                offset_obj = pytz.utc
            else:
                match_object = _ISO_8601_OFFSET.match(from_)
                if match_object:
                    sign, hours, minutes = match_object.groups()
                    offset_obj = tzoffset(
                        name=from_, offset=timedelta(
                            hours=(-1 if sign == '-' else 1) * int(hours),
                            minutes=int(minutes or 0)
                        )
                    )

    elif isinstance(from_, timedelta):
        offset_obj = tzoffset(
            name="{} s".format(from_.total_seconds()), offset=from_
        )

    elif isinstance(from_, int):
        offset_obj = tzoffset(
            name="{} s".format(from_), offset=timedelta(seconds=from_)
        )

    elif issubclass(type(from_), tzinfo) or all(
        hasattr(from_, attr_name)
        for attr_name in ['dst', 'fromutc', 'tzname', 'utcoffset']
    ):
        offset_obj = from_

    if offset_obj is None:
        raise ValueError('Unable to parse time offset: {}'.format(from_))

    return offset_obj


def ensure_tzinfo(val, tz_or_offset='UTC', is_dst=False):
    """
    Creates timezone aware datetime object for ``val``.

    - if ``val`` is naive datetime, new value will be created as datetime
      localized in ``tz_or_offset`` timezone
    - if ``val`` is already timezone aware, it will be converted to
      ``tz_or_offset`` timezone using `datetime.datetime.astimezone`

    Arguments:
        val(datetime.datetime): Input value for conversion
        tz_or_offset: Anything that `timezone_or_offset` accepts
        is_dst(bool): used to determine the correct timezone in the ambiguous
            period at the end of daylight saving time. Use ``is_dst=None`` to
            raise an AmbiguousTimeError for ambiguous times at the end of
            daylight saving time.

    Return:
        datetime.datetime: Timezone aware datetime object

    Raises:
        ValueError: When timezone of offset can't be parsed / determined from
            ``tz_or_offset``
        ``pytz.exceptions.AmbiguousTimeError``: When ``is_dst is None`` and
            localization of tz unaware object would result with ambiguous (regarding
            to DST) time.

    Note:
        This tries to provide safe(ish) implementation for handling naive
        datetime objects, but ultimate solution is to not use naive datetime
        objects ever/anywhere. Recommendation is to go with ``pip install
        pendulum`` and leave this crap behind to history.
    """
    if not isinstance(val, datetime):
        raise ValueError(
            "Input is not datetime! ensure_tzinfo doesn't parse datetime, you "
            "need to do that beforehand."
        )

    tz_or_offset = timezone_or_offset(tz_or_offset)

    if not val.tzinfo:
        if hasattr(tz_or_offset, 'localize'):
            # pytz recommended way for creating timezone aware objects ...
            val = tz_or_offset.localize(val, is_dst=is_dst)
        else:
            # ... but it is not always possible so we fallback to stdlib
            val = val.replace(tzinfo=tz_or_offset)
    else:
        val = val.astimezone(tz_or_offset)

    return val
