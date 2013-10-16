# coding=utf-8

import json
import unittest

from loadimpact.clients import Client
from loadimpact.fields import IntegerField
from loadimpact.resources import Resource, TestConfig, UserScenario


class MockRequestsResponse(object):
    def __init__(self, status_code=200, **kwargs):
        self.status_code = status_code
        self.kwargs = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def json(self):
        d = self.kwargs
        d.update({'status_code': self.status_code})
        return d


class MockClient(Client):
    def __init__(self, **kwargs):
        super(MockClient, self).__init__()
        self.kwargs = kwargs
        self.last_request_method = None
        self.last_request_args = None
        self.last_request_kwargs = None

    def _requests_request(self, method, *args, **kwargs):
        self.last_request_method = method
        self.last_request_args = args
        self.last_request_kwargs = kwargs
        if isinstance(kwargs.get('data'), str):
            self.last_request_kwargs['data'] = json.loads(kwargs['data'])
        nkwargs = {}
        if kwargs.get('data'):
            if isinstance(kwargs['data'], dict):
                nkwargs = kwargs['data']
            elif isinstance(kwargs['data'], str):
                nkwargs = json.loads(kwargs['data'])
        return MockRequestsResponse(**nkwargs)


class MockResource(Resource):
    fields = {}
    resource_name = 'resource'

    def __init__(self, client, field_cls, field_value=None):
        self.__class__.fields['field'] = field_cls
        super(MockResource, self).__init__(client, field=field_value)


class TestResourcesResource(unittest.TestCase):
    def test___getattr__(self):
        r = MockResource(None, IntegerField, 0)
        def raises():
            r.field2
        self.assertRaises(AttributeError, raises)

    def test__path(self):
        self.assertEquals(MockResource._path(), MockResource.resource_name)
        self.assertEquals(MockResource._path(resource_id=None),
                          MockResource.resource_name)
        self.assertEquals(MockResource._path(resource_id=0),
                          '%s/%s' % (MockResource.resource_name, 0))
        self.assertEquals(MockResource._path(resource_id=1),
                          '%s/%s' % (MockResource.resource_name, 1))
        self.assertEquals(MockResource._path(resource_id=1, action='action'),
                          '%s/%s/%s' % (MockResource.resource_name, 1, 'action'))


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


class TestResourcesUserScenario(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_update_with_dict(self):
        name_change = 'Test User Scenario'
        user_scenario = UserScenario(self.client)
        user_scenario.update({'name': name_change})

        self.assertEquals(self.client.last_request_method, 'put')
        self.assertEquals(self.client.last_request_kwargs['data']['name'],
                          name_change)
        self.assertEquals(user_scenario.name, name_change)

    def test_update_with_attribute(self):
        name_change = 'Test User Scenario'
        user_scenario = UserScenario(self.client)
        user_scenario.name = name_change
        user_scenario.update()

        self.assertEquals(self.client.last_request_method, 'put')
        self.assertEquals(self.client.last_request_kwargs['data']['name'],
                          name_change)
        self.assertEquals(user_scenario.name, name_change)
