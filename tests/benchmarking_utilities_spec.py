import time

from seveno_pyutil import Stopwatch


class DescribeStopwatch(object):
    def it_provides_context_manager_for_duration_measurement(self):
        with Stopwatch() as stopwatch:
            time.sleep(1)

        assert stopwatch.duration_ms >= 1000
