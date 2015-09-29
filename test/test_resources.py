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

import hashlib
import json
import sys
import unittest

from loadimpact.clients import Client
from loadimpact.fields import IntegerField
from loadimpact.resources import (
    DataStore, LoadZone, Resource, Test, TestConfig, TestResult,
    _TestResultStream, UserScenario, UserScenarioValidation,
    _UserScenarioValidationResultStream)


class MockRequestsResponse(object):
    def __init__(self, status_code=200, **kwargs):
        self.url = 'http://example.com/'
        self.status_code = status_code
        self.text = ''
        self.kwargs = kwargs
        for k, v in kwargs.items():
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
        if self.kwargs.get('response_body'):
            if isinstance(self.kwargs['response_body'], dict):
                nkwargs = self.kwargs['response_body']
            elif isinstance(self.kwargs['response_body'], str):
                nkwargs = json.loads(self.kwargs['response_body'])
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
        self.assertEqual(MockResource._path(), MockResource.resource_name)
        self.assertEqual(MockResource._path(resource_id=None),
                         MockResource.resource_name)
        self.assertEqual(MockResource._path(resource_id=0),
                         '%s/%s' % (MockResource.resource_name, 0))
        self.assertEqual(MockResource._path(resource_id=1),
                         '%s/%s' % (MockResource.resource_name, 1))
        self.assertEqual(MockResource._path(resource_id=1, action='action'),
                         '%s/%s/%s' % (MockResource.resource_name, 1, 'action'))


class TestResourcesDataStore(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_has_conversion_finished(self):
        ds = DataStore(self.client)
        self.assertFalse(ds.has_conversion_finished())
        self.assertEqual(self.client.last_request_method, 'get')

    def test_has_conversion_finished_status_queued(self):
        self._check_has_conversion_finished(DataStore.STATUS_QUEUED, False)

    def test_has_conversion_finished_status_converting(self):
        self._check_has_conversion_finished(DataStore.STATUS_CONVERTING, False)

    def test_has_conversion_finished_status_finished(self):
        self._check_has_conversion_finished(DataStore.STATUS_FINISHED, True)

    def test_has_conversion_finished_status_failed(self):
        self._check_has_conversion_finished(DataStore.STATUS_FAILED, True)

    def test_status_code_to_text(self):
        self.assertEqual(
            DataStore.status_code_to_text(DataStore.STATUS_QUEUED), 'queued')
        self.assertEqual(
            DataStore.status_code_to_text(DataStore.STATUS_CONVERTING),
            'converting')
        self.assertEqual(
            DataStore.status_code_to_text(DataStore.STATUS_FINISHED),
            'finished')
        self.assertEqual(
            DataStore.status_code_to_text(DataStore.STATUS_FAILED), 'failed')
        self.assertEqual(
            Test.status_code_to_text(0xffffffff),
            'unknown')

    def _check_has_conversion_finished(self, status, expected):
        ds = DataStore(self.client)
        ds.status = status
        self.assertEqual(ds.has_conversion_finished(), expected)
        self.assertEqual(self.client.last_request_method, 'get')


class TestResourcesLoadZone(unittest.TestCase):
    def test_name_to_id(self):
        self.assertEqual(LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD), 1)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_US_ASHBURN), 11)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_US_PALOALTO), 12)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_IE_DUBLIN), 13)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_SG_SINGAPORE), 14)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_JP_TOKYO), 15)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_US_PORTLAND), 22)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_BR_SAOPAULO), 23)
        self.assertEqual(LoadZone.name_to_id(LoadZone.AMAZON_AU_SYDNEY), 25)
        self.assertEqual(LoadZone.name_to_id(LoadZone.RACKSPACE_US_CHICAGO), 26)
        self.assertEqual(LoadZone.name_to_id(LoadZone.RACKSPACE_US_DALLAS), 27)
        self.assertEqual(LoadZone.name_to_id(LoadZone.RACKSPACE_UK_LONDON), 28)
        self.assertEqual(LoadZone.name_to_id(LoadZone.RACKSPACE_AU_SYDNEY), 29)

    def test_name_to_id_exception(self):
        self.assertRaises(ValueError, LoadZone.name_to_id, 'unknown')


class TestResourcesTest(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_abort(self):
        test = Test(self.client)
        result = test.abort()
        self.assertEqual(self.client.last_request_method, 'post')
        self.assertTrue(result)

    def test_abort_failed_409(self):
        client = MockClient(response_status_code=409)
        test = Test(client)
        result = test.abort()
        self.assertEqual(client.last_request_method, 'post')
        self.assertFalse(result)

    def test_is_done(self):
        test = Test(self.client)
        self.assertFalse(test.is_done())
        self.assertEqual(self.client.last_request_method, 'get')

    def test_is_done_status_created(self):
        self._check_is_done(Test.STATUS_CREATED, False)

    def test_is_done_status_queued(self):
        self._check_is_done(Test.STATUS_QUEUED, False)

    def test_is_done_status_initializing(self):
        self._check_is_done(Test.STATUS_INITIALIZING, False)

    def test_is_done_status_running(self):
        self._check_is_done(Test.STATUS_RUNNING, False)

    def test_is_done_status_finished(self):
        self._check_is_done(Test.STATUS_FINISHED, True)

    def test_is_done_status_timed_out(self):
        self._check_is_done(Test.STATUS_TIMED_OUT, True)

    def test_is_done_status_aborting_user(self):
        self._check_is_done(Test.STATUS_ABORTING_USER, False)

    def test_is_done_status_aborted_user(self):
        self._check_is_done(Test.STATUS_ABORTED_USER, True)

    def test_is_done_status_aborting_system(self):
        self._check_is_done(Test.STATUS_ABORTING_SYSTEM, False)

    def test_is_done_status_aborted_system(self):
        self._check_is_done(Test.STATUS_ABORTED_SYSTEM, True)

    def test_result_stream(self):
        test = Test(self.client)
        result_stream = test.result_stream()
        self.assertTrue(isinstance(
            result_stream, _TestResultStream))
        self.assertEqual(result_stream.test, test)
        self.assertEqual(result_stream.result_ids, [
            TestResult.result_id_from_name(
                TestResult.USER_LOAD_TIME,
                load_zone_id=LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD)),
            TestResult.result_id_from_name(
                TestResult.ACTIVE_USERS,
                load_zone_id=LoadZone.name_to_id(LoadZone.AGGREGATE_WORLD))
        ])

    def test_status_code_to_text(self):
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_CREATED), 'created')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_QUEUED), 'queued')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_INITIALIZING), 'initializing')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_RUNNING), 'running')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_FINISHED), 'finished')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_TIMED_OUT), 'timed out')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_ABORTING_USER),
            'aborting (by user)')
        self.assertEqual(Test.status_code_to_text(Test.STATUS_ABORTED_USER),
                         'aborted (by user)')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_ABORTING_SYSTEM),
            'aborting (by system)')
        self.assertEqual(
            Test.status_code_to_text(Test.STATUS_ABORTED_SYSTEM),
            'aborted (by system)')
        self.assertEqual(
            Test.status_code_to_text(0xffffffff),
            'unknown')

    def _check_is_done(self, status, expected):
        test = Test(self.client)
        test.status = status
        self.assertEqual(test.is_done(), expected)
        self.assertEqual(self.client.last_request_method, 'get')


class TestResourcesTestResult(unittest.TestCase):
    def test_result_id_from_name_with_name(self):
        self.assertEqual(TestResult.result_id_from_name('__li_user_load_time'),
                         '__li_user_load_time')

    def test_result_id_from_name_with_name_load_zone(self):
        self.assertEqual(TestResult.result_id_from_name('__li_user_load_time',
                                                        load_zone_id=1),
                         '__li_user_load_time:1')

    def test_result_id_from_name_with_name_load_zone_user_scenario(self):
        self.assertEqual(TestResult.result_id_from_name('__li_user_load_time',
                                                        load_zone_id=1,
                                                        user_scenario_id=1),
                         '__li_user_load_time:1:1')

    def test_result_id_from_custom_metric_name(self):
        name = 'my metric'
        result_id = TestResult.result_id_from_custom_metric_name(name, 1, 1)
        if sys.version_info >= (3, 0) and isinstance(name, str):
            name = name.encode('utf-8')
        self.assertEqual(result_id, '__custom_%s:1:1'
                                    % hashlib.md5(name).hexdigest())

    def test_result_id_for_page(self):
        name = 'my page'
        result_id = TestResult.result_id_for_page(name, 1, 1)
        if sys.version_info >= (3, 0) and isinstance(name, str):
            name = name.encode('utf-8')
        self.assertEqual(result_id, '__li_page%s:1:1'
                                    % hashlib.md5(name).hexdigest())

    def test_result_id_for_url(self):
        url = 'http://example.com/'
        result_id = TestResult.result_id_for_url(url, 1, 1, method='GET',
                                                 status_code=200)
        if sys.version_info >= (3, 0) and isinstance(url, str):
            url = url.encode('utf-8')
        self.assertEqual(result_id, '__li_url%s:1:1:200:GET'
                                    % hashlib.md5(url).hexdigest())


class TestResourcesTestConfig(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_user_type_enums(self):
        self.assertEqual(TestConfig.SBU, 'sbu')
        self.assertEqual(TestConfig.VU, 'vu')

    def test_user_type_getter(self):
        c = TestConfig(self.client)
        self.assertEqual(c.user_type, TestConfig.SBU)

    def test_user_type_setter(self):
        c = TestConfig(self.client)
        c.user_type = TestConfig.VU
        self.assertEqual(c.user_type, TestConfig.VU)

    def test_user_type_setter_valueerror(self):
        c = TestConfig(self.client)

        def assign_bad_user_type():
            c.user_type = 'something bad'
        self.assertRaises(ValueError, assign_bad_user_type)

    def test_clone(self):
        name = 'Cloned Test Config'
        test_config = TestConfig(self.client)
        test_config_clone = test_config.clone(name)
        self.assertEqual(self.client.last_request_method, 'post')
        self.assertEqual(self.client.last_request_kwargs['data']['name'],
                         name)
        self.assertTrue(isinstance(test_config_clone, TestConfig))

    def test_update_with_dict(self):
        name_change = 'Test Config'
        client = MockClient(response_body={'name': name_change})
        test_config = TestConfig(client)
        test_config.update({'name': name_change})

        self.assertEqual(client.last_request_method, 'put')
        self.assertEqual(client.last_request_kwargs['data']['name'],
                         name_change)
        self.assertEqual(client.last_request_kwargs['headers']['Content-Type'],
                         'application/json')
        self.assertEqual(test_config.name, name_change)

    def test_update_with_attribute(self):
        name_change = 'Test Config'
        test_config = TestConfig(self.client)
        test_config.name = name_change
        test_config.update()

        self.assertEqual(self.client.last_request_method, 'put')
        self.assertEqual(self.client.last_request_kwargs['data']['name'],
                         name_change)
        self.assertEqual(self.client.last_request_kwargs['headers']['Content-Type'],
                         'application/json')
        self.assertEqual(test_config.name, name_change)


class TestResourcesUserScenario(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_get(self):
        client = MockClient(response_body={
            'data_stores': [{'id': 1}, {'id': 2}]
        })
        user_scenario = client.get_user_scenario(1)
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(user_scenario.data_stores, [1, 2])

    def test_clone(self):
        name = 'Cloned User Scenario'
        user_scenario = UserScenario(self.client)
        user_scenario_clone = user_scenario.clone(name)
        self.assertEqual(self.client.last_request_method, 'post')
        self.assertEqual(self.client.last_request_kwargs['data']['name'],
                         name)
        self.assertTrue(isinstance(user_scenario_clone, UserScenario))

    def test_update_with_dict(self):
        name_change = 'Test User Scenario'
        client = MockClient(response_body={'name': name_change})
        user_scenario = UserScenario(client)
        user_scenario.update({'name': name_change})

        self.assertEqual(client.last_request_method, 'put')
        self.assertEqual(client.last_request_kwargs['data']['name'],
                         name_change)
        self.assertEqual(client.last_request_kwargs['headers']['Content-Type'],
                         'application/json')
        self.assertEqual(user_scenario.name, name_change)

    def test_update_with_attribute(self):
        name_change = 'Test User Scenario'
        user_scenario = UserScenario(self.client)
        user_scenario.name = name_change
        user_scenario.update()

        self.assertEqual(self.client.last_request_method, 'put')
        self.assertEqual(self.client.last_request_kwargs['data']['name'],
                         name_change)
        self.assertEqual(self.client.last_request_kwargs['headers']['Content-Type'],
                         'application/json')
        self.assertEqual(user_scenario.name, name_change)


class TestResourcesUserScenarioValidation(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_is_done(self):
        validation = UserScenarioValidation(self.client)
        self.assertFalse(validation.is_done())
        self.assertEqual(self.client.last_request_method, 'get')

    def test_is_done_status_queued(self):
        self._check_is_done(UserScenarioValidation.STATUS_QUEUED, False)

    def test_is_done_status_initializing(self):
        self._check_is_done(UserScenarioValidation.STATUS_INITIALIZING, False)

    def test_is_done_status_running(self):
        self._check_is_done(UserScenarioValidation.STATUS_RUNNING, False)

    def test_is_done_status_finished(self):
        self._check_is_done(UserScenarioValidation.STATUS_FINISHED, True)

    def test_is_done_status_failed(self):
        self._check_is_done(UserScenarioValidation.STATUS_FAILED, True)

    def test_status_code_to_text(self):
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            UserScenarioValidation.STATUS_QUEUED), 'queued')
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            UserScenarioValidation.STATUS_INITIALIZING), 'initializing')
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            UserScenarioValidation.STATUS_RUNNING), 'running')
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            UserScenarioValidation.STATUS_FINISHED), 'finished')
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            UserScenarioValidation.STATUS_FAILED), 'failed')
        self.assertEqual(UserScenarioValidation.status_code_to_text(
            0xffffffff), 'unknown')

    def test_result_stream(self):
        validation = UserScenarioValidation(self.client)
        result_stream = validation.result_stream()
        self.assertTrue(isinstance(
            result_stream, _UserScenarioValidationResultStream))
        self.assertEqual(result_stream.validation, validation)

    def _check_is_done(self, status, expected):
        validation = UserScenarioValidation(self.client)
        validation.status = status
        self.assertEqual(validation.is_done(), expected)
        self.assertEqual(self.client.last_request_method, 'get')
