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

import json
import unittest

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from loadimpact3.clients import Client
from loadimpact3.fields import IntegerField
from loadimpact3.resources import (
    DataStore, LoadZone, Resource, TestRun, UserScenario, UserScenarioValidation, TestRunMetric)


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

    def _get_nkwargs(self):
        nkwargs = {}
        response_body = self.kwargs.get('response_body')
        if response_body:
            if isinstance(response_body, dict):
                nkwargs = response_body
            elif isinstance(response_body, str):
                nkwargs = json.loads(response_body)

        return nkwargs

    def _requests_request(self, method, *args, **kwargs):
        self.last_request_method = method
        self.last_request_args = args
        self.last_request_kwargs = kwargs
        if isinstance(kwargs.get('data'), str):
            self.last_request_kwargs['data'] = json.loads(kwargs['data'])

        return MockRequestsResponse(status_code=self.response_status_code,
                                    **self._get_nkwargs())


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
        ds.sync = MagicMock()
        self.assertFalse(ds.has_conversion_finished())

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
        ds.sync = MagicMock()
        self.assertEqual(ds.has_conversion_finished(), expected)


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


class TestResourcesUserScenario(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_get(self):
        client = MockClient(response_body={'user_scenario': {
            'id': 1,
            'name': 'My test user scenario'
        }})
        user_scenario = client.get_user_scenario(1)
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(user_scenario.id, 1)
        self.assertEqual(user_scenario.name, 'My test user scenario')

    def test_update_with_dict(self):
        new_script = '---'
        client = MockClient(response_body={'user_scenario': {'script': new_script}})
        user_scenario = UserScenario(client)
        user_scenario = user_scenario.update_scenario(data={'script': new_script})

        self.assertEqual(client.last_request_method, 'put')
        self.assertEqual(client.last_request_kwargs['data']['script'],
                         new_script)
        self.assertEqual(user_scenario.script, new_script)


class TestResourcesUserScenarioValidation(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_is_done(self):
        client = MockClient(response_body={'user_scenario_validation': {
            'id': 1,
            'status': UserScenarioValidation.STATUS_QUEUED
        }})
        validation = client.get_user_scenario_validation(1)
        self.assertFalse(validation.is_done())
        self.assertEqual(client.last_request_method, 'get')

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

    def _check_is_done(self, status, expected):
        client = MockClient(response_body={'user_scenario_validation': {
            'id': 1
        }})
        validation = client.get_user_scenario_validation(1)
        validation.status = status
        self.assertEqual(validation.is_done(), expected)
        self.assertEqual(client.last_request_method, 'get')


class TestResourcesOrganization(unittest.TestCase):

    def test_list(self):
        client = MockClient(response_body={'organizations': [{
            'id': 1,
            'name': 'My org'
        }]})
        organizations = client.list_organizations()
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(organizations[0].id, 1)
        self.assertEqual(organizations[0].name, 'My org')


class TestResourcesProject(unittest.TestCase):

    def test_list(self):
        client = MockClient(response_body={'projects': [{
            'id': 1,
            'name': 'My project'
        }]})
        projects = client.list_organization_projects(1)
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(projects[0].id, 1)
        self.assertEqual(projects[0].name, 'My project')


class TestResourcesTest(unittest.TestCase):

    def test_get(self):
        client = MockClient(response_body={'test': {
            'id': 1,
            'name': 'test1',
            'config': {'config_key_1': 'config_val_1'},
            'last_test_run_id': 1001,
        }})
        test_ = client.get_test(1)
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(test_.id, 1)
        self.assertEqual(test_.name, 'test1')
        self.assertEqual(test_.last_test_run_id, 1001)

    def test_list(self):
        client = MockClient(response_body={'tests': [{
            'id': 1,
            'name': 'test1',
            'config': {'config_key_1': 'config_val_1'},
            'last_test_run_id': 1001,
        }]})
        tests = client.list_tests([1])
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(tests[0].id, 1)
        self.assertEqual(tests[0].name, 'test1')
        self.assertEqual(tests[0].last_test_run_id, 1001)


class TestResourcesTestRun(unittest.TestCase):

    def test_get(self):
        client = MockClient(response_body={'test_run': {
            'id': 1,
            'status': TestRun.STATUS_CREATED,
            'status_text': 'created',
        }})
        test_run = client.get_test_run(1)
        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(test_run.id, 1)
        self.assertEqual(test_run.status, TestRun.STATUS_CREATED)
        self.assertEqual(test_run.status_text, 'created')

    def test_create(self):
        client = MockClient(response_body={'test_run': {
            'id': 1,
            'status': TestRun.STATUS_CREATED,
            'status_text': 'created',
        }})
        test_run = client.create_test_run(1)
        self.assertEqual(client.last_request_method, 'post')
        self.assertEqual(test_run.id, 1)
        self.assertEqual(test_run.status, TestRun.STATUS_CREATED)
        self.assertEqual(test_run.status_text, 'created')


class TestRunResultsIds(unittest.TestCase):

    def test_list(self):
        client = MockClient(response_body={'test_run_result_ids': [{
            'type': 1,
            'offset': 2,
            'ids': {'_li_foo': '', '_li_bar': ''},
        }]})
        test_run = client.list_test_run_result_ids(1, data={'types': '1'})
        self.assertEqual(client.last_request_method, 'post')
        self.assertEqual(test_run[0].type, 1)
        self.assertEqual(test_run[0].offset, 2)
        self.assertEqual(len(test_run[0].ids), 2)


class TestStreaming(unittest.TestCase):
    @staticmethod
    def mocked_response_body(id_='__li_user_load_time:1', offset=1, data_len=1):
        """
        Generate the response body of a "test_run_results" API request.

        :param id_: metric name (including loadzone specifier, if needed).
        :param offset: offset of the returned results.
        :param data_len: number of data points to include.
        :return: dict with the response body.
        """
        return {
            "test_run_results": [
                {
                    "load_zone_id": 1,
                    "offset": offset,
                    "data": [{"timestamp": 1000 + i, "data": {"value": 2000 + i}}
                             for i in range(offset, offset+data_len)],
                    "id": id_.split(':')[0],
                    "sid": id_
                }]
        }

    def test_streaming_basic(self):
        """
        Test the streaming of results for 1 metric with 2 data points.
        """
        metric_id = TestRunMetric.result_id_from_name(TestRunMetric.ACTIVE_USERS, load_zone_id=1)
        client = MockClient(response_body=True)
        client._get_nkwargs = MagicMock(side_effect=[
            self.mocked_response_body(id_=metric_id, offset=1),
            self.mocked_response_body(id_=metric_id, offset=2),
            # Use two responses with the same information, combined with stream(post_polls=1)
            # so stream() is exhausted in a graceful way.
            self.mocked_response_body(id_=metric_id, offset=2),
        ])
        test_run = TestRun(client, id=1, status=TestRun.STATUS_FINISHED)
        test_run.sync = MagicMock()

        stream = test_run.result_stream([metric_id])
        for i, data in enumerate(stream(poll_rate=1, post_polls=1), 1):
            self.assertEqual(client.last_request_method, 'post')
            self.assertEqual(data[metric_id].value, 2000 + i)
        self.assertEqual(i, 2)
