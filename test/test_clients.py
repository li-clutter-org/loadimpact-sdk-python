# coding=utf-8

import json
import os
import requests
import unittest

from loadimpact.clients import ApiTokenClient, Client
from loadimpact.exceptions import (
    ApiError, BadRequestError, ClientError, ConflictError, ConnectionError,
    ForbiddenError, GoneError, HTTPError, MethodNotAllowedError,
    MissingApiTokenError, NotFoundError, RateLimitError, ServerError,
    TimeoutError, UnauthorizedError)
from loadimpact.resources import (
    DataStore, Test, TestConfig, UserScenario, UserScenarioValidation)
from StringIO import StringIO


class MockRequestsResponse(object):
    def __init__(self, expecting_list=False, status_code=200, **kwargs):
        self.expecting_list = expecting_list
        self.url = 'http://example.com/'
        self.status_code = status_code
        self.kwargs = kwargs
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def json(self):
        d = self.kwargs
        return [d] if self.expecting_list else d


class MockClient(Client):
    def __init__(self, expecting_list=False, timeout=Client.default_timeout,
                 **kwargs):
        super(MockClient, self).__init__(timeout=timeout)
        self.expecting_list = expecting_list
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
        return MockRequestsResponse(expecting_list=self.expecting_list,
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


class TestClientsClient(unittest.TestCase):
    def test_timeout(self):
        timeout = 12345
        client = MockClient(timeout=timeout)
        client.get('some-fake-path')
        self.assertEquals(client.last_request_kwargs['timeout'], timeout)

    def test_create_data_store(self):
        client = MockClient()
        data = {
            'name': 'Test Data Store',
            'fromline': 0,
            'separator': 'comma',
            'delimeter': 'double'
        }
        csv = 'column1,column2,column3'
        data_store = client.create_data_store(data, StringIO(csv))

        self.assertEquals(client.last_request_method, 'post')
        self.assertEquals(client.last_request_kwargs['data']['name'],
                          data['name'])
        self.assertEquals(client.last_request_kwargs['data']['fromline'],
                          data['fromline'])
        self.assertEquals(client.last_request_kwargs['data']['separator'],
                          data['separator'])
        self.assertEquals(client.last_request_kwargs['data']['delimeter'],
                          data['delimeter'])
        self.assertEquals(client.last_request_kwargs['files']['file'].read(),
                          StringIO(csv).read())
        self.assertEquals(data_store.name, data['name'])
        self.assertEquals(data_store.status, DataStore.STATUS_QUEUED)
        self.assertEquals(data_store.rows, 0)

    def test_get_data_store(self):
        client = MockClient()
        data_store = client.get_data_store(1)

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(data_store.id, 0)  # ID = 0 by default
        self.assertEquals(data_store.name, '')
        self.assertEquals(data_store.status, DataStore.STATUS_QUEUED)
        self.assertEquals(data_store.rows, 0)

    def test_list_data_stores(self):
        client = MockClient(expecting_list=True)
        data_stores = client.list_data_stores()

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(len(data_stores), 1)
        self.assertEquals(data_stores[0].id, 0)  # ID = 0 by default
        self.assertEquals(data_stores[0].name, '')
        self.assertEquals(data_stores[0].status, DataStore.STATUS_QUEUED)
        self.assertEquals(data_stores[0].rows, 0)

    def test_create_test_config(self):
        client = MockClient()
        data = {
            'name': 'Test Config',
            'url': 'http://example.com/',
            'config': {
                "load_schedule": [{"users": 10, "duration": 10}],
                "tracks": [{
                    "clips": [{
                        "user_scenario_id": 1, "percent": 100
                    }],
                    "loadzone": 11
                }]
            }
        }
        test_config = client.create_test_config(data)

        self.assertEquals(client.last_request_method, 'post')
        self.assertEquals(client.last_request_kwargs['data']['name'],
                          data['name'])
        self.assertEquals(client.last_request_kwargs['data']['url'],
                          data['url'])
        self.assertEquals(client.last_request_kwargs['data']['config'],
                          data['config'])
        self.assertEquals(test_config.name, data['name'])
        self.assertEquals(test_config.url, data['url'])
        self.assertEquals(test_config.config, data['config'])

    def test_get_test_config(self):
        client = MockClient()
        test_config = client.get_test_config(1)

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(test_config.id, 0)  # ID = 0 by default
        self.assertEquals(test_config.name, '')
        self.assertEquals(test_config.url, '')
        self.assertEquals(test_config.config, {})

    def test_list_test_configs(self):
        client = MockClient(expecting_list=True)
        test_configs = client.list_test_configs()

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(len(test_configs), 1)
        self.assertEquals(test_configs[0].id, 0)  # ID = 0 by default
        self.assertEquals(test_configs[0].name, '')
        self.assertEquals(test_configs[0].url, '')
        self.assertEquals(test_configs[0].config, {})

    def test_create_user_scenario(self):
        client = MockClient()
        data = {
            'name': 'Test User Scenario',
            'load_script': 'log.info("Hello World!")',
            'data_stores': []
        }
        user_scenario = client.create_user_scenario(data)

        self.assertEquals(client.last_request_method, 'post')
        self.assertEquals(client.last_request_kwargs['data']['name'],
                          data['name'])
        self.assertEquals(client.last_request_kwargs['data']['load_script'],
                          data['load_script'])
        self.assertEquals(client.last_request_kwargs['data']['data_stores'],
                          data['data_stores'])
        self.assertEquals(user_scenario.name, data['name'])
        self.assertEquals(user_scenario.load_script, data['load_script'])
        self.assertEquals(user_scenario.data_stores, data['data_stores'])

    def test_get_user_scenario(self):
        client = MockClient()
        user_scenario = client.get_user_scenario(1)

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(user_scenario.id, 0)  # ID = 0 by default
        self.assertEquals(user_scenario.name, '')
        self.assertEquals(user_scenario.script_type, '')
        self.assertEquals(user_scenario.load_script, '')
        self.assertEquals(user_scenario.data_stores, [])

    def test_list_user_scenarios(self):
        client = MockClient(expecting_list=True)
        user_scenarios = client.list_user_scenarios()

        self.assertEquals(client.last_request_method, 'get')
        self.assertEquals(len(user_scenarios), 1)
        self.assertEquals(user_scenarios[0].id, 0)  # ID = 0 by default
        self.assertEquals(user_scenarios[0].name, '')
        self.assertEquals(user_scenarios[0].script_type, '')
        self.assertEquals(user_scenarios[0].load_script, '')
        self.assertEquals(user_scenarios[0].data_stores, [])

    def test_create_user_scenario_validation(self):
        client = MockClient()
        data = {
            'user_scenario_id': 1
        }
        validation = client.create_user_scenario_validation(data)

        self.assertEquals(client.last_request_method, 'post')
        self.assertEquals(client.last_request_kwargs['data']['user_scenario_id'],
                          data['user_scenario_id'])
        self.assertEquals(validation.user_scenario_id, data['user_scenario_id'])

    def test__check_response_200(self):
        client = MockClient()
        r = MockRequestsResponse(status_code=200, message='OK')
        self.assertEquals(client._check_response(r), r)

    def test__check_response_300(self):
        client = MockClient()
        r = MockRequestsResponse(status_code=300, message='Redirection')
        self.assertEquals(client._check_response(r), r)

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
        self.assertRaises(MissingApiTokenError, MockApiTokenClient,
                          api_token=None)

    def test_api_token_in_env(self):
        api_token = 'test_token'
        old = os.environ.get('LOADIMPACT_API_TOKEN')
        os.environ['LOADIMPACT_API_TOKEN'] = api_token
        client = MockApiTokenClient(api_token=None)
        client.get('some-fake-path')
        self.assertEquals(client.last_request_kwargs['auth'], (api_token, ''))
        if old:
            os.environ['LOADIMPACT_API_TOKEN'] = old
        else:
            del os.environ['LOADIMPACT_API_TOKEN']

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
        self.assertEquals(client.last_request_kwargs['auth'], (api_token, ''))
