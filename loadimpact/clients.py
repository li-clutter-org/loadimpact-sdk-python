# coding=utf-8

__all__ = ['ApiTokenClient']


import httplib
import os
import platform
import requests

from exceptions import (
    ApiError, BadRequestError, ConflictError, ConnectionError, ClientError,
    ForbiddenError, HTTPError, GoneError, MethodNotAllowedError,
    MissingApiTokenError, NotFoundError, RateLimitError, ServerError,
    TimeoutError, UnauthorizedError)
from resources import (
    DataStore, TestConfig, UserScenario, UserScenarioValidation)
from urlparse import urljoin
from version import __version__


def requests_exceptions_handling(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError, e:
            raise ConnectionError(str(e))
        except requests.exceptions.HTTPError, e:
            raise HTTPError(str(e))
        except requests.exceptions.Timeout, e:
            raise TimeoutError(str(e))
        except requests.exceptions.RequestException, e:
            raise ApiError(str(e))
    return wrapper


class Client(object):
    """Base client class handling all communication with the Load Impact REST API,
    using simple API token based authentication."""

    api_base_url = 'https://api.loadimpact.com/v2/'
    default_timeout = 30
    error_classes = {
        400: BadRequestError,
        401: UnauthorizedError,
        403: ForbiddenError,
        404: NotFoundError,
        405: MethodNotAllowedError,
        409: ConflictError,
        410: GoneError,
        427: RateLimitError
    }
    library_versions = "python %s; requests %s" % (platform.python_version(),
                                                   requests.__version__)
    user_agent = "LoadImpactPythonSDK/%s (%s)" % (__version__, library_versions)

    def __init__(self, timeout=default_timeout, debug=False):
        self.timeout = timeout
        if debug:
            httplib.HTTPConnection.debuglevel = 1

    def create_data_store(self, data, file_object):
        return DataStore.create(self, data, file_object=file_object)

    def get_data_store(self, resource_id):
        return DataStore.get(self, resource_id)

    def list_data_stores(self):
        return DataStore.list(self)

    def create_test_config(self, data):
        return TestConfig.create(self, data)

    def get_test_config(self, resource_id):
        return TestConfig.get(self, resource_id)

    def list_test_configs(self):
        return TestConfig.list(self)

    def create_user_scenario(self, data):
        return UserScenario.create(self, data)

    def get_user_scenario(self, resource_id):
        return UserScenario.get(self, resource_id)

    def list_user_scenarios(self):
        return UserScenario.list(self)

    def create_user_scenario_validation(self, data):
        return UserScenarioValidation.create(self, data)

    @requests_exceptions_handling
    def delete(self, path, headers=None, params=None):
        """Make a DELETE request to the API.

        Args:
            path: Path of resource URI to where we're making the request.
            headers: Dict of headers to send with request.
            params: Dict with query string parameters.

        Returns:
            A requests response object on success.

        Raises:
            BadRequestError: Request was deemed formatted incorrectly by server.
            UnauthorizedError: API token is incorrect/not valid.
            ForbiddenError: Permission denied.
            APIError: Generic error from requests library.
        """
        url = urljoin(self.__class__.api_base_url, path)
        response = self._request('delete', url, headers=headers, params=params)
        return self._check_response(response)

    @requests_exceptions_handling
    def get(self, path, headers=None, params=None):
        """Make a GET request to the API.

        Args:
            path: Path of resource URI to where we're making the request.
            headers: Dict of headers to send with request.
            params: Dict with query string parameters.

        Returns:
            A requests response object on success.

        Raises:
            BadRequestError: Request was deemed formatted incorrectly by server.
            UnauthorizedError: API token is incorrect/not valid.
            ForbiddenError: Permission denied.
            APIError: Generic error from requests library.
        """
        url = urljoin(self.__class__.api_base_url, path)
        response = self._request('get', url, headers=headers, params=params)
        return self._check_response(response)

    @requests_exceptions_handling
    def post(self, path, headers=None, params=None, data=None,
             file_object=None):
        """Make a POST request to the API.

        Args:
            path: Path of resource URI to where we're making the request.
            headers: Dict of headers to send with request.
            params: Dict with query string parameters.
            data: Body data to send with request.
            file_object: File object with data to send as file.

        Returns:
            A requests response object on success.

        Raises:
            BadRequestError: Request was deemed formatted incorrectly by server.
            UnauthorizedError: API token is incorrect/not valid.
            ForbiddenError: Permission denied.
            APIError: Generic error from requests library.
        """
        url = urljoin(self.__class__.api_base_url, path)
        files = {'file': file_object} if file_object else None
        response = self._request('post', url, headers=headers, params=params,
                                 data=data, files=files)
        return self._check_response(response)

    @requests_exceptions_handling
    def put(self, path, headers=None, params=None, data=None, file_object=None):
        """Make a PUT request to the API.

        Args:
            path: Path of resource URI to where we're making the request.
            headers: Dict of headers to send with request.
            params: Dict with query string parameters.
            data: Body data to send with request.
            file_object: File object with data to send as file.

        Returns:
            A requests response object on success.

        Raises:
            BadRequestError: Request was deemed formatted incorrectly by server.
            UnauthorizedError: API token is incorrect/not valid.
            ForbiddenError: Permission denied.
            APIError: Generic error from requests library.
        """
        url = urljoin(self.__class__.api_base_url, path)
        files = {'file': file_object} if file_object else None
        response = self._request('put', url, headers=headers, params=params,
                                 data=data, files=files)
        return self._check_response(response)

    def _check_response(self, response):
        status_code = response.status_code

        if 399 < status_code and 600 > status_code:
            try:
                error = response.json()
                msg = u"%s (%s)" % (error['message'], response.url)
            except KeyError:
                msg = response.url

            if status_code in self.__class__.error_classes:
                raise self.__class__.error_classes[status_code](
                    msg, response=response)
            elif 399 < response.status_code and 500 > response.status_code:
                raise ClientError(msg, response=response)
            elif 499 < response.status_code and 600 > response.status_code:
                raise ServerError(msg, response=response)

        return response

    def _prepare_requests_kwargs(self, kwargs):
        return kwargs

    def _request(self, method, *args, **kwargs):
        headers = {'user-agent': self.__class__.user_agent}
        if 'headers' not in kwargs:
            kwargs['headers'] = headers
        else:
            if not kwargs['headers']:
                kwargs['headers'] = {}
            kwargs['headers']['user-agent'] = headers['user-agent']
        kwargs['timeout'] = self.timeout
        kwargs = self._prepare_requests_kwargs(kwargs)
        return self._requests_request(method, *args, **kwargs)

    def _requests_request(self, method, *args, **kwargs):
        return getattr(requests, method)(*args, **kwargs)


class ApiTokenClient(Client):
    """Client class handling all communication with the Load Impact REST API,
    using simple API token based authentication."""

    def __init__(self, api_token=None, *args, **kwargs):
        super(ApiTokenClient, self).__init__(*args, **kwargs)
        if not api_token:
            try:
                self.api_token = os.environ['LOADIMPACT_API_TOKEN']
            except KeyError:
                raise MissingApiTokenError(u"An API token must be specified "
                                           u"either as the first argument to "
                                           u"ApiClient or by setting the "
                                           u"environment variable "
                                           u"LOADIMPACT_API_TOKEN.")
        self.api_token = api_token

    def _prepare_requests_kwargs(self, kwargs):
        kwargs['auth'] = (self.api_token, '')
        return kwargs
