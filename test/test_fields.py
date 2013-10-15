# coding=utf-8

import unittest

from datetime import datetime
from loadimpact.clients import Client
from loadimpact.exceptions import CoercionError
from loadimpact.fields import (
    Field, DateTimeField, DictField, IntegerField, StringField, UnicodeField)
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


class TestFieldsDateTimeField(unittest.TestCase):
    def setUp(self):
        self.now = datetime.utcnow().replace(tzinfo=UTC(), microsecond=0)
        self.client = MockClient()

    def test_coerce(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        coerced = DateTimeField.coerce(value)
        self.assertEquals(coerced, self.now)

    def test_coerce_bad_format(self):
        self.assertRaises(CoercionError, DateTimeField.coerce, '2013-01-01')

    def test_construct_bad_format(self):
        self.assertRaises(CoercionError, MockResource, self.client,
                          DateTimeField, '2013-01-01')

    def test_get(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        r = MockResource(self.client, DateTimeField, value)
        self.assertEquals(r.field, self.now)
