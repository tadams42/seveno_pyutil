from datetime import datetime, timedelta

import pytz

from seveno_pyutil import ensure_tzinfo


class describe_ensure_tzinfo(object):
    def it_converts_naive_datetime_to_timezone_aware_datetime(self):
        dt = datetime.now()
        assert ensure_tzinfo(dt, tz_or_offset=None).tzinfo is pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='Z').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='UTC').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset=pytz.utc).tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='-02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='-0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='-02').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='02').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+02').tzinfo is not None
        assert ensure_tzinfo(
            dt, tz_or_offset=timedelta(hours=2, minutes=30)
        ).tzinfo is not None
        assert ensure_tzinfo(
            dt, tz_or_offset=timedelta(hours=-2, minutes=30)
        ).tzinfo is not None

    def it_converts_timezone_aware_datetime_to_different_timezone(self):
        dt = pytz.timezone("Europe/Zagreb").localize(datetime.now())

        assert ensure_tzinfo(dt, tz_or_offset=None).tzinfo is pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='Z').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='UTC').tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset=pytz.utc).tzinfo == pytz.utc
        assert ensure_tzinfo(dt, tz_or_offset='-02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+02:00').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='-0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+0200').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='-02').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='02').tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset='+02').tzinfo is not None
        assert ensure_tzinfo(
            dt, tz_or_offset=timedelta(hours=2, minutes=30)
        ).tzinfo is not None
        assert ensure_tzinfo(
            dt, tz_or_offset=timedelta(hours=-2, minutes=30)
        ).tzinfo is not None
