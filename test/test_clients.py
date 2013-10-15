# coding=utf-8

import requests
import unittest

from loadimpact.clients import ApiTokenClient, Client
from loadimpact.exceptions import (
    ApiError, ConnectionError, HTTPError, TimeoutError)


class MockRequestsResponse(object):
    def __init__(self, status_code=200):
        self.status_code = status_code


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
        return MockRequestsResponse()


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
