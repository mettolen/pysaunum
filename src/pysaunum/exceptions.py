"""Exceptions for pysaunum library."""

__all__ = [
    "SaunumException",
    "SaunumConnectionError",
    "SaunumCommunicationError",
    "SaunumTimeoutError",
    "SaunumInvalidDataError",
]


class SaunumException(Exception):
    """Base exception for pysaunum library."""


class SaunumConnectionError(SaunumException):
    """Exception raised when connection to sauna controller fails."""


class SaunumCommunicationError(SaunumException):
    """Exception raised when communication with sauna controller fails."""


class SaunumTimeoutError(SaunumException):
    """Exception raised when a request to sauna controller times out."""


class SaunumInvalidDataError(SaunumException):
    """Exception raised when invalid data is received from sauna controller."""
