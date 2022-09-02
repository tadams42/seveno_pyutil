import re
from datetime import date, datetime, timedelta, tzinfo
from typing import Optional, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.tz import tzoffset

_ISO_8601_OFFSET = re.compile(r"([+-]?)([0-9]{2})[:]?([0-9]{0,2})")


TzOffsetLike = Optional[Union[str, int, timedelta, tzinfo]]


def timezone_or_offset(from_: TzOffsetLike):
    """
    Given ``from_`` creates `datetime.tzinfo` or `dateutil.tz.tzoffset` as
    result.

    ``from_`` can be any of following:

    - `str` (ie. "-02:42", None, "", "Z", ...) which is ISO8601 offset
    - `str` (ie. "Europe/Zagreb") which is timezone name
    - `int` (ie. -9000) which is total number of seconds in time offset
    - `datetime.timedelta`
    - `datetime.tzinfo` or something that behaves like it
    """
    offset_obj = None

    if from_ is None:
        offset_obj = ZoneInfo("UTC")

    elif isinstance(from_, str):
        try:
            offset_obj = ZoneInfo(from_)
        except (ZoneInfoNotFoundError, ValueError):
            pass

        if not offset_obj:
            if from_.strip() in ["Z", ""]:
                offset_obj = ZoneInfo("UTC")
            else:
                match_object = _ISO_8601_OFFSET.match(from_)
                if match_object:
                    sign, hours, minutes = match_object.groups()
                    offset_obj = tzoffset(
                        name=from_,
                        offset=timedelta(
                            hours=(-1 if sign == "-" else 1) * int(hours),
                            minutes=int(minutes or 0),
                        ),
                    )

    elif isinstance(from_, timedelta):
        offset_obj = tzoffset(name="{} s".format(from_.total_seconds()), offset=from_)

    elif isinstance(from_, int):
        offset_obj = tzoffset(
            name="{} s".format(from_), offset=timedelta(seconds=from_)
        )

    elif issubclass(type(from_), tzinfo) or all(
        hasattr(from_, attr_name)
        for attr_name in ["dst", "fromutc", "tzname", "utcoffset"]
    ):
        offset_obj = from_

    if offset_obj is None:
        raise ValueError("Unable to parse time offset: {}".format(from_))

    return offset_obj


def ensure_tzinfo(
    val: datetime, tz_or_offset: TzOffsetLike = "UTC", is_dst: bool = False
) -> datetime:
    """
    Creates timezone aware datetime object for ``val``.

    - if ``val`` is naive datetime, new value will be created as datetime
      localized in ``tz_or_offset`` timezone
    - if ``val`` is already timezone aware, it will be converted to
      ``tz_or_offset`` timezone using `datetime.datetime.astimezone`

    Arguments:
        val: Input value for conversion
        tz_or_offset: Anything that `timezone_or_offset` accepts
        is_dst: used to determine the correct timezone in the ambiguous
            period at the end of daylight saving time. Use ``is_dst=None`` to
            raise an AmbiguousTimeError for ambiguous times at the end of
            daylight saving time.

    Return:
        Timezone aware datetime object

    Raises:
        ValueError: When timezone of offset can't be parsed / determined from
            ``tz_or_offset``

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
        val = val.replace(tzinfo=tz_or_offset)
    else:
        val = val.astimezone(tz_or_offset)

    return val


def iter_year_month(
    start: Union[date, datetime],
    end: Optional[date] = None,
    include_start: bool = False,
    include_end: bool = False,
):
    """
    Generates range of date(year, month, 1) from ``start`` to ``end``.

    - when ``start > end`` generated range is empty
    - when ``start == end`` generated range may contain single ``date`` object
      depending on ``include_start`` or ``include_end``

    Arguments:
        start: begin of range
        end: end of range. If ``None``, assumes, ``start == end``
        include_start: include ``start`` in generated range
        include_end: include ``end`` in generated range
    """

    if not end:
        end = start

    start = date(year=start.year, month=start.month, day=1)
    end = date(year=end.year, month=end.month, day=1)

    if start > end:
        return

    if start == end:
        if include_start or include_end:
            yield start
        return

    val = date(year=start.year, month=start.month, day=1)

    if include_start:
        yield val

    end_reached = False
    while not end_reached:
        try:
            val = val.replace(month=val.month + 1)

        except ValueError:
            if val.month == 12:
                val = val.replace(year=val.year + 1, month=1)

        if val == end:
            if include_end:
                yield val
            end_reached = True

        else:
            yield val
