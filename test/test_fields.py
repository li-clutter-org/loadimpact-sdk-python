# coding=utf-8

import unittest

from datetime import datetime
from loadimpactsdk.exceptions import CoercionError
from loadimpactsdk.fields import (
    Field, DateTimeField, DictField, IntegerField, StringField, UnicodeField)
from loadimpactsdk.resources import Resource
from loadimpactsdk.utils import UTC


class MockResource(Resource):
    fields = {}

    def __init__(self, field_cls, field_value=None):
        self.__class__.fields['field'] = field_cls
        super(MockResource, self).__init__(field=field_value)


class TestFieldsField(unittest.TestCase):
    def test_coerce(self):
        with self.assertRaises(NotImplementedError):
            Field.coerce(None)


class TestFieldsDateTimeField(unittest.TestCase):
    def setUp(self):
        self.now = datetime.utcnow().replace(tzinfo=UTC(), microsecond=0)

    def test_coerce(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        coerced = DateTimeField.coerce(value)
        self.assertEquals(coerced, self.now)

    def test_coerce_bad_format(self):
        with self.assertRaises(CoercionError):
            DateTimeField.coerce('2013-01-01')

    def test_construct_bad_format(self):
        with self.assertRaises(CoercionError):
            MockResource(DateTimeField, '2013-01-01')

    def test_get(self):
        value = '%s+00:00' % self.now.strftime(DateTimeField.format)
        r = MockResource(DateTimeField, value)
        self.assertEquals(r.field, self.now)
