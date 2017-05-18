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
import requests
import unittest

from loadimpact3.clients import ApiTokenClient, Client
from loadimpact3.exceptions import (
    ApiError, BadRequestError, ClientError, ConnectionError,
    ForbiddenError, GoneError, HTTPError, MethodNotAllowedError,
    MissingApiTokenError, NotFoundError, RateLimitError, ServerError,
    TimeoutError, UnauthorizedError)
from loadimpact3.resources import DataStore

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class MockRequestsResponse(object):
    def __init__(self, expecting_list=False, resource_type='object', status_code=200, **kwargs):
        self.expecting_list = expecting_list
        self.url = 'http://example.com/'
        self.status_code = status_code
        self.text = ''
        self.resource_type = resource_type
        self.kwargs = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    def json(self):
        return {self.resource_type: [self.kwargs]} if self.expecting_list else {self.resource_type: self.kwargs}


class MockClient(Client):
    def __init__(self, expecting_list=False, resource_type=None, timeout=Client.default_timeout,
                 **kwargs):
        super(MockClient, self).__init__(timeout=timeout)
        self.expecting_list = expecting_list
        self.resource_type = resource_type
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
        if 'raise_exception_cls' in self.kwargs:
            raise self.kwargs.get('raise_exception_cls')
        nkwargs = {}
        if kwargs.get('data'):
            if isinstance(kwargs['data'], dict):
                nkwargs = kwargs['data']
            elif isinstance(kwargs['data'], str):
                nkwargs = json.loads(kwargs['data'])
        return MockRequestsResponse(expecting_list=self.expecting_list, resource_type=self.resource_type,
                                    **nkwargs)


class MockApiTokenClient(ApiTokenClient):
    def __init__(self, api_token=None, **kwargs):
        super(MockApiTokenClient, self).__init__(api_token=api_token, **kwargs)
        self.kwargs = kwargs
        self.last_request_method = None
        self.last_request_args = None
        self.last_request_kwargs = None

    def _requests_request(self, method, *args, **kwargs):
        self.last_request_method = method
        self.last_request_args = args
        self.last_request_kwargs = kwargs
        return MockRequestsResponse()


class MockApiTokenFromEnvClient(MockApiTokenClient):
    def __init__(self, api_token_env=None, **kwargs):
        self.api_token_env = api_token_env
        super(MockApiTokenFromEnvClient, self).__init__(api_token=None,
                                                        **kwargs)

    def _get_api_token_from_environment(self):
        return self.api_token_env


class MockApiTokenFromEnvErrorClient(MockApiTokenClient):
    def _get_api_token_from_environment(self):
        raise KeyError


class TestClientsClient(unittest.TestCase):
    def test_timeout(self):
        timeout = 12345
        client = MockClient(timeout=timeout)
        client.get('some-fake-path')
        self.assertEqual(client.last_request_kwargs['timeout'], timeout)

    def test_create_data_store(self):
        client = MockClient(resource_type='data_store')

        data = {
            'name': 'Test Data Store',
            'project_id': 1,
            'fromline': 0,
            'separator': 'comma',
            'delimeter': 'tab',
            'quotechar': 'double',
            'file': ''
        }
        csv = 'column1,column2,column3'
        data_store = client.create_data_store(data, StringIO(csv))

        self.assertEqual(client.last_request_method, 'post')
        self.assertEqual(client.last_request_kwargs['data']['name'],
                         data['name'])
        self.assertEqual(client.last_request_kwargs['data']['fromline'],
                         data['fromline'])
        self.assertEqual(client.last_request_kwargs['data']['separator'],
                         data['separator'])
        self.assertEqual(client.last_request_kwargs['data']['delimeter'],
                         data['delimeter'])
        self.assertEqual(client.last_request_kwargs['files']['file'].read(),
                         StringIO(csv).read())
        self.assertEqual(data_store.name, data['name'])
        self.assertEqual(data_store.status, DataStore.STATUS_QUEUED)
        self.assertEqual(data_store.rows, 0)

    def test_get_data_store(self):
        client = MockClient(resource_type='data_store')
        data_store = client.get_data_store(1)

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(data_store.id, 0)  # ID = 0 by default
        self.assertEqual(data_store.name, '')
        self.assertEqual(data_store.status, DataStore.STATUS_QUEUED)
        self.assertEqual(data_store.rows, 0)

    def test_list_data_stores(self):
        client = MockClient(resource_type='data_stores', expecting_list=True)
        data_stores = client.list_data_stores(project_id=1)

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(len(data_stores), 1)
        self.assertEqual(data_stores[0].id, 0)  # ID = 0 by default
        self.assertEqual(data_stores[0].name, '')
        self.assertEqual(data_stores[0].status, DataStore.STATUS_QUEUED)
        self.assertEqual(data_stores[0].rows, 0)

    def test_create_user_scenario(self):
        client = MockClient(resource_type='user_scenario')
        data = {
            'name': 'Test User Scenario',
            'script': 'log.info("Hello World!")',
            'project_id': 1
        }
        user_scenario = client.create_user_scenario(data)

        self.assertEqual(client.last_request_method, 'post')
        self.assertEqual(client.last_request_kwargs['data']['name'],
                         data['name'])
        self.assertEqual(client.last_request_kwargs['data']['script'],
                         data['script'])
        self.assertEqual(user_scenario.name, data['name'])
        self.assertEqual(user_scenario.script, data['script'])

    def test_get_user_scenario(self):
        client = MockClient(resource_type='user_scenario')
        user_scenario = client.get_user_scenario(1)

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(user_scenario.id, 0)  # ID = 0 by default
        self.assertEqual(user_scenario.name, '')
        self.assertEqual(user_scenario.script, '')

    def test_list_user_scenarios(self):
        client = MockClient(expecting_list=True, resource_type='user_scenarios')
        user_scenarios = client.list_user_scenarios(project_id=1)

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(len(user_scenarios), 1)
        self.assertEqual(user_scenarios[0].id, 0)  # ID = 0 by default
        self.assertEqual(user_scenarios[0].name, '')
        self.assertEqual(user_scenarios[0].script, '')

    def test_create_user_scenario_validation(self):
        client = MockClient(resource_type='user_scenario_validation')
        data = {
            'user_scenario_id': 1
        }
        validation = client.create_user_scenario_validation(data)

        self.assertEqual(client.last_request_method, 'post')
        self.assertEqual(client.last_request_kwargs['data']['user_scenario_id'],
                         data['user_scenario_id'])
        self.assertEqual(validation.user_scenario_id, data['user_scenario_id'])

    def test_list_organizations(self):
        client = MockClient(resource_type='organizations', expecting_list=True)
        organizations = client.list_organizations()

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(len(organizations), 1)
        self.assertEqual(organizations[0].id, 0)  # ID = 0 by default
        self.assertEqual(organizations[0].name, '')

    def test_list_projects_for_organization(self):
        client = MockClient(resource_type='projects', expecting_list=True)
        projects = client.list_organization_projects(1)

        self.assertEqual(client.last_request_method, 'get')
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].id, 0)  # ID = 0 by default
        self.assertEqual(projects[0].name, '')

    def test__check_response_200(self):
        client = MockClient()
        r = MockRequestsResponse(status_code=200, message='OK')
        self.assertEqual(client._check_response(r), r)

    def test__check_response_300(self):
        client = MockClient()
        r = MockRequestsResponse(status_code=300, message='Redirection')
        self.assertEqual(client._check_response(r), r)

    def test__check_response_400(self):
        self._check_response_exception(BadRequestError, 400, 'Bad request')

    def test__check_response_400_no_error_msg(self):
        client = MockClient()
        r = MockRequestsResponse(status_code=400)
        self.assertRaises(BadRequestError, client._check_response, r)

    def test__check_response_401(self):
        self._check_response_exception(UnauthorizedError, 401, 'Unauthorized')

    def test__check_response_402(self):
        self._check_response_exception(ClientError, 402, 'Payment required')

    def test__check_response_403(self):
        self._check_response_exception(ForbiddenError, 403, 'Forbidden')

    def test__check_response_404(self):
        self._check_response_exception(NotFoundError, 404, 'Not found')

    def test__check_response_405(self):
        self._check_response_exception(MethodNotAllowedError, 405,
                                       'Method not allowed')

    def test__check_response_410(self):
        self._check_response_exception(GoneError, 410, 'Gone')

    def test__check_response_427(self):
        self._check_response_exception(RateLimitError, 427, 'Rate limited')

    def test__check_response_500(self):
        self._check_response_exception(ServerError, 500, 'Internal Server Error')

    def test_requests_httperror_exceptions_wrapping(self):
        self._exceptions_wrapping_all_http_verbs(
            requests.exceptions.HTTPError, HTTPError)

    def test_requests_connectionerror_exceptions_wrapping(self):
        self._exceptions_wrapping_all_http_verbs(
            requests.exceptions.ConnectionError, ConnectionError)

    def test_requests_timeouterror_exceptions_wrapping(self):
        self._exceptions_wrapping_all_http_verbs(
            requests.exceptions.Timeout, TimeoutError)

    def test_requests_requestexception_exceptions_wrapping(self):
        self._exceptions_wrapping_all_http_verbs(
            requests.exceptions.RequestException, ApiError)

    def _check_response_exception(self, raise_cls, status_code, message):
        client = MockClient()
        r = MockRequestsResponse(status_code=status_code, message=message)
        self.assertRaises(raise_cls, client._check_response, r)

    def _exceptions_wrapping_all_http_verbs(self, raise_cls, expected_cls):
        client = MockClient(raise_exception_cls=raise_cls)
        self.assertRaises(expected_cls, client.delete, 'some-fake-path')
        self.assertRaises(expected_cls, client.get, 'some-fake-path')
        self.assertRaises(expected_cls, client.post, 'some-fake-path')
        self.assertRaises(expected_cls, client.put, 'some-fake-path')


class TestClientsApiTokenClient(unittest.TestCase):
    def test_missing_api_token_exception(self):
        self.assertRaises(MissingApiTokenError, MockApiTokenFromEnvErrorClient)

    def test_api_token_in_env(self):
        api_token = 'test_token'
        client = MockApiTokenFromEnvClient(api_token_env=api_token)
        client.get('some-fake-path')
        self.assertEqual(client.last_request_kwargs['auth'], (api_token, ''))

    def test_api_token_in_delete_kwarg(self):
        self._check_api_token_in_kwarg('delete')

    def test_api_token_in_get_kwarg(self):
        self._check_api_token_in_kwarg('get')

    def test_api_token_in_post_kwargs(self):
        self._check_api_token_in_kwarg('post')

    def test_api_token_in_put_kwarg(self):
        self._check_api_token_in_kwarg('put')

    def _check_api_token_in_kwarg(self, method):
        api_token = 'test_token'
        client = MockApiTokenClient(api_token=api_token)
        getattr(client, method)('some-fake-path')
        self.assertEqual(client.last_request_kwargs['auth'], (api_token, ''))
