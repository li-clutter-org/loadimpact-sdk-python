# coding=utf-8

import requests
import unittest

from loadimpactsdk.clients import ApiTokenClient
from loadimpactsdk.exceptions import ApiError, ConnectionError, HTTPError, TimeoutError


class MockApiTokenClient(ApiTokenClient):
    def __init__(self, **kwargs):
        super(MockApiTokenClient, self).__init__('FAKE_API_TOKEN_FOR_TESTING')
        self.kwargs = kwargs

    def _request(self, method, *args, **kwargs):
        if 'raise_exception_cls' in self.kwargs:
            raise self.kwargs.get('raise_exception_cls')


class TestClientsApiTokenClient(unittest.TestCase):
    def test_requests_httperror_exceptions_wrapping(self):
        client = MockApiTokenClient(
            raise_exception_cls=requests.exceptions.HTTPError)
        with self.assertRaises(HTTPError):
            client.get('some-fake-path')
        with self.assertRaises(HTTPError):
            client.post('some-fake-path')
        with self.assertRaises(HTTPError):
            client.put('some-fake-path')
        with self.assertRaises(HTTPError):
            client.delete('some-fake-path')

    def test_requests_connectionerror_exceptions_wrapping(self):
        client = MockApiTokenClient(
            raise_exception_cls=requests.exceptions.ConnectionError)
        with self.assertRaises(ConnectionError):
            client.get('some-fake-path')
        with self.assertRaises(ConnectionError):
            client.post('some-fake-path')
        with self.assertRaises(ConnectionError):
            client.put('some-fake-path')
        with self.assertRaises(ConnectionError):
            client.delete('some-fake-path')

    def test_requests_timeouterror_exceptions_wrapping(self):
        client = MockApiTokenClient(
            raise_exception_cls=requests.exceptions.Timeout)
        with self.assertRaises(TimeoutError):
            client.get('some-fake-path')
        with self.assertRaises(TimeoutError):
            client.post('some-fake-path')
        with self.assertRaises(TimeoutError):
            client.put('some-fake-path')
        with self.assertRaises(TimeoutError):
            client.delete('some-fake-path')

    def test_requests_requestexception_exceptions_wrapping(self):
        client = MockApiTokenClient(
            raise_exception_cls=requests.exceptions.RequestException)
        with self.assertRaises(ApiError):
            client.get('some-fake-path')
        with self.assertRaises(ApiError):
            client.post('some-fake-path')
        with self.assertRaises(ApiError):
            client.put('some-fake-path')
        with self.assertRaises(ApiError):
            client.delete('some-fake-path')
