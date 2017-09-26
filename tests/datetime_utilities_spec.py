from datetime import datetime

from seveno_pyutil import datetime_utilities


class describe_ensure_tzinfo(object):
    def it_ensures_tz_aware_datetime(self):
        assert datetime_utilities.ensure_tzinfo(datetime.now()).tzinfo
