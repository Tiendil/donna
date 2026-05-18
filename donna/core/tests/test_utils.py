import datetime

from donna.core import utils


class TestNow:
    def test_returns_timezone_aware_utc_datetime(self) -> None:
        value = utils.now()

        assert isinstance(value, datetime.datetime)
        assert value.tzinfo == datetime.UTC
