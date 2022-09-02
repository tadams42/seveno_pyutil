from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from seveno_pyutil import ensure_tzinfo
from seveno_pyutil.datetime_utilities import iter_year_month


class describe_ensure_tzinfo(object):
    def it_converts_naive_datetime_to_timezone_aware_datetime(self):
        dt = datetime.now()
        assert ensure_tzinfo(dt, tz_or_offset=None).tzinfo is ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="Z").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="UTC").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset=ZoneInfo("UTC")).tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="-02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="-0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="-02").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="02").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+02").tzinfo is not None
        assert (
            ensure_tzinfo(dt, tz_or_offset=timedelta(hours=2, minutes=30)).tzinfo
            is not None
        )
        assert (
            ensure_tzinfo(dt, tz_or_offset=timedelta(hours=-2, minutes=30)).tzinfo
            is not None
        )

    def it_converts_timezone_aware_datetime_to_different_timezone(self):
        dt = datetime.now().replace(tzinfo=ZoneInfo("Europe/Zagreb"))

        assert ensure_tzinfo(dt, tz_or_offset=None).tzinfo is ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="Z").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="UTC").tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset=ZoneInfo("UTC")).tzinfo == ZoneInfo("UTC")
        assert ensure_tzinfo(dt, tz_or_offset="-02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+02:00").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="-0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+0200").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="-02").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="02").tzinfo is not None
        assert ensure_tzinfo(dt, tz_or_offset="+02").tzinfo is not None
        assert (
            ensure_tzinfo(dt, tz_or_offset=timedelta(hours=2, minutes=30)).tzinfo
            is not None
        )
        assert (
            ensure_tzinfo(dt, tz_or_offset=timedelta(hours=-2, minutes=30)).tzinfo
            is not None
        )


class describe_iter_year_month:
    def it_generates_empty_range_when_start_is_after_end(self):
        start = date(2022, 12, 1)
        end = date(2022, 9, 1)

        assert not list(iter_year_month(start, end))
        assert not list(iter_year_month(start, end, include_start=True))
        assert not list(iter_year_month(start, end, include_end=True))
        assert not list(
            iter_year_month(start, end, include_start=True, include_end=True)
        )

    def it_generates_empty_range_when_start_is_equal_to_end_and_borders_are_excluded(
        self,
    ):
        start = date(2022, 12, 1)
        end = date(2022, 12, 1)
        assert not list(iter_year_month(start, end))

    def it_generated_single_entry_when_start_is_equal_to_end_and_any_of_borders_is_included(
        self,
    ):
        start = date(2022, 12, 1)
        end = date(2022, 12, 1)
        assert len(list(iter_year_month(start, end, include_start=True))) == 1
        assert len(list(iter_year_month(start, end, include_end=True))) == 1
        assert (
            len(list(iter_year_month(start, end, include_start=True, include_end=True)))
            == 1
        )

    def it_generates_date_range(self):
        start = date(2022, 9, 15)
        end = date(2023, 3, 31)

        assert list(iter_year_month(start, end)) == [
            date(2022, 10, 1),
            date(2022, 11, 1),
            date(2022, 12, 1),
            date(2023, 1, 1),
            date(2023, 2, 1),
        ]

    def it_may_include_borders(self):
        start = date(2022, 9, 15)
        end = date(2023, 3, 31)

        assert list(iter_year_month(start, end, include_start=True)) == [
            date(2022, 9, 1),
            date(2022, 10, 1),
            date(2022, 11, 1),
            date(2022, 12, 1),
            date(2023, 1, 1),
            date(2023, 2, 1),
        ]

        assert list(iter_year_month(start, end, include_end=True)) == [
            date(2022, 10, 1),
            date(2022, 11, 1),
            date(2022, 12, 1),
            date(2023, 1, 1),
            date(2023, 2, 1),
            date(2023, 3, 1),
        ]

        assert list(
            iter_year_month(start, end, include_start=True, include_end=True)
        ) == [
            date(2022, 9, 1),
            date(2022, 10, 1),
            date(2022, 11, 1),
            date(2022, 12, 1),
            date(2023, 1, 1),
            date(2023, 2, 1),
            date(2023, 3, 1),
        ]
