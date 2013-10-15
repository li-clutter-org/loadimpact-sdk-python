# coding=utf-8

import json
import requests
import unittest

from loadimpact.clients import ApiTokenClient, Client
from loadimpact.exceptions import (
    ApiError, ConnectionError, HTTPError, TimeoutError)
from loadimpact.resources import (
    DataStore, Test, TestConfig, UserScenario, UserScenarioValidation)
from StringIO import StringIO


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
        if 'raise_exception_cls' in self.kwargs:
            raise self.kwargs.get('raise_exception_cls')
        nkwargs = {}
        if kwargs.get('data'):
            nkwargs = kwargs['data']
        return MockRequestsResponse(**nkwargs)


class MockApiTokenClient(ApiTokenClient):
    def __init__(self, api_token=None, **kwargs):
        super(MockApiTokenClient, self).__init__(api_token, **kwargs)
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
        url = MockClient.api_base_url + DataStore.resource_name

        self.assertEquals(client.last_request_method, 'post')
        self.assertEquals(client.last_request_args[0], url)
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

    def _exceptions_wrapping_all_http_verbs(self, raise_cls, expected_cls):
        client = MockClient(raise_exception_cls=raise_cls)
        self.assertRaises(expected_cls, client.delete, 'some-fake-path')
        self.assertRaises(expected_cls, client.get, 'some-fake-path')
        self.assertRaises(expected_cls, client.post, 'some-fake-path')
        self.assertRaises(expected_cls, client.put, 'some-fake-path')


class TestClientsApiTokenClient(unittest.TestCase):
    def test_api_token_in_delete_kwarg(self):
        self._api_token_in_put_kwarg('delete')

    def test_api_token_in_get_kwarg(self):
        self._api_token_in_put_kwarg('get')

    def test_api_token_in_post_kwargs(self):
        self._api_token_in_put_kwarg('post')

    def test_api_token_in_put_kwarg(self):
        self._api_token_in_put_kwarg('put')

    def _api_token_in_put_kwarg(self, method):
        api_token = 'test_token'
        client = MockApiTokenClient(api_token=api_token)
        getattr(client, method)('some-fake-path')
        self.assertEquals(client.last_request_kwargs['auth'], (api_token, ''))
