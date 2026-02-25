"""Shared test fixtures for pysaunum tests."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_modbus_client() -> Iterator[MagicMock]:
    """Mock the AsyncModbusTcpClient."""
    with patch("pysaunum.client.AsyncModbusTcpClient") as mock_client:
        # Set up the mock client instance
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Configure the connected property
        mock_instance.connected = False

        # Mock successful connection
        mock_instance.connect = AsyncMock(return_value=None)
        mock_instance.close = MagicMock(return_value=None)

        # Mock successful read operations
        mock_instance.read_holding_registers = AsyncMock()

        # Mock successful write operation
        mock_write_result = MagicMock()
        mock_write_result.isError.return_value = False
        mock_instance.write_register = AsyncMock(return_value=mock_write_result)

        yield mock_instance
