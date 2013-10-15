# coding=utf-8

import unittest

from loadimpact.clients import Client
from loadimpact.resources import Resource, TestConfig


class MockClient(Client):
    def _requests_request(self, method, *args, **kwargs):
        pass


class MockResource(Resource):
    fields = {}

    def __init__(self, client, field_cls, field_value=None):
        self.__class__.fields['field'] = field_cls
        super(MockResource, self).__init__(client, field=field_value)


class TestResourcesResource(unittest.TestCase):
    def test_getattr(self):
        pass

    def test_setattr(self):
        pass


class TestResourcesTestConfig(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_user_type_enums(self):
        self.assertEquals(TestConfig.SBU, 'sbu')
        self.assertEquals(TestConfig.VU, 'vu')

    def test_user_type_getter(self):
        c = TestConfig(self.client)
        self.assertEquals(c.user_type, TestConfig.SBU)

    def test_user_type_setter(self):
        c = TestConfig(self.client)
        c.user_type = TestConfig.VU
        self.assertEquals(c.user_type, TestConfig.VU)

    def test_user_type_setter_valueerror(self):
        c = TestConfig(self.client)
        def assign_bad_user_type():
            c.user_type = 'something bad'
        self.assertRaises(ValueError, assign_bad_user_type)
