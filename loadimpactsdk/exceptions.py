# coding=utf-8

__all__ = ['ApiError', 'MissingApiTokenError', 'ResponseParseError',
           'ConnectionError', 'TimeoutError', 'HTTPError', 'ClientError',
           'BadRequestError', 'UnauthorizedError', 'ForbiddenError',
           'NotFoundError', 'MethodNotAllowedError', 'ConflictError',
           'GoneError', 'RateLimitError', 'ServerError']


class ApiError(Exception):
    """All Load Impact API exceptions derive from this class."""


class MissingApiTokenError(ApiError):
    """Raised when AI client is created and an API token can't be found."""


class CoercionError(ApiError):
    """Raised when a resource field value coercion fails."""


class ResponseParseError(ApiError):
    """Raised when parsing of API response fails."""


class ConnectionError(ApiError):
    """Raised when a TCP connection error is encountered."""


class TimeoutError(ApiError):
    """Raised when a TCP connection timeout is encountered."""


class HTTPError(ApiError):
    """All HTTP exception classes derive from this base class."""

    def __init__(self, msg=None, response=None):
        super(HTTPError, self).__init__(msg)
        self.response = response


class ClientError(HTTPError):
    """Raised when 4xx HTTP response code is encountered with no specialized
    exception class.
    """


class BadRequestError(ClientError):
    """Raised when 400 HTTP status code is encountered."""


class UnauthorizedError(ClientError):
    """Raised when 401 HTTP status code is encountered."""


class ForbiddenError(ClientError):
    """Raised when 403 HTTP status code is encountered."""


class NotFoundError(ClientError):
    """Raised when 404 HTTP status code is encountered."""


class MethodNotAllowedError(ClientError):
    """Raised when 405 HTTP status code is encountered."""


class ConflictError(ClientError):
    """Raised when 409 HTTP status code is encountered."""


class GoneError(ClientError):
    """Raised when 410 HTTP status code is encountered."""


class RateLimitError(ClientError):
    """Raised when 427 HTTP status code is encountered."""


class ServerError(HTTPError):
    """Raised when 5xx HTTP response code is encountered with no specialized
    exception class.
    """
