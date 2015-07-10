# coding=utf-8

"""
Copyright 2015 Load Impact

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

from datetime import datetime
from loadimpact.clients import Client
from loadimpact.exceptions import CoercionError
from loadimpact.fields import (
    Field, DataStoreListField, DateTimeField, DictField, IntegerField,
    StringField)
from loadimpact.resources import Resource
from loadimpact.utils import UTC


class MockClient(Client):
    def _requests_request(self, method, *args, **kwargs):
        pass


class MockResource(Resource):
    fields = {}

    def __init__(self, client, field_cls, field_value=None):
        self.__class__.fields['field'] = field_cls
        super(MockResource, self).__init__(client, field=field_value)


class TestFieldsField(unittest.TestCase):
    def test_coerce(self):
        self.assertRaises(NotImplementedError, Field.coerce, None)


class TestFieldsDataStoreListField(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_coerce(self):
        coerced = DataStoreListField.coerce([1, 2, 3, 4, 5])
        self.assertEqual(coerced, [1, 2, 3, 4, 5])

    def test_coerce_from_list_of_dicts(self):
        coerced = DataStoreListField.coerce([{'id': 6}, {'id': 7}, {'id': 8}])
        self.assertEqual(coerced, [6, 7, 8])

    def test_get(self):
        r = MockResource(self.client, DataStoreListField, [1, 2, 3, 4, 5])
        self.assertEqual(r.field, [1, 2, 3, 4, 5])


class TestFieldsDateTimeField(unittest.TestCase):
    def setUp(self):
        self.now = datetime.utcnow().replace(tzinfo=UTC(), microsecond=0)
        self.client = MockClient()

    def test_coerce(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        coerced = DateTimeField.coerce(value)
        self.assertEqual(coerced, self.now)

    def test_coerce_bad_format(self):
        self.assertRaises(CoercionError, DateTimeField.coerce, '2013-01-01')

    def test_construct_bad_format(self):
        self.assertRaises(CoercionError, MockResource, self.client,
                          DateTimeField, '2013-01-01')

    def test_get(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        r = MockResource(self.client, DateTimeField, value)
        self.assertEqual(r.field, self.now)


class TestFieldsIntegerField(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_coerce(self):
        coerced = IntegerField.coerce(1)
        self.assertEqual(coerced, 1)

    def test_coerce_from_string(self):
        coerced = IntegerField.coerce('1')
        self.assertEqual(coerced, 1)

    def test_get(self):
        r = MockResource(self.client, IntegerField, 1)
        self.assertEqual(r.field, 1)
