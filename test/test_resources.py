# coding=utf-8

import hashlib
import json
import unittest

from loadimpact.clients import Client
from loadimpact.fields import IntegerField
from loadimpact.resources import (
    DataStore, LoadZone, Resource, Test, TestConfig, TestResult, UserScenario)


class MockRequestsResponse(object):
    def __init__(self, status_code=200, **kwargs):
        self.url = 'http://example.com/'
        self.status_code = status_code
        self.kwargs = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def json(self):
        return self.kwargs


class MockClient(Client):
    def __init__(self, response_status_code=200, **kwargs):
        super(MockClient, self).__init__()
        self.response_status_code = response_status_code
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
        return MockRequestsResponse(status_code=self.response_status_code,
                                    **nkwargs)


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


class TestResourcesDataStore(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_has_conversion_finished(self):
        ds = DataStore(self.client)
        self.assertFalse(ds.has_conversion_finished())
        self.assertEquals(self.client.last_request_method, 'get')

    def test_has_conversion_finished_status_queued(self):
        self._check_has_conversion_finished(DataStore.STATUS_QUEUED, False)

    def test_has_conversion_finished_status_converting(self):
        self._check_has_conversion_finished(DataStore.STATUS_CONVERTING, False)

    def test_has_conversion_finished_status_finished(self):
        self._check_has_conversion_finished(DataStore.STATUS_FINISHED, True)

    def test_has_conversion_finished_status_failed(self):
        self._check_has_conversion_finished(DataStore.STATUS_FAILED, True)

    def _check_has_conversion_finished(self, status, expected):
        ds = DataStore(self.client)
        ds.status = status
        self.assertEquals(ds.has_conversion_finished(), expected)
        self.assertEquals(self.client.last_request_method, 'get')


class TestResourcesTest(unittest.TestCase):
    def test_abort(self):
        client = MockClient()
        test = Test(client)
        result = test.abort()
        self.assertEquals(client.last_request_method, 'post')
        self.assertTrue(result)

    def test_abort_failed_409(self):
        client = MockClient(response_status_code=409)
        test = Test(client)
        result = test.abort()
        self.assertEquals(client.last_request_method, 'post')
        self.assertFalse(result)

    def test_status_code_to_text(self):
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_CREATED), 'created')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_QUEUED), 'queued')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_INITIALIZING), 'initializing')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_RUNNING), 'running')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_FINISHED), 'finished')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_TIMED_OUT), 'timed out')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_ABORTING_USER),
            'aborting (by user)')
        self.assertEquals(Test.status_code_to_text(Test.STATUS_ABORTED_USER),
            'aborted (by user)')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_ABORTING_SYSTEM),
            'aborting (by system)')
        self.assertEquals(
            Test.status_code_to_text(Test.STATUS_ABORTED_SYSTEM),
            'aborted (by system)')
        self.assertEquals(
            Test.status_code_to_text(0xffffffff),
            'unknown')


class TestResourcesTestResult(unittest.TestCase):
    def test_result_id_from_name_with_name(self):
        self.assertEquals(TestResult.result_id_from_name('__li_user_load_time'),
                          '__li_user_load_time')

    def test_result_id_from_name_with_name_load_zone(self):
        self.assertEquals(TestResult.result_id_from_name('__li_user_load_time',
                                                         load_zone_id=1),
                          '__li_user_load_time:1')

    def test_result_id_from_name_with_name_load_zone_user_scenario(self):
        self.assertEquals(TestResult.result_id_from_name('__li_user_load_time',
                                                         load_zone_id=1,
                                                         user_scenario_id=1),
                          '__li_user_load_time:1:1')

    def test_result_id_from_custom_metric_name(self):
        name = 'my metric'
        self.assertEquals(TestResult.result_id_from_custom_metric_name(name,
                                                                       1, 1),
                          '__custom_%s:1:1' % hashlib.md5(name).hexdigest())

    def test_result_id_for_page(self):
        name = 'my page'
        self.assertEquals(TestResult.result_id_for_page(name, 1, 1),
                          '__li_page%s:1:1' % hashlib.md5(name).hexdigest())

    def test_result_id_for_url(self):
        url = 'http://example.com/'
        self.assertEquals(TestResult.result_id_for_url(url, 1, 1, 
                                                       method='GET',
                                                       status_code=200),
                          '__li_url%s:1:1:GET:200'
                          % hashlib.md5(url).hexdigest())


class TestResourcesLoadZone(unittest.TestCase):
    def test_name_to_id(self):
        self.assertEquals(LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD), 1)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_US_ASHBURN), 11)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_US_PALOALTO), 12)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_IE_DUBLIN), 13)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_SG_SINGAPORE), 14)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_JP_TOKYO), 15)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_US_PORTLAND), 22)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_BR_SAOPAULO), 23)
        self.assertEquals(LoadZone.name_to_id(LoadZone.AMAZON_AU_SYDNEY), 25)
        self.assertEquals(LoadZone.name_to_id(LoadZone.RACKSPACE_US_CHICAGO), 26)
        self.assertEquals(LoadZone.name_to_id(LoadZone.RACKSPACE_US_DALLAS), 27)
        self.assertEquals(LoadZone.name_to_id(LoadZone.RACKSPACE_UK_LONDON), 28)
        self.assertEquals(LoadZone.name_to_id(LoadZone.RACKSPACE_AU_SYDNEY), 29)

    def test_name_to_id_exception(self):
        self.assertRaises(ValueError, LoadZone.name_to_id, 'unknown')


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

    def test_update_with_dict(self):
        name_change = 'Test Config'
        test_config = TestConfig(self.client)
        test_config.update({'name': name_change})

        self.assertEquals(self.client.last_request_method, 'put')
        self.assertEquals(self.client.last_request_kwargs['data']['name'],
                          name_change)
        self.assertEquals(test_config.name, name_change)

    def test_update_with_attribute(self):
        name_change = 'Test Config'
        test_config = TestConfig(self.client)
        test_config.name = name_change
        test_config.update()

        self.assertEquals(self.client.last_request_method, 'put')
        self.assertEquals(self.client.last_request_kwargs['data']['name'],
                          name_change)
        self.assertEquals(test_config.name, name_change)


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
