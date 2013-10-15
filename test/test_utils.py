# coding=utf-8

import unittest

from loadimpact.utils import UTC


class TestUtilsUTC(unittest.TestCase):
    def setUp(self):
        self.tz = UTC()

    def assertTimeDeltaZero(self, td):
        self.assertEquals(td.days, 0)
        self.assertEquals(td.seconds, 0)
        self.assertEquals(td.microseconds, 0)

    def test_utcoffset(self):
        self.assertTimeDeltaZero(self.tz.utcoffset(None))

    def test_tzname(self):
        self.assertEquals(self.tz.tzname(None), 'UTC')

    def test_dst(self):
        self.assertTimeDeltaZero(self.tz.dst(None))
