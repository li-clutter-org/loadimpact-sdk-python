# coding=utf-8

import unittest

from loadimpactsdk.resources import Resource, TestConfig


class MockResource(Resource):
    fields = {}

    def __init__(self, field_cls, field_value=None):
        self.__class__.fields['field'] = field_cls
        super(MockResource, self).__init__(field=field_value)


class TestResourcesResource(unittest.TestCase):
    def test_getattr(self):
        pass

    def test_setattr(self):
        pass


class TestResourcesTestConfig(unittest.TestCase):
    def test_user_type_enums(self):
        self.assertEquals(TestConfig.SBU, 'sbu')
        self.assertEquals(TestConfig.VU, 'vu')

    def test_user_type_getter(self):
        c = TestConfig()
        self.assertEquals(c.user_type, TestConfig.SBU)

    def test_user_type_setter(self):
        c = TestConfig()
        c.user_type = TestConfig.VU
        self.assertEquals(c.user_type, TestConfig.VU)

    def test_user_type_setter_valueerror(self):
        c = TestConfig()
        with self.assertRaises(ValueError): 
            c.user_type = 'something bad'
