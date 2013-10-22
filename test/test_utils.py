# coding=utf-8

"""
Copyright 2013 Load Impact

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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
        self.assertEqual(td.days, 0)
        self.assertEqual(td.seconds, 0)
        self.assertEqual(td.microseconds, 0)

    def test_utcoffset(self):
        self.assertTimeDeltaZero(self.tz.utcoffset(None))

    def test_tzname(self):
        self.assertEqual(self.tz.tzname(None), 'UTC')

    def test_dst(self):
        self.assertTimeDeltaZero(self.tz.dst(None))
