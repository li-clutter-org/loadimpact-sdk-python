# coding=utf-8

import unittest

from loadimpact.utils import is_dict_different, UTC


class TestUtilsFunctions(unittest.TestCase):
    def test_is_dict_different_false(self):
        d1 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        d2 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        self.assertFalse(is_dict_different(d1, d2))

    def test_is_dict_different_true_int(self):
        d1 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        d2 = {
            'int': 1,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        self.assertTrue(is_dict_different(d1, d2))

    def test_is_dict_different_true_string(self):
        d1 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        d2 = {
            'int': 0,
            'string': "I'm a string2",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        self.assertTrue(is_dict_different(d1, d2))

    def test_is_dict_different_true_float(self):
        d1 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        d2 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.123456,
            'dict': {'key': 'value'}
        }
        self.assertTrue(is_dict_different(d1, d2))

    def test_is_dict_different_false_float_epsilon(self):
        d1 = {
            'float': 0.123457
        }
        d2 = {
            'float': 0.123456
        }
        self.assertFalse(is_dict_different(d1, d2, epsilon=0.00001))

    def test_is_dict_different_true_float_epsilon(self):
        d1 = {
            'float': 0.123457
        }
        d2 = {
            'float': 0.123456
        }
        self.assertTrue(is_dict_different(d1, d2, epsilon=0.0000001))

    def test_is_dict_different_true_dict(self):
        d1 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value'}
        }
        d2 = {
            'int': 0,
            'string': "I'm a string",
            'float': 0.12345,
            'dict': {'key': 'value2'}
        }
        self.assertTrue(is_dict_different(d1, d2))


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
