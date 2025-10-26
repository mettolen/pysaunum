"""Tests for exceptions."""

import pytest

from pysaunum import (
    SaunumCommunicationError,
    SaunumConnectionError,
    SaunumException,
    SaunumInvalidDataError,
    SaunumTimeoutError,
)


def test_saunum_exception():
    """Test basic SaunumException."""
    error = SaunumException("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_saunum_connection_error():
    """Test SaunumConnectionError."""
    error = SaunumConnectionError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, SaunumException)
    assert isinstance(error, Exception)


def test_saunum_communication_error():
    """Test SaunumCommunicationError."""
    error = SaunumCommunicationError("Communication failed")
    assert str(error) == "Communication failed"
    assert isinstance(error, SaunumException)
    assert isinstance(error, Exception)


def test_saunum_timeout_error():
    """Test SaunumTimeoutError."""
    error = SaunumTimeoutError("Request timed out")
    assert str(error) == "Request timed out"
    assert isinstance(error, SaunumException)
    assert isinstance(error, Exception)


def test_saunum_invalid_data_error():
    """Test SaunumInvalidDataError."""
    error = SaunumInvalidDataError("Invalid data received")
    assert str(error) == "Invalid data received"
    assert isinstance(error, SaunumException)
    assert isinstance(error, Exception)


def test_exception_inheritance_chain():
    """Test exception inheritance hierarchy."""
    # All custom exceptions should inherit from SaunumException
    exceptions: list[type[SaunumException]] = [
        SaunumConnectionError,
        SaunumCommunicationError,
        SaunumTimeoutError,
        SaunumInvalidDataError,
    ]

    for exception_class in exceptions:
        # Check class inheritance
        assert issubclass(exception_class, SaunumException)
        assert issubclass(exception_class, Exception)

        # Check instance inheritance
        instance = exception_class("test")
        assert isinstance(instance, SaunumException)
        assert isinstance(instance, Exception)


def test_exception_with_cause():
    """Test exceptions with cause chaining."""
    original_error = ValueError("Original error")

    try:
        raise SaunumConnectionError("Connection error") from original_error
    except SaunumConnectionError as e:
        assert str(e) == "Connection error"
        assert e.__cause__ is original_error
        assert isinstance(e.__cause__, ValueError)


def test_exception_without_message():
    """Test exceptions can be raised without message."""
    error = SaunumException()
    assert str(error) == ""

    # Test that we can raise and catch
    with pytest.raises(SaunumException):
        raise SaunumException()
